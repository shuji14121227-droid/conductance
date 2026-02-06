import streamlit as st
import numpy as np
from scipy.optimize import brentq

# Page Config
st.set_page_config(page_title="Vacuum Conductance Calculator", layout="centered")
st.title("🕳️ Vacuum Conductance Design Tool")
st.caption("Gas: Cl2 / Temp: 293K / Pressure: 1.1Pa (Transition Flow)")

# --- Sidebar: Constants & Settings ---
with st.sidebar:
    st.header("Constants & Settings")
    T = st.number_input("Temperature T [K]", value=293.0)
    P_avg = st.number_input("Avg Pressure P_avg [Pa]", value=1.1)
    M_val = st.number_input("Molar Mass M [g/mol]", value=70.9) # Cl2
    mu_val = st.number_input("Dynamic Viscosity μ [1e-5 Pa s]", value=1.32)
    
    # Unit Conversion
    R_gas = 8.314
    M = M_val * 1e-3
    mu = mu_val * 1e-5
    v_avg = np.sqrt(8 * R_gas * T / (np.pi * M))
    st.write(f"Mean Molecular Speed: {v_avg:.1f} m/s")

# --- Calculation Logic ---
def calc_C_single(L_m, D_m):
    if L_m <= 0 or D_m <= 0: return 1e-20
    r = D_m / 2
    A = np.pi * r**2
    
    # Molecular Flow (Clausing factor approximation)
    alpha = 1 / (1 + (3 * L_m) / (4 * D_m))
    C_mol = (1/4) * A * v_avg * alpha
    
    # Viscous Flow
    C_visc = (np.pi * D_m**4 * P_avg) / (128 * mu * L_m)
    
    # Series Conductance (Transition Flow)
    return 1 / ((1/C_mol) + (1/C_visc))

# --- Main Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Calc Conductance", 
    "2. Calc Hole Count", 
    "3. Solve Diameter", 
    "4. Solve Thickness"
])

# Tab 1: Calculate Total Conductance
with tab1:
    st.subheader("Calculate Total Conductance")
    col1, col2 = st.columns(2)
    L1 = col1.number_input("Plate Thickness L [mm]", value=10.0, key="L1")
    D1 = col2.number_input("Hole Diameter D [mm]", value=2.5, key="D1")
    N1 = st.number_input("Number of Holes N", value=2200, step=10, key="N1")
    
    if st.button("Calculate", key="btn1"):
        C_single = calc_C_single(L1*1e-3, D1*1e-3)
        C_total = C_single * N1
        st.success(f"Total Conductance: {C_total:.5f} m³/s")
        st.info(f"({C_total*1000:.2f} L/s)")

# Tab 2: Calculate Required Hole Count
with tab2:
    st.subheader("Calculate Required Number of Holes")
    col1, col2 = st.columns(2)
    L2 = col1.number_input("Plate Thickness L [mm]", value=10.0, key="L2")
    D2 = col2.number_input("Hole Diameter D [mm]", value=3.0, key="D2")
    C_target2 = st.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f", key="Ct2")
    
    if st.button("Calculate", key="btn2"):
        C_single = calc_C_single(L2*1e-3, D2*1e-3)
        N2 = C_target2 / C_single
        st.success(f"Required Holes: {N2:.1f}")
        st.info(f"Estimate (Integer): {int(round(N2))} holes")

# Tab 3: Solve for Hole Diameter
with tab3:
    st.subheader("Solve for Required Hole Diameter")
    col1, col2 = st.columns(2)
    L3 = col1.number_input("Plate Thickness L [mm]", value=10.0, key="L3")
    N3 = col2.number_input("Number of Holes N", value=1000, key="N3")
    C_target3 = st.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f", key="Ct3")
    
    if st.button("Calculate", key="btn3"):
        target_single = C_target3 / N3
        def func(D_guess):
            return calc_C_single(L3*1e-3, D_guess) - target_single
        try:
            ans = brentq(func, 1e-5, 0.050) # Search range 0.01mm ~ 50mm
            st.success(f"Required Diameter: {ans*1000:.4f} mm")
        except:
            st.error("No solution found. Please check your inputs.")

# Tab 4: Solve for Plate Thickness
with tab4:
    st.subheader("Solve for Required Plate Thickness")
    col1, col2 = st.columns(2)
    D4 = col1.number_input("Hole Diameter D [mm]", value=2.5, key="D4")
    N4 = col2.number_input("Number of Holes N", value=2200, key="N4")
    C_target4 = st.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f", key="Ct4")
    
    if st.button("Calculate", key="btn4"):
        target_single = C_target4 / N4
        def func(L_guess):
            return calc_C_single(L_guess, D4*1e-3) - target_single
        try:
            ans = brentq(func, 1e-4, 1.0) # Search range 0.1mm ~ 1000mm
            st.success(f"Required Thickness: {ans*1000:.4f} mm")
        except:
            st.error("No solution found. Conductance might be out of range.")
