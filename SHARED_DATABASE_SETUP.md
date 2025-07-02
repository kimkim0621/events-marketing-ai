# 🗄️ 共有データベース設定ガイド

## 概要
現在のシステムはローカルSQLiteを使用しているため、メンバー間でのデータ共有ができません。  
このガイドでは、**Supabase**（無料PostgreSQL）を使用して共有データベースを構築する方法を説明します。

## 🎯 解決される問題
- ✅ チームメンバー間でのリアルタイムデータ共有
- ✅ 複数人で同時にデータ追加・編集が可能
- ✅ バックアップとデータ永続化
- ✅ セキュリティとアクセス制御

## 📋 セットアップ手順

### 1. Supabaseアカウント作成

1. **Supabaseにアクセス**: https://supabase.com
2. **「Start your project」**をクリック
3. **GitHubアカウントでサインアップ**（推奨）
4. **新しいプロジェクトを作成**
   - Organization: 新規作成またはexisting
   - Project name: `findy-events-marketing-ai`
   - Database password: **強力なパスワードを設定**（保存しておく）
   - Region: `Tokyo (ap-northeast-1)` を選択

### 2. データベース接続情報取得

1. **Supabaseダッシュボード**で作成したプロジェクトを開く
2. **左サイドバー** → **Settings** → **Database**
3. **Connection string**をコピー
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

### 3. ローカル設定ファイル更新

`.streamlit/secrets.toml`ファイルを編集:

```toml
[database]
connection_string = "postgresql://postgres:your_actual_password@db.your_project_ref.supabase.co:5432/postgres"
```

**⚠️ 重要**: 実際のパスワードとプロジェクトIDに置き換えてください

### 4. 依存関係インストール

```bash
pip install psycopg2-binary toml
```

### 5. アプリケーション更新

`streamlit_app.py`に以下を追加:

```python
# 共有データベース設定
try:
    from database_setup import setup_shared_database
    SHARED_DB_AVAILABLE = True
except ImportError:
    SHARED_DB_AVAILABLE = False

# データベース初期化
if SHARED_DB_AVAILABLE:
    shared_db = setup_shared_database()
```

## 🚀 使用方法

### データベース切り替え
- **共有モード**: Supabase PostgreSQL（チーム共有）
- **ローカルモード**: SQLite（個人用）

### データ移行
既存のローカルデータを共有データベースに移行:

```python
# 移行スクリプト（管理者実行）
def migrate_local_to_shared():
    # ローカルSQLiteから読み込み
    local_data = read_local_database()
    
    # 共有データベースに挿入
    for event in local_data:
        shared_db.insert_event_data(event)
```

## 🔒 セキュリティ設定

### Supabaseセキュリティ設定
1. **Row Level Security (RLS)** を有効化
2. **適切なポリシー**を設定
3. **API キー**の適切な管理

### 環境変数設定（本番環境）
```bash
export SUPABASE_DB_URL="postgresql://postgres:password@db.project.supabase.co:5432/postgres"
```

## 📊 料金について

### Supabase無料プラン
- **データベース**: 500MB
- **帯域幅**: 5GB/月
- **API リクエスト**: 50,000回/月
- **同時接続**: 最大60

**→ 小〜中規模チームには十分です**

## 🔄 代替案

### 1. **Neon** (サーバーレスPostgreSQL)
- 無料プラン: 1GB + 10時間/月のコンピュート
- 自動スケーリング

### 2. **PlanetScale** (MySQL)
- 無料プラン: 1GB + 1億行reads/月
- ブランチング機能

### 3. **Google Sheets API**
- 簡単な統合
- 非技術者でも編集可能
- リアルタイム同期

## 🛠️ トラブルシューティング

### 接続エラー
```
psycopg2.OperationalError: could not connect to server
```
**解決策**: 
1. 接続文字列の確認
2. ファイアウォール設定
3. Supabaseプロジェクトの状態確認

### パフォーマンス問題
- **接続プール**の設定
- **クエリ最適化**
- **インデックス**の追加

## 📝 次のステップ

1. **✅ Supabaseプロジェクト作成**
2. **✅ 接続設定更新**
3. **✅ 依存関係インストール**
4. **✅ アプリケーション更新**
5. **✅ データ移行実行**
6. **✅ チームメンバーに共有**

## 🤝 チーム共有

### メンバー招待
1. **Supabaseダッシュボード** → **Settings** → **Team**
2. **メンバーのメールアドレス**を招待
3. **適切な権限**を付与

### 設定ファイル共有
`.streamlit/secrets.toml`をセキュアに共有（Slack DM、暗号化など）

---

**💡 推奨**: まず**開発環境**でテストしてから、**本番環境**に適用してください。 