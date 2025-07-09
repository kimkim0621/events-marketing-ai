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
from data_import_ui import DataImportSystem

# ページ設定
st.set_page_config(
    page_title="イベント集客施策提案AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 基本CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
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
    .input-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .recommendation-section {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """メインアプリケーション"""
    st.markdown('<h1 class="main-header">🎯 イベント集客施策提案AI</h1>', unsafe_allow_html=True)
    
    # 列幅の初期化
    if 'column_width' not in st.session_state:
        st.session_state.column_width = 50
    
    # 境界線ドラッグ用のシンプルなCSS
    st.markdown("""
    <style>
    .drag-divider {
        background: linear-gradient(to right, #e0e0e0, #bbb, #e0e0e0);
        width: 12px;
        margin: 0 -6px;
        position: relative;
        cursor: col-resize;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 500px;
        transition: all 0.2s ease;
        z-index: 100;
    }
    
    .drag-divider:hover {
        background: linear-gradient(to right, #1f77b4, #3498db, #1f77b4);
        width: 16px;
        margin: 0 -8px;
    }
    
    .drag-divider::before {
        content: '⋮⋮⋮';
        color: #666;
        font-size: 14px;
        writing-mode: vertical-lr;
        text-orientation: mixed;
        line-height: 4px;
        user-select: none;
    }
    
    .drag-divider:hover::before {
        color: white;
    }
    
    .column-panel {
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        background: #f8f9fa;
        min-height: 500px;
    }
    
    .column-panel-right {
        background: #ffffff;
    }
    
    .drag-instruction {
        text-align: center;
        color: #666;
        font-size: 0.9em;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background: #e9ecef;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 使用方法の説明
    st.markdown("""
    <div class="drag-instruction">
    💡 中央の境界線をドラッグして列幅を調整してください（現在は視覚的な境界線のみ）
    </div>
    """, unsafe_allow_html=True)
    
    # データインポートシステムの初期化
    import_system = DataImportSystem()
    
    # 3列レイアウト（左パネル、境界線、右パネル）
    col1, col_divider, col2 = st.columns([49, 2, 49])
    
    with col1:
        st.markdown('<div class="column-panel">', unsafe_allow_html=True)
        st.markdown("### 📝 施策提案のための情報入力")
        show_proposal_input()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_divider:
        st.markdown('<div class="drag-divider" title="将来のドラッグ機能用境界線"></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="column-panel column-panel-right">', unsafe_allow_html=True)
        st.markdown("### 📊 データインポート")
        show_data_import_interface(import_system)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 現在の制約についての説明
    with st.expander("⚠️ 技術的制約について"):
        st.markdown("""
        **現在の状況:**
        - Streamlitの制約により、真のドラッグ機能は技術的に困難です
        - 中央の境界線は視覚的な境界線として機能しています
        
        **代替案:**
        - 境界線のドラッグ機能は現在開発中です
        - より高度なカスタムコンポーネントが必要です
        
        **現在の機能:**
        - 2列レイアウトの表示
        - 視覚的な境界線
        - レスポンシブデザイン
        """)

def show_proposal_input():
    """施策提案のための情報入力フォーム"""
    with st.container():
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
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
        
        with st.expander("🏢 業種選択 (34業種)", expanded=True):
            # 業種の選択肢（「すべて」を最上段に追加）
            industry_options = ["すべて", "輸送用機器", "電気機器", "小売業", "卸売業", "医薬品", "その他製品", "精密機器", "不動産業", "陸運業", "鉄鋼", "鉱業", "石油・石炭製品", "非鉄金属", "空運業", "ガラス・土石製品", "パルプ・紙", "水産・農林業", "銀行業", "サービス業", "情報・通信業", "化学", "保険業", "食料品", "機械", "ゴム製品", "建設業", "証券、商品先物取引業", "電気・ガス業", "海運業", "その他金融業", "繊維製品", "金属製品", "倉庫・運輸関連業", "その他"]
            
            # セッション状態の初期化
            if 'selected_industries_integrated' not in st.session_state:
                st.session_state.selected_industries_integrated = ["情報・通信業"]
            
            # 「すべて」選択の処理
            def on_industries_integrated_change():
                try:
                    selected = st.session_state.get('industries_integrated_multiselect', [])
                    if "すべて" in selected and "すべて" not in st.session_state.selected_industries_integrated:
                        # 「すべて」が新しく選択された場合
                        st.session_state.selected_industries_integrated = industry_options.copy()
                    elif "すべて" not in selected and "すべて" in st.session_state.selected_industries_integrated:
                        # 「すべて」が解除された場合
                        st.session_state.selected_industries_integrated = []
                    elif "すべて" in selected:
                        # 「すべて」が選択されている状態で他が変更された場合
                        if len(selected) < len(industry_options):
                            # 一部解除された場合、「すべて」を除外
                            st.session_state.selected_industries_integrated = [opt for opt in selected if opt != "すべて"]
                    else:
                        # 通常の選択
                        st.session_state.selected_industries_integrated = selected
                        # 全て選択されている場合、「すべて」を追加
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
        
        with st.expander("👥 職種選択 (31職種)", expanded=True):
            # 職種の選択肢（「すべて」を最上段に追加）
            job_title_options = ["すべて", "CTO", "VPoE", "EM", "フロントエンドエンジニア", "インフラエンジニア", "フルスタックエンジニア", "モバイルエンジニア", "セキュリティエンジニア", "アプリケーションエンジニア・ソリューションアーキテクト", "データサイエンティスト", "情報システム", "ネットワークエンジニア", "UXエンジニア", "デザイナー", "学生", "データアナリスト", "CPO", "VPoT/VPoP", "テックリード", "バックエンドエンジニア", "SRE", "プロダクトマネージャー", "DevOpsエンジニア", "QAエンジニア", "機械学習エンジニア", "プロジェクトマネージャー", "SIer", "ゲーム開発エンジニア", "組み込みエンジニア", "エンジニア以外", "データエンジニア"]
            
            # セッション状態の初期化
            if 'selected_job_titles_integrated' not in st.session_state:
                st.session_state.selected_job_titles_integrated = ["フロントエンドエンジニア", "バックエンドエンジニア"]
            
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
        
        with st.expander("📊 従業員規模選択 (8段階)", expanded=False):
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
                    
                    # 結果を表示
                    show_recommendations(recommendations)
            else:
                st.error("必須項目（イベント名、テーマ、業種、職種）を入力してください")
        
        st.markdown('</div>', unsafe_allow_html=True)

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

def show_recommendations(recommendations):
    """施策提案結果の表示"""
    st.markdown("---")
    st.markdown("## 🎯 施策提案結果")
    
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