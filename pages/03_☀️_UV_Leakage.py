import streamlit as st
import numpy as np
import pandas as pd

# Page Configuration
st.set_page_config(page_title="UV Leakage Simulator", layout="wide")
st.title("☀️ UV Leakage Simulator for High AR Apertures")

# --- Introduction ---
st.markdown("""
### Background
In Neutral Beam Etching (NBE), minimizing UV damage to the substrate is critical. 
This tool calculates the geometric UV leakage rate based on the **Diagonal Path Model**.
""")

# --- Sidebar Inputs ---
st.sidebar.header("Design Parameters")
t_uv = st.sidebar.slider("Aperture Thickness (t) [mm]", 1.0, 30.0, 10.0)
D_uv = st.sidebar.slider("Hole Diameter (D) [mm]", 0.1, 10.0, 2.5)

# --- Calculation Logic ---
# Aspect Ratio (AR)
AR = t_uv / D_uv

# UV Leakage Rate Calculation based on Diagonal Path Model
# tan(theta_max) = D / t = 1 / AR
# R = sin^2(theta_max) = 1 / (1 + AR^2)
leakage_rate = (1 / (1 + AR**2)) * 100

# --- Results Display ---
st.subheader("Calculation Results")
col1, col2 = st.columns(2)
col1.metric("Aspect Ratio (AR)", f"{AR:.2f}")
col2.metric("UV Leakage Rate", f"{leakage_rate:.2f} %")

# --- Visualization ---
st.markdown("---")
st.subheader("Leakage Trend vs. Aspect Ratio")
ar_range = np.linspace(1, 20, 100)
leakage_trend = (1 / (1 + ar_range**2)) * 100
chart_data = pd.DataFrame({
    "Aspect Ratio": ar_range,
    "Leakage Rate (%)": leakage_trend
})

# Highlight current point
st.line_chart(chart_data.set_index("Aspect Ratio"))
st.info(f"Current design (AR={AR:.2f}) blocks {100-leakage_rate:.2f}% of UV radiation.")

# --- Theory Section (The contents you provided) ---
st.markdown("---")
st.header("Theory: Diagonal Path Model")

col_text, col_img = st.columns([2, 1])

with col_text:
    st.markdown("""
    **The Core Concept:**
    Since the plasma source is a planar source, the maximum angle at which light can pass ($\theta_{max}$) 
    is determined by the diagonal path from the entrance edge to the opposite exit edge.
    
    This diagonal passes through the geometric center of the aperture. The ratio of the right triangle 
    (height $t/2$, base $D/2$) gives:
    """)
    st.latex(r"\tan(\theta_{max}) = \frac{D/2}{t/2} = \frac{D}{t} = \frac{1}{AR}")
    
    st.markdown("""
    **Leakage Rate Derivation:**
    Assuming an isotropic source, the leakage rate is proportional to the "apparent area" from the wafer.
    1. **Projected Radius:** $\sin(\theta_{max})$
    2. **UV Leakage Rate ($R$):**
    """)
    st.latex(r"R = \sin^2(\theta_{max}) = \frac{1}{1 + AR^2}")
    st.write("This formula allow us to predict UV leakage directly from the Aspect Ratio.")

with col_img:
    st.write("*(Conceptual Diagram)*")
    # 代替として幾何学的な説明を表示
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Trigonometry_triangle.svg/300px-Trigonometry_triangle.svg.png", caption="Geometric Model Basis")

# CSV Download for the trend data
csv = chart_data.to_csv(index=False).encode('utf-8')
st.download_button("Download Trend Data (CSV)", csv, "uv_trend.csv", "text/csv")
