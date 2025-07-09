#!/usr/bin/env python3
"""
データ初期化モジュール
- アプリケーション起動時のサンプルデータ作成
- データベースの初期設定
"""

import sqlite3
import os
from datetime import datetime

def initialize_sample_data(db_path: str = "events_marketing.db"):
    """サンプルデータの初期化"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 既存データの確認
    cursor.execute("SELECT COUNT(*) FROM campaign_performance")
    campaign_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM internal_knowledge")
    knowledge_count = cursor.fetchone()[0]
    
    # サンプルデータが既に存在する場合はスキップ
    if campaign_count > 0 and knowledge_count > 0:
        conn.close()
        return f"既存データ確認: 施策実績{campaign_count}件、知見{knowledge_count}件"
    
    # 施策実績サンプルデータ
    if campaign_count == 0:
        sample_campaigns = [
            ('AI Engineering Summit', 'Meta広告', 'paid', 'IT・ソフトウェア', 'エンジニア', '100-999人', 50000, 120, 2000000, 16667),
            ('AI Engineering Summit', 'TechPlay', 'paid', 'IT・ソフトウェア', 'エンジニア', '100-999人', 30000, 80, 800000, 10000),
            ('AI Engineering Summit', 'FCメルマガ', 'free', 'IT・ソフトウェア', 'エンジニア', 'すべて', 8000, 200, 0, 0),
            ('AI Engineering Summit', 'Connpass', 'free', 'IT・ソフトウェア', 'エンジニア', 'すべて', 5000, 150, 0, 0),
            ('Developer Conference', 'Google広告', 'paid', 'IT・ソフトウェア', 'エンジニア', '100-999人', 40000, 100, 1500000, 15000),
            ('Developer Conference', 'LinkedIn広告', 'paid', 'IT・ソフトウェア', 'エンジニア', '100-999人', 25000, 60, 1200000, 20000),
            ('Developer Conference', 'X(Twitter)投稿', 'free', 'IT・ソフトウェア', 'エンジニア', 'すべて', 3000, 80, 0, 0),
            ('マーケティングサミット', 'Meta広告', 'paid', 'マーケティング・広告', 'マーケティング', '100-999人', 60000, 90, 1800000, 20000),
            ('マーケティングサミット', 'LinkedIn広告', 'paid', 'マーケティング・広告', 'マーケティング', '100-999人', 25000, 60, 1200000, 20000),
            ('マーケティングサミット', 'FCメルマガ', 'free', 'マーケティング・広告', 'マーケティング', 'すべて', 10000, 150, 0, 0),
            ('データサイエンス勉強会', 'Connpass', 'free', 'IT・ソフトウェア', 'データサイエンティスト', 'すべて', 8000, 200, 0, 0),
            ('データサイエンス勉強会', 'Meta広告', 'paid', 'IT・ソフトウェア', 'データサイエンティスト', '100-999人', 35000, 70, 1000000, 14286),
            ('セキュリティカンファレンス', 'TechPlay', 'paid', 'IT・ソフトウェア', 'セキュリティエンジニア', '100-999人', 20000, 50, 600000, 12000),
            ('セキュリティカンファレンス', 'FCメルマガ', 'free', 'IT・ソフトウェア', 'セキュリティエンジニア', 'すべて', 6000, 120, 0, 0),
            ('HR Tech Summit', 'LinkedIn広告', 'paid', '人事・採用', '人事', '100-999人', 30000, 80, 1500000, 18750),
            ('HR Tech Summit', 'FCメルマガ', 'free', '人事・採用', '人事', 'すべて', 8000, 160, 0, 0),
        ]
        
        for data in sample_campaigns:
            cursor.execute('''
                INSERT INTO campaign_performance 
                (event_name, campaign_name, campaign_type, target_industry, target_job_title, 
                 target_company_size, reach_count, conversion_count, cost_excluding_tax, cpa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
    
    # 知見データサンプル
    if knowledge_count == 0:
        sample_knowledge = [
            ('campaign', 'FCメルマガ効果', 'FCメルマガは開封率が高く、エンジニア向けイベントで特に効果的。既存リストの質が重要。', None, 1.2),
            ('campaign', 'Meta広告最適化', 'Meta広告は予算を多く投入するほどリーチが拡大し、CPAが改善される。ターゲティング精度が鍵。', None, 1.1),
            ('audience', 'エンジニア特性', 'エンジニアはTechPlayやConnpassなどの専門プラットフォームを好む。技術的な内容への関心が高い。', None, 1.3),
            ('budget', '予算配分', '無料施策と有料施策の組み合わせで最大効果を発揮。無料施策でベースを作り、有料で拡大。', None, 1.0),
            ('timing', '告知タイミング', '開催2-3週間前の告知が最も効果的。早すぎると忘れられ、遅すぎると予定が埋まる。', None, 1.1),
            ('media', 'SNS活用', 'X(Twitter)での拡散は技術系イベントで高い効果。影響力のあるエンジニアのリツイートが重要。', None, 1.2),
            ('campaign', 'LinkedIn広告', 'LinkedIn広告はBtoBイベントで効果的。職種・業界ターゲティングが精密。', None, 1.1),
            ('audience', 'マーケティング職特性', 'マーケティング職はLinkedInを活用する傾向が高い。新しい手法への関心が強い。', None, 1.2),
            ('campaign', 'TechPlay効果', 'TechPlayは技術者向けイベントで高いコンバージョン率。有料だが費用対効果が良い。', None, 1.3),
            ('timing', '平日開催', '平日開催のイベントは企業からの参加が多い。土日は個人参加が中心。', None, 1.0),
            ('budget', '小予算戦略', '予算50万円以下の場合は無料施策中心。FCメルマガ+SNS+Connpassの組み合わせが効果的。', None, 1.1),
            ('campaign', 'Google広告', 'Google広告は検索意図が明確なユーザーにリーチ。イベント名やテーマでの検索に有効。', None, 1.0),
        ]
        
        for category, title, content, conditions, impact in sample_knowledge:
            cursor.execute('''
                INSERT INTO internal_knowledge
                (category, title, content, conditions, impact_score, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (category, title, content, conditions, impact, 0.8, 'sample_data'))
    
    conn.commit()
    conn.close()
    
    return f"サンプルデータ初期化完了: 施策実績{len(sample_campaigns)}件、知見{len(sample_knowledge)}件を追加"

def ensure_database_structure(db_path: str = "events_marketing.db"):
    """データベース構造の確保"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # campaign_performanceテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT,
            campaign_name TEXT,
            campaign_type TEXT,
            target_industry TEXT,
            target_job_title TEXT,
            target_company_size TEXT,
            reach_count INTEGER,
            conversion_count INTEGER,
            cost_excluding_tax REAL,
            cpa REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # internal_knowledgeテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS internal_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            conditions TEXT,
            impact_score REAL DEFAULT 1.0,
            confidence REAL DEFAULT 0.8,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def initialize_app_data(db_path: str = "events_marketing.db"):
    """アプリケーション起動時のデータ初期化"""
    
    # データベース構造の確保
    ensure_database_structure(db_path)
    
    # サンプルデータの初期化
    result = initialize_sample_data(db_path)
    
    return result

if __name__ == "__main__":
    result = initialize_app_data()
    print(result) 