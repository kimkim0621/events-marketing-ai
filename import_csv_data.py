#!/usr/bin/env python3
"""
添付されたCSVファイルを直接インポートするスクリプト
"""

import pandas as pd
import sqlite3
import os
from data_import_ui import DataImportSystem

def import_conference_csv_file():
    """カンファレンス集客実績CSVファイルをインポート"""
    
    # CSVファイルのパスを確認
    csv_path = "/Users/hidetoshi.kimura/Desktop/claude-projects/カンファレンス集客実績まとめ - 過去カンファレンス実績.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSVファイルが見つかりません: {csv_path}")
        return
    
    print(f"📂 CSVファイルを読み込み中: {csv_path}")
    
    # DataImportSystemを初期化
    import_system = DataImportSystem()
    
    try:
        # CSVファイルを読み込み
        df = pd.read_csv(csv_path)
        print(f"📊 読み込み完了: {len(df)}行 x {len(df.columns)}列")
        print(f"📋 列名: {list(df.columns)}")
        
        # 最初の数行を表示
        print("\n📝 データサンプル:")
        print(df.head())
        
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
        conn = sqlite3.connect(import_system.db_path)
        cursor = conn.cursor()
        
        # 既存データをクリア（オプション）
        clear_existing = input("既存のデータをクリアしますか？ (y/n): ")
        if clear_existing.lower() == 'y':
            cursor.execute('DELETE FROM conference_campaign_results')
            print("🗑️ 既存データをクリアしました")
        
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
                print(f"⚠️ データ挿入エラー: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ インポート完了: {inserted_count}件のデータを挿入しました")
        
        # データ概要を表示
        summary = import_system.get_data_summary()
        print(f"\n📊 データベース概要:")
        print(f"   カンファレンス集客施策実績: {summary['campaign_results']}件")
        print(f"   申込者データ: {summary['participants']}件")
        print(f"   有償メディアデータ: {summary['media_data']}件")
        print(f"   知見データ: {summary['knowledge']}件")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")

def show_imported_data():
    """インポートされたデータを表示"""
    import_system = DataImportSystem()
    
    conn = sqlite3.connect(import_system.db_path)
    cursor = conn.cursor()
    
    # カンファレンス集客施策実績データを取得
    cursor.execute('SELECT * FROM conference_campaign_results ORDER BY created_at DESC LIMIT 10')
    columns = [description[0] for description in cursor.description]
    results = cursor.fetchall()
    
    if results:
        print("\n📋 インポートされたデータ（最新10件）:")
        df = pd.DataFrame(results, columns=columns)
        print(df.to_string(index=False))
    else:
        print("📋 データがありません")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 カンファレンス集客実績データインポートスクリプト")
    print("=" * 60)
    
    # CSVファイルをインポート
    import_conference_csv_file()
    
    # インポートされたデータを表示
    show_imported_data() 