import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(page_title="UV Leakage Simulator", layout="wide")
st.title("☀️ UV Leakage Simulator")

# セッション状態の初期化
if 'snapshots' not in st.session_state:
    st.session_state.snapshots = []

# --- Sidebar Inputs ---
st.sidebar.header("Design Parameters")

# 🌟 追加機能: ShujiモデルとHuangモデルの切り替え
model_choice = st.sidebar.radio(
    "Leakage Calculation Model", 
    ["Shuji Model (Diagonal Path)", "Huang Model (Center Path)"]
)
st.sidebar.markdown("---")

# 入力モードの切り替え
input_mode = st.sidebar.radio("Input Mode", [
    "1. Manual (t & D)", 
    "2. Direct AR Input",
    "3. Optimize Holes (Target C)",
    "4. Trade-off (Leakage vs Conductance)"
])

st.sidebar.markdown("---")

# ==========================================
# ガスパラメータ (Mode 3 & 4 で共通使用)
# ==========================================
if input_mode in ["3. Optimize Holes (Target C)", "4. Trade-off (Leakage vs Conductance)"]:
    with st.sidebar.expander("⚙️ Gas Parameters"):
        T = st.number_input("Temperature [K]", value=293.0)
        P_avg = st.number_input("Pressure [Pa]", value=1.1)
        M_val = st.number_input("Molar Mass [g/mol]", value=70.9)
        mu_val = st.number_input("Viscosity [1e-5 Pa s]", value=1.32)

    R_gas = 8.314
    M = M_val * 1e-3
    mu = mu_val * 1e-5
    v_bar = np.sqrt((8 * R_gas * T) / (np.pi * M))

    # コンダクタンス計算の共通関数
    def calc_single_conductance(D_m, t_m):
        A = np.pi * (D_m**2) / 4
        alpha = 1 / (1 + (3 * t_m) / (4 * D_m))
        C_mol = 0.25 * A * v_bar * alpha
        C_visc = (np.pi * (D_m**4) * P_avg) / (128 * mu * t_m)
        return 1 / ((1 / C_mol) + (1 / C_visc))

# ==========================================
# 漏洩率計算の共通関数 (モデル切り替え対応)
# ==========================================
def calculate_leakage(ar):
    if model_choice == "Shuji Model (Diagonal Path)":
        return 100 / (1 + ar**2)
    else:
        return 100 / (1 + 4 * ar**2)

# ==========================================
# Mode 1 & 2: シンプルな単孔漏洩率の計算
# ==========================================
if input_mode in ["1. Manual (t & D)", "2. Direct AR Input"]:
    if input_mode == "1. Manual (t & D)":
        t_input = st.sidebar.number_input("Aperture Thickness (t) [mm]", value=10.0, step=0.1)
        D_input = st.sidebar.number_input("Hole Diameter (D) [mm]", value=2.5, step=0.1)
        final_AR = t_input / D_input if D_input > 0 else 0
    else:
        # AR=0 を許可
        final_AR = st.sidebar.number_input("Aspect Ratio (AR)", value=4.0, min_value=0.0, step=0.1)
        st.sidebar.info(f"Using AR = {final_AR}")

    leakage_rate = calculate_leakage(final_AR)

    st.subheader("Current Performance Analysis (Single Hole)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Aspect Ratio (AR)", f"{final_AR:.2f}")
    c2.metric("Single UV Leakage", f"{leakage_rate:.2f} %")
    c3.metric("UV Blocking Rate", f"{100-leakage_rate:.2f} %")

    if st.button("📸 Take Snapshot"):
        st.session_state.snapshots.append({"Mode": "Simple", "AR": round(final_AR, 2), "UV Leakage (%)": round(leakage_rate, 4)})
        st.success(f"Snapshot saved: AR={final_AR:.2f}")

    st.subheader("UV Leakage Trend vs. AR")
    ar_range = np.linspace(0.0, 20, 100)
    leakage_trend = calculate_leakage(ar_range)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ar_range, y=leakage_trend, mode='lines', name=model_choice, line=dict(color='royalblue')))
    fig.add_trace(go.Scatter(x=[final_AR], y=[leakage_rate], mode='markers+text', name='Current Point', text=[f"AR={final_AR:.1f}"], textposition="top right", marker=dict(color='red', size=12)))
    fig.update_layout(xaxis_title="Aspect Ratio (AR)", yaxis_title="Single Hole UV Leakage Rate (%)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# Mode 3: 目標コンダクタンスから穴数と単孔漏洩率を逆算
# ==========================================
elif input_mode == "3. Optimize Holes (Target C)":
    t_opt = st.sidebar.number_input("Fixed Thickness (t) [mm]", value=10.0, step=0.1)
    C_target = st.sidebar.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f")
    opt_variable = st.sidebar.radio("Vary Parameter by:", ["Aspect Ratio (AR)", "Hole Diameter (D)"])
    
    if opt_variable == "Aspect Ratio (AR)":
        # 🌟 AR=0.0 を許可 (min_value=0.0)
        ar_test = st.sidebar.slider("Test Aspect Ratio (AR)", 0.0, 15.0, 4.0, step=0.1)
        D_test = t_opt / ar_test if ar_test > 0 else float('inf')
    else:
        D_test = st.sidebar.slider("Test Hole Diameter (D) [mm]", 0.5, 10.0, 2.5, step=0.1)
        ar_test = t_opt / D_test

    def calc_opt(ar_val, t_mm):
        # 🌟 AR=0 の時のゼロ除算回避ロジック
        if ar_val == 0:
            return float('inf'), float('inf'), 0, 100.0
        
        t_m = t_mm * 1e-3
        D_m = t_m / ar_val
        C_single = calc_single_conductance(D_m, t_m)
        N_req = C_target / C_single
        R_pct = calculate_leakage(ar_val)
        return D_m * 1000, C_single, np.ceil(N_req), R_pct

    curr_D, curr_C, curr_N, curr_R = calc_opt(ar_test, t_opt)

    st.subheader(f"Optimization Analysis (Target = {C_target} m³/s)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aspect Ratio (AR)", f"{ar_test:.2f}")
    
    # Infinity表示のハンドリング
    disp_D = "∞" if curr_D == float('inf') else f"{curr_D:.2f} mm"
    c2.metric("Hole Diameter (D)", disp_D)
    c3.metric("Required Holes (N)", f"{int(curr_N):,}" if curr_N != float('inf') else "0")
    c4.metric("Single Hole Leakage", f"{curr_R:.2f} %")

    if st.button("📸 Take Snapshot"):
        st.session_state.snapshots.append({
            "Mode": "Opt. Holes", 
            "t [mm]": t_opt, 
            "AR": round(ar_test, 2), 
            "D [mm]": "inf" if curr_D == float('inf') else round(curr_D, 2), 
            "Req. Holes": int(curr_N), 
            "Single Leak (%)": round(curr_R, 2)
        })
        st.success(f"Snapshot saved: AR={ar_test:.2f}")

    st.subheader(f"Optimization Graph: {opt_variable} vs Single Leakage & Holes")
    # グラフのX軸も 0.0 からスタート
    x_array = np.linspace(0.0, 15.0, 100) if opt_variable == "Aspect Ratio (AR)" else np.linspace(0.5, 10.0, 100)
    x_title = "Aspect Ratio (AR)" if opt_variable == "Aspect Ratio (AR)" else "Hole Diameter (D) [mm]"
    curr_x = ar_test if opt_variable == "Aspect Ratio (AR)" else D_test
        
    trend_R, trend_N = [], []
    for x_val in x_array:
        temp_ar = x_val if opt_variable == "Aspect Ratio (AR)" else (t_opt / x_val)
        _, _, n, r_pct = calc_opt(temp_ar, t_opt)
        trend_R.append(r_pct)
        # グラフ描画用に、Nが0の場合はNaNまたは0にする（見栄えの調整）
        trend_N.append(n if n > 0 else np.nan)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(go.Scatter(x=x_array, y=trend_R, mode='lines', name='Single Hole Leakage (%)', 
                             line=dict(color='red', width=3), hovertemplate='%{y:.2f} %<extra></extra>'), secondary_y=False)
    fig.add_trace(go.Scatter(x=x_array, y=trend_N, mode='lines', name='Required Holes (N)', 
                             line=dict(color='royalblue', dash='dash'), hovertemplate='%{y:.0f} holes<extra></extra>'), secondary_y=True)
    fig.add_trace(go.Scatter(x=[curr_x], y=[curr_R], mode='markers+text', name='Current Point', text=["Current"], 
                             textposition="top right", marker=dict(color='orange', size=12)), secondary_y=False)
    
    fig.update_layout(xaxis_title=x_title, template="plotly_white", hovermode="x unified")
    fig.update_yaxes(title_text="Single Hole Leakage (%) (Red)", secondary_y=False)
    fig.update_yaxes(title_text="Required Holes (Blue Dash)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# Mode 4: Trade-off (Leakage vs Conductance)
# ==========================================
elif input_mode == "4. Trade-off (Leakage vs Conductance)":
    st.sidebar.markdown("---")
    fixed_param = st.sidebar.radio("What is your physical constraint?", ["Fixed Thickness (t)", "Fixed Diameter (D)"])
    
    if fixed_param == "Fixed Thickness (t)":
        fixed_val = st.sidebar.number_input("Thickness (t) [mm]", value=10.0, step=0.1)
    else:
        fixed_val = st.sidebar.number_input("Diameter (D) [mm]", value=2.5, step=0.1)

    st.subheader(f"Trade-off Analysis: Single UV Leakage vs Conductance ({fixed_param} = {fixed_val} mm)")
    st.write("This graph perfectly illustrates the core dilemma of NBE aperture design: Increasing AR blocks UV light, but drastically reduces gas flow.")

    # ここも 0.01 などの微小値からスタート (0だとコンダクタンス無限大でグラフが崩れるため)
    ar_array = np.linspace(0.1, 15.0, 100)
    leakage_array = [calculate_leakage(ar) for ar in ar_array]
    conductance_array = []

    for ar in ar_array:
        if fixed_param == "Fixed Thickness (t)":
            t_m = fixed_val * 1e-3
            D_m = t_m / ar
        else:
            D_m = fixed_val * 1e-3
            t_m = D_m * ar
        
        C_single = calc_single_conductance(D_m, t_m)
        conductance_array.append(C_single)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(go.Scatter(x=ar_array, y=leakage_array, mode='lines', name='Single UV Leakage Rate (%)', 
                             line=dict(color='red', width=3),
                             hovertemplate='%{y:.2f} %<extra></extra>'), secondary_y=False)
    
    fig.add_trace(go.Scatter(x=ar_array, y=conductance_array, mode='lines', name='Single Hole Conductance', 
                             line=dict(color='green', width=3),
                             hovertemplate='%{y:.6f} m³/s<extra></extra>'), secondary_y=True)

    fig.update_layout(
        xaxis_title="Aspect Ratio (AR)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text="<b>Single UV Leakage Rate (%)</b> (Red Line)", secondary_y=False)
    fig.update_yaxes(title_text="<b>Conductance [m³/s]</b> (Green Line)", tickformat=".6f", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 共通: Snapshot Table & Theory
# ==========================================
st.markdown("---")
if st.session_state.snapshots:
    st.subheader("📋 Design Comparison List")
    df_snap = pd.DataFrame(st.session_state.snapshots)
    st.dataframe(df_snap)
    csv_data = df_snap.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results (CSV)", data=csv_data, file_name="uv_leakage_snapshots.csv")
    if st.button("🗑️ Clear All"):
        st.session_state.snapshots = []
        st.rerun()

# 🌟 モデル切り替えに合わせて数式表示も動的に変更
st.header("Theory: Mathematical Model")
if model_choice == "Shuji Model (Diagonal Path)":
    st.write("**Diagonal Limit Model (Integrates all paths)**")
    st.latex(r"\tan(\theta_{max}) = \frac{D}{t} = \frac{1}{AR}")
    st.latex(r"R = \sin^2(\theta_{max}) = \frac{1}{1 + AR^2}")
    st.latex(r"UV\ Leakage\ (\%) = \frac{100}{1 + AR^2}\ \%")
else:
    st.write("**Full Clearance Model (Center path only)**")
    st.latex(r"\tan(\theta_{max}) = \frac{D/2}{t} = \frac{1}{2AR}")
    st.latex(r"R = \sin^2(\theta_{max}) = \frac{1}{1 + (2AR)^2}")
    st.latex(r"UV\ Leakage\ (\%) = \frac{100}{1 + 4AR^2}\ \%")
