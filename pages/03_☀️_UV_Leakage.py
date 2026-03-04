import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="UV Leakage Snapshot", layout="wide")
st.title("☀️ UV Leakage Simulator & Snapshot")

# セッション状態（スナップショット保存用）の初期化
if 'snapshots' not in st.session_state:
    st.session_state.snapshots = []

# --- Sidebar Inputs ---
st.sidebar.header("Design Parameters")

t_uv = st.sidebar.slider("Aperture Thickness (t) [mm]", 1.0, 30.0, 10.0)
t_input = st.sidebar.number_input("Direct Input (t)", value=float(t_uv), step=0.1)

D_uv = st.sidebar.slider("Hole Diameter (D) [mm]", 0.1, 10.0, 2.5)
D_input = st.sidebar.number_input("Direct Input (D)", value=float(D_uv), step=0.1)

final_t = t_input
final_D = D_input

# --- Calculation Logic ---
AR = final_t / final_D
leakage_rate = (1 / (1 + AR**2)) * 100

# --- Results Display ---
st.subheader("Current Performance")
c1, c2, c3 = st.columns(3)
c1.metric("Aspect Ratio (AR)", f"{AR:.2f}")
c2.metric("UV Leakage Rate", f"{leakage_rate:.2f} %")
c3.metric("UV Blocking Rate", f"{100-leakage_rate:.2f} %")

# --- Snapshot Action ---
st.markdown("---")
if st.button("📸 Take Snapshot (Save Current Values)"):
    new_snapshot = {
        "Thickness (t)": final_t,
        "Diameter (D)": final_D,
        "Aspect Ratio (AR)": round(AR, 2),
        "UV Leakage (%)": round(leakage_rate, 4),
        "UV Blocking (%)": round(100 - leakage_rate, 4)
    }
    st.session_state.snapshots.append(new_snapshot)
    st.success(f"Snapshot saved: t={final_t}, D={final_D}")

# --- Visualization ---
st.subheader("UV Leakage Trend")
ar_range = np.linspace(0.5, 20, 100)
leakage_trend = (1 / (1 + ar_range**2)) * 100

fig = go.Figure()
fig.add_trace(go.Scatter(x=ar_range, y=leakage_trend, mode='lines', name='Trend', line=dict(color='royalblue')))
fig.add_trace(go.Scatter(x=[AR], y=[leakage_rate], mode='markers+text', name='Current', 
                         text=["Current"], textposition="top right", marker=dict(color='red', size=12)))

# 保存されたスナップショットもグラフに表示
if st.session_state.snapshots:
    snap_ar = [s["Aspect Ratio (AR)"] for s in st.session_state.snapshots]
    snap_leak = [s["UV Leakage (%)"] for s in st.session_state.snapshots]
    fig.add_trace(go.Scatter(x=snap_ar, y=snap_leak, mode='markers', name='History', marker=dict(color='orange', size=8, symbol='diamond')))

fig.update_layout(xaxis_title="Aspect Ratio (t/D)", yaxis_title="UV Leakage Rate (%)", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# --- Snapshot Table & CSV ---
if st.session_state.snapshots:
    st.subheader("📋 Saved Snapshots")
    df_snap = pd.DataFrame(st.session_state.snapshots)
    st.table(df_snap)
    
    col_dl1, col_dl2 = st.columns(2)
    csv_data = df_snap.to_csv(index=False).encode('utf-8')
    col_dl1.download_button("📥 Download Snapshots as CSV", data=csv_data, file_name="uv_leakage_snapshots.csv", mime="text/csv")
    
    if col_dl2.button("🗑️ Clear All Snapshots"):
        st.session_state.snapshots = []
        st.rerun()

# --- Theory Section ---
st.markdown("---")
st.header("Theory: Diagonal Path Model")
st.latex(r"R_{UV} = \frac{1}{1 + (t/D)^2}")
