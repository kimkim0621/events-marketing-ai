import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import sqlite3
from datetime import datetime
import logging

from services.data_manager import DataManager

class DataImporter:
    """データインポート機能"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
    
    async def import_events_from_csv(self, file_path: str, 
                                   mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        CSVファイルからイベントデータをインポート
        
        Args:
            file_path: CSVファイルのパス
            mapping: カラム名のマッピング辞書
        
        Returns:
            インポート結果の統計情報
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # デフォルトマッピング
            default_mapping = {
                'イベント名': 'event_name',
                'カテゴリ': 'category',
                'テーマ': 'theme',
                '目標参加者数': 'target_attendees',
                '実際参加者数': 'actual_attendees',
                '予算': 'budget',
                '実際コスト': 'actual_cost',
                '開催日': 'event_date',
                '使用施策': 'campaigns_used',
                'CTR': 'ctr',
                'CVR': 'cvr',
                'CPA': 'cpa'
            }
            
            if mapping:
                default_mapping.update(mapping)
            
            # カラム名の変換
            df = df.rename(columns=default_mapping)
            
            # データクレンジング
            df = await self._clean_event_data(df)
            
            # データベースに挿入
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    event_data = await self._convert_to_event_data(row)
                    await self.data_manager.add_event_data(event_data)
                    imported_count += 1
                except Exception as e:
                    errors.append(f"行 {index + 1}: {str(e)}")
            
            return {
                'total_rows': len(df),
                'imported_count': imported_count,
                'error_count': len(errors),
                'errors': errors[:10]  # 最初の10個のエラーのみ
            }
            
        except Exception as e:
            self.logger.error(f"CSVインポートエラー: {str(e)}")
            raise
    
    async def import_media_from_csv(self, file_path: str,
                                  mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        CSVファイルからメディアデータをインポート
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            default_mapping = {
                'メディア名': 'media_name',
                'メディアタイプ': 'media_type',
                '対象業界': 'target_industries',
                '対象職種': 'target_job_titles',
                '平均CTR': 'average_ctr',
                '平均CVR': 'average_cvr',
                '平均CPA': 'average_cpa',
                'リーチポテンシャル': 'reach_potential',
                '最小コスト': 'min_cost',
                '最大コスト': 'max_cost'
            }
            
            if mapping:
                default_mapping.update(mapping)
            
            df = df.rename(columns=default_mapping)
            df = await self._clean_media_data(df)
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    media_data = await self._convert_to_media_data(row)
                    await self.data_manager.add_media_data(media_data)
                    imported_count += 1
                except Exception as e:
                    errors.append(f"行 {index + 1}: {str(e)}")
            
            return {
                'total_rows': len(df),
                'imported_count': imported_count,
                'error_count': len(errors),
                'errors': errors[:10]
            }
            
        except Exception as e:
            self.logger.error(f"メディアCSVインポートエラー: {str(e)}")
            raise
    
    async def _clean_event_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """イベントデータのクレンジング"""
        # 欠損値の処理
        df['budget'] = df['budget'].fillna(0)
        df['actual_cost'] = df['actual_cost'].fillna(0)
        
        # 数値型の変換
        numeric_columns = ['target_attendees', 'actual_attendees', 'budget', 'actual_cost', 'ctr', 'cvr', 'cpa']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 日付形式の統一
        if 'event_date' in df.columns:
            df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
        
        # 異常値の除外
        df = df[df['target_attendees'] > 0]
        df = df[df['actual_attendees'] >= 0]
        
        return df
    
    async def _clean_media_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """メディアデータのクレンジング"""
        # 数値型の変換
        numeric_columns = ['average_ctr', 'average_cvr', 'average_cpa', 'reach_potential', 'min_cost', 'max_cost']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 異常値の除外
        df = df[df['average_ctr'] >= 0]
        df = df[df['average_cvr'] >= 0]
        df = df[df['average_cpa'] >= 0]
        
        return df
    
    async def _convert_to_event_data(self, row: pd.Series) -> Dict[str, Any]:
        """行データをイベントデータ形式に変換"""
        campaigns_used = []
        if pd.notna(row.get('campaigns_used')):
            campaigns_str = str(row['campaigns_used'])
            campaigns_used = [c.strip() for c in campaigns_str.split(',')]
        
        performance_metrics = {
            'ctr': float(row.get('ctr', 0)),
            'cvr': float(row.get('cvr', 0)),
            'cpa': float(row.get('cpa', 0))
        }
        
        return {
            'event_name': str(row['event_name']),
            'category': str(row.get('category', 'seminar')),
            'theme': str(row.get('theme', '')),
            'target_attendees': int(row['target_attendees']),
            'actual_attendees': int(row['actual_attendees']),
            'budget': int(row.get('budget', 0)),
            'actual_cost': int(row.get('actual_cost', 0)),
            'event_date': row['event_date'].strftime('%Y-%m-%d') if pd.notna(row.get('event_date')) else datetime.now().strftime('%Y-%m-%d'),
            'campaigns_used': campaigns_used,
            'performance_metrics': performance_metrics
        }
    
    async def _convert_to_media_data(self, row: pd.Series) -> Dict[str, Any]:
        """行データをメディアデータ形式に変換"""
        target_industries = []
        if pd.notna(row.get('target_industries')):
            target_industries = [i.strip() for i in str(row['target_industries']).split(',')]
        
        target_job_titles = []
        if pd.notna(row.get('target_job_titles')):
            target_job_titles = [j.strip() for j in str(row['target_job_titles']).split(',')]
        
        target_audience = {
            'industries': target_industries,
            'job_titles': target_job_titles
        }
        
        cost_range = {
            'min': int(row.get('min_cost', 0)),
            'max': int(row.get('max_cost', 0))
        }
        
        return {
            'media_name': str(row['media_name']),
            'media_type': str(row.get('media_type', '')),
            'target_audience': target_audience,
            'average_ctr': float(row.get('average_ctr', 0)),
            'average_cvr': float(row.get('average_cvr', 0)),
            'average_cpa': int(row.get('average_cpa', 0)),
            'reach_potential': int(row.get('reach_potential', 0)),
            'cost_range': cost_range,
            'best_performing_content_types': []
        }
    
    async def export_template_csv(self, data_type: str, output_path: str):
        """
        データインポート用のテンプレートCSVを生成
        
        Args:
            data_type: 'events' または 'media'
            output_path: 出力ファイルパス
        """
        if data_type == 'events':
            template_data = {
                'イベント名': ['サンプルセミナー'],
                'カテゴリ': ['seminar'],
                'テーマ': ['AI技術動向'],
                '目標参加者数': [100],
                '実際参加者数': [85],
                '予算': [500000],
                '実際コスト': [450000],
                '開催日': ['2025-03-01'],
                '使用施策': ['email_marketing,social_media'],
                'CTR': [2.5],
                'CVR': [5.0],
                'CPA': [5294]
            }
        elif data_type == 'media':
            template_data = {
                'メディア名': ['サンプルメディア'],
                'メディアタイプ': ['ディスプレイ広告'],
                '対象業界': ['IT,製造業'],
                '対象職種': ['エンジニア,マネージャー'],
                '平均CTR': [3.0],
                '平均CVR': [150.0],
                '平均CPA': [8000],
                'リーチポテンシャル': [5000],
                '最小コスト': [300000],
                '最大コスト': [1000000]
            }
        else:
            raise ValueError("data_type は 'events' または 'media' である必要があります")
        
        df = pd.DataFrame(template_data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        return output_path 