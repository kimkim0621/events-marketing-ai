import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="テストアプリ",
    page_icon="🧪",
    layout="wide"
)

def main():
    st.title("🧪 Streamlit Cloud テストアプリ")
    
    # 基本的な情報表示
    st.header("システム情報")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Streamlit Version", st.__version__)
    
    with col2:
        st.metric("Pandas Version", f"{pd.__version__}")
    
    with col3:
        st.metric("現在時刻", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 簡単なデータ表示
    st.header("データ表示テスト")
    
    # サンプルデータ
    data = {
        'カテゴリ': ['A', 'B', 'C', 'D'],
        '値': [10, 20, 30, 40],
        '日付': pd.date_range('2024-01-01', periods=4)
    }
    
    df = pd.DataFrame(data)
    st.dataframe(df)
    
    # 簡単なチャート
    st.header("チャートテスト")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['a', 'b', 'c']
    )
    st.line_chart(chart_data)
    
    # 入力フォーム
    st.header("入力フォームテスト")
    
    with st.form("test_form"):
        name = st.text_input("名前")
        age = st.number_input("年齢", min_value=0, max_value=120, value=25)
        hobby = st.selectbox("趣味", ["読書", "映画鑑賞", "スポーツ", "音楽"])
        
        submitted = st.form_submit_button("送信")
        
        if submitted:
            st.success(f"入力されました: {name}さん（{age}歳）の趣味は{hobby}です")
    
    # 状態管理テスト
    st.header("状態管理テスト")
    
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    
    if st.button("カウンターを増やす"):
        st.session_state.counter += 1
    
    st.write(f"現在のカウンター: {st.session_state.counter}")
    
    # 接続テスト
    st.header("接続テスト")
    
    if st.button("接続テスト実行"):
        try:
            # 簡単な計算テスト
            result = sum(range(1000))
            st.success(f"計算テスト成功: {result}")
            
            # メモリテスト
            import sys
            st.info(f"メモリ使用量: {sys.getsizeof(chart_data)} bytes")
            
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
    
    # フッター
    st.markdown("---")
    st.markdown("✅ 基本機能が正常に動作しています")

if __name__ == "__main__":
    main() 