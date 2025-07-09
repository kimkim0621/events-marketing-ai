#!/usr/bin/env python3
"""
強化版施策提案エンジン
- データ駆動型の提案
- 過去実績の活用
- ターゲット最適化
- 予算効率化
- 知見ベース提案
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

class EnhancedRecommendationEngine:
    """強化版施策提案エンジン"""
    
    def __init__(self, db_path: str = "events_marketing.db"):
        self.db_path = db_path
        self.ensure_tables()
        
    def ensure_tables(self):
        """必要なテーブルの確認と作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 施策実績テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT,
                campaign_name TEXT,
                campaign_type TEXT,
                target_industry TEXT,
                target_job_title TEXT,
                target_company_size TEXT,
                reach_count INTEGER,
                conversion_count INTEGER,
                cost_excluding_tax REAL,
                cpa REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_enhanced_recommendations(self, event_data: Dict) -> Dict:
        """
        強化版施策提案の生成
        
        Args:
            event_data: イベント情報（名前、カテゴリ、テーマ、ターゲット、予算等）
            
        Returns:
            提案結果（施策リスト、予測パフォーマンス、根拠等）
        """
        # 1. 過去の類似イベントデータを取得
        similar_events = self._get_similar_events(event_data)
        
        # 2. ターゲット特性に基づく施策候補を生成
        campaign_candidates = self._generate_campaign_candidates(event_data, similar_events)
        
        # 3. 予算制約を考慮した最適化
        optimized_campaigns = self._optimize_budget_allocation(campaign_candidates, event_data['budget'])
        
        # 4. 知見データの適用
        enhanced_campaigns = self._apply_knowledge_insights(optimized_campaigns, event_data)
        
        # 5. パフォーマンス予測
        performance_predictions = self._predict_performance(enhanced_campaigns, event_data)
        
        return {
            "event_info": event_data,
            "campaigns": enhanced_campaigns,
            "performance_analysis": performance_predictions,
            "recommendation_basis": self._generate_recommendation_basis(similar_events, enhanced_campaigns)
        }
    
    def _get_similar_events(self, event_data: Dict) -> List[Dict]:
        """類似イベントの取得"""
        conn = sqlite3.connect(self.db_path)
        
        # 類似条件でのクエリ
        query = '''
            SELECT DISTINCT event_name, campaign_name, campaign_type,
                   target_industry, target_job_title, target_company_size,
                   AVG(reach_count) as avg_reach,
                   AVG(conversion_count) as avg_conversion,
                   AVG(cost_excluding_tax) as avg_cost,
                   AVG(cpa) as avg_cpa
            FROM campaign_performance
            WHERE 1=1
        '''
        
        params = []
        
        # ターゲット業界での絞り込み
        if event_data.get('industries'):
            placeholders = ','.join(['?' for _ in event_data['industries']])
            query += f" AND target_industry IN ({placeholders})"
            params.extend(event_data['industries'])
        
        query += " GROUP BY event_name, campaign_name"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df.to_dict('records')
    
    def _generate_campaign_candidates(self, event_data: Dict, similar_events: List[Dict]) -> List[Dict]:
        """施策候補の生成"""
        candidates = []
        
        # 基本施策（常に含める）
        base_campaigns = [
            {
                "name": "FCメルマガ配信",
                "type": "free",
                "channel": "email",
                "description": "既存メルマガリストを活用した告知",
                "base_reach": 8000,
                "base_conversion_rate": 0.04,
                "cost": 0,
                "confidence": 0.9
            },
            {
                "name": "SNS有機投稿",
                "type": "free", 
                "channel": "social",
                "description": "X(Twitter)、LinkedIn等での告知",
                "base_reach": 5000,
                "base_conversion_rate": 0.02,
                "cost": 0,
                "confidence": 0.8
            }
        ]
        
        # 予算がある場合の有料施策
        if event_data['budget'] > 0:
            # 過去実績から効果的な施策を抽出
            if similar_events:
                # CPA効率の良い施策を優先
                effective_campaigns = sorted(
                    [e for e in similar_events if e['avg_cpa'] and e['avg_cpa'] > 0],
                    key=lambda x: x['avg_cpa']
                )[:5]
                
                for campaign in effective_campaigns:
                    candidates.append({
                        "name": campaign['campaign_name'],
                        "type": "paid",
                        "channel": self._determine_channel(campaign['campaign_name']),
                        "description": f"過去実績: CPA ¥{int(campaign['avg_cpa']):,}",
                        "base_reach": int(campaign['avg_reach']),
                        "base_conversion_rate": campaign['avg_conversion'] / campaign['avg_reach'] if campaign['avg_reach'] > 0 else 0.03,
                        "cost": campaign['avg_cost'],
                        "confidence": 0.85,
                        "historical_data": campaign
                    })
            
            # デフォルト有料施策
            default_paid = [
                {
                    "name": "Meta広告（Facebook/Instagram）",
                    "type": "paid",
                    "channel": "paid_social",
                    "description": "精密なターゲティングが可能",
                    "base_reach": 50000,
                    "base_conversion_rate": 0.025,
                    "cost": min(event_data['budget'] * 0.4, 2000000),
                    "confidence": 0.7
                },
                {
                    "name": "Google広告",
                    "type": "paid",
                    "channel": "paid_search",
                    "description": "検索連動型広告",
                    "base_reach": 30000,
                    "base_conversion_rate": 0.035,
                    "cost": min(event_data['budget'] * 0.3, 1500000),
                    "confidence": 0.75
                }
            ]
            
            # 既存候補にない施策を追加
            existing_names = [c['name'] for c in candidates]
            for campaign in default_paid:
                if campaign['name'] not in existing_names:
                    candidates.append(campaign)
        
        return base_campaigns + candidates
    
    def _determine_channel(self, campaign_name: str) -> str:
        """キャンペーン名からチャネルを推定"""
        name_lower = campaign_name.lower()
        if 'メール' in name_lower or 'mail' in name_lower:
            return 'email'
        elif 'meta' in name_lower or 'facebook' in name_lower or 'instagram' in name_lower:
            return 'paid_social'
        elif 'google' in name_lower or '検索' in name_lower:
            return 'paid_search'
        elif 'techplay' in name_lower or 'connpass' in name_lower:
            return 'event_platform'
        else:
            return 'other'
    
    def _optimize_budget_allocation(self, candidates: List[Dict], budget: float) -> List[Dict]:
        """予算配分の最適化"""
        # 無料施策は全て含める
        free_campaigns = [c for c in candidates if c['type'] == 'free']
        paid_campaigns = [c for c in candidates if c['type'] == 'paid']
        
        if not paid_campaigns or budget == 0:
            return free_campaigns
        
        # 有料施策の効率性でソート（信頼度とコンバージョン率を考慮）
        paid_campaigns.sort(
            key=lambda x: x['confidence'] * x['base_conversion_rate'], 
            reverse=True
        )
        
        # 予算制約内で施策を選択
        selected_paid = []
        remaining_budget = budget
        
        for campaign in paid_campaigns:
            if campaign['cost'] <= remaining_budget:
                selected_paid.append(campaign)
                remaining_budget -= campaign['cost']
            elif remaining_budget > budget * 0.1:  # 予算の10%以上残っている場合
                # コストを調整して追加
                adjusted_campaign = campaign.copy()
                adjusted_campaign['cost'] = remaining_budget
                adjusted_campaign['base_reach'] = int(
                    campaign['base_reach'] * (remaining_budget / campaign['cost'])
                )
                selected_paid.append(adjusted_campaign)
                break
        
        return free_campaigns + selected_paid
    
    def _apply_knowledge_insights(self, campaigns: List[Dict], event_data: Dict) -> List[Dict]:
        """知見データの適用"""
        try:
            from internal_data_system import InternalDataSystem
            data_system = InternalDataSystem(self.db_path)
            
            # イベント条件の準備
            event_conditions = {
                "target_audience": {
                    "industries": event_data.get('industries', []),
                    "job_titles": event_data.get('job_titles', []),
                    "company_sizes": event_data.get('company_sizes', [])
                },
                "budget": event_data.get('budget', 0),
                "category": event_data.get('event_category', ''),
                "format": event_data.get('event_format', '')
            }
            
            # 適用可能な知見を取得
            knowledge_list = data_system.get_applicable_knowledge(event_conditions)
            
            # 各施策に知見を適用
            for campaign in campaigns:
                for knowledge in knowledge_list:
                    if self._is_knowledge_applicable_to_campaign(knowledge, campaign):
                        # 影響度に基づいてパフォーマンスを調整
                        impact = knowledge.get('impact_score', 1.0)
                        campaign['base_reach'] = int(campaign['base_reach'] * (1 + (impact - 1) * 0.2))
                        campaign['base_conversion_rate'] *= (1 + (impact - 1) * 0.3)
                        
                        # 知見情報を追加
                        if 'applied_knowledge' not in campaign:
                            campaign['applied_knowledge'] = []
                        campaign['applied_knowledge'].append({
                            'title': knowledge['title'],
                            'impact': impact
                        })
            
        except Exception as e:
            print(f"知見データ適用エラー: {e}")
        
        return campaigns
    
    def _is_knowledge_applicable_to_campaign(self, knowledge: Dict, campaign: Dict) -> bool:
        """知見が施策に適用可能かを判定"""
        content = knowledge.get('content', '').lower()
        campaign_name = campaign['name'].lower()
        
        # キーワードマッチング
        keywords = {
            'email': ['メール', 'mail', 'メルマガ'],
            'paid_social': ['meta', 'facebook', 'instagram', 'sns広告'],
            'paid_search': ['google', '検索広告', 'リスティング'],
            'event_platform': ['techplay', 'connpass', 'イベントプラットフォーム']
        }
        
        channel = campaign.get('channel', '')
        if channel in keywords:
            return any(keyword in content for keyword in keywords[channel])
        
        return campaign_name in content
    
    def _predict_performance(self, campaigns: List[Dict], event_data: Dict) -> Dict:
        """パフォーマンス予測"""
        total_reach = 0
        total_conversions = 0
        total_cost = 0
        
        for campaign in campaigns:
            # ターゲット規模に基づく調整
            audience_factor = self._calculate_audience_factor(event_data)
            
            # 予測値の計算
            reach = campaign['base_reach'] * audience_factor
            conversions = reach * campaign['base_conversion_rate']
            
            campaign['estimated_reach'] = int(reach)
            campaign['estimated_conversions'] = int(conversions)
            campaign['estimated_cost'] = campaign['cost']
            campaign['estimated_cpa'] = campaign['cost'] / conversions if conversions > 0 else 0
            
            total_reach += reach
            total_conversions += conversions
            total_cost += campaign['cost']
        
        # 重複を考慮した調整（複数施策でリーチが重なる）
        adjusted_reach = total_reach * 0.85
        adjusted_conversions = total_conversions * 0.9
        
        return {
            "total_estimated_reach": int(adjusted_reach),
            "total_estimated_conversions": int(adjusted_conversions),
            "total_cost": total_cost,
            "average_cpa": total_cost / adjusted_conversions if adjusted_conversions > 0 else 0,
            "conversion_rate": adjusted_conversions / adjusted_reach if adjusted_reach > 0 else 0,
            "target_achievement_rate": adjusted_conversions / event_data['target_attendees'] if event_data.get('target_attendees', 0) > 0 else 0
        }
    
    def _calculate_audience_factor(self, event_data: Dict) -> float:
        """オーディエンス規模に基づく調整係数"""
        factor = 1.0
        
        # 業界数による調整
        num_industries = len(event_data.get('industries', []))
        if num_industries > 5:
            factor *= 1.2  # 幅広い業界
        elif num_industries == 1:
            factor *= 0.8  # 特定業界に絞り込み
        
        # 無料/有料による調整
        if event_data.get('is_free_event', True):
            factor *= 1.3
        else:
            factor *= 0.7
        
        return factor
    
    def _generate_recommendation_basis(self, similar_events: List[Dict], campaigns: List[Dict]) -> Dict:
        """提案根拠の生成"""
        basis = {
            "data_sources": [],
            "confidence_level": "medium",
            "key_insights": []
        }
        
        if similar_events:
            basis["data_sources"].append(f"過去{len(similar_events)}件の類似イベント実績")
            basis["confidence_level"] = "high"
            
            # 平均パフォーマンスを計算
            avg_cpa = np.mean([e['avg_cpa'] for e in similar_events if e.get('avg_cpa', 0) > 0])
            if avg_cpa > 0:
                basis["key_insights"].append(f"類似イベントの平均CPA: ¥{int(avg_cpa):,}")
        
        # 知見の適用状況
        knowledge_applied = sum(len(c.get('applied_knowledge', [])) for c in campaigns)
        if knowledge_applied > 0:
            basis["data_sources"].append(f"{knowledge_applied}件の社内知見を適用")
            basis["key_insights"].append("過去の成功パターンに基づく最適化済み")
        
        return basis 