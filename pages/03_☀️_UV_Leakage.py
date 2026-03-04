import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="UV Leakage Simulator", layout="wide")
st.title("☀️ UV Leakage Simulator (Diagonal Path Model)")

# --- Sidebar Inputs ---
st.sidebar.header("Design Parameters")

# 数値入力とスライダーを同期させるための設定
col_t1, col_t2 = st.sidebar.columns([2, 1])
t_uv = st.sidebar.slider("Aperture Thickness (t) [mm]", 1.0, 30.0, 10.0)
t_input = st.sidebar.number_input("Direct Input (t)", value=float(t_uv), step=0.1)

st.sidebar.markdown("---")

col_d1, col_d2 = st.sidebar.columns([2, 1])
D_uv = st.sidebar.slider("Hole Diameter (D) [mm]", 0.1, 10.0, 2.5)
D_input = st.sidebar.number_input("Direct Input (D)", value=float(D_uv), step=0.1)

# 入力値の確定（数値入力を優先）
final_t = t_input
final_D = D_input

# --- Calculation Logic ---
AR = final_t / final_D
# R = 1 / (1 + AR^2) * 100
leakage_rate = (1 / (1 + AR**2)) * 100

# --- Results Display ---
st.subheader("Calculation Results")
c1, c2, c3 = st.columns(3)
c1.metric("Aspect Ratio (AR)", f"{AR:.2f}")
c2.metric("UV Leakage Rate", f"{leakage_rate:.2f} %")
c3.metric("UV Blocking Rate", f"{100-leakage_rate:.2f} %")

# --- Visualization with Plotly (To show the dot on the line) ---
st.markdown("---")
st.subheader("Leakage Trend & Current Design Point")

# グラフ用データの作成
ar_range = np.linspace(0.5, 15, 100)
leakage_trend = (1 / (1 + ar_range**2)) * 100

# Plotlyを使用してインタラクティブなグラフを作成
fig = go.Figure()

# トレンドラインの追加
fig.add_trace(go.Scatter(
    x=ar_range, y=leakage_trend,
    mode='lines',
    name='Theoretical Trend',
    line=dict(color='royalblue', width=2)
))

# 現在の設計ポイントを「赤い点」で追加
fig.add_trace(go.Scatter(
    x=[AR], y=[leakage_rate],
    mode='markers+text',
    name='Current Design',
    text=[f"Current (AR={AR:.2f})"],
    textposition="top right",
    marker=dict(color='red', size=12, symbol='circle')
))

fig.update_layout(
    xaxis_title="Aspect Ratio (t/D)",
    yaxis_title="UV Leakage Rate (%)",
    hovermode="x unified",
    template="plotly_white",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# --- Theory Section ---
st.markdown("---")
st.header("Theory: Diagonal Path Model")
st.markdown("""
Based on your geometric model, the maximum leakage angle $\\theta_{max}$ is determined by the diagonal path.
""")

st.latex(r"\tan(\theta_{max}) = \frac{D}{t} = \frac{1}{AR}")
st.latex(r"R = \sin^2(\theta_{max}) = \frac{1}{1 + AR^2}")

# CSV Download
chart_data = pd.DataFrame({"Aspect Ratio": ar_range, "Leakage Rate (%)": leakage_trend})
csv = chart_data.to_csv(index=False).encode('utf-8')
st.download_button("Download Trend Data", csv, "uv_leakage_trend.csv", "text/csv")
