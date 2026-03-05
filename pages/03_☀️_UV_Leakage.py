import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(page_title="NBE Aperture Optimizer", layout="wide")
st.title("☀️ NBE Aperture Optimizer (AR vs Required Holes)")
st.markdown("Calculate the required number of holes to maintain a **Target Conductance**, and find the optimal Aspect Ratio to minimize **Total UV Leakage**.")

# セッション状態の初期化
if 'snapshots' not in st.session_state:
    st.session_state.snapshots = []

# --- Sidebar: Global Settings ---
st.sidebar.header("1. Design Constraints")
t_input = st.sidebar.number_input("Fixed Thickness (t) [mm]", value=10.0, step=0.1)
C_target = st.sidebar.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f", help="Example: 0.0157 for SPP ICP standard")

st.sidebar.header("2. Test Current AR")
final_AR = st.sidebar.slider("Test Aspect Ratio (AR)", 1.0, 15.0, 4.0, step=0.1)

# Gas Parameters (Expander to keep sidebar clean)
with st.sidebar.expander("⚙️ Gas Parameters (Default: Cl2)"):
    T = st.number_input("Temperature [K]", value=293.0)
    P_avg = st.number_input("Pressure [Pa]", value=1.1)
    M_val = st.number_input("Molar Mass [g/mol]", value=70.9)
    mu_val = st.number_input("Viscosity [1e-5 Pa s]", value=1.32)

# Gas Constants
R_gas = 8.314
M = M_val * 1e-3
mu = mu_val * 1e-5
v_bar = np.sqrt((8 * R_gas * T) / (np.pi * M))

# --- Calculation Logic (Vectorized for graphing) ---
def calc_aperture_physics(ar_array, t_mm):
    t_m = t_mm * 1e-3
    D_m = t_m / ar_array
    
    # Conductance Calculation
    A = np.pi * (D_m**2) / 4
    alpha = 1 / (1 + (3 * t_m) / (4 * D_m))
    C_mol = 0.25 * A * v_bar * alpha
    C_visc = (np.pi * (D_m**4) * P_avg) / (128 * mu * t_m)
    
    C_single = 1 / ((1 / C_mol) + (1 / C_visc))
    
    # Required Holes
    N_req = C_target / C_single
    
    # UV Leakage (Single and Total)
    # R_single = 1 / (1 + 4*AR^2)
    R_single_pct = 100 / (1 + 4 * ar_array**2)
    Total_Index = N_req * (R_single_pct / 100)
    
    return D_m * 1000, C_single, np.ceil(N_req), R_single_pct, Total_Index

# Calculate for Current Point
curr_D, curr_C, curr_N, curr_R, curr_Total = calc_aperture_physics(np.array([final_AR]), t_input)

# --- Results Display ---
st.subheader(f"Current Design Point (t = {t_input} mm, Target = {C_target} m³/s)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Aspect Ratio (AR)", f"{final_AR:.1f}")
c2.metric("Hole Diameter (D)", f"{curr_D[0]:.2f} mm")
c3.metric("Required Holes (N)", f"{int(curr_N[0]):,}")
c4.metric("Total UV Leakage Index", f"{curr_Total[0]:.2f}", help="Lower is better. Represents total UV photons passing through.")

# --- Snapshot Action ---
st.markdown("---")
if st.button("📸 Take Snapshot (Compare Designs)"):
    st.session_state.snapshots.append({
        "t [mm]": t_input,
        "AR": round(final_AR, 2),
        "D [mm]": round(curr_D[0], 2),
        "Req. Holes (N)": int(curr_N[0]),
        "Single Leak (%)": round(curr_R[0], 4),
        "Total Index": round(curr_Total[0], 2)
    })
    st.success("Snapshot saved!")

# --- Visualization (The Game-Changer Graph) ---
st.subheader("Optimization Graph: Finding the Sweet Spot")
st.write("This graph shows how the required number of holes ($N$) explodes as AR increases, and how it affects the overall UV leakage.")

ar_range = np.linspace(1.0, 15.0, 200)
trend_D, trend_C, trend_N, trend_R, trend_Total = calc_aperture_physics(ar_range, t_input)

# Create Subplots with dual Y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# 1. Total UV Leakage Index (Primary Y) - The most important metric!
fig.add_trace(go.Scatter(x=ar_range, y=trend_Total, mode='lines', name='Total UV Leakage Index', 
                         line=dict(color='red', width=3)), secondary_y=False)

# 2. Required Number of Holes (Secondary Y)
fig.add_trace(go.Scatter(x=ar_range, y=trend_N, mode='lines', name='Required Holes (N)', 
                         line=dict(color='royalblue', width=2, dash='dash')), secondary_y=True)

# Current Point
fig.add_trace(go.Scatter(x=[final_AR], y=[curr_Total[0]], mode='markers+text', name='Current Design',
                         text=["Current"], textposition="top center", marker=dict(color='orange', size=12)), secondary_y=False)

fig.update_layout(
    xaxis_title="Aspect Ratio (AR)",
    template="plotly_white",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig.update_yaxes(title_text="<b>Total UV Leakage Index</b> (Red Line)", secondary_y=False)
fig.update_yaxes(title_text="<b>Required Holes N</b> (Blue Dash)", secondary_y=True)

st.plotly_chart(fig, use_container_width=True)

# --- Comparison Table ---
if st.session_state.snapshots:
    st.subheader("📋 Design Comparison List")
    df_snap = pd.DataFrame(st.session_state.snapshots)
    st.dataframe(df_snap.style.highlight_min(subset=['Total Index'], color='lightgreen'))
    
    csv_data = df_snap.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results (CSV)", data=csv_data, file_name="nbe_optimization.csv")
    if st.button("🗑️ Clear All"):
        st.session_state.snapshots = []
        st.rerun()

# --- Theory Section ---
st.markdown("---")
st.header("Theory: Constrained Optimization")
st.markdown("""
To find the optimal aperture geometry, we fix the **Target Conductance ($C_{target}$)** and **Thickness ($t$)**, and vary the Aspect Ratio ($AR$).
1. **Diameter:** $D = t / AR$
2. **Required Holes ($N$):** Derived from combining Molecular and Viscous flow models to match $C_{target}$.
3. **Total Leakage Index:** $N \times \frac{1}{1+4AR^2}$
""")
