import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import brentq

# Page Config
st.set_page_config(page_title="Vacuum Conductance Calculator", layout="wide") # Use wide layout for table
st.title("🕳️ Vacuum Conductance Design Tool")
st.caption("Gas: Cl2 / Temp: 293K / Pressure: 1.1Pa (Transition Flow)")

# --- Sidebar: Constants & Settings ---
with st.sidebar:
    st.header("Constants & Settings")
    T = st.number_input("Temperature T [K]", value=293.0)
    P_avg = st.number_input("Avg Pressure P_avg [Pa]", value=1.1)
    Delta_P = st.number_input("Diff Pressure ΔP [Pa]", value=1.8) # Needed for Q
    M_val = st.number_input("Molar Mass M [g/mol]", value=70.9) # Cl2
    mu_val = st.number_input("Dynamic Viscosity μ [1e-5 Pa s]", value=1.32)
    
    # Unit Conversion
    R_gas = 8.314
    M = M_val * 1e-3
    mu = mu_val * 1e-5
    v_avg = np.sqrt(8 * R_gas * T / (np.pi * M))
    st.markdown("---")
    st.write(f"Mean Molecular Speed: **{v_avg:.1f} m/s**")

# --- Core Calculation Functions ---
def calc_C_single(L_m, D_m):
    if L_m <= 0 or D_m <= 0: return 1e-20
    r = D_m / 2
