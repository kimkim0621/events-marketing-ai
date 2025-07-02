#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabaseデータベース接続テストスクリプト
設定が正しいかどうかを確認するために使用
"""

import os
import sys
import toml

def test_secrets_file():
    """secrets.tomlファイルの確認"""
    secrets_path = ".streamlit/secrets.toml"
    
    print("🔍 secrets.tomlファイルの確認...")
    
    if not os.path.exists(secrets_path):
        print("❌ .streamlit/secrets.toml ファイルが見つかりません")
        return False
    
    try:
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = toml.load(f)
        
        if 'database' not in secrets:
            print("❌ [database] セクションが見つかりません")
            return False
        
        connection_string = secrets['database'].get('connection_string', '')
        
        if 'your_actual_password' in connection_string or 'your_project_ref' in connection_string:
            print("⚠️  まだテンプレート値が残っています")
            print(f"   現在の値: {connection_string}")
            print("   実際のSupabase接続情報に置き換えてください")
            return False
        
        print("✅ secrets.tomlファイルは正しく設定されています")
        print(f"   接続先: {connection_string.split('@')[1].split('/')[0] if '@' in connection_string else 'unknown'}")
        return True
        
    except Exception as e:
        print(f"❌ secrets.tomlファイルの読み込みエラー: {str(e)}")
        return False

def test_database_connection():
    """実際のデータベース接続テスト"""
    print("\n🔗 データベース接続テスト...")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("❌ psycopg2がインストールされていません")
        print("   以下のコマンドでインストールしてください:")
        print("   pip install psycopg2-binary")
        return False
    
    try:
        # secrets.tomlから接続情報を読み込み
        with open(".streamlit/secrets.toml", 'r', encoding='utf-8') as f:
            secrets = toml.load(f)
        
        connection_string = secrets['database']['connection_string']
        
        # データベースに接続
        print("   接続中...")
        conn = psycopg2.connect(connection_string, cursor_factory=RealDictCursor)
        
        # 簡単なクエリを実行
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        
        print("✅ データベース接続成功！")
        print(f"   PostgreSQLバージョン: {version['version'][:50]}...")
        
        # テーブル一覧を取得
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"   既存テーブル数: {len(tables)}")
            for table in tables[:5]:  # 最初の5つだけ表示
                print(f"     - {table['table_name']}")
            if len(tables) > 5:
                print(f"     ... 他 {len(tables) - 5} テーブル")
        else:
            print("   まだテーブルは作成されていません（正常）")
        
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print("❌ データベース接続エラー")
        print(f"   エラー詳細: {str(e)}")
        print("\n🔧 考えられる原因:")
        print("   1. 接続文字列が間違っている")
        print("   2. パスワードが間違っている") 
        print("   3. Supabaseプロジェクトが停止している")
        print("   4. ネットワーク接続の問題")
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False

def show_setup_help():
    """設定方法のヘルプを表示"""
    print("\n📚 設定方法のヘルプ:")
    print("=" * 50)
    print("1. Supabaseダッシュボード (https://app.supabase.com) にログイン")
    print("2. あなたのプロジェクトをクリック")
    print("3. 左サイドバー「Settings」→「Database」")
    print("4. 「Connection string」をコピー")
    print("5. .streamlit/secrets.toml の connection_string に貼り付け")
    print("\n例:")
    print('connection_string = "postgresql://postgres:yourpassword@db.abc123.supabase.co:5432/postgres"')

def main():
    """メイン実行関数"""
    print("🧪 Supabaseデータベース接続テスト")
    print("=" * 50)
    
    # 1. secrets.tomlファイルの確認
    if not test_secrets_file():
        show_setup_help()
        return False
    
    # 2. 実際の接続テスト
    if not test_database_connection():
        show_setup_help()
        return False
    
    print("\n🎉 すべてのテストが完了しました！")
    print("   共有データベースの準備ができています。")
    
    return True

if __name__ == "__main__":
    main() 