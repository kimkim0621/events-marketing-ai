# 🖥️ Supabase Database Settings UI 操作ガイド

## 🎯 目的
Database設定画面から接続情報を取得し、ローカル設定ファイルに反映させる

## 📋 詳細手順

### 1. Supabaseダッシュボードへアクセス

```
https://app.supabase.com
```

**ログイン後の画面**:
```
┌─────────────────────────────────────────────────┐
│ Supabase Dashboard                              │
├─────────────────────────────────────────────────┤
│ 📦 Your Projects                                │
│                                                 │
│ ┌──────────────┐  ┌──────────────┐             │
│ │              │  │              │             │
│ │ プロジェクト名 │  │   + New      │             │
│ │              │  │   Project    │             │
│ └──────────────┘  └──────────────┘             │
│        ↑                                       │
│   これをクリック！                               │
└─────────────────────────────────────────────────┘
```

### 2. プロジェクト画面の構成

**左サイドバー（上から下へ）**:
```
┌─────────────────┐
│ 🏠 Home         │
│ 📊 Table Editor │ 
│ 🔍 SQL Editor   │
│ 🔐 Auth         │
│ 📁 Storage      │
│ 🚀 Functions    │
│ 📊 Database     │ 
│ 📈 Reports      │
│ ⚙️ Settings     │ ← これをクリック！
└─────────────────┘
```

### 3. Settings サブメニュー

**Settingsをクリックすると展開**:
```
⚙️ Settings
  ├── 📋 General
  ├── 🔑 API
  ├── 🔐 Authentication  
  ├── 🗄️ Database      ← これをクリック！
  ├── 📁 Storage
  ├── 💳 Billing
  └── 👥 Team
```

### 4. Database設定画面の詳細

#### 🔍 **重要な情報の場所**

**A. Connection Parameters（画面上部）**
```
┌──────────────────────────────────────────────┐
│ Connection parameters                        │
├──────────────────────────────────────────────┤
│ Host: db.xxxxxxxxxxxxxxxxx.supabase.co      │
│ Database name: postgres                      │
│ Port: 5432                                   │
│ User: postgres                               │
│ Password: •••••••••••••••                   │
│          ［👁️ Show］ ← パスワード表示ボタン  │
└──────────────────────────────────────────────┘
```

**B. Connection String（画面中央）**
```
┌──────────────────────────────────────────────┐
│ Connection string                            │
├──────────────────────────────────────────────┤
│ postgresql://postgres:パスワード@db.xxxxx.   │
│ supabase.co:5432/postgres                    │
├──────────────────────────────────────────────┤
│ ［📋 Copy］ ← これをクリックして全体をコピー  │
└──────────────────────────────────────────────┘
```

**C. Connection Pooling（画面下部）**
```
┌──────────────────────────────────────────────┐
│ Connection pooling                           │
├──────────────────────────────────────────────┤
│ Host: db.xxxxxxxxxxxxxxxxx.supabase.co      │
│ Database name: postgres                      │
│ Port: 6543                                   │
│ User: postgres                               │
│ Password: •••••••••••••••                   │
└──────────────────────────────────────────────┘
```

## ⚠️ **注意点**

### ❌ 間違いやすいポイント
1. **Connection Pooling**の情報を使わない（ポート6543）
2. **上部のConnection parameters**の方を使う（ポート5432）
3. **Connection string**をそのままコピーする

### ✅ 正しい手順
1. **Connection string**の［📋 Copy］ボタンをクリック
2. コピーされた文字列をそのまま使用
3. パスワードも自動的に含まれている

## 🔧 **実際にコピーする文字列の例**

```
postgresql://postgres:your_real_password@db.abcdefghijk.supabase.co:5432/postgres
```

**このような形式**になっているはずです：
- `postgresql://` : プロトコル
- `postgres:` : ユーザー名
- `your_real_password` : 実際のパスワード（隠されていない）
- `@db.abcdefghijk.supabase.co` : ホスト名
- `:5432` : ポート番号
- `/postgres` : データベース名

## 🚨 **よくある問題**

### 問題1: パスワードが表示されない
**解決策**: Connection parametersの「👁️ Show」ボタンをクリック

### 問題2: 文字列が途中で切れる
**解決策**: 必ず「📋 Copy」ボタンを使用（手動選択ではなく）

### 問題3: Connection stringが見つからない
**解決策**: 画面をスクロールダウンして中央部を確認

### 問題4: ポート番号6543の文字列をコピーした
**解決策**: 上部のConnection string（ポート5432）を使用

## 📝 **次の作業**

コピーした接続文字列を`.streamlit/secrets.toml`ファイルに設定：

```toml
[database]
connection_string = "ここにコピーした文字列を貼り付け"
```

## ✅ **設定確認**

設定後、以下のコマンドでテスト：
```bash
python3 test_database_connection.py
```

## 🆘 **まだ分からない場合**

以下の情報を教えてください：
1. どの画面が表示されているか
2. 「Settings」は見つかったか
3. 「Database」サブメニューは見えるか
4. Connection stringは表示されているか

詳しくサポートいたします！ 