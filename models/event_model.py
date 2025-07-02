from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class EventCategory(str, Enum):
    """イベントカテゴリ"""
    CONFERENCE = "conference"
    SEMINAR = "seminar"
    WORKSHOP = "workshop"
    WEBINAR = "webinar"
    NETWORKING = "networking"
    PRODUCT_LAUNCH = "product_launch"

class TargetAudience(BaseModel):
    """ターゲットオーディエンス"""
    job_titles: List[str] = Field(..., description="職種リスト")
    industries: List[str] = Field(..., description="業界リスト") 
    company_sizes: List[str] = Field(..., description="企業規模リスト")
    age_range: Optional[Dict[str, int]] = Field(None, description="年齢範囲")
    experience_level: Optional[List[str]] = Field(None, description="経験レベル")

class EventRequest(BaseModel):
    """イベント施策提案リクエスト"""
    event_name: str = Field(..., description="イベント名")
    event_category: EventCategory = Field(..., description="イベントカテゴリ")
    event_theme: str = Field(..., description="イベントテーマ・内容")
    target_audience: TargetAudience = Field(..., description="ターゲットオーディエンス")
    target_attendees: int = Field(..., description="目標参加者数", gt=0)
    budget: int = Field(..., description="集客予算（円）", gt=0)
    event_date: datetime = Field(..., description="イベント開催日")
    registration_deadline: Optional[datetime] = Field(None, description="申込締切日")
    is_free_event: bool = Field(True, description="無料イベントかどうか")
    event_format: Literal["online", "offline", "hybrid"] = Field(..., description="開催形式")
    priority_metrics: List[str] = Field(["conversions", "cost_efficiency"], description="重視する指標")

class CampaignChannel(str, Enum):
    """施策チャネル"""
    EMAIL_MARKETING = "email_marketing"
    SOCIAL_MEDIA = "social_media"
    PAID_ADVERTISING = "paid_advertising"
    CONTENT_MARKETING = "content_marketing"
    PARTNER_PROMOTION = "partner_promotion"
    ORGANIC_SEARCH = "organic_search"
    DIRECT_OUTREACH = "direct_outreach"
    EVENT_LISTING = "event_listing"

class CampaignRecommendation(BaseModel):
    """施策推奨内容"""
    channel: CampaignChannel = Field(..., description="施策チャネル")
    campaign_name: str = Field(..., description="施策名")
    description: str = Field(..., description="施策詳細")
    is_paid: bool = Field(..., description="有償施策かどうか")
    estimated_cost: int = Field(..., description="推定コスト（円）")
    estimated_reach: int = Field(..., description="推定リーチ数")
    estimated_conversions: int = Field(..., description="推定コンバージョン数")
    estimated_ctr: float = Field(..., description="推定CTR")
    estimated_cvr: float = Field(..., description="推定CVR")
    estimated_cpa: int = Field(..., description="推定CPA（円）")
    confidence_score: float = Field(..., description="信頼度スコア", ge=0, le=1)
    implementation_timeline: str = Field(..., description="実施タイムライン")
    required_resources: List[str] = Field(..., description="必要リソース")

class PerformancePrediction(BaseModel):
    """パフォーマンス予測"""
    total_reach: int = Field(..., description="総リーチ数")
    total_conversions: int = Field(..., description="総コンバージョン数")
    total_cost: int = Field(..., description="総コスト（円）")
    overall_ctr: float = Field(..., description="全体CTR")
    overall_cvr: float = Field(..., description="全体CVR")
    overall_cpa: int = Field(..., description="全体CPA（円）")
    goal_achievement_probability: float = Field(..., description="目標達成確率", ge=0, le=1)
    risk_factors: List[str] = Field(..., description="リスク要因")
    optimization_suggestions: List[str] = Field(..., description="最適化提案")

class EventResponse(BaseModel):
    """イベント施策提案レスポンス"""
    event_info: EventRequest = Field(..., description="イベント情報")
    recommended_campaigns: List[CampaignRecommendation] = Field(..., description="推奨施策リスト")
    performance_predictions: PerformancePrediction = Field(..., description="パフォーマンス予測")
    total_estimated_cost: int = Field(..., description="総推定コスト（円）")
    total_estimated_reach: int = Field(..., description="総推定リーチ数")
    total_estimated_conversions: int = Field(..., description="総推定コンバージョン数")
    budget_allocation: Dict[str, float] = Field(..., description="予算配分比率")
    alternative_scenarios: Optional[List[Dict[str, Any]]] = Field(None, description="代替シナリオ")

# 過去データ用モデル
class HistoricalEvent(BaseModel):
    """過去のイベントデータ"""
    event_id: int
    event_name: str
    category: str
    theme: str
    target_attendees: int
    actual_attendees: int
    budget: int
    actual_cost: int
    event_date: datetime
    campaigns_used: List[str]
    performance_metrics: Dict[str, Any]

class MediaPerformance(BaseModel):
    """メディア別パフォーマンスデータ"""
    media_name: str
    media_type: str
    target_audience: Dict[str, Any]
    average_ctr: float
    average_cvr: float
    average_cpa: int
    reach_potential: int
    cost_range: Dict[str, int]
    best_performing_content_types: List[str] 