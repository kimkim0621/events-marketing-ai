#!/usr/bin/env python3
"""
データクリーニング専用ツール
- サンプルデータの検出・削除
- データ品質チェック
- バックアップ・復元機能
"""

import sqlite3
import json
import re
import os
from datetime import datetime
from pathlib import Path
import shutil
import argparse

class DataCleaner:
    """データクリーニング専用クラス"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # クラウド対応のデータベースパス設定
            if "STREAMLIT_CLOUD" in os.environ or not os.path.exists("data"):
                self.db_path = "events_marketing.db"
                self.backup_dir = Path("backups")
            else:
                self.db_path = "data/events_marketing.db"
                self.backup_dir = Path("data/backups")
        else:
            self.db_path = db_path
            self.backup_dir = Path("data/backups")
        
        self.backup_dir.mkdir(exist_ok=True)
    
    def check_sample_data(self) -> dict:
        """サンプルデータの検出"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sample_data = {
            "historical_events": [],
            "media_performance": [],
            "internal_knowledge": [],
            "media_detailed_attributes": []
        }
        
        # イベントデータのサンプル検出
        try:
            cursor.execute("SELECT id, event_name FROM historical_events")
            events = cursor.fetchall()
            
            sample_patterns = [
                r'.*セミナー\s*#\d+',
                r'^Event_\d+$',
                r'.*サンプル.*',
                r'.*テスト.*',
                r'.*生成.*',
                r'.*ダミー.*'
            ]
            
            for event_id, event_name in events:
                for pattern in sample_patterns:
                    if re.search(pattern, event_name, re.IGNORECASE):
                        sample_data["historical_events"].append({
                            "id": event_id,
                            "name": event_name,
                            "reason": f"パターン一致: {pattern}"
                        })
                        break
        except Exception as e:
            print(f"イベントデータチェックエラー: {e}")
        
        # メディアデータのサンプル検出
        try:
            cursor.execute("SELECT id, media_name FROM media_performance")
            media = cursor.fetchall()
            
            for media_id, media_name in media:
                if any(word in media_name.lower() for word in ['sample', 'test', 'テスト', 'サンプル', 'ダミー']):
                    sample_data["media_performance"].append({
                        "id": media_id,
                        "name": media_name,
                        "reason": "サンプル文字列を含む"
                    })
        except Exception as e:
            print(f"メディアデータチェックエラー: {e}")
        
        # 知見データのサンプル検出
        try:
            cursor.execute("SELECT id, title, source FROM internal_knowledge")
            knowledge = cursor.fetchall()
            
            for knowledge_id, title, source in knowledge:
                if any(word in title for word in ['PDF抽出知見', 'サンプル', 'テスト', 'ダミー']):
                    sample_data["internal_knowledge"].append({
                        "id": knowledge_id,
                        "title": title,
                        "source": source,
                        "reason": "サンプル知見"
                    })
        except Exception as e:
            print(f"知見データチェックエラー: {e}")
        
        conn.close()
        return sample_data
    
    def create_backup(self) -> str:
        """バックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_before_cleaning_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(self.db_path, backup_path)
        return str(backup_path)
    
    def remove_sample_data(self, sample_data: dict, create_backup: bool = True) -> dict:
        """サンプルデータの削除"""
        if create_backup:
            backup_path = self.create_backup()
            print(f"📦 バックアップ作成: {backup_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        removed_counts = {}
        
        # イベントデータの削除
        if sample_data["historical_events"]:
            event_ids = [item["id"] for item in sample_data["historical_events"]]
            placeholders = ",".join(["?" for _ in event_ids])
            cursor.execute(f"DELETE FROM historical_events WHERE id IN ({placeholders})", event_ids)
            removed_counts["historical_events"] = len(event_ids)
        
        # メディアデータの削除
        if sample_data["media_performance"]:
            media_ids = [item["id"] for item in sample_data["media_performance"]]
            placeholders = ",".join(["?" for _ in media_ids])
            cursor.execute(f"DELETE FROM media_performance WHERE id IN ({placeholders})", media_ids)
            removed_counts["media_performance"] = len(media_ids)
        
        # 知見データの削除
        if sample_data["internal_knowledge"]:
            knowledge_ids = [item["id"] for item in sample_data["internal_knowledge"]]
            placeholders = ",".join(["?" for _ in knowledge_ids])
            cursor.execute(f"DELETE FROM internal_knowledge WHERE id IN ({placeholders})", knowledge_ids)
            removed_counts["internal_knowledge"] = len(knowledge_ids)
        
        conn.commit()
        conn.close()
        
        return removed_counts
    
    def reset_all_data(self, create_backup: bool = True) -> str:
        """全データのリセット"""
        backup_path = ""
        if create_backup:
            backup_path = self.create_backup()
            print(f"📦 バックアップ作成: {backup_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = ['historical_events', 'media_performance', 'media_detailed_attributes', 'internal_knowledge']
        
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"🗑️ {table} テーブルをクリア")
            except Exception as e:
                print(f"⚠️ {table} クリアエラー: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return backup_path
    
    def show_data_status(self):
        """データ状況の表示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n📊 現在のデータ状況:")
        
        tables = ['historical_events', 'media_performance', 'media_detailed_attributes', 'internal_knowledge']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count}件")
                
                if count > 0 and table in ['historical_events', 'media_performance']:
                    # サンプル例を表示
                    if table == 'historical_events':
                        cursor.execute(f"SELECT event_name FROM {table} LIMIT 3")
                        samples = cursor.fetchall()
                        print(f"    例: {[s[0] for s in samples]}")
                    elif table == 'media_performance':
                        cursor.execute(f"SELECT media_name FROM {table} LIMIT 3")
                        samples = cursor.fetchall()
                        print(f"    例: {[s[0] for s in samples]}")
                        
            except Exception as e:
                print(f"  {table}: エラー - {str(e)}")
        
        conn.close()
    
    def interactive_clean(self):
        """インタラクティブなクリーニング"""
        print("🧹 データクリーニングツール")
        print("="*50)
        
        # 現在の状況確認
        self.show_data_status()
        
        # サンプルデータ検出
        sample_data = self.check_sample_data()
        
        total_sample_items = sum(len(items) for items in sample_data.values())
        
        if total_sample_items == 0:
            print("\n✅ サンプルデータは検出されませんでした")
            return
        
        print(f"\n🔍 サンプルデータを {total_sample_items}件 検出しました:")
        
        for table, items in sample_data.items():
            if items:
                print(f"\n📋 {table}:")
                for item in items:
                    if table == "historical_events":
                        print(f"  - {item['name']} (ID: {item['id']}) - {item['reason']}")
                    elif table == "media_performance":
                        print(f"  - {item['name']} (ID: {item['id']}) - {item['reason']}")
                    elif table == "internal_knowledge":
                        print(f"  - {item['title']} (ID: {item['id']}) - {item['reason']}")
        
        # 削除確認
        choice = input(f"\n削除オプションを選択してください:\n1. サンプルデータのみ削除\n2. 全データ削除\n3. キャンセル\n選択 (1/2/3): ")
        
        if choice == "1":
            removed = self.remove_sample_data(sample_data)
            print(f"\n✅ サンプルデータを削除しました: {removed}")
            
        elif choice == "2":
            confirm = input("⚠️ 全データを削除します。本当によろしいですか？ (yes/N): ")
            if confirm.lower() == "yes":
                backup_path = self.reset_all_data()
                print(f"\n✅ 全データを削除しました。バックアップ: {backup_path}")
            else:
                print("キャンセルしました")
                
        else:
            print("キャンセルしました")
        
        # 削除後の状況確認
        if choice in ["1", "2"]:
            print("\n削除後の状況:")
            self.show_data_status()

def main():
    parser = argparse.ArgumentParser(description='データクリーニングツール')
    parser.add_argument('--check', action='store_true', help='サンプルデータ検出のみ')
    parser.add_argument('--status', action='store_true', help='データ状況表示')
    parser.add_argument('--clean-samples', action='store_true', help='サンプルデータ削除')
    parser.add_argument('--reset-all', action='store_true', help='全データリセット')
    parser.add_argument('--interactive', action='store_true', help='インタラクティブモード')
    
    args = parser.parse_args()
    
    cleaner = DataCleaner()
    
    if args.check:
        sample_data = cleaner.check_sample_data()
        total = sum(len(items) for items in sample_data.values())
        print(f"🔍 サンプルデータ検出: {total}件")
        for table, items in sample_data.items():
            if items:
                print(f"  {table}: {len(items)}件")
    
    elif args.status:
        cleaner.show_data_status()
    
    elif args.clean_samples:
        sample_data = cleaner.check_sample_data()
        removed = cleaner.remove_sample_data(sample_data)
        print(f"🧹 サンプルデータ削除完了: {removed}")
    
    elif args.reset_all:
        confirm = input("⚠️ 全データを削除します。よろしいですか？ (yes/N): ")
        if confirm.lower() == "yes":
            backup_path = cleaner.reset_all_data()
            print(f"🔄 全データリセット完了。バックアップ: {backup_path}")
    
    elif args.interactive:
        cleaner.interactive_clean()
    
    else:
        cleaner.interactive_clean()  # デフォルトはインタラクティブモード

if __name__ == "__main__":
    main() 