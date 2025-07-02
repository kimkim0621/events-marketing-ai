from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime

from models.event_model import EventRequest, EventResponse
from services.campaign_optimizer import CampaignOptimizer
from services.data_manager import DataManager
from services.prediction_engine import PredictionEngine

app = FastAPI(
    title="イベント集客施策提案AI",
    description="イベントのテーマ、ターゲット、目標人数、予算に基づいて最適な集客施策ポートフォリオを提案するAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# サービスインスタンス
data_manager = DataManager()
campaign_optimizer = CampaignOptimizer(data_manager)
prediction_engine = PredictionEngine(data_manager)

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    await data_manager.initialize()

@app.get("/")
async def root():
    return {"message": "イベント集客施策提案AI API", "version": "1.0.0"}

@app.post("/api/campaigns/suggest", response_model=EventResponse)
async def suggest_campaigns(event_request: EventRequest):
    """
    イベント情報に基づいて最適な集客施策ポートフォリオを提案
    """
    try:
        # 施策最適化の実行
        optimized_portfolio = await campaign_optimizer.optimize_portfolio(event_request)
        
        # 成果予測の実行
        predictions = await prediction_engine.predict_performance(
            event_request, optimized_portfolio
        )
        
        # 予算配分の計算
        total_cost = sum(c.estimated_cost for c in optimized_portfolio)
        free_cost = sum(c.estimated_cost for c in optimized_portfolio if not c.is_paid)
        paid_cost = sum(c.estimated_cost for c in optimized_portfolio if c.is_paid)
        
        budget_allocation = {
            "無料施策": free_cost / total_cost if total_cost > 0 else 0,
            "有料施策": paid_cost / total_cost if total_cost > 0 else 0
        }
        
        return EventResponse(
            event_info=event_request,
            recommended_campaigns=optimized_portfolio,
            performance_predictions=predictions,
            total_estimated_cost=sum(c.estimated_cost for c in optimized_portfolio),
            total_estimated_reach=sum(c.estimated_reach for c in optimized_portfolio),
            total_estimated_conversions=sum(c.estimated_conversions for c in optimized_portfolio),
            budget_allocation=budget_allocation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"施策提案の生成に失敗しました: {str(e)}")

@app.get("/api/historical-data/events")
async def get_historical_events():
    """過去のイベントデータを取得"""
    try:
        events = await data_manager.get_historical_events()
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得に失敗しました: {str(e)}")

@app.get("/api/media-data/performance")
async def get_media_performance():
    """メディア別パフォーマンスデータを取得"""
    try:
        performance_data = await data_manager.get_media_performance()
        return {"media_performance": performance_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得に失敗しました: {str(e)}")

@app.post("/api/data/upload-event")
async def upload_event_data(event_data: Dict[str, Any]):
    """新しいイベントデータをアップロード"""
    try:
        result = await data_manager.add_event_data(event_data)
        return {"message": "イベントデータが正常に追加されました", "id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ追加に失敗しました: {str(e)}")

@app.post("/api/data/upload-media")
async def upload_media_data(media_data: Dict[str, Any]):
    """新しいメディアデータをアップロード"""
    try:
        result = await data_manager.add_media_data(media_data)
        return {"message": "メディアデータが正常に追加されました", "id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ追加に失敗しました: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 