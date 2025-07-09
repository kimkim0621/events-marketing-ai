import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import json
import os
import tempfile
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import io
from typing import List, Dict
import plotly.express as px
import plotly.graph_objects as go

# データインポートシステムのインポート
try:
    from data_import_ui import DataImportSystem
except ImportError as e:
    st.error(f"データインポートシステムのインポートエラー: {e}")
    st.error("data_import_ui.pyファイルが見つかりません。")
    st.stop()

# ページ設定
st.set_page_config(
    page_title="イベント集客施策提案AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS - 上部余白を完全に削除
st.markdown("""
<style>
    /* Streamlitのデフォルト設定を完全に上書き */
    .stApp > header {
        display: none !important;
    }
    
    .main > .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }
    
    /* iframeの場合の対策 */
    iframe {
        display: block;
    }
    
    /* 最初の要素の余白を削除 */
    .element-container:first-of-type {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* タイトルのスタイル */
    .main-header {
        font-size: 2rem !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
        text-align: center !important;
        margin: 0 !important;
        padding: 1rem 0 !important;
        background-color: #f8f9fa;
        border-bottom: 2px solid #e9ecef;
    }
    
    /* 列のスタイル */
    .column-panel {
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1.5rem;
        background: #ffffff;
        height: calc(100vh - 100px);
        overflow-y: auto;
    }
    
    .column-panel-left {
        border-radius: 8px 0 0 8px;
    }
    
    .column-panel-right {
        border-radius: 0 8px 8px 0;
        border-left: none;
    }
    
    /* ドラッグハンドル */
    .drag-handle {
        position: absolute;
        width: 4px;
        height: 100%;
        background: #e9ecef;
        cursor: col-resize;
        right: -2px;
        top: 0;
        transition: all 0.2s ease;
    }
    
    .drag-handle:hover {
        background: #1f77b4;
        width: 8px;
        right: -4px;
    }
    
    /* タブのスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        background-color: white;
        border-radius: 4px;
        border: 1px solid #e9ecef;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
        border-color: #1f77b4;
    }
    
    /* その他のスタイル */
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    
    .campaign-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .free-campaign {
        border-left: 4px solid #28a745;
    }
    
    .paid-campaign {
        border-left: 4px solid #ffc107;
    }
</style>

<script>
function setupColumnResize() {
    // Streamlitの列要素を取得
    const columns = document.querySelectorAll('[data-testid="column"]');
    if (columns.length < 2) {
        setTimeout(setupColumnResize, 100);
        return;
    }
    
    const col1 = columns[0];
    const col2 = columns[1];
    const container = col1.parentElement;
    
    // 既存のハンドルを削除
    const existingHandle = document.querySelector('.column-resize-handle');
    if (existingHandle) {
        existingHandle.remove();
    }
    
    // リサイズハンドルを作成
    const handle = document.createElement('div');
    handle.className = 'column-resize-handle';
    handle.style.cssText = `
        position: absolute;
        width: 4px;
        height: 100%;
        background: #e9ecef;
        cursor: col-resize;
        z-index: 1000;
        transition: all 0.2s ease;
    `;
    
    // ハンドルにホバー効果を追加
    handle.onmouseenter = () => {
        handle.style.background = '#1f77b4';
        handle.style.width = '8px';
    };
    
    handle.onmouseleave = () => {
        if (!isResizing) {
            handle.style.background = '#e9ecef';
            handle.style.width = '4px';
        }
    };
    
    container.style.position = 'relative';
    container.appendChild(handle);
    
    let isResizing = false;
    let startX = 0;
    let startCol1Width = 0;
    let startCol2Width = 0;
    
    // ハンドルの位置を更新
    function updateHandlePosition() {
        const col1Rect = col1.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        handle.style.left = (col1Rect.right - containerRect.left - 2) + 'px';
        handle.style.height = containerRect.height + 'px';
    }
    
    updateHandlePosition();
    
    handle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startCol1Width = col1.offsetWidth;
        startCol2Width = col2.offsetWidth;
        
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const deltaX = e.clientX - startX;
        const totalWidth = startCol1Width + startCol2Width;
        const newCol1Width = startCol1Width + deltaX;
        const col1Percent = (newCol1Width / totalWidth) * 100;
        
        // 最小・最大幅の制限（20%〜80%）
        if (col1Percent >= 20 && col1Percent <= 80) {
            col1.style.flex = `0 0 ${col1Percent}%`;
            col2.style.flex = `0 0 ${100 - col1Percent}%`;
            updateHandlePosition();
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            handle.style.background = '#e9ecef';
            handle.style.width = '4px';
        }
    });
    
    // ウィンドウリサイズ時にハンドル位置を更新
    window.addEventListener('resize', updateHandlePosition);
}

// DOM読み込み後に実行
setTimeout(setupColumnResize, 100);
setTimeout(setupColumnResize, 500);
setTimeout(setupColumnResize, 1000);

// MutationObserverで動的な変更を監視
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList') {
            setTimeout(setupColumnResize, 100);
        }
    });
});

if (document.body) {
    observer.observe(document.body, { 
        childList: true, 
        subtree: true
    });
}
</script>
""", unsafe_allow_html=True)

def main():
    """メインアプリケーション"""
    # タイトル
    st.markdown('<h1 class="main-header">🎯 イベント集客施策提案AI</h1>', unsafe_allow_html=True)
    
    # セッション状態の初期化
    if 'show_recommendations' not in st.session_state:
        st.session_state.show_recommendations = False
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    
    # データインポートシステムの初期化
    import_system = DataImportSystem()
    
    # 2列レイアウト
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 施策提案のための情報入力")
        show_proposal_input()
    
    with col2:
        # タブ切り替えUI
        if st.session_state.show_recommendations and st.session_state.recommendations:
            # タブの順序を変更：施策提案結果を左、データインポートを右に
            tab1, tab2 = st.tabs(["🎯 施策提案結果", "📊 データインポート"])
            
            with tab1:
                show_recommendations_in_tab(st.session_state.recommendations)
            
            with tab2:
                show_data_import_interface(import_system)
        else:
            st.markdown("### 📊 データインポート")
            show_data_import_interface(import_system)

def show_proposal_input():
    """施策提案のための情報入力フォーム"""
    # 基本情報
    st.markdown("### 🎯 基本情報")
    event_name = st.text_input("イベント名", placeholder="例: AI技術セミナー")
    
    event_category = st.selectbox(
        "イベントカテゴリ",
        ["conference", "seminar", "workshop", "webinar", "networking", "product_launch"],
        format_func=lambda x: {
            "conference": "カンファレンス",
            "seminar": "セミナー", 
            "workshop": "ワークショップ",
            "webinar": "ウェビナー",
            "networking": "ネットワーキング",
            "product_launch": "製品発表"
        }[x]
    )
    
    event_theme = st.text_area("イベントテーマ・内容", placeholder="例: 最新のAI技術動向と実践事例")
    
    # ターゲット設定
    st.markdown("### 🎯 ターゲット設定")
    
    # 業種選択
    with st.expander("🏢 業種選択", expanded=False):
        # 業種の選択肢（「すべて」を最上段に追加）
        industry_options = [
            "すべて", "輸送用機器", "電気機器", "小売業", "卸売業", "医薬品", "その他製品", "精密機器", 
            "不動産業", "陸運業", "鉄鋼", "鉱業", "石油・石炭製品", "非鉄金属", "空運業", 
            "ガラス・土石製品", "パルプ・紙", "水産・農林業", "銀行業", "サービス業", "情報・通信業", 
            "化学", "保険業", "食料品", "機械", "ゴム製品", "建設業", "証券・商品先物取引業", 
            "電気・ガス業", "海運業", "その他金融業", "繊維製品", "金属製品", "倉庫・運輸関連業", "その他"
        ]
        
        # セッション状態の初期化
        if 'selected_industries_integrated' not in st.session_state:
            st.session_state.selected_industries_integrated = ["情報・通信業", "サービス業"]
        
        # 「すべて」選択の処理
        def on_industries_integrated_change():
            try:
                selected = st.session_state.get('industries_integrated_multiselect', [])
                if "すべて" in selected and "すべて" not in st.session_state.selected_industries_integrated:
                    st.session_state.selected_industries_integrated = industry_options.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_industries_integrated:
                    st.session_state.selected_industries_integrated = []
                elif "すべて" in selected:
                    if len(selected) < len(industry_options):
                        st.session_state.selected_industries_integrated = [opt for opt in selected if opt != "すべて"]
                else:
                    st.session_state.selected_industries_integrated = selected
                    if len(selected) == len(industry_options) - 1:
                        st.session_state.selected_industries_integrated = ["すべて"] + selected
            except Exception as e:
                st.error(f"業種選択でエラー: {str(e)}")
        
        industries = st.multiselect(
            "業種",
            industry_options,
            default=st.session_state.selected_industries_integrated,
            key="industries_integrated_multiselect",
            on_change=on_industries_integrated_change,
            help="複数選択可能です。「すべて」を選択すると全業種が対象になります。"
        )
        
        # 表示用に実際の業種のみを抽出
        industries_actual = [ind for ind in industries if ind != "すべて"] if "すべて" not in industries else [ind for ind in industry_options if ind != "すべて"]
    
    # 職種選択
    with st.expander("👥 職種選択", expanded=False):
        # 職種の選択肢（「すべて」を最上段に追加）
        job_title_options = [
            "すべて", "CTO", "VPoE", "EM", "フロントエンドエンジニア", "インフラエンジニア", 
            "フルスタックエンジニア", "モバイルエンジニア", "セキュリティエンジニア", 
            "アプリケーションエンジニア・ソリューションアーキテクト", "データサイエンティスト", 
            "情報システム", "ネットワークエンジニア", "UXエンジニア", "デザイナー", "学生", 
            "データアナリスト", "CPO", "VPoT/VPoP", "テックリード", "バックエンドエンジニア", 
            "SRE", "プロダクトマネージャー", "DevOpsエンジニア", "QAエンジニア", "機械学習エンジニア", 
            "プロジェクトマネージャー", "SIer", "ゲーム開発エンジニア", "組み込みエンジニア", 
            "エンジニア以外", "データエンジニア"
        ]
        
        # セッション状態の初期化
        if 'selected_job_titles_integrated' not in st.session_state:
            st.session_state.selected_job_titles_integrated = ["CTO", "VPoE", "EM"]
        
        # 「すべて」選択の処理
        def on_job_titles_integrated_change():
            try:
                selected = st.session_state.get('job_titles_integrated_multiselect', [])
                if "すべて" in selected and "すべて" not in st.session_state.selected_job_titles_integrated:
                    st.session_state.selected_job_titles_integrated = job_title_options.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_job_titles_integrated:
                    st.session_state.selected_job_titles_integrated = []
                elif "すべて" in selected:
                    if len(selected) < len(job_title_options):
                        st.session_state.selected_job_titles_integrated = [opt for opt in selected if opt != "すべて"]
                else:
                    st.session_state.selected_job_titles_integrated = selected
                    if len(selected) == len(job_title_options) - 1:
                        st.session_state.selected_job_titles_integrated = ["すべて"] + selected
            except Exception as e:
                st.error(f"職種選択でエラー: {str(e)}")
        
        job_titles = st.multiselect(
            "職種",
            job_title_options,
            default=st.session_state.selected_job_titles_integrated,
            key="job_titles_integrated_multiselect",
            on_change=on_job_titles_integrated_change,
            help="複数選択可能です。「すべて」を選択すると全職種が対象になります。"
        )
        
        # 表示用に実際の職種のみを抽出
        job_titles_actual = [jt for jt in job_titles if jt != "すべて"] if "すべて" not in job_titles else [jt for jt in job_title_options if jt != "すべて"]
    
    # 従業員規模選択
    with st.expander("📊 従業員規模選択", expanded=False):
        # 従業員規模の選択肢（「すべて」を最上段に追加）
        company_size_options = ["すべて", "10名以下", "11名～50名", "51名～100名", "101名～300名", "301名～500名", "501名～1,000名", "1,001～5,000名", "5,001名以上"]
        
        # セッション状態の初期化
        if 'selected_company_sizes_integrated' not in st.session_state:
            st.session_state.selected_company_sizes_integrated = ["101名～300名", "301名～500名"]
        
        # 「すべて」選択の処理
        def on_company_sizes_integrated_change():
            try:
                selected = st.session_state.get('company_sizes_integrated_multiselect', [])
                if "すべて" in selected and "すべて" not in st.session_state.selected_company_sizes_integrated:
                    st.session_state.selected_company_sizes_integrated = company_size_options.copy()
                elif "すべて" not in selected and "すべて" in st.session_state.selected_company_sizes_integrated:
                    st.session_state.selected_company_sizes_integrated = []
                elif "すべて" in selected:
                    if len(selected) < len(company_size_options):
                        st.session_state.selected_company_sizes_integrated = [opt for opt in selected if opt != "すべて"]
                else:
                    st.session_state.selected_company_sizes_integrated = selected
                    if len(selected) == len(company_size_options) - 1:
                        st.session_state.selected_company_sizes_integrated = ["すべて"] + selected
            except Exception as e:
                st.error(f"従業員規模選択でエラー: {str(e)}")
        
        company_sizes = st.multiselect(
            "従業員規模",
            company_size_options,
            default=st.session_state.selected_company_sizes_integrated,
            key="company_sizes_integrated_multiselect",
            on_change=on_company_sizes_integrated_change,
            help="複数選択可能です。「すべて」を選択すると全規模が対象になります。"
        )
        
        # 表示用に実際の従業員規模のみを抽出
        company_sizes_actual = [cs for cs in company_sizes if cs != "すべて"] if "すべて" not in company_sizes else [cs for cs in company_size_options if cs != "すべて"]
    
    # 目標・予算設定
    st.markdown("### 💰 目標・予算設定")
    
    col1, col2 = st.columns(2)
    with col1:
        target_attendees = st.number_input("目標申込人数", min_value=1, value=100, step=10)
        budget = st.number_input("集客予算（円）", min_value=0, value=500000, step=50000)
    
    with col2:
        event_date = st.date_input(
            "開催日",
            value=datetime.now().date() + timedelta(days=30),
            min_value=datetime.now().date()
        )
        is_free_event = st.checkbox("無料イベント", value=True)
    
    event_format = st.selectbox(
        "開催形式",
        ["online", "offline", "hybrid"],
        format_func=lambda x: {"online": "オンライン", "offline": "オフライン", "hybrid": "ハイブリッド"}[x]
    )
    
    # AI予測エンジン選択
    use_ai_engine = st.checkbox("🧠 高度AI予測エンジンを使用", value=False, help="機械学習ベースの高度な予測を行います（ベータ版）")
    
    # 提案実行ボタン
    if st.button("🚀 施策提案を実行", type="primary", use_container_width=True):
        if event_name and event_theme and industries_actual and job_titles_actual:
            with st.spinner("施策を分析中..."):
                recommendations = generate_recommendations(
                    event_name, event_category, event_theme, industries_actual,
                    job_titles_actual, company_sizes_actual, target_attendees, budget,
                    event_date, is_free_event, event_format
                )
                
                # セッション状態を更新
                st.session_state.recommendations = recommendations
                st.session_state.show_recommendations = True
                
                # 成功メッセージを表示
                st.success("✅ 施策提案が完了しました！右側の「🎯 施策提案結果」タブで結果をご確認ください。")
                st.rerun()
        else:
            st.error("必須項目（イベント名、テーマ、業種、職種）を入力してください")

def show_data_import_interface(import_system):
    """データインポートインターフェース"""
    with st.container():
        # データ概要
        st.markdown("### 📈 データ概要")
        summary = import_system.get_data_summary()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("施策実績", summary["campaign_results"])
            st.metric("参加者属性", summary["participants"])
        with col2:
            st.metric("有償メディア", summary["media_data"])
            st.metric("知見データ", summary["knowledge"])
        
        st.markdown("---")
        
        # タブ形式でデータインポート
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 施策実績",
            "👥 参加者属性", 
            "💰 有償メディア",
            "🧠 知見データ"
        ])
        
        with tab1:
            show_campaign_import(import_system)
        
        with tab2:
            show_participant_import(import_system)
        
        with tab3:
            show_media_import(import_system)
        
        with tab4:
            show_knowledge_import(import_system)

def show_campaign_import(import_system):
    """施策実績データのインポート"""
    st.markdown("**CSVファイル一括インポート**")
    
    # CSVテンプレート
    template_csv = """施策名,カンファレンス名,テーマ・カテゴリ,形式,ターゲット(業種),ターゲット(職種),ターゲット(従業員規模),配信数/PV,クリック数,申込(CV数),費用(税抜),CPA
FCメルマガ,AI技術セミナー,AI・機械学習,ハイブリッド,IT・ソフトウェア,エンジニア,すべて,50000,500,50,0,0
Meta広告,AI技術セミナー,AI・機械学習,ハイブリッド,IT・ソフトウェア,エンジニア,すべて,100000,2000,100,1000000,10000"""
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 テンプレートDL",
            data=template_csv,
            file_name="campaign_template.csv",
            mime="text/csv"
        )
    
    with col2:
        uploaded_file = st.file_uploader("CSVファイル", type=['csv'], key="campaign_csv")
    
    if uploaded_file and st.button("インポート", key="import_campaign"):
        result = import_system.import_conference_campaign_csv(uploaded_file)
        if result["success"]:
            st.success(result["message"])
        else:
            st.error(result["error"])
    
    st.markdown("---")
    st.markdown("**個別入力**")
    
    with st.form("campaign_form"):
        col1, col2 = st.columns(2)
        with col1:
            campaign_name = st.text_input("施策名*")
            conference_name = st.text_input("カンファレンス名*")
            theme_category = st.text_input("テーマ・カテゴリ*")
        with col2:
            format_type = st.selectbox("形式*", ["ハイブリッド", "オンライン", "オフライン"])
            target_industry = st.text_input("ターゲット(業種)")
            target_job_title = st.text_input("ターゲット(職種)")
        
        col1, col2 = st.columns(2)
        with col1:
            distribution_count = st.number_input("配信数/PV", min_value=0, value=0)
            click_count = st.number_input("クリック数", min_value=0, value=0)
            conversion_count = st.number_input("申込(CV数)", min_value=0, value=0)
        with col2:
            cost_excluding_tax = st.number_input("費用(税抜)", min_value=0, value=0)
            cpa = st.number_input("CPA", min_value=0, value=0)
        
        submitted = st.form_submit_button("データを追加")
        
        if submitted and campaign_name and conference_name and theme_category:
            campaign_data = {
                'campaign_name': campaign_name,
                'conference_name': conference_name,
                'theme_category': theme_category,
                'format': format_type,
                'target_industry': target_industry,
                'target_job_title': target_job_title,
                'target_company_size': '',
                'distribution_count': distribution_count,
                'click_count': click_count,
                'conversion_count': conversion_count,
                'cost_excluding_tax': cost_excluding_tax,
                'cpa': cpa
            }
            
            result = import_system.add_campaign_data(campaign_data)
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["error"])

def show_participant_import(import_system):
    """参加者属性データのインポート"""
    st.markdown("**CSVファイル一括インポート**")
    
    template_csv = """職種,役職,業種,企業名,従業員規模
エンジニア,シニアエンジニア,IT・ソフトウェア,テック株式会社,101-1000名
マネージャー,開発マネージャー,IT・ソフトウェア,イノベーション株式会社,1001-5000名"""
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 テンプレートDL",
            data=template_csv,
            file_name="participant_template.csv",
            mime="text/csv"
        )
    
    with col2:
        uploaded_file = st.file_uploader("CSVファイル", type=['csv'], key="participant_csv")
    
    if uploaded_file and st.button("インポート", key="import_participant"):
        result = import_system.import_participant_csv(uploaded_file)
        if result["success"]:
            st.success(result["message"])
        else:
            st.error(result["error"])

def show_media_import(import_system):
    """有償メディアデータのインポート"""
    st.markdown("**CSVファイル一括インポート**")
    
    template_csv = """メディア名,リーチ可能数,ターゲット業界,ターゲット職種,ターゲット企業規模,費用(税抜),メディアタイプ,説明,連絡先情報
Meta広告,1000000,IT・ソフトウェア,エンジニア,すべて,2000000,Web広告,Facebook・Instagram広告,meta-ads@example.com"""
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 テンプレートDL",
            data=template_csv,
            file_name="media_template.csv",
            mime="text/csv"
        )
    
    with col2:
        uploaded_file = st.file_uploader("CSVファイル", type=['csv'], key="media_csv")
    
    if uploaded_file and st.button("インポート", key="import_media"):
        result = import_system.import_media_csv(uploaded_file)
        if result["success"]:
            st.success(result["message"])
        else:
            st.error(result["error"])

def show_knowledge_import(import_system):
    """知見データのインポート"""
    st.markdown("**テキスト一括入力**")
    
    bulk_text = st.text_area(
        "知見データ（1行1件）",
        height=150,
        placeholder="例:\nFCメルマガは開封率が高い\nMeta広告は予算をかければリーチ数を増やせる"
    )
    
    if st.button("一括追加", key="bulk_knowledge"):
        if bulk_text.strip():
            lines = [line.strip() for line in bulk_text.split('\n') if line.strip()]
            success_count = 0
            
            for i, line in enumerate(lines, 1):
                knowledge_data = {
                    'title': f"知見 {i}",
                    'content': line,
                    'knowledge_type': 'general',
                    'impact_degree': 1.0,
                    'impact_scope': None,
                    'impact_frequency': '時々',
                    'applicable_conditions': None,
                    'tags': None,
                    'source': "一括入力",
                    'confidence_score': 0.8
                }
                
                result = import_system.add_knowledge_data(knowledge_data)
                if result["success"]:
                    success_count += 1
            
            st.success(f"✅ {success_count}件の知見データを追加しました")
            st.rerun()

def generate_recommendations(event_name, event_category, event_theme, industries,
                           job_titles, company_sizes, target_attendees, budget,
                           event_date, is_free_event, event_format):
    """施策提案の生成（簡易版）"""
    
    # 基本的な施策提案
    recommendations = {
        "event_info": {
            "name": event_name,
            "category": event_category,
            "theme": event_theme,
            "format": event_format,
            "target_attendees": target_attendees,
            "budget": budget,
            "is_free": is_free_event
        },
        "campaigns": [
            {
                "name": "FCメルマガ配信",
                "type": "free",
                "description": "既存メルマガリストを活用した告知",
                "estimated_reach": min(10000, target_attendees * 100),
                "estimated_conversion": target_attendees * 0.3,
                "cost": 0,
                "cpa": 0
            },
            {
                "name": "Meta広告",
                "type": "paid",
                "description": "Facebook・Instagram広告による集客",
                "estimated_reach": min(100000, target_attendees * 500),
                "estimated_conversion": target_attendees * 0.4,
                "cost": budget * 0.6,
                "cpa": (budget * 0.6) / (target_attendees * 0.4) if target_attendees > 0 else 0
            },
            {
                "name": "TechPlay掲載",
                "type": "paid",
                "description": "技術者向けイベントプラットフォーム",
                "estimated_reach": min(50000, target_attendees * 200),
                "estimated_conversion": target_attendees * 0.3,
                "cost": budget * 0.4,
                "cpa": (budget * 0.4) / (target_attendees * 0.3) if target_attendees > 0 else 0
            }
        ],
        "performance_analysis": {
            "total_estimated_reach": 0,
            "total_estimated_conversion": 0,
            "total_cost": 0,
            "average_cpa": 0
        }
    }
    
    # パフォーマンス分析の計算
    total_reach = sum(c["estimated_reach"] for c in recommendations["campaigns"])
    total_conversion = sum(c["estimated_conversion"] for c in recommendations["campaigns"])
    total_cost = sum(c["cost"] for c in recommendations["campaigns"])
    
    recommendations["performance_analysis"] = {
        "total_estimated_reach": total_reach,
        "total_estimated_conversion": total_conversion,
        "total_cost": total_cost,
        "average_cpa": total_cost / total_conversion if total_conversion > 0 else 0
    }
    
    return recommendations

def show_recommendations_in_tab(recommendations):
    """施策提案結果をタブ内に表示"""
    # 概要
    st.markdown("### 📊 概要")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総リーチ数", f"{recommendations['performance_analysis']['total_estimated_reach']:,}")
    with col2:
        st.metric("予想申込数", f"{recommendations['performance_analysis']['total_estimated_conversion']:.0f}")
    with col3:
        st.metric("総費用", f"¥{recommendations['performance_analysis']['total_cost']:,.0f}")
    with col4:
        st.metric("平均CPA", f"¥{recommendations['performance_analysis']['average_cpa']:.0f}")
    
    # 施策一覧
    st.markdown("### 🚀 推奨施策")
    
    for campaign in recommendations["campaigns"]:
        with st.container():
            st.markdown(f"""
            <div class="campaign-card {'free-campaign' if campaign['type'] == 'free' else 'paid-campaign'}">
                <h4>{campaign['name']} {'🆓' if campaign['type'] == 'free' else '💰'}</h4>
                <p>{campaign['description']}</p>
                <div style="display: flex; gap: 20px; margin-top: 10px;">
                    <div><strong>リーチ数:</strong> {campaign['estimated_reach']:,}</div>
                    <div><strong>予想申込:</strong> {campaign['estimated_conversion']:.0f}</div>
                    <div><strong>費用:</strong> ¥{campaign['cost']:,.0f}</div>
                    <div><strong>CPA:</strong> ¥{campaign['cpa']:.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 