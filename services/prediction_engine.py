import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

from models.event_model import EventRequest, CampaignRecommendation, PerformancePrediction
from services.data_manager import DataManager

class PredictionEngine:
    """パフォーマンス予測エンジン"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.models = {}
    
    async def predict_performance(self, event_request: EventRequest,
                                campaigns: List[CampaignRecommendation]) -> PerformancePrediction:
        """
        施策ポートフォリオのパフォーマンス予測
        """
        # 基本予測値の計算
        total_reach = sum(c.estimated_reach for c in campaigns)
        total_conversions = sum(c.estimated_conversions for c in campaigns)
        total_cost = sum(c.estimated_cost for c in campaigns)
        
        # 重複リーチの調整
        adjusted_reach = self._adjust_for_reach_overlap(campaigns)
        adjusted_conversions = self._adjust_for_conversion_overlap(campaigns, event_request)
        
        # 全体指標の計算
        overall_ctr = self._calculate_overall_ctr(campaigns)
        overall_cvr = self._calculate_overall_cvr(campaigns, adjusted_reach, adjusted_conversions)
        overall_cpa = int(total_cost / adjusted_conversions) if adjusted_conversions > 0 else 0
        
        # 目標達成確率の計算
        goal_achievement_prob = await self._calculate_goal_achievement_probability(
            event_request, adjusted_conversions
        )
        
        # リスク要因の分析
        risk_factors = await self._analyze_risk_factors(event_request, campaigns)
        
        # 最適化提案の生成
        optimization_suggestions = await self._generate_optimization_suggestions(
            event_request, campaigns, adjusted_conversions
        )
        
        return PerformancePrediction(
            total_reach=int(adjusted_reach),
            total_conversions=int(adjusted_conversions),
            total_cost=total_cost,
            overall_ctr=overall_ctr,
            overall_cvr=overall_cvr,
            overall_cpa=overall_cpa,
            goal_achievement_probability=goal_achievement_prob,
            risk_factors=risk_factors,
            optimization_suggestions=optimization_suggestions
        )
    
    def _adjust_for_reach_overlap(self, campaigns: List[CampaignRecommendation]) -> float:
        """リーチ重複の調整"""
        total_reach = sum(c.estimated_reach for c in campaigns)
        
        # チャネル間の重複率を考慮
        overlap_factors = {
            ("email_marketing", "social_media"): 0.3,
            ("email_marketing", "paid_advertising"): 0.2,
            ("social_media", "paid_advertising"): 0.4,
            ("organic_search", "paid_advertising"): 0.1,
        }
        
        channels = [c.channel.value for c in campaigns]
        overlap_adjustment = 1.0
        
        for i, channel1 in enumerate(channels):
            for j, channel2 in enumerate(channels[i+1:], i+1):
                key = tuple(sorted([channel1, channel2]))
                if key in overlap_factors:
                    overlap_adjustment -= overlap_factors[key] * 0.1
        
        return total_reach * max(0.6, overlap_adjustment)
    
    def _adjust_for_conversion_overlap(self, campaigns: List[CampaignRecommendation],
                                     event_request: EventRequest) -> float:
        """コンバージョン重複の調整"""
        total_conversions = sum(c.estimated_conversions for c in campaigns)
        
        # 複数チャネルからの影響を受けるユーザーの考慮
        multi_touch_factor = 0.85  # 15%の重複を仮定
        
        # イベントタイプによる調整
        event_type_factors = {
            "webinar": 1.1,    # オンラインイベントは参加しやすい
            "conference": 0.9,  # 大規模イベントは参加ハードルが高い
            "workshop": 0.95,   # 実践的な内容は参加意欲が高い
            "seminar": 1.0,     # 標準的な参加率
        }
        
        event_factor = event_type_factors.get(event_request.event_category.value, 1.0)
        
        # 無料/有料による調整
        price_factor = 1.2 if event_request.is_free_event else 0.8
        
        adjusted_conversions = total_conversions * multi_touch_factor * event_factor * price_factor
        
        return max(1, adjusted_conversions)
    
    def _calculate_overall_ctr(self, campaigns: List[CampaignRecommendation]) -> float:
        """全体CTRの計算"""
        total_impressions = sum(c.estimated_reach for c in campaigns)
        total_clicks = sum(c.estimated_reach * (c.estimated_ctr / 100) for c in campaigns)
        
        if total_impressions == 0:
            return 0.0
        
        return (total_clicks / total_impressions) * 100
    
    def _calculate_overall_cvr(self, campaigns: List[CampaignRecommendation],
                              adjusted_reach: float, adjusted_conversions: float) -> float:
        """全体CVRの計算"""
        total_clicks = sum(c.estimated_reach * (c.estimated_ctr / 100) for c in campaigns)
        
        if total_clicks == 0:
            return 0.0
        
        return (adjusted_conversions / total_clicks) * 100
    
    async def _calculate_goal_achievement_probability(self, event_request: EventRequest,
                                                    predicted_conversions: float) -> float:
        """目標達成確率の計算"""
        target_attendees = event_request.target_attendees
        
        # 基本確率の計算
        base_probability = min(1.0, predicted_conversions / target_attendees)
        
        # 過去データに基づく調整
        historical_events = await self.data_manager.get_historical_events()
        
        if historical_events:
            # 類似イベントの成功率を分析
            similar_events = [
                e for e in historical_events 
                if e['category'] == event_request.event_category.value
            ]
            
            if similar_events:
                success_rate = len([
                    e for e in similar_events 
                    if e['actual_attendees'] >= e['target_attendees'] * 0.8
                ]) / len(similar_events)
                
                # 過去の成功率を考慮
                base_probability = base_probability * 0.7 + success_rate * 0.3
        
        # 信頼区間を考慮した調整
        confidence_adjustment = 0.85  # 85%の信頼度
        
        return min(1.0, base_probability * confidence_adjustment)
    
    async def _analyze_risk_factors(self, event_request: EventRequest,
                                  campaigns: List[CampaignRecommendation]) -> List[str]:
        """リスク要因の分析"""
        risk_factors = []
        
        # 予算関連のリスク
        total_cost = sum(c.estimated_cost for c in campaigns)
        if total_cost > event_request.budget * 0.9:
            risk_factors.append("予算使用率が90%を超えており、追加費用が発生する可能性があります")
        
        # 施策の多様性リスク
        paid_campaigns = [c for c in campaigns if c.is_paid]
        if len(paid_campaigns) < 2:
            risk_factors.append("有料施策の種類が少なく、リーチが限定的になる可能性があります")
        
        # 開催日までの期間リスク
        days_until_event = (event_request.event_date - datetime.now()).days
        if days_until_event < 14:
            risk_factors.append("開催まで2週間を切っており、十分な集客期間が確保できない可能性があります")
        elif days_until_event > 90:
            risk_factors.append("開催まで3ヶ月以上あり、早期の告知による関心の低下リスクがあります")
        
        # ターゲット設定のリスク
        if len(event_request.target_audience.industries) > 5:
            risk_factors.append("ターゲット業界が多すぎて、メッセージが散漫になる可能性があります")
        
        # 信頼度スコアのリスク
        avg_confidence = np.mean([c.confidence_score for c in campaigns])
        if avg_confidence < 0.6:
            risk_factors.append("施策の信頼度スコアが低く、予測精度に不安があります")
        
        return risk_factors
    
    async def _generate_optimization_suggestions(self, event_request: EventRequest,
                                               campaigns: List[CampaignRecommendation],
                                               predicted_conversions: float) -> List[str]:
        """最適化提案の生成"""
        suggestions = []
        
        # 目標達成度に基づく提案
        achievement_rate = predicted_conversions / event_request.target_attendees
        
        if achievement_rate < 0.7:
            suggestions.append("目標達成率が70%未満です。追加の有料施策を検討してください")
            suggestions.append("既存リストの活用を強化し、メール配信頻度を増やすことを推奨します")
        
        if achievement_rate > 1.3:
            suggestions.append("目標を大幅に上回る予測です。会場キャパシティの確認をお勧めします")
        
        # 予算効率の提案
        total_cost = sum(c.estimated_cost for c in campaigns)
        if total_cost < event_request.budget * 0.7:
            suggestions.append("予算に余裕があります。追加の広告施策でリーチ拡大を検討してください")
        
        # チャネル多様性の提案
        channel_types = set(c.channel.value for c in campaigns)
        if "content_marketing" not in channel_types:
            suggestions.append("コンテンツマーケティングの追加で、長期的な関係構築を図ることを推奨します")
        
        if "partner_promotion" not in channel_types:
            suggestions.append("パートナー企業との連携で、新規リーチの獲得を検討してください")
        
        # 施策タイミングの提案
        days_until_event = (event_request.event_date - datetime.now()).days
        if days_until_event > 30:
            suggestions.append("開催まで時間があります。段階的な告知戦略で関心を維持してください")
        
        # パフォーマンス改善の提案
        low_performing_campaigns = [c for c in campaigns if c.estimated_cpa > 15000]
        if low_performing_campaigns:
            suggestions.append("CPAが高い施策があります。ターゲティングの見直しを検討してください")
        
        return suggestions 