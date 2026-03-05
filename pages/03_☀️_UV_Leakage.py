import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="UV Leakage Simulator", layout="wide")
st.title("☀️ UV Leakage Simulator (Direct AR Input Mode)")

# セッション状態の初期化
if 'snapshots' not in st.session_state:
    st.session_state.snapshots = []

# --- Sidebar Inputs ---
st.sidebar.header("Design Parameters")

# 入力モードの切り替え
input_mode = st.sidebar.radio("Input Mode", ["Manual (t & D)", "Direct AR Input"])

if input_mode == "Manual (t & D)":
    t_input = st.sidebar.number_input("Aperture Thickness (t) [mm]", value=10.0, step=0.1)
    D_input = st.sidebar.number_input("Hole Diameter (D) [mm]", value=2.5, step=0.1)
    final_AR = t_input / D_input
    display_t, display_D = t_input, D_input
else:
    final_AR = st.sidebar.number_input("Aspect Ratio (AR)", value=4.0, step=0.1)
    st.sidebar.info(f"Using AR = {final_AR}")
    # AR入力時はtとDは便宜上の値を表示（必要なら）
    display_t, display_D = final_AR, 1.0 

# 穴の数（総漏洩量計算用）
N_holes = st.sidebar.number_input("Number of Holes (N)", value=2200, step=1)

# --- Calculation Logic (Formula from your images) ---
# tan(theta) = 1 / (2 * AR)
# R = sin^2(theta) = 1 / (1 + (2*AR)^2)
leakage_rate = (100 / (1 + (2 * final_AR)**2))
total_leakage_index = N_holes * (leakage_rate / 100)

# --- Results Display ---
st.subheader("Current Performance Analysis")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Aspect Ratio (AR)", f"{final_AR:.2f}")
c2.metric("Single Hole Leakage", f"{leakage_rate:.4f} %")
c3.metric("Number of Holes", f"{N_holes}")
c4.metric("Total Leakage Index", f"{total_leakage_index:.2f}")

# --- Snapshot Action ---
st.markdown("---")
if st.button("📸 Take Snapshot"):
    new_snapshot = {
        "Input Mode": input_mode,
        "AR": round(final_AR, 2),
        "N (Holes)": N_holes,
        "Single Leak (%)": round(leakage_rate, 6),
        "Total Index": round(total_leakage_index, 2)
    }
    st.session_state.snapshots.append(new_snapshot)
    st.success(f"Snapshot saved: AR={final_AR:.2f}")

# --- Visualization ---
st.subheader("UV Leakage Trend vs. AR")
ar_range = np.linspace(0.5, 20, 100)
leakage_trend = 100 / (1 + (2 * ar_range)**2)

fig = go.Figure()
fig.add_trace(go.Scatter(x=ar_range, y=leakage_trend, mode='lines', name='Theoretical Trend', line=dict(color='royalblue')))
fig.add_trace(go.Scatter(x=[final_AR], y=[leakage_rate], mode='markers+text', name='Current Point', 
                         text=[f"AR={final_AR:.1f}"], textposition="top right", marker=dict(color='red', size=12)))

fig.update_layout(xaxis_title="Aspect Ratio (AR)", yaxis_title="UV Leakage Rate (%)", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# --- Comparison Table ---
if st.session_state.snapshots:
    st.subheader("📋 Design Comparison List")
    df_snap = pd.DataFrame(st.session_state.snapshots)
    st.table(df_snap)
    csv_data = df_snap.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results (CSV)", data=csv_data, file_name="uv_leakage_ar_analysis.csv")
    if st.button("🗑️ Clear All"):
        st.session_state.snapshots = []
        st.rerun()

# --- Theory Section (Updated with images formulas) ---
st.markdown("---")
st.header("Theory: Diagonal Path Model (Direct AR Derivation)")
st.write("Based on the geometric diagonal path and Lambert's Cosine Law:")

st.latex(r"\tan(\theta_{max}) = \frac{D/2}{t} = \frac{1}{2AR}")
st.latex(r"R = \sin^2(\theta_{max}) = \frac{1}{1 + \tan^{-2}(\theta_{max})} = \frac{1}{1 + (2AR)^2}")
st.write("Final percentage formula used in this app:")
st.latex(r"UV\ Leakage\ (\%) = \frac{100}{1 + 4AR^2}\ \%")
