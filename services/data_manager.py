import sqlite3
import pandas as pd
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path

from models.event_model import HistoricalEvent, MediaPerformance

class DataManager:
    """データ管理クラス"""
    
    def __init__(self, db_path: str = "data/events_marketing.db"):
        self.db_path = db_path
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """データディレクトリの存在確認・作成"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """データベースの初期化"""
        await self.create_tables()
        await self.load_sample_data()
    
    async def create_tables(self):
        """テーブルの作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 過去のイベントテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                category TEXT NOT NULL,
                theme TEXT NOT NULL,
                target_attendees INTEGER NOT NULL,
                actual_attendees INTEGER NOT NULL,
                budget INTEGER NOT NULL,
                actual_cost INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                campaigns_used TEXT NOT NULL,
                performance_metrics TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # メディアパフォーマンステーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_name TEXT NOT NULL,
                media_type TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                average_ctr REAL NOT NULL,
                average_cvr REAL NOT NULL,
                average_cpa INTEGER NOT NULL,
                reach_potential INTEGER NOT NULL,
                cost_range TEXT NOT NULL,
                best_performing_content_types TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 施策パフォーマンステーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT NOT NULL,
                channel TEXT NOT NULL,
                event_category TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                impressions INTEGER,
                clicks INTEGER,
                conversions INTEGER,
                cost INTEGER,
                ctr REAL,
                cvr REAL,
                cpa INTEGER,
                event_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def load_sample_data(self):
        """サンプルデータの読み込み（添付画像のデータを基に）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 既存データの確認
        cursor.execute("SELECT COUNT(*) FROM historical_events")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # サンプルイベントデータ
        sample_events = [
            {
                "event_name": "PR Times一般申し込み開始",
                "category": "seminar",
                "theme": "無料媒体・経路",
                "target_attendees": 100,
                "actual_attendees": 59,
                "budget": 0,
                "actual_cost": 0,
                "event_date": "2025-01-08",
                "campaigns_used": json.dumps(["organic_search", "direct_outreach"]),
                "performance_metrics": json.dumps({"ctr": 0.0, "cvr": 0.59, "cpa": 0})
            },
            {
                "event_name": "転職サービス会員向け施策",
                "category": "webinar",
                "theme": "転職・キャリア",
                "target_attendees": 50,
                "actual_attendees": 13,
                "budget": 100000,
                "actual_cost": 70953,
                "event_date": "2025-01-08",
                "campaigns_used": json.dumps(["email_marketing", "paid_advertising"]),
                "performance_metrics": json.dumps({"ctr": 0.47, "cvr": 3.9, "cpa": 5458})
            },
            {
                "event_name": "Meta明及川さん求人",
                "category": "seminar",
                "theme": "技術・エンジニア",
                "target_attendees": 30,
                "actual_attendees": 26,
                "budget": 200000,
                "actual_cost": 147200,
                "event_date": "2025-01-08",
                "event_format": "online",
                "campaigns_used": json.dumps(["paid_advertising", "social_media"]),
                "performance_metrics": json.dumps({"ctr": 0.95, "cvr": 1.9, "cpa": 5662})
            }
        ]
        
        for event in sample_events:
            cursor.execute('''
                INSERT INTO historical_events 
                (event_name, category, theme, target_attendees, actual_attendees, 
                 budget, actual_cost, event_date, campaigns_used, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event["event_name"], event["category"], event["theme"],
                event["target_attendees"], event["actual_attendees"],
                event["budget"], event["actual_cost"], event["event_date"],
                event["campaigns_used"], event["performance_metrics"]
            ))
        
        # サンプルメディアデータ（添付画像の下部テーブルを基に）
        sample_media = [
            {
                "media_name": "Meta",
                "media_type": "ディスプレイ広告",
                "target_audience": json.dumps({"industries": ["IT", "スタートアップ"], "job_titles": ["エンジニア", "デザイナー"]}),
                "average_ctr": 5.0,
                "average_cvr": 250.0,
                "average_cpa": 8000,
                "reach_potential": 5000,
                "cost_range": json.dumps({"min": 500000, "max": 2000000}),
                "best_performing_content_types": json.dumps(["動画", "インフォグラフィック"])
            },
            {
                "media_name": "TechPlay",
                "media_type": "組み合わせ",
                "target_audience": json.dumps({"industries": ["IT", "テクノロジー"], "job_titles": ["エンジニア", "プロダクトマネージャー"]}),
                "average_ctr": 4.0,
                "average_cvr": 200.0,
                "average_cpa": 3500,
                "reach_potential": 5000,
                "cost_range": json.dumps({"min": 300000, "max": 700000}),
                "best_performing_content_types": json.dumps(["技術記事", "イベント告知"])
            },
            {
                "media_name": "ITmedia",
                "media_type": "組み合わせ",
                "target_audience": json.dumps({"industries": ["IT", "製造業"], "job_titles": ["IT管理者", "システム管理者"]}),
                "average_ctr": 3.0,
                "average_cvr": 27.0,
                "average_cpa": 33937,
                "reach_potential": 884,
                "cost_range": json.dumps({"min": 500000, "max": 900000}),
                "best_performing_content_types": json.dumps(["技術解説", "事例紹介"])
            }
        ]
        
        for media in sample_media:
            cursor.execute('''
                INSERT INTO media_performance 
                (media_name, media_type, target_audience, average_ctr, average_cvr, 
                 average_cpa, reach_potential, cost_range, best_performing_content_types)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                media["media_name"], media["media_type"], media["target_audience"],
                media["average_ctr"], media["average_cvr"], media["average_cpa"],
                media["reach_potential"], media["cost_range"], media["best_performing_content_types"]
            ))
        
        conn.commit()
        conn.close()
    
    async def get_historical_events(self) -> List[Dict[str, Any]]:
        """過去のイベントデータを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM historical_events ORDER BY event_date DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        events = []
        
        for row in cursor.fetchall():
            event = dict(zip(columns, row))
            event['campaigns_used'] = json.loads(event['campaigns_used'])
            event['performance_metrics'] = json.loads(event['performance_metrics'])
            events.append(event)
        
        conn.close()
        return events
    
    async def get_media_performance(self) -> List[Dict[str, Any]]:
        """メディア別パフォーマンスデータを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM media_performance ORDER BY average_cpa ASC
        ''')
        
        columns = [description[0] for description in cursor.description]
        media_data = []
        
        for row in cursor.fetchall():
            media = dict(zip(columns, row))
            media['target_audience'] = json.loads(media['target_audience'])
            media['cost_range'] = json.loads(media['cost_range'])
            media['best_performing_content_types'] = json.loads(media['best_performing_content_types'])
            media_data.append(media)
        
        conn.close()
        return media_data
    
    async def add_event_data(self, event_data: Dict[str, Any]) -> int:
        """新しいイベントデータを追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historical_events 
            (event_name, category, theme, target_attendees, actual_attendees, 
             budget, actual_cost, event_date, campaigns_used, performance_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_data["event_name"], event_data["category"], event_data["theme"],
            event_data["target_attendees"], event_data["actual_attendees"],
            event_data["budget"], event_data["actual_cost"], event_data["event_date"],
            json.dumps(event_data["campaigns_used"]), json.dumps(event_data["performance_metrics"])
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id
    
    async def add_media_data(self, media_data: Dict[str, Any]) -> int:
        """新しいメディアデータを追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO media_performance 
            (media_name, media_type, target_audience, average_ctr, average_cvr, 
             average_cpa, reach_potential, cost_range, best_performing_content_types)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            media_data["media_name"], media_data["media_type"], 
            json.dumps(media_data["target_audience"]),
            media_data["average_ctr"], media_data["average_cvr"], media_data["average_cpa"],
            media_data["reach_potential"], json.dumps(media_data["cost_range"]), 
            json.dumps(media_data["best_performing_content_types"])
        ))
        
        media_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return media_id
    
    async def get_similar_events(self, event_category: str, target_audience: Dict[str, Any], 
                                budget_range: tuple) -> List[Dict[str, Any]]:
        """類似イベントデータを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM historical_events 
            WHERE category = ? AND budget BETWEEN ? AND ?
            ORDER BY event_date DESC
        ''', (event_category, budget_range[0], budget_range[1]))
        
        columns = [description[0] for description in cursor.description]
        similar_events = []
        
        for row in cursor.fetchall():
            event = dict(zip(columns, row))
            event['campaigns_used'] = json.loads(event['campaigns_used'])
            event['performance_metrics'] = json.loads(event['performance_metrics'])
            similar_events.append(event)
        
        conn.close()
        return similar_events 