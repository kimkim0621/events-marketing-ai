#!/usr/bin/env python3
"""
社内データ統合インポートシステム
- CSV/Excel読み込み
- PDF解析・データ抽出
- メディア属性管理
- 知見データベース構築
"""

import pandas as pd
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# PDF処理ライブラリ
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    print("📋 PDF処理ライブラリが不足しています。インストール: pip install PyPDF2 pdfplumber")
    PDF_AVAILABLE = False

class AdvancedDataImporter:
    """高度なデータインポート・管理システム"""
    
    def __init__(self, db_path: str = "data/events_marketing.db"):
        self.db_path = db_path
        self.ensure_database()
    
    def ensure_database(self):
        """データベースとテーブルの確保"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 知見データベーステーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,  -- 'media_insight', 'audience_insight', 'campaign_rule'
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                conditions TEXT,  -- JSON: 適用条件
                impact_score REAL DEFAULT 1.0,  -- 影響度スコア
                confidence_level REAL DEFAULT 0.8,  -- 信頼度
                source TEXT,  -- データソース
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # メディア詳細属性テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_name TEXT NOT NULL,
                attribute_type TEXT NOT NULL,  -- 'audience', 'content', 'pricing'
                attribute_key TEXT NOT NULL,
                attribute_value TEXT NOT NULL,
                data_source TEXT,  -- PDF, manual, survey等
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # インポート履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                import_type TEXT NOT NULL,
                records_imported INTEGER,
                status TEXT,
                error_message TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def import_csv_advanced(self, file_path: str, import_type: str) -> Dict[str, Any]:
        """高度なCSVインポート機能"""
        print(f"📊 CSVファイル分析中: {file_path}")
        
        if not Path(file_path).exists():
            return {"success": False, "error": f"ファイルが見つかりません: {file_path}"}
        
        try:
            # CSVファイルの構造分析
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            print(f"📋 {len(df)}行 x {len(df.columns)}列のデータを検出")
            print(f"🔍 列名: {list(df.columns)}")
            
            # インポートタイプに応じた処理
            if import_type == "events":
                return self._import_event_data(df, file_path)
            elif import_type == "media":
                return self._import_media_data(df, file_path)
            elif import_type == "media_attributes":
                return self._import_media_attributes(df, file_path)
            elif import_type == "knowledge":
                return self._import_knowledge_base(df, file_path)
            else:
                return {"success": False, "error": f"不明なインポートタイプ: {import_type}"}
                
        except Exception as e:
            error_msg = f"CSVインポートエラー: {str(e)}"
            self._log_import_history(file_path, "csv", import_type, 0, "error", error_msg)
            return {"success": False, "error": error_msg}
    
    def _import_event_data(self, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """イベントデータの高度インポート"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 列名の自動マッピング
        column_mapping = {
            # 標準的な列名
            'イベント名': 'event_name',
            'event_name': 'event_name',
            'カテゴリ': 'category', 
            'category': 'category',
            'テーマ': 'theme',
            'theme': 'theme',
            '目標参加者数': 'target_attendees',
            '目標申込数': 'target_attendees',
            'target_attendees': 'target_attendees',
            '実際参加者数': 'actual_attendees',
            '実際申込数': 'actual_attendees',
            'actual_attendees': 'actual_attendees',
            '予算': 'budget',
            'budget': 'budget',
            '実際コスト': 'actual_cost',
            'actual_cost': 'actual_cost',
            '開催日': 'event_date',
            'event_date': 'event_date',
            '使用施策': 'campaigns_used',
            'campaigns_used': 'campaigns_used',
            'CTR': 'ctr',
            'CVR': 'cvr', 
            'CPA': 'cpa'
        }
        
        # 列名の正規化
        df_normalized = df.rename(columns=column_mapping)
        imported_count = 0
        
        for _, row in df_normalized.iterrows():
            try:
                # 必須データの取得・変換
                event_name = str(row.get('event_name', f'インポートイベント_{imported_count+1}'))
                category = str(row.get('category', 'seminar'))
                theme = str(row.get('theme', ''))
                target_attendees = int(row.get('target_attendees', 0))
                actual_attendees = int(row.get('actual_attendees', 0))
                budget = int(row.get('budget', 0))
                actual_cost = int(row.get('actual_cost', 0))
                
                # 日付の処理
                event_date = row.get('event_date', datetime.now().strftime('%Y-%m-%d'))
                if pd.notna(event_date) and isinstance(event_date, str):
                    try:
                        # 日付形式の自動変換
                        parsed_date = pd.to_datetime(event_date).strftime('%Y-%m-%d')
                        event_date = parsed_date
                    except:
                        event_date = datetime.now().strftime('%Y-%m-%d')
                
                # 施策データの処理
                campaigns_used = row.get('campaigns_used', '["email_marketing"]')
                if isinstance(campaigns_used, str) and not campaigns_used.startswith('['):
                    # カンマ区切りの場合
                    campaigns_list = [c.strip() for c in campaigns_used.split(',')]
                    campaigns_used = json.dumps(campaigns_list)
                elif not isinstance(campaigns_used, str):
                    campaigns_used = '["email_marketing"]'
                
                # パフォーマンス指標の処理
                ctr = float(row.get('ctr', 2.0))
                cvr = float(row.get('cvr', 5.0))
                cpa = float(row.get('cpa', actual_cost / max(actual_attendees, 1) if actual_cost > 0 else 0))
                
                performance_metrics = json.dumps({
                    "ctr": ctr,
                    "cvr": cvr,
                    "cpa": cpa
                })
                
                # データベースに挿入
                cursor.execute('''
                    INSERT INTO historical_events 
                    (event_name, category, theme, target_attendees, actual_attendees, 
                     budget, actual_cost, event_date, campaigns_used, performance_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_name, category, theme, target_attendees, actual_attendees,
                    budget, actual_cost, event_date, campaigns_used, performance_metrics
                ))
                
                imported_count += 1
                
            except Exception as e:
                print(f"⚠️ 行 {imported_count + 1} でエラー: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        self._log_import_history(file_path, "csv", "events", imported_count, "success")
        return {"success": True, "imported_count": imported_count}
    
    def _import_media_attributes(self, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """メディア属性データのインポート"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                media_name = str(row.get('media_name', row.get('メディア名', '')))
                
                # 属性データの抽出
                for column in df.columns:
                    if column in ['media_name', 'メディア名']:
                        continue
                    
                    value = row[column]
                    if pd.notna(value) and str(value).strip():
                        # 属性タイプの推定
                        attribute_type = self._classify_attribute_type(column)
                        
                        cursor.execute('''
                            INSERT INTO media_attributes 
                            (media_name, attribute_type, attribute_key, attribute_value, data_source)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (media_name, attribute_type, column, str(value), file_path))
                        
                        imported_count += 1
                        
            except Exception as e:
                print(f"⚠️ メディア属性インポートエラー: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        self._log_import_history(file_path, "csv", "media_attributes", imported_count, "success")
        return {"success": True, "imported_count": imported_count}
    
    def _classify_attribute_type(self, column_name: str) -> str:
        """列名から属性タイプを推定"""
        column_lower = column_name.lower()
        
        if any(keyword in column_lower for keyword in ['職種', 'job', 'position', 'title']):
            return 'audience'
        elif any(keyword in column_lower for keyword in ['業界', 'industry', 'sector']):
            return 'audience'
        elif any(keyword in column_lower for keyword in ['価格', 'cost', 'price', '料金']):
            return 'pricing'
        elif any(keyword in column_lower for keyword in ['コンテンツ', 'content', '形式', 'format']):
            return 'content'
        elif any(keyword in column_lower for keyword in ['リーチ', 'reach', 'impression']):
            return 'performance'
        else:
            return 'other'
    
    def import_pdf_data(self, file_path: str, extraction_type: str = "media_info") -> Dict[str, Any]:
        """PDFからのデータ抽出"""
        if not PDF_AVAILABLE:
            return {"success": False, "error": "PDF処理ライブラリが不足しています"}
        
        print(f"📄 PDF解析中: {file_path}")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
            
            if extraction_type == "media_info":
                return self._extract_media_info_from_text(full_text, file_path)
            elif extraction_type == "audience_data":
                return self._extract_audience_data_from_text(full_text, file_path)
            else:
                return {"success": False, "error": f"不明な抽出タイプ: {extraction_type}"}
                
        except Exception as e:
            error_msg = f"PDF処理エラー: {str(e)}"
            self._log_import_history(file_path, "pdf", extraction_type, 0, "error", error_msg)
            return {"success": False, "error": error_msg}
    
    def _extract_media_info_from_text(self, text: str, file_path: str) -> Dict[str, Any]:
        """PDFテキストからメディア情報を抽出"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        extracted_count = 0
        
        # メディア名の抽出パターン
        media_patterns = [
            r'([A-Za-z]+(?:\s+[A-Za-z]+)*)\s*(?:媒体|メディア|広告)',
            r'媒体名[:：]\s*([^\n]+)',
            r'メディア名[:：]\s*([^\n]+)'
        ]
        
        # CTR/CVR/CPAの抽出パターン
        performance_patterns = {
            'ctr': r'CTR[:：]\s*([0-9.]+)%?',
            'cvr': r'CVR[:：]\s*([0-9.]+)%?',
            'cpa': r'CPA[:：]\s*([0-9,]+)円?'
        }
        
        # ターゲット属性の抽出
        audience_patterns = {
            'job_titles': r'(?:職種|対象職種)[:：]\s*([^\n]+)',
            'industries': r'(?:業界|対象業界)[:：]\s*([^\n]+)',
            'age_range': r'年齢[:：]\s*([^\n]+)'
        }
        
        # メディア名の検索
        media_names = []
        for pattern in media_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            media_names.extend(matches)
        
        for media_name in set(media_names):
            media_name = media_name.strip()
            if len(media_name) > 2:  # 短すぎる名前を除外
                
                # パフォーマンス指標の抽出
                for metric, pattern in performance_patterns.items():
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        value = match.replace(',', '')
                        cursor.execute('''
                            INSERT INTO media_attributes 
                            (media_name, attribute_type, attribute_key, attribute_value, data_source)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (media_name, 'performance', metric, value, file_path))
                        extracted_count += 1
                
                # オーディエンス情報の抽出
                for attr, pattern in audience_patterns.items():
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        cursor.execute('''
                            INSERT INTO media_attributes 
                            (media_name, attribute_type, attribute_key, attribute_value, data_source)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (media_name, 'audience', attr, match.strip(), file_path))
                        extracted_count += 1
        
        conn.commit()
        conn.close()
        
        self._log_import_history(file_path, "pdf", "media_info", extracted_count, "success")
        return {"success": True, "extracted_count": extracted_count, "media_found": len(set(media_names))}
    
    def add_knowledge_entry(self, category: str, title: str, content: str, 
                          conditions: Dict = None, impact_score: float = 1.0, 
                          confidence_level: float = 0.8, source: str = "manual") -> int:
        """知見データベースへの手動追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge_base 
            (category, title, content, conditions, impact_score, confidence_level, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            category, title, content, 
            json.dumps(conditions) if conditions else None,
            impact_score, confidence_level, source
        ))
        
        knowledge_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return knowledge_id
    
    def get_knowledge_for_conditions(self, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """条件に基づく知見の取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM knowledge_base 
            WHERE conditions IS NULL OR conditions = '' 
            ORDER BY impact_score DESC, confidence_level DESC
        ''')
        
        all_knowledge = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        relevant_knowledge = []
        for row in all_knowledge:
            knowledge = dict(zip(columns, row))
            
            # 条件マッチングロジック
            if knowledge['conditions']:
                try:
                    stored_conditions = json.loads(knowledge['conditions'])
                    if self._matches_conditions(conditions, stored_conditions):
                        relevant_knowledge.append(knowledge)
                except:
                    continue
            else:
                # 汎用的な知見
                relevant_knowledge.append(knowledge)
        
        conn.close()
        return relevant_knowledge
    
    def _matches_conditions(self, current_conditions: Dict, stored_conditions: Dict) -> bool:
        """条件マッチング判定"""
        for key, value in stored_conditions.items():
            if key in current_conditions:
                current_value = current_conditions[key]
                if isinstance(value, list):
                    if not any(v in current_value for v in value if isinstance(current_value, (list, str))):
                        return False
                elif str(value).lower() not in str(current_value).lower():
                    return False
        return True
    
    def _log_import_history(self, file_name: str, file_type: str, import_type: str, 
                           records_imported: int, status: str, error_message: str = None):
        """インポート履歴の記録"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO import_history 
            (file_name, file_type, import_type, records_imported, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_name, file_type, import_type, records_imported, status, error_message))
        
        conn.commit()
        conn.close()
    
    def show_import_statistics(self):
        """インポート統計の表示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 基本統計
        cursor.execute("SELECT COUNT(*) FROM historical_events")
        events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM media_performance")
        media_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM media_attributes")
        attributes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        knowledge_count = cursor.fetchone()[0]
        
        # インポート履歴
        cursor.execute('''
            SELECT file_type, import_type, COUNT(*), SUM(records_imported)
            FROM import_history WHERE status = 'success'
            GROUP BY file_type, import_type
        ''')
        import_stats = cursor.fetchall()
        
        print("\n📊 データベース統計")
        print(f"  📅 イベントデータ: {events_count}件")
        print(f"  📺 メディアデータ: {media_count}件") 
        print(f"  🎯 メディア属性: {attributes_count}件")
        print(f"  🧠 知見データ: {knowledge_count}件")
        
        print("\n📁 インポート履歴")
        for file_type, import_type, count, total_records in import_stats:
            print(f"  {file_type.upper()} ({import_type}): {count}回, {total_records}件")
        
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='社内データ統合インポートシステム')
    parser.add_argument('--file', type=str, help='インポートファイルのパス')
    parser.add_argument('--type', choices=['events', 'media', 'media_attributes', 'knowledge'], 
                       default='events', help='インポートデータタイプ')
    parser.add_argument('--format', choices=['csv', 'pdf'], default='csv', help='ファイル形式')
    parser.add_argument('--stats', action='store_true', help='統計情報の表示')
    
    args = parser.parse_args()
    
    importer = AdvancedDataImporter()
    
    if args.stats:
        importer.show_import_statistics()
        return
    
    if not args.file:
        print("❌ --file オプションでファイルを指定してください")
        return
    
    if args.format == 'csv':
        result = importer.import_csv_advanced(args.file, args.type)
    elif args.format == 'pdf':
        result = importer.import_pdf_data(args.file, args.type)
    
    if result['success']:
        print(f"✅ インポート完了: {result}")
        importer.show_import_statistics()
    else:
        print(f"❌ インポート失敗: {result['error']}")

if __name__ == "__main__":
    main() 