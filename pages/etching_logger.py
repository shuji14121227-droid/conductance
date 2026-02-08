import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Etching Data Logger", layout="wide")
st.title("⚗️ Etching Data Logger")
st.caption("Calculate Rates, Selectivity, Uniformity & Save History")

# --- 1. セッション状態の初期化（履歴データ保存用） ---
if 'etching_history' not in st.session_state:
    # 履歴を保存する空のデータフレームを作成
    st.session_state.etching_history = pd.DataFrame(columns=[
        "Date", "Sample ID", "Time(min)", 
        "Mat. Depth(nm)", "PR Init(nm)", "PR Final(nm)",
        "Mat. ER(nm/min)", "PR ER(nm/min)", "Selectivity", "Uniformity(±%)"
    ])

# --- 2. サイドバー：データ入力フォーム ---
with st.sidebar:
    st.header("📝 New Data Input")
    
    # サンプル情報
    sample_id = st.text_input("Sample ID", "Sample-001")
    process_time = st.number_input("Etching Time [min]", value=10.0, min_value=0.1)
    
    st.markdown("---")
    st.subheader("1. Target Material (Under Layer)")
    # 均一性を計算するために複数の値を入力可能にする
    mat_depth_str = st.text_area(
        "Etched Depth measurements [nm]\n(Space separated: e.g. 500 510 490 505)", 
        "500"
    )
    
    st.markdown("---")
    st.subheader("2. Photo Resist (PR)")
    pr_initial = st.number_input("PR Initial Thickness [nm]", value=1000.0)
    pr_final = st.number_input("PR Final Thickness [nm]", value=800.0)
    
    add_btn = st.button("Calculate & Add to History", type="primary")

# --- 3. メイン画面：計算と履歴表示 ---

# 計算ロジック
if add_btn:
    try:
        # データの解析
        depth_values = [float(x) for x in mat_depth_str.split()]
        
        if len(depth_values) > 0 and process_time > 0:
            # 平均値の計算
            avg_depth = sum(depth_values) / len(depth_values)
            pr_removed = pr_initial - pr_final
            
            # 1. エッチングレート (ER)
            mat_rate = avg_depth / process_time
            pr_rate = pr_removed / process_time
            
            # 2. 選択比 (Selectivity)
            # ゼロ除算回避
            if pr_rate > 0:
                selectivity = mat_rate / pr_rate
            else:
                selectivity = 9999.9 # Infinite
            
            # 3. 均一性 (Uniformity)
            # Formula: (Max - Min) / (2 * Avg) * 100
            d_max = max(depth_values)
            d_min = min(depth_values)
            if avg_depth > 0:
                uniformity = ((d_max - d_min) / (2 * avg_depth)) * 100
            else:
                uniformity = 0.0
            
            # 結果を辞書にまとめる
            new_entry = {
                "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Sample ID": sample_id,
                "Time(min)": process_time,
                "Mat. Depth(nm)": f"{avg_depth:.1f}",
                "PR Init(nm)": pr_initial,
                "PR Final(nm)": pr_final,
                "Mat. ER(nm/min)": f"{mat_rate:.2f}",
                "PR ER(nm/min)": f"{pr_rate:.2f}",
                "Selectivity": f"{selectivity:.2f}",
                "Uniformity(±%)": f"{uniformity:.2f}"
            }
            
            # データフレームに追加 (concatを使用)
            new_df = pd.DataFrame([new_entry])
            st.session_state.etching_history = pd.concat(
                [new_df, st.session_state.etching_history], 
                ignore_index=True
            )
            
            st.success(f"Added {sample_id} to history!")
            
        else:
            st.error("Please enter valid numeric values.")
            
    except ValueError:
        st.error("Input Error: Ensure measurements are numbers separated by space.")

# --- 4. データの表示エリア ---

# 最新の計算結果をカード表示（直近の確認用）
if not st.session_state.etching_history.empty:
    latest = st.session_state.etching_history.iloc[0]
    
    st.subheader("📊 Latest Calculation Result")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Material ER", f"{latest['Mat. ER(nm/min)']} nm/min")
    col2.metric("PR ER", f"{latest['PR ER(nm/min)']} nm/min")
    col3.metric("Selectivity", f"{latest['Selectivity']}")
    col4.metric("Uniformity", f"± {latest['Uniformity(±%)']} %")

# 過去データの履歴テーブル
st.markdown("---")
st.subheader("🗂️ Data History (Session Only)")
st.info("⚠️ Note: This data will disappear if you refresh the browser. Please download CSV to save.")

# データフレームの表示
st.dataframe(st.session_state.etching_history, use_container_width=True)

# CSVダウンロードボタン
csv = st.session_state.etching_history.to_csv(index=False).encode('utf-8')
st.download_button(
    label="💾 Download Data as CSV",
    data=csv,
    file_name='etching_data_log.csv',
    mime='text/csv',
)
