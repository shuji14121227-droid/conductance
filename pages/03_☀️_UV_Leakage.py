import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="UV vs Conductance Trade-off", layout="wide")
st.title("☀️ UV Leakage & Conductance Trade-off")

# --- Sidebar Inputs ---
st.sidebar.header("Design Parameters")

# Thickness Input
t_uv = st.sidebar.slider("Aperture Thickness (t) [mm]", 1.0, 30.0, 10.0)
t_input = st.sidebar.number_input("Direct Input (t)", value=float(t_uv), step=0.1)

# Diameter Input
D_uv = st.sidebar.slider("Hole Diameter (D) [mm]", 0.1, 10.0, 2.5)
D_input = st.sidebar.number_input("Direct Input (D)", value=float(D_uv), step=0.1)

# Final Values
final_t = t_input
final_D = D_input

# --- Calculation Logic ---
# 1. UV Leakage (Diagonal Path Model)
AR = final_t / final_D
leakage_rate = (1 / (1 + AR**2)) * 100

# 2. Relative Conductance (Molecular Flow Approximation)
# Clausing Factor alpha = 1 / (1 + 3L/4D)
# We use this as "Relative Conductance" (Conductance compared to L=0)
rel_conductance = 1 / (1 + (3 * final_t) / (4 * final_D))

# --- Results Display ---
st.subheader("Current Performance")
c1, c2, c3 = st.columns(3)
c1.metric("Aspect Ratio (AR)", f"{AR:.2f}")
c2.metric("UV Leakage Rate", f"{leakage_rate:.2f} %", delta=f"{leakage_rate:.1f}%", delta_color="inverse")
c3.metric("Rel. Conductance", f"{rel_conductance:.2f}", help="Conductance efficiency (Max = 1.0)")

# --- Visualization: Trade-off Chart ---
st.markdown("---")
st.subheader("Trade-off Analysis: UV Blocking vs. Gas Flow")

# Data for Trend Lines
t_range = np.linspace(1, 30, 100)
ar_trend = t_range / final_D
uv_trend = (1 / (1 + ar_trend**2)) * 100
cond_trend = 1 / (1 + (3 * t_range) / (4 * final_D))

# Create Figure
fig = go.Figure()

# UV Leakage Line
fig.add_trace(go.Scatter(
    x=t_range, y=uv_trend,
    mode='lines', name='UV Leakage (%)',
    line=dict(color='red', width=3)
))

# Relative Conductance Line
# Scale to 100% for comparison on the same axis
fig.add_trace(go.Scatter(
    x=t_range, y=cond_trend * 100,
    mode='lines', name='Rel. Conductance (%)',
    line=dict(color='green', width=3, dash='dash')
))

# Current Point (UV)
fig.add_trace(go.Scatter(
    x=[final_t], y=[leakage_rate],
    mode='markers', name='Current UV',
    marker=dict(color='red', size=12)
))

# Current Point (Cond)
fig.add_trace(go.Scatter(
    x=[final_t], y=[rel_conductance * 100],
    mode='markers', name='Current Flow',
    marker=dict(color='green', size=12, symbol='x')
))

fig.update_layout(
    xaxis_title="Aperture Thickness (t) [mm]",
    yaxis_title="Efficiency / Rate (%)",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
st.caption("※ Rel. Conductance is based on the Clausing factor (Transmission probability).")

# --- Practical Insight ---
st.info(f"💡 **Insight:** At t={final_t}mm, you are blocking {100-leakage_rate:.1f}% of UV, "
        f"but gas flow efficiency has dropped to {rel_conductance*100:.1f}% compared to an open hole.")

# --- Theory Section ---
st.markdown("---")
st.header("Theoretical Background")
col1, col2 = st.columns(2)
with col1:
    st.write("**UV Leakage (Geometric)**")
    st.latex(r"R_{UV} = \frac{1}{1 + (t/D)^2}")
with col2:
    st.write("**Gas Transmission (Molecular)**")
    st.latex(r"\alpha \approx \frac{1}{1 + \frac{3t}{4D}}")
