import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json

from models.event_model import EventRequest, CampaignRecommendation, CampaignChannel
from services.data_manager import DataManager

class CampaignOptimizer:
    """施策最適化エンジン"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    async def optimize_portfolio(self, event_request: EventRequest) -> List[CampaignRecommendation]:
        """
        イベント条件に基づいて最適な施策ポートフォリオを生成
        """
        # 過去データの分析
        historical_data = await self._analyze_historical_data(event_request)
        media_data = await self._analyze_media_data(event_request)
        
        # 施策候補の生成
        campaign_candidates = await self._generate_campaign_candidates(
            event_request, historical_data, media_data
        )
        
        # 予算配分の最適化
        optimized_campaigns = await self._optimize_budget_allocation(
            campaign_candidates, event_request
        )
        
        return optimized_campaigns
    
    async def _analyze_historical_data(self, event_request: EventRequest) -> Dict[str, Any]:
        """過去データの分析"""
        # 類似イベントの検索
        budget_range = (
            max(0, event_request.budget * 0.5),
            event_request.budget * 1.5
        )
        
        similar_events = await self.data_manager.get_similar_events(
            event_request.event_category.value,
            event_request.target_audience.dict(),
            budget_range
        )
        
        if not similar_events:
            # デフォルト値を返す
            return {
                "average_ctr": 2.0,
                "average_cvr": 5.0,
                "average_cpa": 10000,
                "successful_channels": ["email_marketing", "social_media"],
                "performance_trends": {}
            }
        
        # パフォーマンス指標の集計
        total_events = len(similar_events)
        avg_ctr = np.mean([event['performance_metrics'].get('ctr', 0) for event in similar_events])
        avg_cvr = np.mean([event['performance_metrics'].get('cvr', 0) for event in similar_events])
        avg_cpa = np.mean([event['performance_metrics'].get('cpa', 0) for event in similar_events if event['performance_metrics'].get('cpa', 0) > 0])
        
        # 成功した施策チャネルの分析
        successful_channels = []
        for event in similar_events:
            if event['actual_attendees'] >= event['target_attendees'] * 0.8:
                successful_channels.extend(event['campaigns_used'])
        
        channel_counts = {}
        for channel in successful_channels:
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        top_channels = sorted(channel_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_similar_events": total_events,
            "average_ctr": avg_ctr,
            "average_cvr": avg_cvr,
            "average_cpa": avg_cpa,
            "successful_channels": [channel[0] for channel in top_channels],
            "performance_trends": channel_counts
        }
    
    async def _analyze_media_data(self, event_request: EventRequest) -> Dict[str, Any]:
        """メディアデータの分析"""
        media_performance = await self.data_manager.get_media_performance()
        
        # ターゲットオーディエンスとの適合性を評価
        relevant_media = []
        for media in media_performance:
            compatibility_score = self._calculate_audience_compatibility(
                event_request.target_audience.dict(),
                media['target_audience']
            )
            
            if compatibility_score > 0.3:  # 30%以上の適合性
                media['compatibility_score'] = compatibility_score
                relevant_media.append(media)
        
        # CPAでソート
        relevant_media.sort(key=lambda x: x['average_cpa'])
        
        return {
            "relevant_media": relevant_media,
            "total_media_count": len(relevant_media),
            "cost_efficient_media": relevant_media[:3] if relevant_media else []
        }
    
    def _calculate_audience_compatibility(self, target_audience: Dict[str, Any], 
                                        media_audience: Dict[str, Any]) -> float:
        """ターゲットオーディエンスとメディアオーディエンスの適合性を計算"""
        compatibility_score = 0.0
        
        # 業界の適合性
        target_industries = set(target_audience.get('industries', []))
        media_industries = set(media_audience.get('industries', []))
        if target_industries and media_industries:
            industry_overlap = len(target_industries.intersection(media_industries))
            compatibility_score += (industry_overlap / len(target_industries)) * 0.5
        
        # 職種の適合性
        target_jobs = set(target_audience.get('job_titles', []))
        media_jobs = set(media_audience.get('job_titles', []))
        if target_jobs and media_jobs:
            job_overlap = len(target_jobs.intersection(media_jobs))
            compatibility_score += (job_overlap / len(target_jobs)) * 0.5
        
        return min(compatibility_score, 1.0)
    
    async def _generate_campaign_candidates(self, event_request: EventRequest,
                                          historical_data: Dict[str, Any],
                                          media_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """施策候補の生成"""
        candidates = []
        
        # 無料施策の生成
        free_campaigns = self._generate_free_campaigns(event_request, historical_data)
        candidates.extend(free_campaigns)
        
        # 有料施策の生成
        paid_campaigns = self._generate_paid_campaigns(event_request, media_data)
        candidates.extend(paid_campaigns)
        
        return candidates
    
    def _generate_free_campaigns(self, event_request: EventRequest, 
                                historical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """無料施策の生成"""
        free_campaigns = []
        
        # メール配信（既存リスト）
        email_campaign = {
            "channel": CampaignChannel.EMAIL_MARKETING,
            "name": "既存リスト向けメール配信",
            "description": "社内の既存顧客・見込み客リストへのメール配信",
            "is_paid": False,
            "estimated_cost": 0,
            "estimated_reach": min(5000, event_request.target_attendees * 20),
            "estimated_ctr": historical_data.get("average_ctr", 2.0),
            "estimated_cvr": historical_data.get("average_cvr", 5.0),
            "confidence_score": 0.8,
            "timeline": "1-2週間前から開始",
            "resources": ["メール配信ツール", "既存リスト", "コンテンツ作成"]
        }
        email_campaign["estimated_conversions"] = int(
            email_campaign["estimated_reach"] * 
            (email_campaign["estimated_ctr"] / 100) * 
            (email_campaign["estimated_cvr"] / 100)
        )
        email_campaign["estimated_cpa"] = 0
        free_campaigns.append(email_campaign)
        
        # SNS投稿
        social_campaign = {
            "channel": CampaignChannel.SOCIAL_MEDIA,
            "name": "SNS有機投稿",
            "description": "Twitter、LinkedIn、Facebookでの有機投稿",
            "is_paid": False,
            "estimated_cost": 0,
            "estimated_reach": min(2000, event_request.target_attendees * 10),
            "estimated_ctr": 1.5,
            "estimated_cvr": 3.0,
            "confidence_score": 0.6,
            "timeline": "3-4週間前から開始",
            "resources": ["SNSアカウント", "コンテンツ作成", "運用担当者"]
        }
        social_campaign["estimated_conversions"] = int(
            social_campaign["estimated_reach"] * 
            (social_campaign["estimated_ctr"] / 100) * 
            (social_campaign["estimated_cvr"] / 100)
        )
        social_campaign["estimated_cpa"] = 0
        free_campaigns.append(social_campaign)
        
        # オーガニック検索
        organic_campaign = {
            "channel": CampaignChannel.ORGANIC_SEARCH,
            "name": "SEO対策・イベントページ最適化",
            "description": "イベントページのSEO最適化とオーガニック検索流入",
            "is_paid": False,
            "estimated_cost": 0,
            "estimated_reach": min(1000, event_request.target_attendees * 5),
            "estimated_ctr": 3.0,
            "estimated_cvr": 8.0,
            "confidence_score": 0.7,
            "timeline": "4-6週間前から開始",
            "resources": ["Webサイト", "SEO知識", "コンテンツ最適化"]
        }
        organic_campaign["estimated_conversions"] = int(
            organic_campaign["estimated_reach"] * 
            (organic_campaign["estimated_ctr"] / 100) * 
            (organic_campaign["estimated_cvr"] / 100)
        )
        organic_campaign["estimated_cpa"] = 0
        free_campaigns.append(organic_campaign)
        
        return free_campaigns
    
    def _generate_paid_campaigns(self, event_request: EventRequest,
                                media_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """有料施策の生成"""
        paid_campaigns = []
        
        # メディア広告
        for media in media_data.get("cost_efficient_media", []):
            campaign = {
                "channel": CampaignChannel.PAID_ADVERTISING,
                "name": f"{media['media_name']}広告",
                "description": f"{media['media_name']}での{media['media_type']}広告",
                "is_paid": True,
                "estimated_cost": min(media['cost_range']['min'], event_request.budget * 0.4),
                "estimated_reach": media['reach_potential'],
                "estimated_ctr": media['average_ctr'],
                "estimated_cvr": media['average_cvr'],
                "confidence_score": media['compatibility_score'],
                "timeline": "2-3週間前から開始",
                "resources": ["広告予算", "クリエイティブ", "運用担当者"]
            }
            
            campaign["estimated_conversions"] = int(
                campaign["estimated_reach"] * 
                (campaign["estimated_ctr"] / 100) * 
                (campaign["estimated_cvr"] / 100)
            )
            
            if campaign["estimated_conversions"] > 0:
                campaign["estimated_cpa"] = int(campaign["estimated_cost"] / campaign["estimated_conversions"])
            else:
                campaign["estimated_cpa"] = media['average_cpa']
            
            paid_campaigns.append(campaign)
        
        # リスティング広告
        listing_campaign = {
            "channel": CampaignChannel.PAID_ADVERTISING,
            "name": "Google/Yahoo!リスティング広告",
            "description": "検索連動型広告によるターゲット獲得",
            "is_paid": True,
            "estimated_cost": min(200000, event_request.budget * 0.3),
            "estimated_reach": 3000,
            "estimated_ctr": 3.5,
            "estimated_cvr": 6.0,
            "confidence_score": 0.75,
            "timeline": "2-4週間前から開始",
            "resources": ["広告予算", "キーワード設定", "ランディングページ"]
        }
        listing_campaign["estimated_conversions"] = int(
            listing_campaign["estimated_reach"] * 
            (listing_campaign["estimated_ctr"] / 100) * 
            (listing_campaign["estimated_cvr"] / 100)
        )
        if listing_campaign["estimated_conversions"] > 0:
            listing_campaign["estimated_cpa"] = int(
                listing_campaign["estimated_cost"] / listing_campaign["estimated_conversions"]
            )
        else:
            listing_campaign["estimated_cpa"] = 10000
        
        paid_campaigns.append(listing_campaign)
        
        return paid_campaigns
    
    async def _optimize_budget_allocation(self, candidates: List[Dict[str, Any]],
                                        event_request: EventRequest) -> List[CampaignRecommendation]:
        """予算配分の最適化"""
        # 無料施策は全て採用
        free_campaigns = [c for c in candidates if not c["is_paid"]]
        paid_campaigns = [c for c in candidates if c["is_paid"]]
        
        # 有料施策の最適化
        remaining_budget = event_request.budget
        selected_paid = []
        
        # CPAの効率性でソート
        paid_campaigns.sort(key=lambda x: x["estimated_cpa"] if x["estimated_conversions"] > 0 else float('inf'))
        
        for campaign in paid_campaigns:
            if remaining_budget >= campaign["estimated_cost"]:
                # 予算に合わせて調整
                adjusted_cost = min(campaign["estimated_cost"], remaining_budget)
                cost_ratio = adjusted_cost / campaign["estimated_cost"]
                
                campaign["estimated_cost"] = adjusted_cost
                campaign["estimated_reach"] = int(campaign["estimated_reach"] * cost_ratio)
                campaign["estimated_conversions"] = int(campaign["estimated_conversions"] * cost_ratio)
                
                selected_paid.append(campaign)
                remaining_budget -= adjusted_cost
                
                if remaining_budget <= 0:
                    break
        
        # CampaignRecommendationオブジェクトに変換
        all_campaigns = free_campaigns + selected_paid
        recommendations = []
        
        for campaign in all_campaigns:
            recommendation = CampaignRecommendation(
                channel=campaign["channel"],
                campaign_name=campaign["name"],
                description=campaign["description"],
                is_paid=campaign["is_paid"],
                estimated_cost=campaign["estimated_cost"],
                estimated_reach=campaign["estimated_reach"],
                estimated_conversions=campaign["estimated_conversions"],
                estimated_ctr=campaign["estimated_ctr"],
                estimated_cvr=campaign["estimated_cvr"],
                estimated_cpa=campaign["estimated_cpa"],
                confidence_score=campaign["confidence_score"],
                implementation_timeline=campaign["timeline"],
                required_resources=campaign["resources"]
            )
            recommendations.append(recommendation)
        
        return recommendations 