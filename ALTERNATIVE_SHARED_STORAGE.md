# 🔄 代替案：Google Sheets で簡単共有データベース

## 🎯 概要
Supabaseの設定が複雑な場合、Google Sheetsを使った簡単な共有データベースを構築できます。

## ✅ メリット
- ✅ **設定が超簡単**（5分で完了）
- ✅ **無料**で使用可能
- ✅ **リアルタイム共有**
- ✅ **ブラウザで直接編集**可能
- ✅ **非エンジニアでも使いやすい**
- ✅ **バックアップ自動**

## 📋 設定手順

### 1. Google Sheetsでデータベース作成

#### A. 新しいスプレッドシートを作成
1. https://sheets.google.com にアクセス
2. 「+ 新しいスプレッドシート」をクリック
3. 名前を「イベント集客データベース」に変更

#### B. データシート構成
以下の4つのシートを作成：

**Sheet 1: イベント実績**
```
| ID | イベント名 | テーマ | カテゴリ | 目標申込数 | 実際申込数 | 予算 | 実際コスト | 開催日 | 作成者 |
|----|-----------|-------|----------|------------|------------|------|------------|--------|--------|
| 1  | AI Summit | AI技術 | セミナー | 100        | 85         | 500000 | 450000   | 2025-01-15 | 田中 |
```

**Sheet 2: メディア情報**
```
| ID | メディア名 | 種別 | 料金 | 想定リーチ | 想定CTR | 想定CVR | 説明 | 作成者 |
|----|-----------|------|------|-----------|---------|---------|------|--------|
| 1  | TechCrunch | メディア | 100000 | 50000 | 0.02 | 0.05 | 技術系メディア | 佐藤 |
```

**Sheet 3: 申込者情報**
```
| ID | イベントID | 職種 | 役職 | 企業名 | 業界 | 従業員規模 | 申込経路 | 申込日 |
|----|-----------|------|------|--------|------|-----------|---------|--------|
| 1  | 1         | エンジニア | リーダー | ABC社 | IT | 101-300名 | メディア | 2025-01-10 |
```

**Sheet 4: 知見データ**
```
| ID | タイトル | 内容 | カテゴリ | タグ | 作成者 | 作成日 |
|----|----------|------|----------|------|--------|--------|
| 1  | メディア効果 | TechCrunchは効果が高い | メディア | 効果,実績 | 田中 | 2025-01-01 |
```

### 2. 共有設定

1. **右上の「共有」ボタン**をクリック
2. **「リンクを知っている全員」**に設定
3. **「編集者」**権限を付与
4. **共有リンクをコピー**してチームに送信

### 3. Google Sheets API設定（アプリ連携用）

#### A. Google Cloud Consoleでプロジェクト作成
1. https://console.cloud.google.com にアクセス
2. 新しいプロジェクトを作成：「event-marketing-ai」
3. **Google Sheets API**を有効化
4. **サービスアカウント**を作成
5. **JSONキー**をダウンロード

#### B. Sheets APIアクセス設定
```python
# requirements.txt に追加
google-auth==2.17.3
google-auth-oauthlib==1.0.0
google-auth-httplib2==0.2.0
google-api-python-client==2.88.0
gspread==5.9.0
```

## 🛠️ アプリケーション側の実装

### Google Sheets連携クラス
```python
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

class GoogleSheetsDatabase:
    def __init__(self):
        # サービスアカウントキーで認証
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # secrets.tomlから認証情報取得
        creds_dict = st.secrets["google_sheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        self.client = gspread.authorize(creds)
        
        # スプレッドシートを開く
        self.sheet = self.client.open("イベント集客データベース")
    
    def get_events(self):
        """イベント実績データを取得"""
        worksheet = self.sheet.worksheet("イベント実績")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    
    def add_event(self, event_data):
        """新しいイベントデータを追加"""
        worksheet = self.sheet.worksheet("イベント実績")
        row = [
            len(worksheet.get_all_records()) + 1,  # ID
            event_data['event_name'],
            event_data['theme'],
            event_data['category'],
            event_data['target_attendees'],
            event_data['actual_attendees'],
            event_data['budget'],
            event_data['actual_cost'],
            event_data['event_date'],
            event_data['created_by']
        ]
        worksheet.append_row(row)
```

### 設定ファイル
```toml
# .streamlit/secrets.toml
[google_sheets]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

## 📊 使用方法

### 1. 手動でのデータ入力
- **Google Sheetsで直接編集**
- **チームメンバーが同時編集可能**
- **変更履歴が自動保存**

### 2. アプリからのデータアクセス
```python
# Streamlitアプリでの使用例
@st.cache_data
def load_shared_data():
    db = GoogleSheetsDatabase()
    events = db.get_events()
    return events

# データ表示
st.title("📊 共有イベントデータ")
events_df = load_shared_data()
st.dataframe(events_df)
```

## 🎉 **この方法の特徴**

### ✅ **良い点**
- 設定が簡単（30分で完了）
- 非エンジニアでも直接編集可能
- リアルタイム同期
- 無料で使用可能
- バックアップが自動
- 権限管理が簡単

### ⚠️ **制限事項**
- 大量データには不向き（1000行程度まで）
- 複雑なクエリは難しい
- リレーショナルな操作が限定的

## 🚀 **実装判断**

**Google Sheetsを選ぶべき場合：**
- チームが5人以下
- データ量が少ない（月100件程度）
- 非エンジニアが多い
- 簡単に始めたい

**Supabaseを選ぶべき場合：**
- チームが大きい
- データ量が多い
- 複雑な分析が必要
- 長期的な運用を考えている

## 💡 **どちらがおすすめ？**

**初期段階**では**Google Sheets**から始めて、**データが増えてきたらSupabase**に移行するのが実用的です。

どちらの方法で進めたいですか？ 