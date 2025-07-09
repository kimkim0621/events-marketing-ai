#!/usr/bin/env python3
"""
新しいデータ仕様に対応したデータインポートUI
- カンファレンス集客施策実績データ
- カンファレンス申込者ユーザーデータ
- 有償メディアデータ
- 知見データ
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class DataImportSystem:
    """データインポートシステム"""
    
    def __init__(self, db_path: str = "data/events_marketing.db"):
        # Streamlit Cloud対応のデータベースパス
        is_cloud = ("STREAMLIT_CLOUD" in os.environ or 
                   "STREAMLIT_SHARING" in os.environ or 
                   not os.path.exists("/tmp"))
        
        if is_cloud:
            # Streamlit Cloud環境では一時的なデータベースを使用
            self.db_path = ":memory:"
        else:
            # ローカル環境
            self.db_path = db_path
            # データディレクトリの作成
            try:
                os.makedirs("data", exist_ok=True)
            except Exception:
                pass
        
        self.ensure_tables()
    
    def ensure_tables(self):
        """テーブル作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. カンファレンス集客施策実績データ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conference_campaign_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT NOT NULL,
                conference_name TEXT NOT NULL,
                theme_category TEXT NOT NULL,
                format TEXT NOT NULL,
                target_industry TEXT,
                target_job_title TEXT,
                target_company_size TEXT,
                distribution_count INTEGER,
                click_count INTEGER,
                conversion_count INTEGER,
                cost_excluding_tax INTEGER,
                cpa INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. カンファレンス申込者ユーザーデータ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conference_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conference_name TEXT,
                job_title TEXT,
                position TEXT,
                industry TEXT,
                company_name TEXT,
                company_size TEXT,
                registration_source TEXT,
                registration_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. 有償メディアデータ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paid_media_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_name TEXT NOT NULL UNIQUE,
                reachable_count INTEGER,
                target_industry TEXT,
                target_job_title TEXT,
                target_company_size TEXT,
                cost_excluding_tax INTEGER,
                media_type TEXT,
                description TEXT,
                contact_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4. 知見データ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                knowledge_type TEXT DEFAULT 'general',
                impact_degree REAL DEFAULT 1.0,
                impact_scope TEXT,
                impact_frequency TEXT,
                applicable_conditions TEXT,
                tags TEXT,
                source TEXT,
                confidence_score REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def import_conference_campaign_csv(self, uploaded_file) -> Dict:
        """カンファレンス集客施策実績CSVのインポート"""
        try:
            df = pd.read_csv(uploaded_file)
            
            # 列名のマッピング
            column_mapping = {
                '施策名': 'campaign_name',
                'カンファレンス名': 'conference_name',
                'テーマ・カテゴリ': 'theme_category',
                '形式': 'format',
                'ターゲット(業種)': 'target_industry',
                'ターゲット(職種)': 'target_job_title',
                'ターゲット(従業員規模)': 'target_company_size',
                '配信数/PV': 'distribution_count',
                'クリック数': 'click_count',
                '申込(CV数)': 'conversion_count',
                '費用(税抜)': 'cost_excluding_tax',
                'CPA': 'cpa'
            }
            
            # データの前処理
            processed_data = []
            for _, row in df.iterrows():
                data = {}
                for csv_col, db_col in column_mapping.items():
                    if csv_col in row.index:
                        value = row[csv_col]
                        
                        # 数値データの処理
                        if db_col in ['distribution_count', 'click_count', 'conversion_count', 'cost_excluding_tax', 'cpa']:
                            if pd.isna(value):
                                data[db_col] = None
                            else:
                                # 金額表記の処理（¥記号やカンマを除去）
                                str_value = str(value).replace('¥', '').replace(',', '').strip()
                                if str_value == '' or str_value == 'nan':
                                    data[db_col] = None
                                else:
                                    try:
                                        data[db_col] = int(float(str_value))
                                    except (ValueError, TypeError):
                                        data[db_col] = None
                        else:
                            data[db_col] = str(value) if pd.notna(value) else None
                    else:
                        data[db_col] = None
                
                processed_data.append(data)
            
            # データベースに挿入
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            inserted_count = 0
            for data in processed_data:
                try:
                    cursor.execute('''
                        INSERT INTO conference_campaign_results 
                        (campaign_name, conference_name, theme_category, format, 
                         target_industry, target_job_title, target_company_size,
                         distribution_count, click_count, conversion_count, 
                         cost_excluding_tax, cpa)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['campaign_name'], data['conference_name'], 
                        data['theme_category'], data['format'],
                        data['target_industry'], data['target_job_title'], 
                        data['target_company_size'], data['distribution_count'],
                        data['click_count'], data['conversion_count'],
                        data['cost_excluding_tax'], data['cpa']
                    ))
                    inserted_count += 1
                except Exception as e:
                    st.error(f"データ挿入エラー: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"カンファレンス集客施策実績データ {inserted_count}件をインポートしました",
                "imported_count": inserted_count,
                "total_rows": len(processed_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"CSVインポートエラー: {str(e)}"
            }
    
    def import_participant_csv(self, uploaded_file, conference_name: str = None) -> Dict:
        """カンファレンス申込者ユーザーデータのインポート"""
        try:
            df = pd.read_csv(uploaded_file)
            
            # 列名のマッピング
            column_mapping = {
                '職種': 'job_title',
                '役職': 'position',
                '業種': 'industry',
                '企業名': 'company_name',
                '従業員規模': 'company_size'
            }
            
            processed_data = []
            for _, row in df.iterrows():
                data = {}
                for csv_col, db_col in column_mapping.items():
                    if csv_col in row.index:
                        value = row[csv_col]
                        data[db_col] = str(value) if pd.notna(value) else None
                    else:
                        data[db_col] = None
                
                # カンファレンス名が指定されている場合は関連付け
                if conference_name:
                    data['conference_name'] = conference_name
                
                processed_data.append(data)
            
            # データベースに挿入
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            inserted_count = 0
            for data in processed_data:
                try:
                    cursor.execute('''
                        INSERT INTO conference_participants 
                        (conference_name, job_title, position, industry, company_name, company_size)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('conference_name'), data['job_title'], data['position'], 
                        data['industry'], data['company_name'], data['company_size']
                    ))
                    inserted_count += 1
                except Exception as e:
                    st.error(f"データ挿入エラー: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"カンファレンス申込者データ {inserted_count}件をインポートしました",
                "imported_count": inserted_count,
                "total_rows": len(processed_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"CSVインポートエラー: {str(e)}"
            }
    
    def add_paid_media_data(self, media_data: Dict) -> Dict:
        """有償メディアデータの追加"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO paid_media_data 
                (media_name, reachable_count, target_industry, target_job_title,
                 target_company_size, cost_excluding_tax, media_type, description, contact_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                media_data.get('media_name'),
                media_data.get('reachable_count'),
                media_data.get('target_industry'),
                media_data.get('target_job_title'),
                media_data.get('target_company_size'),
                media_data.get('cost_excluding_tax'),
                media_data.get('media_type'),
                media_data.get('description'),
                media_data.get('contact_info')
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"有償メディアデータ '{media_data.get('media_name')}' を追加しました"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"メディアデータ追加エラー: {str(e)}"
            }
    
    def add_campaign_data(self, campaign_data: Dict) -> Dict:
        """施策実績データの追加"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conference_campaign_results 
                (campaign_name, conference_name, theme_category, format, 
                 target_industry, target_job_title, target_company_size,
                 distribution_count, click_count, conversion_count, 
                 cost_excluding_tax, cpa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                campaign_data.get('campaign_name'),
                campaign_data.get('conference_name'),
                campaign_data.get('theme_category'),
                campaign_data.get('format'),
                campaign_data.get('target_industry'),
                campaign_data.get('target_job_title'),
                campaign_data.get('target_company_size'),
                campaign_data.get('distribution_count'),
                campaign_data.get('click_count'),
                campaign_data.get('conversion_count'),
                campaign_data.get('cost_excluding_tax'),
                campaign_data.get('cpa')
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"施策実績データ '{campaign_data.get('campaign_name')}' を追加しました"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"施策実績データ追加エラー: {str(e)}"
            }
    
    def add_participant_data(self, participant_data: Dict) -> Dict:
        """参加者属性データの追加"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conference_participants 
                (conference_name, job_title, position, industry, company_name, company_size)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                participant_data.get('conference_name'),
                participant_data.get('job_title'),
                participant_data.get('position'),
                participant_data.get('industry'),
                participant_data.get('company_name'),
                participant_data.get('company_size')
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"参加者属性データ '{participant_data.get('job_title')}' を追加しました"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"参加者属性データ追加エラー: {str(e)}"
            }
    
    def import_media_csv(self, uploaded_file) -> Dict:
        """有償メディアデータCSVのインポート"""
        try:
            df = pd.read_csv(uploaded_file)
            
            # 列名のマッピング
            column_mapping = {
                'メディア名': 'media_name',
                'リーチ可能数': 'reachable_count',
                'ターゲット業界': 'target_industry',
                'ターゲット職種': 'target_job_title',
                'ターゲット企業規模': 'target_company_size',
                '費用(税抜)': 'cost_excluding_tax',
                'メディアタイプ': 'media_type',
                '説明': 'description',
                '連絡先情報': 'contact_info'
            }
            
            processed_data = []
            for _, row in df.iterrows():
                data = {}
                for csv_col, db_col in column_mapping.items():
                    if csv_col in row.index:
                        value = row[csv_col]
                        
                        # 数値データの処理
                        if db_col in ['reachable_count', 'cost_excluding_tax']:
                            if pd.isna(value):
                                data[db_col] = None
                            else:
                                # 金額表記の処理
                                str_value = str(value).replace('¥', '').replace(',', '').strip()
                                if str_value == '' or str_value == 'nan':
                                    data[db_col] = None
                                else:
                                    try:
                                        data[db_col] = int(float(str_value))
                                    except (ValueError, TypeError):
                                        data[db_col] = None
                        else:
                            data[db_col] = str(value) if pd.notna(value) else None
                    else:
                        data[db_col] = None
                
                processed_data.append(data)
            
            # データベースに挿入
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            inserted_count = 0
            for data in processed_data:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO paid_media_data 
                        (media_name, reachable_count, target_industry, target_job_title,
                         target_company_size, cost_excluding_tax, media_type, description, contact_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['media_name'], data['reachable_count'], data['target_industry'],
                        data['target_job_title'], data['target_company_size'], data['cost_excluding_tax'],
                        data['media_type'], data['description'], data['contact_info']
                    ))
                    inserted_count += 1
                except Exception as e:
                    st.error(f"データ挿入エラー: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"有償メディアデータ {inserted_count}件をインポートしました",
                "imported_count": inserted_count,
                "total_rows": len(processed_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"CSVインポートエラー: {str(e)}"
            }

    def add_knowledge_data(self, knowledge_data: Dict) -> Dict:
        """知見データの追加"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO knowledge_database 
                (title, content, knowledge_type, impact_degree, impact_scope,
                 impact_frequency, applicable_conditions, tags, source, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_data.get('title'),
                knowledge_data.get('content'),
                knowledge_data.get('knowledge_type', 'general'),
                knowledge_data.get('impact_degree', 1.0),
                knowledge_data.get('impact_scope'),
                knowledge_data.get('impact_frequency'),
                knowledge_data.get('applicable_conditions'),
                knowledge_data.get('tags'),
                knowledge_data.get('source'),
                knowledge_data.get('confidence_score', 0.8)
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"知見データ '{knowledge_data.get('title')}' を追加しました"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"知見データ追加エラー: {str(e)}"
            }
    
    def get_data_summary(self) -> Dict:
        """データ概要の取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # カンファレンス集客施策実績データ
            cursor.execute('SELECT COUNT(*) FROM conference_campaign_results')
            campaign_count = cursor.fetchone()[0]
            
            # 申込者データ
            cursor.execute('SELECT COUNT(*) FROM conference_participants')
            participant_count = cursor.fetchone()[0]
            
            # 有償メディアデータ
            cursor.execute('SELECT COUNT(*) FROM paid_media_data')
            media_count = cursor.fetchone()[0]
            
            # 知見データ
            cursor.execute('SELECT COUNT(*) FROM knowledge_database')
            knowledge_count = cursor.fetchone()[0]
            
            return {
                "campaign_results": campaign_count,
                "participants": participant_count,
                "media_data": media_count,
                "knowledge": knowledge_count
            }
            
        except Exception as e:
            return {
                "campaign_results": 0,
                "participants": 0,
                "media_data": 0,
                "knowledge": 0
            }
        finally:
            conn.close()

def main():
    """メインUI"""
    st.set_page_config(
        page_title="データインポートシステム",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 マーケティング施策データインポートシステム")
    st.markdown("---")
    
    # データインポートシステムの初期化
    import_system = DataImportSystem()
    
    # データ概要の表示
    st.header("📈 データ概要")
    summary = import_system.get_data_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("施策実績データ", summary["campaign_results"])
    with col2:
        st.metric("参加者属性データ", summary["participants"])
    with col3:
        st.metric("有償メディアデータ", summary["media_data"])
    with col4:
        st.metric("知見データ", summary["knowledge"])
    
    st.markdown("---")
    
    # 4つのカテゴリごとのタブ
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 施策実績データ",
        "👥 参加者属性データ",
        "💰 有償メディアデータ",
        "🧠 知見データ"
    ])
    
    # タブ1: 施策実績データ
    with tab1:
        st.header("📋 施策実績データの入力")
        
        # 入力方法の選択
        input_method = st.radio(
            "データ入力方法を選択",
            ["CSVファイル一括インポート", "WEB UI個別入力"],
            key="campaign_input_method"
        )
        
        if input_method == "CSVファイル一括インポート":
            st.subheader("📁 CSVファイル一括インポート")
            st.markdown("**必要な列:** 施策名, カンファレンス名, テーマ・カテゴリ, 形式, ターゲット(業種), ターゲット(職種), ターゲット(従業員規模), 配信数/PV, クリック数, 申込(CV数), 費用(税抜), CPA")
            
            # CSVテンプレートダウンロード
            template_csv = """施策名,カンファレンス名,テーマ・カテゴリ,形式,ターゲット(業種),ターゲット(職種),ターゲット(従業員規模),配信数/PV,クリック数,申込(CV数),費用(税抜),CPA
FCメルマガ,AI技術セミナー,AI・機械学習,ハイブリッド,IT・ソフトウェア,エンジニア,すべて,50000,500,50,0,0
Meta広告,AI技術セミナー,AI・機械学習,ハイブリッド,IT・ソフトウェア,エンジニア,すべて,100000,2000,100,1000000,10000"""
            
            st.download_button(
                label="📥 CSVテンプレートをダウンロード",
                data=template_csv,
                file_name="campaign_template.csv",
                mime="text/csv"
            )
            
            uploaded_file = st.file_uploader(
                "CSVファイルをアップロード",
                type=['csv'],
                key="campaign_csv"
            )
            
            if uploaded_file is not None:
                if st.button("インポート実行", key="import_campaign"):
                    with st.spinner("データをインポート中..."):
                        result = import_system.import_conference_campaign_csv(uploaded_file)
                        
                        if result["success"]:
                            st.success(result["message"])
                            st.info(f"処理済み行数: {result['total_rows']}")
                        else:
                            st.error(result["error"])
        
        else:  # WEB UI個別入力
            st.subheader("📝 WEB UI個別入力")
            
            with st.form("campaign_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    campaign_name = st.text_input("施策名*", placeholder="例: FCメルマガ")
                    conference_name = st.text_input("カンファレンス名*", placeholder="例: AI技術セミナー")
                    theme_category = st.text_input("テーマ・カテゴリ*", placeholder="例: AI・機械学習")
                    format_type = st.selectbox("形式*", ["ハイブリッド", "オンライン", "オフライン"])
                    target_industry = st.text_input("ターゲット(業種)", placeholder="例: IT・ソフトウェア")
                    target_job_title = st.text_input("ターゲット(職種)", placeholder="例: エンジニア")
                
                with col2:
                    target_company_size = st.text_input("ターゲット(従業員規模)", placeholder="例: 1-100名")
                    distribution_count = st.number_input("配信数/PV", min_value=0, value=0)
                    click_count = st.number_input("クリック数", min_value=0, value=0)
                    conversion_count = st.number_input("申込(CV数)", min_value=0, value=0)
                    cost_excluding_tax = st.number_input("費用(税抜)", min_value=0, value=0)
                    cpa = st.number_input("CPA", min_value=0, value=0)
                
                submitted = st.form_submit_button("データを追加")
                
                if submitted and campaign_name and conference_name and theme_category:
                    campaign_data = {
                        'campaign_name': campaign_name,
                        'conference_name': conference_name,
                        'theme_category': theme_category,
                        'format': format_type,
                        'target_industry': target_industry,
                        'target_job_title': target_job_title,
                        'target_company_size': target_company_size,
                        'distribution_count': distribution_count,
                        'click_count': click_count,
                        'conversion_count': conversion_count,
                        'cost_excluding_tax': cost_excluding_tax,
                        'cpa': cpa
                    }
                    
                    result = import_system.add_campaign_data(campaign_data)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["error"])
                elif submitted:
                    st.error("必須項目（施策名、カンファレンス名、テーマ・カテゴリ）を入力してください")
    
    # タブ2: 参加者属性データ
    with tab2:
        st.header("👥 参加者属性データの入力")
        
        # 入力方法の選択
        input_method = st.radio(
            "データ入力方法を選択",
            ["CSVファイル一括インポート", "WEB UI個別入力"],
            key="participant_input_method"
        )
        
        if input_method == "CSVファイル一括インポート":
            st.subheader("📁 CSVファイル一括インポート")
            st.markdown("**必要な列:** 職種, 役職, 業種, 企業名, 従業員規模")
            
            # CSVテンプレートダウンロード
            template_csv = """職種,役職,業種,企業名,従業員規模
エンジニア,シニアエンジニア,IT・ソフトウェア,テック株式会社,101-1000名
マネージャー,開発マネージャー,IT・ソフトウェア,イノベーション株式会社,1001-5000名
CTO,最高技術責任者,製造業,マニュファクチャリング株式会社,5001名以上"""
            
            st.download_button(
                label="📥 CSVテンプレートをダウンロード",
                data=template_csv,
                file_name="participant_template.csv",
                mime="text/csv"
            )
            
            conference_name = st.text_input("関連するカンファレンス名（オプション）")
            
            uploaded_file = st.file_uploader(
                "CSVファイルをアップロード",
                type=['csv'],
                key="participant_csv"
            )
            
            if uploaded_file is not None:
                if st.button("インポート実行", key="import_participant"):
                    with st.spinner("データをインポート中..."):
                        result = import_system.import_participant_csv(uploaded_file, conference_name)
                        
                        if result["success"]:
                            st.success(result["message"])
                            st.info(f"処理済み行数: {result['total_rows']}")
                        else:
                            st.error(result["error"])
        
        else:  # WEB UI個別入力
            st.subheader("📝 WEB UI個別入力")
            
            with st.form("participant_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    job_title = st.text_input("職種*", placeholder="例: エンジニア")
                    position = st.text_input("役職", placeholder="例: シニアエンジニア")
                    industry = st.text_input("業種*", placeholder="例: IT・ソフトウェア")
                
                with col2:
                    company_name = st.text_input("企業名", placeholder="例: テック株式会社")
                    company_size = st.selectbox("従業員規模", ["1-100名", "101-1000名", "1001-5000名", "5001名以上"])
                    conference_name = st.text_input("関連カンファレンス名", placeholder="例: AI技術セミナー")
                
                submitted = st.form_submit_button("データを追加")
                
                if submitted and job_title and industry:
                    participant_data = {
                        'job_title': job_title,
                        'position': position,
                        'industry': industry,
                        'company_name': company_name,
                        'company_size': company_size,
                        'conference_name': conference_name
                    }
                    
                    result = import_system.add_participant_data(participant_data)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["error"])
                elif submitted:
                    st.error("必須項目（職種、業種）を入力してください")
    
    # タブ3: 有償メディアデータ
    with tab3:
        st.header("💰 有償メディアデータの入力")
        
        # 入力方法の選択
        input_method = st.radio(
            "データ入力方法を選択",
            ["CSVファイル一括インポート", "WEB UI個別入力"],
            key="media_input_method"
        )
        
        if input_method == "CSVファイル一括インポート":
            st.subheader("📁 CSVファイル一括インポート")
            st.markdown("**必要な列:** メディア名, リーチ可能数, ターゲット業界, ターゲット職種, ターゲット企業規模, 費用(税抜), メディアタイプ, 説明, 連絡先情報")
            
            # CSVテンプレートダウンロード
            template_csv = """メディア名,リーチ可能数,ターゲット業界,ターゲット職種,ターゲット企業規模,費用(税抜),メディアタイプ,説明,連絡先情報
Meta広告,1000000,IT・ソフトウェア,エンジニア,すべて,2000000,Web広告,Facebook・Instagram広告,meta-ads@example.com
日経Xtech,500000,IT・ソフトウェア,エンジニア・マネージャー,1001名以上,2000000,メディア掲載,技術者向けメディア,nikkei-xtech@example.com
TechPlay,200000,IT・ソフトウェア,エンジニア,すべて,700000,イベント,技術者向けイベント支援,techplay@example.com"""
            
            st.download_button(
                label="📥 CSVテンプレートをダウンロード",
                data=template_csv,
                file_name="media_template.csv",
                mime="text/csv"
            )
            
            uploaded_file = st.file_uploader(
                "CSVファイルをアップロード",
                type=['csv'],
                key="media_csv"
            )
            
            if uploaded_file is not None:
                if st.button("インポート実行", key="import_media"):
                    with st.spinner("データをインポート中..."):
                        result = import_system.import_media_csv(uploaded_file)
                        
                        if result["success"]:
                            st.success(result["message"])
                            st.info(f"処理済み行数: {result['total_rows']}")
                        else:
                            st.error(result["error"])
        
        else:  # WEB UI個別入力
            st.subheader("📝 WEB UI個別入力")
            
            with st.form("media_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    media_name = st.text_input("メディア名*", placeholder="例: Meta広告")
                    reachable_count = st.number_input("リーチ可能数", min_value=0, value=0)
                    target_industry = st.text_input("ターゲット業界", placeholder="例: IT・ソフトウェア")
                    target_job_title = st.text_input("ターゲット職種", placeholder="例: エンジニア")
                
                with col2:
                    target_company_size = st.text_input("ターゲット企業規模", placeholder="例: すべて")
                    cost_excluding_tax = st.number_input("費用（税抜）", min_value=0, value=0)
                    media_type = st.selectbox("メディアタイプ", ["Web広告", "メルマガ", "メディア掲載", "イベント", "その他"])
                    description = st.text_area("説明", placeholder="メディアの詳細説明")
                
                contact_info = st.text_input("連絡先情報", placeholder="例: contact@example.com")
                
                submitted = st.form_submit_button("データを追加")
                
                if submitted and media_name:
                    media_data = {
                        'media_name': media_name,
                        'reachable_count': reachable_count,
                        'target_industry': target_industry,
                        'target_job_title': target_job_title,
                        'target_company_size': target_company_size,
                        'cost_excluding_tax': cost_excluding_tax,
                        'media_type': media_type,
                        'description': description,
                        'contact_info': contact_info
                    }
                    
                    result = import_system.add_paid_media_data(media_data)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["error"])
                elif submitted:
                    st.error("必須項目（メディア名）を入力してください")
    
    # タブ4: 知見データ
    with tab4:
        st.header("🧠 知見データの入力")
        
        # 入力方法の選択
        input_method = st.radio(
            "データ入力方法を選択",
            ["テキスト形式一括入力", "WEB UI個別入力"],
            key="knowledge_input_method"
        )
        
        if input_method == "テキスト形式一括入力":
            st.subheader("📝 テキスト形式一括入力")
            st.markdown("**入力形式:** 複数の知見を改行で区切って入力してください")
            
            bulk_text = st.text_area(
                "知見データ（1行1件）",
                height=200,
                placeholder="例:\nFCメルマガは開封率が高く、コンバージョン率も良い\nMeta広告は予算をかければリーチ数を増やせる\nTechPlayは技術者向けイベントで効果的"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                knowledge_type = st.selectbox("知見タイプ（一括適用）", ["general", "campaign", "media", "audience", "timing"])
                impact_degree = st.slider("影響度（一括適用）", 0.0, 5.0, 1.0, 0.1)
            with col2:
                impact_frequency = st.selectbox("影響頻度（一括適用）", ["常時", "頻繁", "時々", "稀"])
                confidence_score = st.slider("信頼度（一括適用）", 0.0, 1.0, 0.8, 0.1)
            
            if st.button("一括追加実行", key="bulk_knowledge"):
                if bulk_text.strip():
                    with st.spinner("知見データを追加中..."):
                        lines = [line.strip() for line in bulk_text.split('\n') if line.strip()]
                        success_count = 0
                        
                        for i, line in enumerate(lines, 1):
                            knowledge_data = {
                                'title': f"知見 {i}",
                                'content': line,
                                'knowledge_type': knowledge_type,
                                'impact_degree': impact_degree,
                                'impact_scope': None,
                                'impact_frequency': impact_frequency,
                                'applicable_conditions': None,
                                'tags': None,
                                'source': "一括入力",
                                'confidence_score': confidence_score
                            }
                            
                            result = import_system.add_knowledge_data(knowledge_data)
                            if result["success"]:
                                success_count += 1
                        
                        st.success(f"✅ {success_count}件の知見データを追加しました")
                        st.rerun()
                else:
                    st.error("知見データを入力してください")
        
        else:  # WEB UI個別入力
            st.subheader("📝 WEB UI個別入力")
            
            with st.form("knowledge_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    title = st.text_input("タイトル*", placeholder="例: FCメルマガの効果")
                    knowledge_type = st.selectbox("知見タイプ", ["general", "campaign", "media", "audience", "timing"])
                    impact_degree = st.slider("影響度", 0.0, 5.0, 1.0, 0.1)
                    impact_scope = st.text_input("影響範囲", placeholder="例: IT業界全般")
                
                with col2:
                    impact_frequency = st.selectbox("影響頻度", ["常時", "頻繁", "時々", "稀"])
                    applicable_conditions = st.text_area("適用条件", placeholder="例: 技術者向けイベントの場合")
                    tags = st.text_input("タグ（カンマ区切り）", placeholder="例: メルマガ,コンバージョン,効果")
                    source = st.text_input("情報源", placeholder="例: 過去実績分析")
                
                content = st.text_area("内容*", height=150, placeholder="知見の詳細内容を入力してください")
                confidence_score = st.slider("信頼度", 0.0, 1.0, 0.8, 0.1)
                
                submitted = st.form_submit_button("データを追加")
                
                if submitted and title and content:
                    knowledge_data = {
                        'title': title,
                        'content': content,
                        'knowledge_type': knowledge_type,
                        'impact_degree': impact_degree,
                        'impact_scope': impact_scope,
                        'impact_frequency': impact_frequency,
                        'applicable_conditions': applicable_conditions,
                        'tags': tags,
                        'source': source,
                        'confidence_score': confidence_score
                    }
                    
                    result = import_system.add_knowledge_data(knowledge_data)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["error"])
                elif submitted:
                    st.error("必須項目（タイトル、内容）を入力してください")

if __name__ == "__main__":
    main() 