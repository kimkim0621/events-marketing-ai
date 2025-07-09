#!/usr/bin/env python3
"""
更新されたStreamlitアプリケーション
新しいデータベース構造と連携
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
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
</style>
""", unsafe_allow_html=True)

class MarketingAISystem:
    """マーケティングAIシステム"""
    
    def __init__(self):
        self.import_system = DataImportSystem()
    
    def get_campaign_performance_data(self, conference_name: str = None) -> pd.DataFrame:
        """キャンペーンパフォーマンスデータの取得"""
        conn = sqlite3.connect(self.import_system.db_path)
        
        if conference_name:
            query = """
                SELECT * FROM conference_campaign_results 
                WHERE conference_name = ?
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(conference_name,))
        else:
            query = """
                SELECT * FROM conference_campaign_results 
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def get_participant_data(self, conference_name: str = None) -> pd.DataFrame:
        """参加者データの取得"""
        conn = sqlite3.connect(self.import_system.db_path)
        
        if conference_name:
            query = """
                SELECT * FROM conference_participants 
                WHERE conference_name = ?
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(conference_name,))
        else:
            query = """
                SELECT * FROM conference_participants 
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def get_media_data(self) -> pd.DataFrame:
        """メディアデータの取得"""
        conn = sqlite3.connect(self.import_system.db_path)
        query = "SELECT * FROM paid_media_data ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_knowledge_data(self, knowledge_type: str = None) -> pd.DataFrame:
        """知見データの取得"""
        conn = sqlite3.connect(self.import_system.db_path)
        
        if knowledge_type:
            query = """
                SELECT * FROM knowledge_database 
                WHERE knowledge_type = ?
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(knowledge_type,))
        else:
            query = """
                SELECT * FROM knowledge_database 
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def analyze_campaign_effectiveness(self, df: pd.DataFrame) -> Dict:
        """キャンペーン効果分析"""
        if df.empty:
            return {"error": "データがありません"}
        
        # 基本統計
        total_campaigns = len(df)
        total_cost = df['cost_excluding_tax'].fillna(0).sum()
        total_conversions = df['conversion_count'].fillna(0).sum()
        avg_cpa = df['cpa'].fillna(0).mean()
        
        # 施策別パフォーマンス
        campaign_performance = df.groupby('campaign_name').agg({
            'conversion_count': 'sum',
            'cost_excluding_tax': 'sum',
            'cpa': 'mean'
        }).fillna(0)
        
        # カンファレンス別パフォーマンス
        conference_performance = df.groupby('conference_name').agg({
            'conversion_count': 'sum',
            'cost_excluding_tax': 'sum',
            'cpa': 'mean'
        }).fillna(0)
        
        return {
            "total_campaigns": total_campaigns,
            "total_cost": total_cost,
            "total_conversions": total_conversions,
            "avg_cpa": avg_cpa,
            "campaign_performance": campaign_performance,
            "conference_performance": conference_performance
        }
    
    def generate_campaign_recommendations(self, target_audience: Dict, budget: int) -> List[Dict]:
        """キャンペーン推奨の生成"""
        # 過去のデータから学習
        df = self.get_campaign_performance_data()
        
        if df.empty:
            return self._generate_basic_recommendations(target_audience, budget)
        
        # 類似のターゲット・予算の成功事例を分析
        similar_campaigns = df[
            (df['target_industry'] == target_audience.get('industry', 'すべて')) |
            (df['target_job_title'] == target_audience.get('job_title', 'すべて'))
        ]
        
        recommendations = []
        
        if not similar_campaigns.empty:
            # 成功事例に基づく推奨
            top_campaigns = similar_campaigns.nlargest(5, 'conversion_count')
            
            for _, campaign in top_campaigns.iterrows():
                rec = {
                    "campaign_name": campaign['campaign_name'],
                    "expected_conversions": int(campaign['conversion_count']),
                    "estimated_cost": int(campaign['cost_excluding_tax'] or 0),
                    "expected_cpa": int(campaign['cpa'] or 0),
                    "confidence": 0.8,
                    "reason": f"過去の{campaign['conference_name']}で{campaign['conversion_count']}件の成果",
                    "media_type": "実績あり"
                }
                recommendations.append(rec)
        
        # 予算に応じた追加推奨
        if budget > 1000000:  # 100万円以上
            recommendations.extend(self._generate_premium_recommendations(target_audience, budget))
        else:
            recommendations.extend(self._generate_budget_recommendations(target_audience, budget))
        
        return recommendations[:10]  # 上位10件
    
    def _generate_basic_recommendations(self, target_audience: Dict, budget: int) -> List[Dict]:
        """基本的な推奨生成"""
        basic_recs = [
            {
                "campaign_name": "FCメルマガ",
                "expected_conversions": 50,
                "estimated_cost": 0,
                "expected_cpa": 0,
                "confidence": 0.9,
                "reason": "高い開封率とコンバージョン率",
                "media_type": "無料施策"
            },
            {
                "campaign_name": "Meta広告",
                "expected_conversions": 100,
                "estimated_cost": min(budget * 0.6, 2000000),
                "expected_cpa": 15000,
                "confidence": 0.7,
                "reason": "幅広いリーチと詳細なターゲティング",
                "media_type": "有料広告"
            },
            {
                "campaign_name": "TechPlay集客支援",
                "expected_conversions": 80,
                "estimated_cost": 700000,
                "expected_cpa": 8750,
                "confidence": 0.8,
                "reason": "技術者向けイベントで高い効果",
                "media_type": "集客支援"
            }
        ]
        
        return [rec for rec in basic_recs if rec['estimated_cost'] <= budget]
    
    def _generate_premium_recommendations(self, target_audience: Dict, budget: int) -> List[Dict]:
        """プレミアム推奨生成"""
        return [
            {
                "campaign_name": "JBpress連載",
                "expected_conversions": 200,
                "estimated_cost": 2000000,
                "expected_cpa": 10000,
                "confidence": 0.7,
                "reason": "長期的なブランド認知向上",
                "media_type": "メディア連載"
            },
            {
                "campaign_name": "日経Xtech掲載",
                "expected_conversions": 150,
                "estimated_cost": 2000000,
                "expected_cpa": 13333,
                "confidence": 0.8,
                "reason": "技術系読者への高い訴求力",
                "media_type": "メディア掲載"
            }
        ]
    
    def _generate_budget_recommendations(self, target_audience: Dict, budget: int) -> List[Dict]:
        """予算重視推奨生成"""
        return [
            {
                "campaign_name": "Connpass投稿",
                "expected_conversions": 30,
                "estimated_cost": 0,
                "expected_cpa": 0,
                "confidence": 0.8,
                "reason": "技術コミュニティへの直接アプローチ",
                "media_type": "無料施策"
            },
            {
                "campaign_name": "X（Twitter）投稿",
                "expected_conversions": 20,
                "estimated_cost": 0,
                "expected_cpa": 0,
                "confidence": 0.6,
                "reason": "SNSでの拡散効果",
                "media_type": "SNS"
            }
        ]

def main():
    """メインアプリケーション"""
    st.markdown('<h1 class="main-header">🎯 イベント集客施策提案AI</h1>', unsafe_allow_html=True)
    
    # システム初期化
    ai_system = MarketingAISystem()
    
    # メニュー
    menu = st.sidebar.selectbox(
        "メニュー",
        ["🎯 施策提案", "📊 データ分析", "📥 データインポート", "🧠 知見管理"]
    )
    
    if menu == "🎯 施策提案":
        show_campaign_recommendation(ai_system)
    elif menu == "📊 データ分析":
        show_data_analysis(ai_system)
    elif menu == "📥 データインポート":
        show_data_import(ai_system)
    elif menu == "🧠 知見管理":
        show_knowledge_management(ai_system)

def show_campaign_recommendation(ai_system: MarketingAISystem):
    """施策推奨画面"""
    st.header("🎯 イベント集客施策提案")
    
    # 入力フォーム
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 イベント情報")
        event_name = st.text_input("イベント名", placeholder="例: AI技術セミナー")
        event_category = st.selectbox(
            "イベントカテゴリ",
            ["conference", "seminar", "workshop", "webinar"],
            format_func=lambda x: {
                "conference": "カンファレンス",
                "seminar": "セミナー",
                "workshop": "ワークショップ",
                "webinar": "ウェビナー"
            }[x]
        )
        target_attendees = st.number_input("目標参加者数", min_value=1, value=100)
        budget = st.number_input("予算（円）", min_value=0, value=1000000)
    
    with col2:
        st.subheader("🎯 ターゲット設定")
        target_industry = st.selectbox(
            "業界",
            ["すべて", "IT・ソフトウェア", "製造業", "金融", "コンサルティング", "その他"]
        )
        target_job_title = st.selectbox(
            "職種",
            ["すべて", "エンジニア", "マネージャー", "CTO", "VPoE", "その他"]
        )
        target_company_size = st.selectbox(
            "企業規模",
            ["すべて", "1-100名", "101-1000名", "1001-5000名", "5001名以上"]
        )
    
    if st.button("💡 施策提案を生成", type="primary"):
        if event_name:
            with st.spinner("施策を分析中..."):
                target_audience = {
                    "industry": target_industry,
                    "job_title": target_job_title,
                    "company_size": target_company_size
                }
                
                recommendations = ai_system.generate_campaign_recommendations(
                    target_audience, budget
                )
                
                if recommendations:
                    st.success(f"✅ {len(recommendations)}件の施策を提案しました")
                    
                    # 推奨施策の表示
                    for i, rec in enumerate(recommendations, 1):
                        with st.expander(f"💡 推奨施策 {i}: {rec['campaign_name']}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("予想コンバージョン", f"{rec['expected_conversions']}件")
                            with col2:
                                st.metric("推定費用", f"¥{rec['estimated_cost']:,}")
                            with col3:
                                st.metric("予想CPA", f"¥{rec['expected_cpa']:,}")
                            
                            st.write(f"**理由:** {rec['reason']}")
                            st.write(f"**メディアタイプ:** {rec['media_type']}")
                            st.write(f"**信頼度:** {rec['confidence']:.1%}")
                else:
                    st.warning("推奨施策が見つかりませんでした")
        else:
            st.error("イベント名を入力してください")

def show_data_analysis(ai_system: MarketingAISystem):
    """データ分析画面"""
    st.header("📊 データ分析")
    
    # データ概要
    summary = ai_system.import_system.get_data_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("キャンペーン実績", summary["campaign_results"])
    with col2:
        st.metric("参加者データ", summary["participants"])
    with col3:
        st.metric("メディアデータ", summary["media_data"])
    with col4:
        st.metric("知見データ", summary["knowledge"])
    
    # キャンペーンパフォーマンス分析
    if summary["campaign_results"] > 0:
        st.subheader("📈 キャンペーンパフォーマンス分析")
        
        df = ai_system.get_campaign_performance_data()
        analysis = ai_system.analyze_campaign_effectiveness(df)
        
        if "error" not in analysis:
            # 基本統計
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総キャンペーン数", analysis["total_campaigns"])
            with col2:
                st.metric("総コンバージョン", f"{analysis['total_conversions']:.0f}件")
            with col3:
                st.metric("平均CPA", f"¥{analysis['avg_cpa']:,.0f}")
            
            # 施策別パフォーマンス
            if not analysis["campaign_performance"].empty:
                st.subheader("🎯 施策別パフォーマンス")
                
                # グラフ作成
                perf_df = analysis["campaign_performance"].reset_index()
                perf_df = perf_df[perf_df['conversion_count'] > 0]  # コンバージョンがある施策のみ
                
                if not perf_df.empty:
                    fig = px.bar(
                        perf_df.head(10),
                        x='campaign_name',
                        y='conversion_count',
                        title='施策別コンバージョン数'
                    )
                    fig.update_xaxis(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # CPA分析
                    cpa_df = perf_df[perf_df['cpa'] > 0]
                    if not cpa_df.empty:
                        fig2 = px.scatter(
                            cpa_df,
                            x='conversion_count',
                            y='cpa',
                            size='cost_excluding_tax',
                            hover_name='campaign_name',
                            title='コンバージョン数 vs CPA'
                        )
                        st.plotly_chart(fig2, use_container_width=True)
            
            # カンファレンス別パフォーマンス
            if not analysis["conference_performance"].empty:
                st.subheader("🏢 カンファレンス別パフォーマンス")
                
                conf_df = analysis["conference_performance"].reset_index()
                conf_df = conf_df[conf_df['conversion_count'] > 0]
                
                if not conf_df.empty:
                    fig3 = px.pie(
                        conf_df,
                        values='conversion_count',
                        names='conference_name',
                        title='カンファレンス別コンバージョン分布'
                    )
                    st.plotly_chart(fig3, use_container_width=True)
        
        # 生データ表示
        with st.expander("📋 生データ表示"):
            st.dataframe(df)

def show_data_import(ai_system: MarketingAISystem):
    """データインポート画面"""
    st.header("📥 データインポート")
    
    # データインポートUIを組み込み
    from data_import_ui import main as import_main
    import_main()

def show_knowledge_management(ai_system: MarketingAISystem):
    """知見管理画面"""
    st.header("🧠 知見管理")
    
    # 知見データの表示
    knowledge_df = ai_system.get_knowledge_data()
    
    if not knowledge_df.empty:
        st.subheader("📚 登録済み知見")
        
        # 知見タイプ別フィルター
        knowledge_types = knowledge_df['knowledge_type'].unique()
        selected_type = st.selectbox("知見タイプでフィルター", ["すべて"] + list(knowledge_types))
        
        if selected_type != "すべて":
            filtered_df = knowledge_df[knowledge_df['knowledge_type'] == selected_type]
        else:
            filtered_df = knowledge_df
        
        # 知見の表示
        for _, knowledge in filtered_df.iterrows():
            with st.expander(f"💡 {knowledge['title']}"):
                st.write(f"**内容:** {knowledge['content']}")
                st.write(f"**タイプ:** {knowledge['knowledge_type']}")
                st.write(f"**影響度:** {knowledge['impact_degree']}")
                st.write(f"**信頼度:** {knowledge['confidence_score']:.1%}")
                if knowledge['impact_scope']:
                    st.write(f"**影響範囲:** {knowledge['impact_scope']}")
                if knowledge['applicable_conditions']:
                    st.write(f"**適用条件:** {knowledge['applicable_conditions']}")
    else:
        st.info("知見データがありません。データインポートから追加してください。")

if __name__ == "__main__":
    main() 