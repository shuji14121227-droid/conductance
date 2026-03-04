import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import brentq

# Page Config
st.set_page_config(page_title="Vacuum Conductance Calculator", layout="wide")
st.title("🕳️ Vacuum Conductance Design Tool")
st.caption("Gas: Cl2 / Temp: 293K / Pressure: 1.1Pa (Transition Flow)")

# セッション状態（スナップショット保存用）の初期化
if 'cond_snapshots' not in st.session_state:
    st.session_state.cond_snapshots = []

# --- Sidebar: Constants & Settings ---
with st.sidebar:
    st.header("Constants & Settings")
    T = st.number_input("Temperature T [K]", value=293.0)
    P_avg = st.number_input("Avg Pressure P_avg [Pa]", value=1.1)
    Delta_P = st.number_input("Diff Pressure ΔP [Pa]", value=1.8) 
    M_val = st.number_input("Molar Mass M [g/mol]", value=70.9) 
    mu_val = st.number_input("Dynamic Viscosity μ [1e-5 Pa s]", value=1.32)
    
    # Unit Conversion
    R_gas = 8.314
    M = M_val * 1e-3
    mu = mu_val * 1e-5
    v_avg = np.sqrt(8 * R_gas * T / (np.pi * M))
    st.markdown("---")
    st.write(f"Mean Molecular Speed: **{v_avg:.1f} m/s**")

# --- Calculation Logic ---
def calc_C_single(L_m, D_m):
    if L_m <= 0 or D_m <= 0: return 1e-20
    r = D_m / 2
    A = np.pi * r**2
    alpha = 1 / (1 + (3 * L_m) / (4 * D_m))
    C_mol = (1/4) * A * v_avg * alpha
    C_visc = (np.pi * D_m**4 * P_avg) / (128 * mu * L_m)
    return 1 / ((1/C_mol) + (1/C_visc))

# --- Helper to create and Save snapshot ---
def handle_results(L_mm, D_mm, N, label=""):
    L_m, D_m = L_mm * 1e-3, D_mm * 1e-3
    C_single = calc_C_single(L_m, D_m)
    C_total = C_single * N
    V_total = N * (np.pi * (D_m/2)**2) * L_m
    Q = C_total * Delta_P
    Res_Time = ((P_avg * V_total) / Q) * 1000 if Q > 0 else 0
    
    # 1. Display Current Result
    st.success(f"Result: Overall Conductance = {C_total:.5f} m³/s")
    res_data = {
        "Thickness [mm]": L_mm,
        "Diameter [mm]": D_mm,
        "Holes": int(N),
        "C_total [m³/s]": round(C_total, 5),
        "Flux Q": round(Q, 4),
        "Res. Time [ms]": round(Res_Time, 2)
    }
    st.table(pd.DataFrame([res_data]))
    
    # 2. Snapshot Button
    if st.button(f"📸 Save this design ({label})"):
        st.session_state.cond_snapshots.append(res_data)
        st.toast("Design saved to snapshot list!")

# --- Main Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Calc Conductance", 
    "2. Calc Hole Count", 
    "3. Solve Diameter", 
    "4. Solve Thickness",
    "📊 Snapshot List"
])

with tab1:
    st.subheader("Calculate Total Conductance")
    c1, c2, c3 = st.columns(3)
    L1 = c1.number_input("Plate Thickness L [mm]", value=10.0, key="L1")
    D1 = c2.number_input("Hole Diameter D [mm]", value=2.5, key="D1")
    N1 = c3.number_input("Number of Holes N", value=2200, step=10, key="N1")
    handle_results(L1, D1, N1, "Tab1")

with tab2:
    st.subheader("Calculate Required Number of Holes")
    c1, c2, c3 = st.columns(3)
    L2 = c1.number_input("Plate Thickness L [mm]", value=10.0, key="L2")
    D2 = c2.number_input("Hole Diameter D [mm]", value=3.0, key="D2")
    Ct2 = c3.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f", key="Ct2")
    if st.button("Run Solver", key="btn2"):
        N2 = Ct2 / calc_C_single(L2*1e-3, D2*1e-3)
        handle_results(L2, D2, int(round(N2)), "Tab2")

with tab3:
    st.subheader("Solve for Required Hole Diameter")
    c1, c2, c3 = st.columns(3)
    L3 = c1.number_input("Plate Thickness L [mm]", value=10.0, key="L3")
    N3 = c2.number_input("Number of Holes N", value=1000, key="N3")
    Ct3 = c3.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f", key="Ct3")
    if st.button("Run Solver", key="btn3"):
        def func(D_guess): return calc_C_single(L3*1e-3, D_guess) - (Ct3/N3)
        try:
            ans = brentq(func, 1e-5, 0.050)
            handle_results(L3, ans*1000, N3, "Tab3")
        except: st.error("No solution found.")

with tab4:
    st.subheader("Solve for Plate Thickness")
    c1, c2, c3 = st.columns(3)
    D4 = c1.number_input("Hole Diameter D [mm]", value=2.5, key="D4")
    N4 = c2.number_input("Number of Holes N", value=2200, key="N4")
    Ct4 = c3.number_input("Target Conductance [m³/s]", value=0.0157, format="%.5f", key="Ct4")
    if st.button("Run Solver", key="btn4"):
        def func(L_guess): return calc_C_single(L_guess, D4*1e-3) - (Ct4/N4)
        try:
            ans = brentq(func, 1e-4, 1.0)
            handle_results(ans*1000, D4, N4, "Tab4")
        except: st.error("No solution found.")

# --- Tab 5: Snapshot Management ---
with tab5:
    st.subheader("Saved Design Comparison")
    if st.session_state.cond_snapshots:
        df_all = pd.DataFrame(st.session_state.cond_snapshots)
        st.dataframe(df_all, use_container_width=True)
        
        col_dl, col_clr = st.columns(2)
        csv = df_all.to_csv(index=False).encode('utf-8')
        col_dl.download_button("📥 Download All as CSV", data=csv, file_name="conductance_designs.csv", mime="text/csv")
        
        if col_clr.button("🗑️ Clear List"):
            st.session_state.cond_snapshots = []
            st.rerun()
    else:
        st.info("No snapshots saved yet. Click the 'Save this design' button after calculating.")
