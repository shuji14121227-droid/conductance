import streamlit as st
import pandas as pd
import datetime

# ページ設定
st.set_page_config(page_title="Etching Data Logger", layout="wide")
st.title("⚗️ Etching Data Logger")
st.caption("Input: Initial PR / Etch Depth / Total Step (PR + Depth)")

# --- 1. セッション状態の初期化（履歴データ保存用） ---
if 'etching_history' not in st.session_state:
    st.session_state.etching_history = pd.DataFrame(columns=[
        "Date", "Sample ID", "Time(min)", 
        "Mat. Depth(nm)", "Total Step(nm)", "Rem. PR(nm)", "PR Loss(nm)",
        "Mat. ER(nm/min)", "PR ER(nm/min)", "Selectivity", "Uniformity(±%)"
    ])

# --- 2. サイドバー：データ入力フォーム ---
with st.sidebar:
    st.header("📝 Measurement Inputs")
    
    # 基本情報
    sample_id = st.text_input("Sample ID", "Sample-001")
    process_time = st.number_input("Etching Time [min]", value=10.0, min_value=0.1)
    
    st.markdown("---")
    st.subheader("1. Initial Photoresist")
    # 元のレジスト厚
    pr_initial = st.number_input("Original PR Thickness [nm]", value=1000.0)

    st.markdown("---")
    st.subheader("2. Material Etch Depth")
    st.caption("材料のエッチング深さ (複数入力で平均算出)")
    # 複数入力して平均を取る
    mat_depth_str = st.text_area(
        "Measured Depths [nm] (Space separated)", 
        "500 510 495 505"
    )

    st.markdown("---")
    st.subheader("3. Total Step Height")
    st.caption("エッチング後の「レジスト + エッチング深さ」")
    # 複数入力して平均を取る
    total_step_str = st.text_area(
        "Measured Total Steps [nm] (Space separated)", 
        "1300 1310 1290 1305"
    )
    
    add_btn = st.button("Calculate & Add", type="primary")

# --- 3. 計算ロジック ---
if add_btn:
    try:
        # 文字列を数値リストに変換
        depth_values = [float(x) for x in mat_depth_str.split()]
        step_values = [float(x) for x in total_step_str.split()]
        
        if len(depth_values) > 0 and len(step_values) > 0 and process_time > 0:
            # A. 平均値の計算
            avg_mat_depth = sum(depth_values) / len(depth_values)
            avg_total_step = sum(step_values) / len(step_values)
            
            # B. レジスト関連の逆算
            # 残っているレジスト厚 = (トータル段差) - (エッチング深さ)
            avg_rem_pr = avg_total_step - avg_mat_depth
            
            # 削れたレジスト量 (Loss) = 初期値 - 残り
            pr_loss = pr_initial - avg_rem_pr
            
            # C. レート計算
            mat_rate = avg_mat_depth / process_time
            pr_rate = pr_loss / process_time
            
            # D. 選択比 (Selectivity)
            if pr_rate > 0:
                selectivity = mat_rate / pr_rate
            else:
                selectivity = 9999.9 # エラー回避
            
            # E. 均一性 (Material Depth Uniformity)
            # Formula: (Max - Min) / (2 * Avg) * 100
            d_max = max(depth_values)
            d_min = min(depth_values)
            if avg_mat_depth > 0:
                uniformity = ((d_max - d_min) / (2 * avg_mat_depth)) * 100
            else:
                uniformity = 0.0
            
            # 結果を辞書にまとめる
            new_entry = {
                "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Sample ID": sample_id,
                "Time(min)": process_time,
                "Mat. Depth(nm)": f"{avg_mat_depth:.1f}",
                "Total Step(nm)": f"{avg_total_step:.1f}",
                "Rem. PR(nm)": f"{avg_rem_pr:.1f}",
                "PR Loss(nm)": f"{pr_loss:.1f}",
                "Mat. ER(nm/min)": f"{mat_rate:.2f}",
                "PR ER(nm/min)": f"{pr_rate:.2f}",
                "Selectivity": f"{selectivity:.2f}",
                "Uniformity(±%)": f"{uniformity:.2f}"
            }
            
            # 履歴に追加
            new_df = pd.DataFrame([new_entry])
            st.session_state.etching_history = pd.concat(
                [new_df, st.session_state.etching_history], 
                ignore_index=True
            )
            
            st.success(f"Added {sample_id} to history!")
            
        else:
            st.error("数値を入力してください。")
            
    except ValueError:
        st.error("入力エラー: 数値をスペース区切りで入力してください (例: 500 510)")

# --- 4. 結果表示エリア ---

# 最新の結果を大きく表示
if not st.session_state.etching_history.empty:
    latest = st.session_state.etching_history.iloc[0]
    
    st.subheader(f"📊 Result: {latest['Sample ID']}")
    
    # 1段目: レートと選択比
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Material ER", f"{latest['Mat. ER(nm/min)']} nm/min")
    col2.metric("PR Etch Rate", f"{latest['PR ER(nm/min)']} nm/min")
    col3.metric("Selectivity", f"{latest['Selectivity']}")
    col4.metric("Uniformity", f"± {latest['Uniformity(±%)']} %")
    
    # 2段目: 深さの詳細
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Depth", f"{latest['Mat. Depth(nm)']} nm")
    col2.metric("Avg Total Step", f"{latest['Total Step(nm)']} nm")
    col3.metric("Remaining PR", f"{latest['Rem. PR(nm)']} nm")
    col4.metric("PR Loss", f"{latest['PR Loss(nm)']} nm")

# 履歴テーブル
st.markdown("---")
st.subheader("🗂️ Experiment History")
st.dataframe(st.session_state.etching_history, use_container_width=True)

# CSVダウンロード
csv = st.session_state.etching_history.to_csv(index=False).encode('utf-8')
st.download_button(
    label="💾 Download Data as CSV",
    data=csv,
    file_name='etching_log.csv',
    mime='text/csv',
)
