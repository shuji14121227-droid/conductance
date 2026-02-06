import streamlit as st
import numpy as np
from scipy.optimize import brentq

# ページ設定
st.set_page_config(page_title="真空コンダクタンス計算機", layout="centered")
st.title("🕳️ 真空コンダクタンス設計ツール")
st.caption("Cl2ガス / 293K / 1.1Pa (Transition Flow)")

# --- サイドバーで定数設定（変更可能にする） ---
with st.sidebar:
    st.header("物理定数・環境設定")
    T = st.number_input("温度 T [K]", value=293.0)
    P_avg = st.number_input("平均圧力 P_avg [Pa]", value=1.1)
    M_val = st.number_input("分子量 M [g/mol]", value=70.9) # Cl2
    mu_val = st.number_input("粘性係数 μ [1e-5 Pa s]", value=1.32)
    
    # 計算用定数変換
    R_gas = 8.314
    M = M_val * 1e-3
    mu = mu_val * 1e-5
    v_avg = np.sqrt(8 * R_gas * T / (np.pi * M))
    st.write(f"平均分子速度: {v_avg:.1f} m/s")

# --- 計算ロジック ---
def calc_C_single(L_m, D_m):
    if L_m <= 0 or D_m <= 0: return 1e-20
    r = D_m / 2
    A = np.pi * r**2
    
    # 分子流 (Clausing factor近似)
    alpha = 1 / (1 + (3 * L_m) / (4 * D_m))
    C_mol = (1/4) * A * v_avg * alpha
    
    # 粘性流
    C_visc = (np.pi * D_m**4 * P_avg) / (128 * mu * L_m)
    
    # 直列合成
    return 1 / ((1/C_mol) + (1/C_visc))

# --- メイン画面：モード選択タブ ---
tab1, tab2, tab3, tab4 = st.tabs([
    "① コンダクタンス算出", 
    "② 必要穴数", 
    "③ 穴径の逆算", 
    "④ 板厚の逆算"
])

# ① コンダクタンス算出
with tab1:
    st.subheader("条件からコンダクタンスを計算")
    col1, col2 = st.columns(2)
    L1 = col1.number_input("板厚 L [mm]", value=10.0, key="L1")
    D1 = col2.number_input("穴径 D [mm]", value=2.5, key="D1")
    N1 = st.number_input("穴の数 N [個]", value=2200, step=10, key="N1")
    
    if st.button("計算実行", key="btn1"):
        C_single = calc_C_single(L1*1e-3, D1*1e-3)
        C_total = C_single * N1
        st.success(f"総コンダクタンス: {C_total:.5f} m³/s")
        st.info(f"({C_total*1000:.2f} L/s)")

# ② 必要穴数
with tab2:
    st.subheader("目標値に必要な穴の数を計算")
    col1, col2 = st.columns(2)
    L2 = col1.number_input("板厚 L [mm]", value=10.0, key="L2")
    D2 = col2.number_input("穴径 D [mm]", value=3.0, key="D2")
    C_target2 = st.number_input("目標コンダクタンス [m³/s]", value=0.0157, format="%.5f", key="Ct2")
    
    if st.button("計算実行", key="btn2"):
        C_single = calc_C_single(L2*1e-3, D2*1e-3)
        N2 = C_target2 / C_single
        st.success(f"必要な穴の数: {N2:.1f} 個")
        st.info(f"目安: {int(round(N2))} 個")

# ③ 穴径の逆算
with tab3:
    st.subheader("穴数と厚さから、最適な穴径を逆算")
    col1, col2 = st.columns(2)
    L3 = col1.number_input("板厚 L [mm]", value=10.0, key="L3")
    N3 = col2.number_input("穴の数 N [個]", value=1000, key="N3")
    C_target3 = st.number_input("目標コンダクタンス [m³/s]", value=0.0157, format="%.5f", key="Ct3")
    
    if st.button("計算実行", key="btn3"):
        target_single = C_target3 / N3
        def func(D_guess):
            return calc_C_single(L3*1e-3, D_guess) - target_single
        try:
            ans = brentq(func, 1e-5, 0.050) # 0.01mm ~ 50mm探索
            st.success(f"必要な穴径: {ans*1000:.4f} mm")
        except:
            st.error("解が見つかりませんでした。条件を見直してください。")

# ④ 板厚の逆算
with tab4:
    st.subheader("穴径と数から、必要な板厚を逆算")
    col1, col2 = st.columns(2)
    D4 = col1.number_input("穴径 D [mm]", value=2.5, key="D4")
    N4 = col2.number_input("穴の数 N [個]", value=2200, key="N4")
    C_target4 = st.number_input("目標コンダクタンス [m³/s]", value=0.0157, format="%.5f", key="Ct4")
    
    if st.button("計算実行", key="btn4"):
        target_single = C_target4 / N4
        def func(L_guess):
            return calc_C_single(L_guess, D4*1e-3) - target_single
        try:
            ans = brentq(func, 1e-4, 1.0) # 0.1mm ~ 1000mm探索
            st.success(f"必要な板厚: {ans*1000:.4f} mm")
        except:
            st.error("解が見つかりませんでした。")
