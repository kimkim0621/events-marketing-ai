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

# カスタムCSS
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
    
    # サイドバーで列幅の調整
    with st.sidebar:
        st.markdown("### ⚙️ レイアウト設定")
        col_ratio = st.slider(
            "左右の列幅比率",
            min_value=0.2,
            max_value=0.8,
            value=0.5,
            step=0.1,
            help="左の列（施策提案）の幅を調整します。0.5が同じ幅です。"
        )
        st.markdown("---")
    
    # データインポートシステムの初期化
    import_system = DataImportSystem()
    
    # 2列レイアウト（動的な幅調整）
    col1, col2 = st.columns([col_ratio, 1-col_ratio])
    
    with col1:
        st.markdown("## 📝 施策提案のための情報入力")
        show_proposal_input()
    
    with col2:
        st.markdown("## 📊 データインポート")
        show_data_import_interface(import_system)

def show_proposal_input():
    """施策提案のための情報入力フォーム"""
    with st.container():
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        # 基本情報
        st.markdown("### 🎯 基本情報")
        event_name = st.text_input("イベント名", placeholder="例: AI技術セミナー")
        
        col1, col2 = st.columns(2)
        with col1:
            event_category = st.selectbox(
                "イベントカテゴリ",
                ["conference", "seminar", "workshop", "webinar", "networking"],
                format_func=lambda x: {
                    "conference": "カンファレンス",
                    "seminar": "セミナー", 
                    "workshop": "ワークショップ",
                    "webinar": "ウェビナー",
                    "networking": "ネットワーキング"
                }[x]
            )
        
        with col2:
            event_format = st.selectbox(
                "開催形式",
                ["hybrid", "online", "offline"],
                format_func=lambda x: {
                    "hybrid": "ハイブリッド",
                    "online": "オンライン",
                    "offline": "オフライン"
                }[x]
            )
        
        # テーマ
        st.markdown("### 🎨 テーマ")
        event_theme = st.text_area("イベントテーマ", placeholder="例: 最新AI技術の実用化と今後の展望")
        
        # ターゲット設定
        st.markdown("### 🎯 ターゲット設定")
        
        col1, col2 = st.columns(2)
        with col1:
            industries = st.multiselect(
                "ターゲット業界",
                ["IT・ソフトウェア", "製造業", "金融・保険", "小売・EC", "医療・ヘルスケア", "教育", "コンサルティング", "その他"],
                default=["IT・ソフトウェア"]
            )
        
        with col2:
            job_titles = st.multiselect(
                "ターゲット職種",
                ["エンジニア", "マネージャー", "CTO", "データサイエンティスト", "プロダクトマネージャー", "営業", "マーケティング", "その他"],
                default=["エンジニア"]
            )
        
        company_sizes = st.multiselect(
            "企業規模",
            ["1-100名", "101-1000名", "1001-5000名", "5001名以上"],
            default=["101-1000名"]
        )
        
        # 予算・規模
        st.markdown("### 💰 予算・規模")
        col1, col2 = st.columns(2)
        with col1:
            target_attendees = st.number_input("目標参加者数", min_value=1, value=100, step=10)
            budget = st.number_input("予算（円）", min_value=0, value=1000000, step=100000)
        
        with col2:
            event_date = st.date_input("開催予定日", value=datetime.now().date() + timedelta(days=30))
            is_free_event = st.checkbox("無料イベント", value=True)
        
        # 提案実行ボタン
        if st.button("🚀 施策提案を実行", type="primary", use_container_width=True):
            if event_name and event_theme:
                with st.spinner("施策を分析中..."):
                    recommendations = generate_recommendations(
                        event_name, event_category, event_theme, industries,
                        job_titles, company_sizes, target_attendees, budget,
                        event_date, is_free_event, event_format
                    )
                    
                    # 結果を表示
                    show_recommendations(recommendations)
            else:
                st.error("イベント名とテーマを入力してください")
        
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