#!/usr/bin/env python3
"""
高度データ管理システム
- サンプルデータ vs 実データの識別・管理
- 選択的削除機能
- データ品質チェック
- バックアップ・復元機能
"""

import sqlite3
import pandas as pd
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import shutil

class AdvancedDataManager:
    """高度データ管理システム"""
    
    def __init__(self, db_path: str = "data/events_marketing.db"):
        self.db_path = db_path
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def analyze_data_sources(self) -> Dict[str, Any]:
        """データソースの分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        analysis = {
            "total_records": {},
            "data_quality": {},
            "sample_data_indicators": {},
            "data_sources": {}
        }
        
        # 各テーブルの分析
        tables = ['historical_events', 'media_performance', 'media_detailed_attributes', 'internal_knowledge']
        
        for table in tables:
            try:
                # 総レコード数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total_count = cursor.fetchone()[0]
                analysis["total_records"][table] = total_count
                
                if total_count > 0:
                    # サンプルデータの検出
                    sample_indicators = self._detect_sample_data(table, cursor)
                    analysis["sample_data_indicators"][table] = sample_indicators
                    
                    # データ品質チェック
                    quality_check = self._check_data_quality(table, cursor)
                    analysis["data_quality"][table] = quality_check
                    
                    # データソース分析
                    source_analysis = self._analyze_data_sources(table, cursor)
                    analysis["data_sources"][table] = source_analysis
                
            except Exception as e:
                analysis["total_records"][table] = f"エラー: {str(e)}"
        
        conn.close()
        return analysis
    
    def _detect_sample_data(self, table: str, cursor) -> Dict[str, Any]:
        """サンプルデータの検出"""
        indicators = {
            "suspected_sample_records": 0,
            "patterns_found": [],
            "suspicious_values": []
        }
        
        # テーブル別のサンプルデータ検出パターン
        if table == "historical_events":
            # イベント名のパターン検出
            cursor.execute(f"SELECT event_name, COUNT(*) as count FROM {table} GROUP BY event_name")
            events = cursor.fetchall()
            
            sample_patterns = [
                r'.*セミナー\s*#\d+$',  # "セミナー #1" 形式
                r'^Event_\d+$',        # "Event_1" 形式  
                r'.*サンプル.*',       # "サンプル" を含む
                r'.*テスト.*',         # "テスト" を含む
                r'.*生成.*',           # "生成" を含む
            ]
            
            for event_name, count in events:
                for pattern in sample_patterns:
                    if re.match(pattern, event_name):
                        indicators["suspected_sample_records"] += count
                        indicators["patterns_found"].append(f"イベント名パターン: {event_name}")
            
            # 異常な数値パターンの検出
            cursor.execute(f"""
                SELECT event_name, target_attendees, actual_attendees, budget 
                FROM {table} 
                WHERE target_attendees > 1000 OR budget > 5000000 
                OR (actual_attendees = target_attendees)
            """)
            suspicious_records = cursor.fetchall()
            
            for record in suspicious_records:
                indicators["suspicious_values"].append({
                    "event": record[0],
                    "reason": "異常な数値またはぴったり一致"
                })
        
        elif table == "media_performance":
            # メディア名のパターン検出
            cursor.execute(f"SELECT media_name FROM {table}")
            media_names = [row[0] for row in cursor.fetchall()]
            
            for media_name in media_names:
                if any(pattern in media_name for pattern in ['Sample', 'Test', 'テスト', 'サンプル']):
                    indicators["suspected_sample_records"] += 1
                    indicators["patterns_found"].append(f"メディア名: {media_name}")
        
        elif table == "internal_knowledge":
            # 知見タイトルのパターン検出
            cursor.execute(f"SELECT title, source FROM {table}")
            knowledge_records = cursor.fetchall()
            
            for title, source in knowledge_records:
                if any(pattern in title for pattern in ['PDF抽出知見', 'サンプル', 'テスト']):
                    indicators["suspected_sample_records"] += 1
                    indicators["patterns_found"].append(f"知見: {title}")
        
        return indicators
    
    def _check_data_quality(self, table: str, cursor) -> Dict[str, Any]:
        """データ品質チェック"""
        quality = {
            "completeness": 0,
            "consistency": 0,
            "issues": []
        }
        
        if table == "historical_events":
            # 必須フィールドの完全性チェック
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN event_name IS NOT NULL AND event_name != '' THEN 1 ELSE 0 END) as has_name,
                       SUM(CASE WHEN target_attendees > 0 THEN 1 ELSE 0 END) as has_target,
                       SUM(CASE WHEN actual_attendees >= 0 THEN 1 ELSE 0 END) as has_actual
                FROM {table}
            """)
            total, has_name, has_target, has_actual = cursor.fetchone()
            
            if total > 0:
                quality["completeness"] = (has_name + has_target + has_actual) / (total * 3) * 100
                
                if has_name < total:
                    quality["issues"].append(f"イベント名未設定: {total - has_name}件")
                if has_target < total:
                    quality["issues"].append(f"目標参加者数未設定: {total - has_target}件")
            
            # 一貫性チェック
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table} 
                WHERE actual_attendees > target_attendees * 2
            """)
            inconsistent = cursor.fetchone()[0]
            if inconsistent > 0:
                quality["issues"].append(f"実績が目標の2倍超: {inconsistent}件")
        
        return quality
    
    def _analyze_data_sources(self, table: str, cursor) -> Dict[str, Any]:
        """データソース分析"""
        sources = {
            "by_source": {},
            "import_methods": [],
            "date_ranges": {}
        }
        
        # ソース情報がある場合の分析
        try:
            if table in ["media_detailed_attributes", "internal_knowledge"]:
                cursor.execute(f"SELECT source, COUNT(*) FROM {table} WHERE source IS NOT NULL GROUP BY source")
                source_counts = cursor.fetchall()
                
                for source, count in source_counts:
                    sources["by_source"][source] = count
                    
                    if source.endswith('.csv'):
                        sources["import_methods"].append("CSV")
                    elif source.endswith('.pdf'):
                        sources["import_methods"].append("PDF")
                    elif source == 'manual':
                        sources["import_methods"].append("手動入力")
        
        except:
            pass  # ソース列がない場合はスキップ
        
        return sources
    
    def clean_sample_data(self, interactive: bool = True) -> Dict[str, int]:
        """サンプルデータのクリーニング"""
        analysis = self.analyze_data_sources()
        removed_counts = {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for table, indicators in analysis["sample_data_indicators"].items():
            if indicators["suspected_sample_records"] > 0:
                if interactive:
                    print(f"\n📋 {table} テーブル:")
                    print(f"  疑わしいレコード数: {indicators['suspected_sample_records']}")
                    print(f"  検出パターン: {indicators['patterns_found']}")
                    
                    response = input(f"  {table} のサンプルデータを削除しますか？ (y/N): ")
                    if response.lower() != 'y':
                        continue
                
                # テーブル別のクリーニング実行
                removed_count = self._clean_table_sample_data(table, cursor)
                removed_counts[table] = removed_count
                
                if interactive:
                    print(f"  ✅ {removed_count}件のサンプルデータを削除しました")
        
        conn.commit()
        conn.close()
        
        return removed_counts
    
    def _clean_table_sample_data(self, table: str, cursor) -> int:
        """特定テーブルのサンプルデータクリーニング"""
        removed_count = 0
        
        if table == "historical_events":
            # サンプルパターンのイベントを削除
            sample_patterns = [
                ".*セミナー\\s*#\\d+$",
                "^Event_\\d+$",
                ".*サンプル.*",
                ".*テスト.*",
                ".*生成.*"
            ]
            
            for pattern in sample_patterns:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} 
                    WHERE event_name REGEXP '{pattern}'
                """)
                try:
                    count_before = cursor.fetchone()[0]
                    cursor.execute(f"""
                        DELETE FROM {table} 
                        WHERE event_name REGEXP '{pattern}'
                    """)
                    removed_count += count_before
                except:
                    # REGEXP が使えない場合はLIKEで代用
                    if "セミナー" in pattern:
                        cursor.execute(f"DELETE FROM {table} WHERE event_name LIKE '%セミナー #%'")
                        removed_count += cursor.rowcount
                    elif "Event_" in pattern:
                        cursor.execute(f"DELETE FROM {table} WHERE event_name LIKE 'Event_%'")
                        removed_count += cursor.rowcount
        
        elif table == "media_performance":
            # サンプルメディアを削除
            cursor.execute(f"""
                DELETE FROM {table} 
                WHERE media_name LIKE '%Sample%' 
                   OR media_name LIKE '%Test%' 
                   OR media_name LIKE '%テスト%' 
                   OR media_name LIKE '%サンプル%'
            """)
            removed_count = cursor.rowcount
        
        elif table == "internal_knowledge":
            # PDF抽出やサンプル知見を削除
            cursor.execute(f"""
                DELETE FROM {table} 
                WHERE title LIKE 'PDF抽出知見%' 
                   OR title LIKE '%サンプル%' 
                   OR title LIKE '%テスト%'
            """)
            removed_count = cursor.rowcount
        
        return removed_count
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """データベースバックアップ作成"""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"events_marketing_backup_{timestamp}.db"
        
        backup_path = self.backup_dir / backup_name
        shutil.copy2(self.db_path, backup_path)
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str) -> bool:
        """バックアップからの復元"""
        try:
            if not Path(backup_path).exists():
                print(f"❌ バックアップファイルが見つかりません: {backup_path}")
                return False
            
            shutil.copy2(backup_path, self.db_path)
            print(f"✅ バックアップから復元しました: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ 復元エラー: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """バックアップファイル一覧"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def reset_to_clean_state(self, create_backup_first: bool = True) -> str:
        """データベースを完全にクリーンな状態にリセット"""
        backup_path = ""
        
        if create_backup_first:
            backup_path = self.create_backup("reset_backup.db")
            print(f"📦 バックアップ作成: {backup_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 全テーブルのデータを削除
        tables = ['historical_events', 'media_performance', 'media_detailed_attributes', 'internal_knowledge']
        
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"🗑️ {table} テーブルをクリア")
            except Exception as e:
                print(f"⚠️ {table} クリアエラー: {str(e)}")
        
        conn.commit()
        conn.close()
        
        print("✅ データベースをクリーンな状態にリセットしました")
        return backup_path
    
    def show_detailed_report(self):
        """詳細データレポート表示"""
        analysis = self.analyze_data_sources()
        
        print("\n" + "="*60)
        print("📊 詳細データ分析レポート")
        print("="*60)
        
        # 総レコード数
        print("\n📈 テーブル別レコード数:")
        for table, count in analysis["total_records"].items():
            print(f"  {table}: {count}")
        
        # サンプルデータ検出
        print("\n🔍 サンプルデータ検出結果:")
        for table, indicators in analysis["sample_data_indicators"].items():
            if indicators["suspected_sample_records"] > 0:
                print(f"  {table}:")
                print(f"    疑わしいレコード数: {indicators['suspected_sample_records']}")
                print(f"    検出パターン: {indicators['patterns_found']}")
                if indicators["suspicious_values"]:
                    print(f"    疑わしい値: {len(indicators['suspicious_values'])}件")
        
        # データ品質
        print("\n✅ データ品質:")
        for table, quality in analysis["data_quality"].items():
            if quality:
                print(f"  {table}:")
                print(f"    完全性: {quality['completeness']:.1f}%")
                if quality["issues"]:
                    print(f"    問題: {quality['issues']}")
        
        # データソース
        print("\n📂 データソース:")
        for table, sources in analysis["data_sources"].items():
            if sources["by_source"]:
                print(f"  {table}:")
                for source, count in sources["by_source"].items():
                    print(f"    {source}: {count}件")

def main():
    parser = argparse.ArgumentParser(description='高度データ管理システム')
    parser.add_argument('--analyze', action='store_true', help='データ分析実行')
    parser.add_argument('--clean', action='store_true', help='サンプルデータクリーニング')
    parser.add_argument('--reset', action='store_true', help='完全リセット')
    parser.add_argument('--backup', type=str, help='バックアップ作成')
    parser.add_argument('--restore', type=str, help='バックアップ復元')
    parser.add_argument('--list-backups', action='store_true', help='バックアップ一覧')
    parser.add_argument('--report', action='store_true', help='詳細レポート')
    
    args = parser.parse_args()
    
    manager = AdvancedDataManager()
    
    if args.analyze:
        analysis = manager.analyze_data_sources()
        print("📊 データ分析結果:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    elif args.clean:
        removed = manager.clean_sample_data(interactive=True)
        print(f"🧹 クリーニング完了: {removed}")
    
    elif args.reset:
        backup_path = manager.reset_to_clean_state()
        print(f"🔄 リセット完了。バックアップ: {backup_path}")
    
    elif args.backup:
        backup_path = manager.create_backup(args.backup)
        print(f"📦 バックアップ作成: {backup_path}")
    
    elif args.restore:
        success = manager.restore_backup(args.restore)
        if success:
            print("✅ 復元完了")
        else:
            print("❌ 復元失敗")
    
    elif args.list_backups:
        backups = manager.list_backups()
        print("📦 バックアップ一覧:")
        for backup in backups:
            print(f"  {backup['name']} ({backup['created']}) - {backup['size']} bytes")
    
    elif args.report:
        manager.show_detailed_report()
    
    else:
        print("使用方法: python3 data_management_system.py --help")

if __name__ == "__main__":
    main() 