#!/usr/bin/env python3
"""
データ収集・拡充ツール
使用方法: python data_collector.py --mode [expand|csv|api]
"""

import sqlite3
import pandas as pd
import json
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse
from pathlib import Path

class DataCollector:
    """データ収集・拡充クラス"""
    
    def __init__(self, db_path: str = "data/events_marketing.db"):
        self.db_path = db_path
        
    def expand_sample_data(self, num_events: int = 100):
        """サンプルデータを大量生成してデータベースを拡充"""
        print(f"📊 {num_events}件のサンプルイベントデータを生成中...")
        
        # イベントカテゴリとテーマの組み合わせ
        categories_themes = {
            "seminar": [
                "AI・機械学習", "クラウド技術", "セキュリティ", "Web開発", 
                "モバイル開発", "データ分析", "DevOps", "アジャイル開発"
            ],
            "conference": [
                "技術カンファレンス", "業界サミット", "イノベーション", 
                "デジタル変革", "スタートアップ", "エンジニア採用"
            ],
            "workshop": [
                "ハンズオン研修", "プログラミング", "設計思考", 
                "プロダクトマネジメント", "リーダーシップ"
            ],
            "webinar": [
                "オンラインセミナー", "リモートワーク", "オンライン営業", 
                "デジタルマーケティング", "Eコマース"
            ]
        }
        
        # 業界リスト
        industries = [
            "情報・通信業", "製造業", "金融業", "小売業", "サービス業",
            "ヘルスケア", "教育", "不動産業", "運輸業", "エネルギー"
        ]
        
        # 職種リスト  
        job_titles = [
            "エンジニア", "マネージャー", "経営者", "マーケター", "営業",
            "デザイナー", "データサイエンティスト", "プロダクトマネージャー",
            "コンサルタント", "研究者"
        ]
        
        # メディア・チャネルリスト
        channels = [
            "email_marketing", "social_media", "paid_advertising", 
            "organic_search", "content_marketing", "partner_promotion",
            "direct_outreach", "pr_media"
        ]
        
        events = []
        for i in range(num_events):
            category = random.choice(list(categories_themes.keys()))
            theme = random.choice(categories_themes[category])
            
            # 基本パラメータの生成
            target_attendees = random.randint(20, 500)
            success_rate = random.uniform(0.5, 1.2)  # 50%~120%の達成率
            actual_attendees = int(target_attendees * success_rate)
            
            # 予算設定（無料イベントも含む）
            is_free = random.choice([True, False])
            if is_free:
                budget = 0
                actual_cost = 0
            else:
                budget = random.randint(50000, 2000000)
                cost_efficiency = random.uniform(0.7, 1.1)
                actual_cost = int(budget * cost_efficiency)
            
            # 使用した施策チャネル
            num_channels = random.randint(1, 4)
            used_channels = random.sample(channels, num_channels)
            
            # パフォーマンス指標の生成
            base_ctr = random.uniform(1.0, 8.0)
            base_cvr = random.uniform(2.0, 25.0)
            
            if actual_cost > 0:
                cpa = actual_cost / max(actual_attendees, 1)
            else:
                cpa = 0
                
            # イベント日付（過去3年間）
            start_date = datetime.now() - timedelta(days=1095)
            random_days = random.randint(0, 1095)
            event_date = start_date + timedelta(days=random_days)
            
            event = {
                "event_name": f"{theme}セミナー #{i+1}",
                "category": category,
                "theme": theme,
                "target_attendees": target_attendees,
                "actual_attendees": actual_attendees,
                "budget": budget,
                "actual_cost": actual_cost,
                "event_date": event_date.strftime("%Y-%m-%d"),
                "campaigns_used": json.dumps(used_channels),
                "performance_metrics": json.dumps({
                    "ctr": round(base_ctr, 2),
                    "cvr": round(base_cvr, 2), 
                    "cpa": round(cpa, 0)
                })
            }
            events.append(event)
        
        # データベースに一括挿入
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in events:
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
        
        conn.commit()
        conn.close()
        
        print(f"✅ {num_events}件のイベントデータを追加しました！")
        
    def expand_media_data(self, num_media: int = 50):
        """メディアパフォーマンスデータを拡充"""
        print(f"📺 {num_media}件のメディアデータを生成中...")
        
        # メディアリスト
        media_list = [
            # 技術系
            {"name": "Qiita", "type": "技術記事", "audience": ["IT", "スタートアップ"], "jobs": ["エンジニア"]},
            {"name": "Zenn", "type": "技術記事", "audience": ["IT"], "jobs": ["エンジニア", "デザイナー"]},
            {"name": "Speaker Deck", "type": "資料共有", "audience": ["IT"], "jobs": ["エンジニア"]},
            {"name": "connpass", "type": "イベント", "audience": ["IT"], "jobs": ["エンジニア"]},
            {"name": "TechPlay", "type": "イベント", "audience": ["IT"], "jobs": ["エンジニア", "プロダクトマネージャー"]},
            {"name": "TECH PLAY", "type": "組み合わせ", "audience": ["IT"], "jobs": ["エンジニア"]},
            
            # ビジネス系
            {"name": "日経xTECH", "type": "メディア記事", "audience": ["製造業", "IT"], "jobs": ["マネージャー", "経営者"]},
            {"name": "ITmedia", "type": "組み合わせ", "audience": ["IT", "製造業"], "jobs": ["IT管理者", "システム管理者"]},
            {"name": "インプレス", "type": "メディア記事", "audience": ["IT"], "jobs": ["エンジニア", "マネージャー"]},
            {"name": "ASCII.jp", "type": "メディア記事", "audience": ["IT"], "jobs": ["エンジニア"]},
            
            # SNS・広告
            {"name": "Meta", "type": "ディスプレイ広告", "audience": ["IT", "スタートアップ"], "jobs": ["エンジニア", "デザイナー"]},
            {"name": "Google Ads", "type": "検索広告", "audience": ["IT", "製造業"], "jobs": ["マネージャー", "マーケター"]},
            {"name": "LinkedIn", "type": "SNS広告", "audience": ["IT", "金融"], "jobs": ["マネージャー", "営業"]},
            {"name": "Twitter", "type": "SNS広告", "audience": ["IT", "サービス業"], "jobs": ["エンジニア", "マーケター"]},
            {"name": "YouTube", "type": "動画広告", "audience": ["IT", "小売"], "jobs": ["デザイナー", "マーケター"]},
            
            # 業界特化
            {"name": "CodeZine", "type": "技術記事", "audience": ["IT"], "jobs": ["エンジニア"]},
            {"name": "@IT", "type": "技術記事", "audience": ["IT"], "jobs": ["エンジニア", "IT管理者"]},
            {"name": "Think IT", "type": "技術記事", "audience": ["IT"], "jobs": ["エンジニア", "システム管理者"]},
            {"name": "EnterpriseZine", "type": "ビジネス記事", "audience": ["IT", "製造業"], "jobs": ["マネージャー", "経営者"]},
            {"name": "MarkeZine", "type": "マーケティング", "audience": ["サービス業", "小売"], "jobs": ["マーケター", "営業"]},
        ]
        
        # 不足分をランダム生成で補完
        while len(media_list) < num_media:
            base_names = ["TechNews", "DevMedia", "BusinessPost", "InnovateTech", "StartupTimes"]
            extensions = ["Plus", "Pro", "Digital", "Online", "Weekly", "Daily"]
            
            name = f"{random.choice(base_names)}{random.choice(extensions)}"
            media_type = random.choice(["技術記事", "ディスプレイ広告", "組み合わせ", "SNS広告", "メルマガ"])
            audience = random.sample(["IT", "製造業", "金融", "小売", "サービス業"], random.randint(1, 3))
            jobs = random.sample(["エンジニア", "マネージャー", "マーケター", "営業"], random.randint(1, 3))
            
            media_list.append({
                "name": name,
                "type": media_type,
                "audience": audience,
                "jobs": jobs
            })
        
        # パフォーマンス指標を生成
        media_data = []
        for media in media_list[:num_media]:
            # CTR: 0.5% ~ 8.0%
            ctr = round(random.uniform(0.5, 8.0), 2)
            
            # CVR: 1% ~ 50% (メディアタイプによって調整)
            if media["type"] == "ディスプレイ広告":
                cvr = round(random.uniform(1.0, 5.0), 2)
                reach = random.randint(1000, 10000)
            elif media["type"] == "技術記事":
                cvr = round(random.uniform(5.0, 20.0), 2)
                reach = random.randint(500, 5000)
            elif media["type"] == "組み合わせ":
                cvr = round(random.uniform(3.0, 15.0), 2)
                reach = random.randint(800, 8000)
            else:
                cvr = round(random.uniform(2.0, 25.0), 2)
                reach = random.randint(300, 3000)
            
            # CPA: 1,000円 ~ 50,000円
            cpa = random.randint(1000, 50000)
            
            # コスト範囲
            min_cost = random.randint(50000, 300000)
            max_cost = min_cost + random.randint(200000, 1500000)
            
            media_record = {
                "media_name": media["name"],
                "media_type": media["type"],
                "target_audience": json.dumps({
                    "industries": media["audience"],
                    "job_titles": media["jobs"]
                }),
                "average_ctr": ctr,
                "average_cvr": cvr,
                "average_cpa": cpa,
                "reach_potential": reach,
                "cost_range": json.dumps({"min": min_cost, "max": max_cost}),
                "best_performing_content_types": json.dumps(
                    random.sample(["動画", "インフォグラフィック", "技術記事", "事例紹介", "ウェビナー"], 
                                random.randint(2, 4))
                )
            }
            media_data.append(media_record)
        
        # データベースに挿入
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for media in media_data:
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
        
        print(f"✅ {num_media}件のメディアデータを追加しました！")
    
    def import_csv_data(self, csv_file: str, data_type: str = "events"):
        """CSVファイルからデータをインポート"""
        print(f"📁 CSVファイル {csv_file} からデータをインポート中...")
        
        if not Path(csv_file).exists():
            print(f"❌ ファイル {csv_file} が見つかりません")
            return
        
        df = pd.read_csv(csv_file)
        print(f"📋 {len(df)}行のデータを読み込みました")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if data_type == "events":
            # イベントデータのインポート
            required_columns = ["event_name", "category", "theme", "target_attendees", "actual_attendees"]
            if not all(col in df.columns for col in required_columns):
                print(f"❌ 必要な列が不足しています: {required_columns}")
                return
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO historical_events 
                    (event_name, category, theme, target_attendees, actual_attendees, 
                     budget, actual_cost, event_date, campaigns_used, performance_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get("event_name", ""),
                    row.get("category", "seminar"),
                    row.get("theme", ""),
                    row.get("target_attendees", 0),
                    row.get("actual_attendees", 0),
                    row.get("budget", 0),
                    row.get("actual_cost", 0),
                    row.get("event_date", datetime.now().strftime("%Y-%m-%d")),
                    row.get("campaigns_used", '["email_marketing"]'),
                    row.get("performance_metrics", '{"ctr": 2.0, "cvr": 5.0, "cpa": 10000}')
                ))
        
        elif data_type == "media":
            # メディアデータのインポート
            required_columns = ["media_name", "media_type", "average_ctr", "average_cvr", "average_cpa"]
            if not all(col in df.columns for col in required_columns):
                print(f"❌ 必要な列が不足しています: {required_columns}")
                return
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO media_performance 
                    (media_name, media_type, target_audience, average_ctr, average_cvr, 
                     average_cpa, reach_potential, cost_range, best_performing_content_types)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get("media_name", ""),
                    row.get("media_type", ""),
                    row.get("target_audience", '{"industries": ["IT"], "job_titles": ["エンジニア"]}'),
                    row.get("average_ctr", 2.0),
                    row.get("average_cvr", 5.0),
                    row.get("average_cpa", 10000),
                    row.get("reach_potential", 1000),
                    row.get("cost_range", '{"min": 100000, "max": 500000}'),
                    row.get("best_performing_content_types", '["技術記事", "動画"]')
                ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ {len(df)}件のデータをインポートしました！")
    
    def show_statistics(self):
        """現在のデータベース統計を表示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM historical_events")
        events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM media_performance")
        media_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaign_performance")
        campaigns_count = cursor.fetchone()[0]
        
        print("\n📊 データベース統計")
        print(f"  イベントデータ: {events_count}件")
        print(f"  メディアデータ: {media_count}件")
        print(f"  施策データ: {campaigns_count}件")
        
        if events_count >= 100:
            print("✅ 機械学習に十分なデータ量です！")
        elif events_count >= 50:
            print("⚠️  機械学習には少し少ないですが、使用可能です")
        else:
            print("❌ 機械学習にはデータが不足しています")
        
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='データ収集・拡充ツール')
    parser.add_argument('--mode', choices=['expand', 'csv', 'stats'], 
                       default='expand', help='実行モード')
    parser.add_argument('--events', type=int, default=100, 
                       help='生成するイベントデータ数')
    parser.add_argument('--media', type=int, default=50, 
                       help='生成するメディアデータ数')
    parser.add_argument('--csv', type=str, help='インポートするCSVファイル')
    parser.add_argument('--type', choices=['events', 'media'], 
                       default='events', help='CSVデータタイプ')
    
    args = parser.parse_args()
    
    collector = DataCollector()
    
    if args.mode == 'expand':
        print("🚀 データベース拡充を開始します...")
        collector.expand_sample_data(args.events)
        collector.expand_media_data(args.media)
        collector.show_statistics()
        
    elif args.mode == 'csv':
        if not args.csv:
            print("❌ --csv オプションでCSVファイルを指定してください")
            return
        collector.import_csv_data(args.csv, args.type)
        collector.show_statistics()
        
    elif args.mode == 'stats':
        collector.show_statistics()

if __name__ == "__main__":
    main() 