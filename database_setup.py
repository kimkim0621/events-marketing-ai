import os
import streamlit as st
from typing import Optional, Dict, Any
import json

# PostgreSQL関連のインポート（エラーハンドリング付き）
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
    st.write("✅ psycopg2 import successful")
except ImportError as e:
    PSYCOPG2_AVAILABLE = False
    st.error(f"❌ psycopg2 import failed: {str(e)}")
    st.info("💡 PostgreSQL接続が利用できません。SQLiteフォールバックのみ利用可能です。")

class SharedDatabase:
    """共有データベース管理クラス（Supabase PostgreSQL）"""
    
    def __init__(self):
        # 環境変数からSupabase接続情報を取得
        self.connection_string = self._get_connection_string()
        self.connection = None
    
    def _get_connection_string(self) -> str:
        """Supabase接続文字列を構築"""
        # Streamlit Secretsから取得（本番環境）
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            return st.secrets.database.connection_string
        
        # 環境変数から取得（開発環境）
        supabase_url = os.getenv('SUPABASE_DB_URL')
        if supabase_url:
            return supabase_url
        
        # 設定ファイルから取得（ローカル開発）
        try:
            with open('.streamlit/secrets.toml', 'r') as f:
                import toml
                secrets = toml.load(f)
                return secrets['database']['connection_string']
        except:
            pass
        
        # フォールバック：ローカルSQLite
        return "sqlite:///data/events_marketing.db"
    
    def connect(self):
        """データベースに接続（詳細デバッグ付き）"""
        try:
            if self.connection_string.startswith('postgresql://'):
                if not PSYCOPG2_AVAILABLE:
                    st.error("❌ psycopg2が利用できません。PostgreSQL接続をスキップします。")
                    return False
                    
                st.write("🔧 PostgreSQL接続を試行中...")
                self.connection = psycopg2.connect(
                    self.connection_string,
                    cursor_factory=RealDictCursor
                )
                st.write("✅ PostgreSQL接続成功")
                return True
            else:
                # SQLiteフォールバック
                st.write("🔧 SQLite接続を試行中...")
                import sqlite3
                sqlite_path = self.connection_string.replace('sqlite:///', '')
                st.write(f"**SQLiteパス**: {sqlite_path}")
                self.connection = sqlite3.connect(sqlite_path)
                st.write("✅ SQLite接続成功")
                return True
        except Exception as e:
            if 'psycopg2' in str(e):
                st.error(f"PostgreSQL接続エラー: {str(e)}")
                if hasattr(e, 'pgcode'):
                    st.write(f"**エラーコード**: {e.pgcode}")
            else:
                st.error(f"データベース接続エラー: {str(e)}")
            st.write(f"**エラータイプ**: {type(e).__name__}")
            return False
    
    def create_tables(self):
        """共有テーブルを作成"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # historical_events テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_events (
                    id SERIAL PRIMARY KEY,
                    event_name VARCHAR(255) NOT NULL,
                    theme TEXT NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    target_attendees INTEGER DEFAULT 0,
                    actual_attendees INTEGER DEFAULT 0,
                    budget INTEGER DEFAULT 0,
                    actual_cost INTEGER DEFAULT 0,
                    event_date DATE,
                    campaigns_used JSONB,
                    performance_metrics JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100) DEFAULT 'unknown'
                )
            """)
            
            # media_basic_info テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_basic_info (
                    id SERIAL PRIMARY KEY,
                    media_name VARCHAR(255) NOT NULL,
                    media_type VARCHAR(100),
                    cost_per_campaign INTEGER,
                    expected_reach INTEGER,
                    expected_ctr DECIMAL(5,4),
                    expected_cvr DECIMAL(5,4),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100) DEFAULT 'unknown'
                )
            """)
            
            # participants テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER REFERENCES historical_events(id),
                    job_title VARCHAR(100),
                    position VARCHAR(100),
                    company_name VARCHAR(255),
                    industry VARCHAR(100),
                    company_size VARCHAR(50),
                    registration_source VARCHAR(100),
                    registration_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # internal_knowledge テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS internal_knowledge (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    knowledge_type VARCHAR(50) DEFAULT 'general',
                    tags JSONB,
                    source_file VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100) DEFAULT 'unknown'
                )
            """)
            
            self.connection.commit()
            return True
            
        except Exception as e:
            st.error(f"テーブル作成エラー: {str(e)}")
            return False
    
    def insert_event_data(self, event_data: Dict[Any, Any], user_name: str = "unknown") -> bool:
        """イベントデータを挿入"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO historical_events 
                (event_name, theme, category, target_attendees, actual_attendees, 
                 budget, actual_cost, event_date, campaigns_used, performance_metrics, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                event_data.get('event_name'),
                event_data.get('theme'),
                event_data.get('category'),
                event_data.get('target_attendees', 0),
                event_data.get('actual_attendees', 0),
                event_data.get('budget', 0),
                event_data.get('actual_cost', 0),
                event_data.get('event_date'),
                json.dumps(event_data.get('campaigns_used', [])),
                json.dumps(event_data.get('performance_metrics', {})),
                user_name
            ))
            self.connection.commit()
            return True
        except Exception as e:
            st.error(f"データ挿入エラー: {str(e)}")
            return False
    
    def get_all_events(self) -> list:
        """すべてのイベントデータを取得"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, event_name, theme, category, target_attendees, 
                       actual_attendees, budget, actual_cost, event_date, 
                       campaigns_used, performance_metrics, created_at, created_by
                FROM historical_events 
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
        except Exception as e:
            st.error(f"データ取得エラー: {str(e)}")
            return []
    
    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()

# 使用例とセットアップ関数
def setup_shared_database():
    """共有データベースをセットアップ（詳細デバッグ付き）"""
    try:
        st.write("🔧 データベース接続を開始...")
        db = SharedDatabase()
        
        # 接続文字列の詳細表示
        connection_string = db.connection_string
        if connection_string.startswith('postgresql://'):
            # パスワード部分を隠して表示
            safe_connection = connection_string.split('@')[1] if '@' in connection_string else connection_string
            st.write(f"**接続先**: {safe_connection}")
        else:
            st.write(f"**接続先**: {connection_string}")
        
        st.write("📡 データベースに接続中...")
        if db.connect():
            st.write("✅ 接続成功！テーブルを作成中...")
            if db.create_tables():
                st.success("✅ 共有データベースの準備完了！")
                return db
            else:
                st.error("❌ テーブル作成に失敗しました")
                return None
        else:
            st.error("❌ データベース接続に失敗しました")
            return None
    except Exception as e:
        st.error(f"❌ セットアップエラー: {str(e)}")
        st.write(f"**エラータイプ**: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc(), language='python')
        return None 