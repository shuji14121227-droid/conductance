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

# 入力モードの切り替え (3つのモード)
input_mode = st.sidebar.radio("Input Mode", [
    "1. Manual (t & D)", 
    "2. Direct AR Input",
    "3. Optimize Holes (Target C)"  # ← NEW! 3つ目の機能
])

st.sidebar.markdown("---")

# ==========================================
# Mode 1 & 2: シンプルな単孔漏洩率の計算
# ==========================================
if input_mode in ["1. Manual (t & D)", "2. Direct AR Input"]:
    if input_mode == "1. Manual (t & D)":
        t_input = st.sidebar.number_input("Aperture Thickness (t) [mm]", value=10.0, step=0.1)
        D_input = st.sidebar.number_input("Hole Diameter (D) [mm]", value=2.5, step=0.1)
        final_AR = t_input / D_input
    else:
        final_AR = st.sidebar.number_input("Aspect Ratio (AR)", value=4.0, step=0.1)
        st.sidebar.info(f"Using AR = {final_AR}")

    # 計算ロジック: R = 100 / (1 + 4*AR^2)
    leakage_rate = 100 / (1 + 4 * final_AR**2)

    st.subheader("Current Performance Analysis")
    c1, c2, c3 = st.columns(3)
    c1.metric("Aspect Ratio (AR)", f"{final_AR:.2f}")
    c2.metric("UV Leakage Rate", f"{leakage_rate:.4f} %")
    c3.metric("UV Blocking Rate", f"{100-leakage_rate:.4f} %")

    if st.button("📸 Take Snapshot"):
        st.session_state.snapshots.append({
            "Mode": "Simple",
            "AR": round(final_AR, 2),
            "UV Leakage (%)": round(leakage_rate, 6)
        })
        st.success(f"Snapshot saved: AR={final_AR:.2f}")

    # グラフ表示
    st.subheader("UV Leakage Trend vs. AR")
    ar_range = np.linspace(0.5, 20, 100)
    leakage_trend = 100 / (1 + 4 * ar_range**2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ar_range, y=leakage_trend, mode='lines', name='Theoretical Trend', line=dict(color='royalblue')))
    fig.add_trace(go.Scatter(x=[final_AR], y=[leakage_rate], mode='markers+text', name='Current Point', 
                             text=[f"AR={final_AR:.1f}"], textposition="top right", marker=dict(color='red', size=12)))
    fig.update_layout(xaxis_title="Aspect Ratio (AR)", yaxis_title="UV Leakage Rate (%)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# Mode 3: 目標コンダクタンスから穴数と総漏洩を逆算
# ==========================================
elif input_mode == "3. Optimize Holes (Target C)":
    t_opt = st.sidebar.number_input("Fixed Thickness (t) [mm]", value=10.0, step=0.1)
    C_target = st.sidebar.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f")
    ar_test = st.sidebar.slider("Test Aspect Ratio (AR)", 1.0, 15.0, 4.0, step=0.1)

    with st.sidebar.expander("⚙️ Gas Parameters"):
        T = st.number_input("Temperature [K]", value=293.0)
        P_avg = st.number_input("Pressure [Pa]", value=1.1)
        M_val = st.number_input("Molar Mass [g/mol]", value=70.9)
        mu_val = st.number_input("Viscosity [1e-5 Pa s]", value=1.32)

    R_gas = 8.314
    M = M_val * 1e-3
    mu = mu_val * 1e-5
    v_bar = np.sqrt((8 * R_gas * T) / (np.pi * M))

    # あなたが書いたロジックの関数化
    def calc_opt(ar_val, t_mm):
        t_m = t_mm * 1e-3
        D_m = t_m / ar_val
        A = np.pi * (D_m**2) / 4
        alpha = 1 / (1 + (3 * t_m) / (4 * D_m))
        C_mol = 0.25 * A * v_bar * alpha
        C_visc = (np.pi * (D_m**4) * P_avg) / (128 * mu * t_m)
        C_single = 1 / ((1 / C_mol) + (1 / C_visc))
        
        N_req = C_target / C_single
        R_pct = 100 / (1 + 4 * ar_val**2)
        Total_idx = N_req * (R_pct / 100)
        return D_m * 1000, C_single, np.ceil(N_req), R_pct, Total_idx

    curr_D, curr_C, curr_N, curr_R, curr_Total = calc_opt(ar_test, t_opt)

    st.subheader(f"Optimization Analysis (Target = {C_target} m³/s)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aspect Ratio (AR)", f"{ar_test:.1f}")
    c2.metric("Required D", f"{curr_D:.2f} mm")
    c3.metric("Required Holes (N)", f"{int(curr_N):,}")
    c4.metric("Total Leakage Index", f"{curr_Total:.2f}")

    if st.button("📸 Take Snapshot"):
        st.session_state.snapshots.append({
            "Mode": "Opt. Holes",
            "t [mm]": t_opt,
            "AR": round(ar_test, 2),
            "Req. D [mm]": round(curr_D, 2),
            "Req. Holes (N)": int(curr_N),
            "Total Index": round(curr_Total, 2)
        })
        st.success(f"Snapshot saved: AR={ar_test:.1f}, N={int(curr_N)}")

    st.subheader("Optimization Graph: AR vs Total Leakage & Required Holes")
    ar_array = np.linspace(1.0, 15.0, 100)
    
    # グラフ描画用の配列計算
    trend_Tot = []
    trend_N = []
    for a in ar_array:
        _, _, n, _, tot = calc_opt(a, t_opt)
        trend_Tot.append(tot)
        trend_N.append(n)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=ar_array, y=trend_Tot, mode='lines', name='Total Leakage Index', line=dict(color='red')), secondary_y=False)
    fig.add_trace(go.Scatter(x=ar_array, y=trend_N, mode='lines', name='Required Holes (N)', line=dict(color='royalblue', dash='dash')), secondary_y=True)
    fig.add_trace(go.Scatter(x=[ar_test], y=[curr_Total], mode='markers+text', name='Current Point', text=["Current"], textposition="top center", marker=dict(color='orange', size=12)), secondary_y=False)

    fig.update_layout(xaxis_title="Aspect Ratio (AR)", template="plotly_white", hovermode="x unified")
    fig.update_yaxes(title_text="Total Leakage Index (Red)", secondary_y=False)
    fig.update_yaxes(title_text="Required Holes (Blue Dash)", secondary_y=True)
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

st.header("Theory: Diagonal Path Model")
st.latex(r"\tan(\theta_{max}) = \frac{1}{2AR}")
st.latex(r"R = \sin^2(\theta_{max}) = \frac{1}{1 + (2AR)^2}")
st.latex(r"UV\ Leakage\ (\%) = \frac{100}{1 + 4AR^2}\ \%")
