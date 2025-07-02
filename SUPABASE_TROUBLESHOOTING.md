# 🔧 Supabase Connection Parameters 探し方

## 🎯 目的
Database接続情報が見つからない場合の解決方法

## 📍 **Connection Parametersの場所（最新版）**

### 方法1: プロジェクトホーム画面から

1. **左サイドバーの一番上「Home」**をクリック
2. **「Connect to your project」**セクションを探す
3. **「Connect」**ボタンまたは**「Database」**タブをクリック

### 方法2: Settings > General から

1. **Settings** → **General**をクリック
2. **「Project Settings」**セクションを確認
3. **「Database」**情報を探す

### 方法3: 直接的な方法

#### A. プロジェクトURL確認
現在のブラウザURLが以下のような形式の場合：
```
https://app.supabase.com/project/[プロジェクトID]/settings/database
```

#### B. 以下のURLに直接アクセス
```
https://app.supabase.com/project/[プロジェクトID]/settings/general
```

## 🔍 **見つけるべき情報**

以下のような表示を探してください：

```
┌──────────────────────────────────────┐
│ Database settings                    │
├──────────────────────────────────────┤
│ Host: db.xxxxxxxxxxxxx.supabase.co   │
│ Database name: postgres              │
│ Port: 5432                           │
│ User: postgres                       │
│ Password: ••••••••••••••             │
│ URI: postgresql://postgres:••••••••@ │
│      db.xxxxxxxxxxxxx.supabase.co:   │
│      5432/postgres                   │
└──────────────────────────────────────┘
```

## 🚨 **まだ見つからない場合**

### 代替方法: プロジェクト情報から手動構築

#### 必要な情報を集める
1. **プロジェクトURL**からプロジェクトIDを取得
2. **Settings > General**でプロジェクト詳細を確認
3. **API Keys**画面でanon public keyを確認

#### 接続文字列を手動構築
```
postgresql://postgres:[パスワード]@db.[プロジェクトID].supabase.co:5432/postgres
```

例：
```
postgresql://postgres:mypassword123@db.abcdefghijk.supabase.co:5432/postgres
```

## 📝 **手動構築の手順**

### Step 1: プロジェクトIDを取得
ブラウザのURLから：
```
https://app.supabase.com/project/abcdefghijk/...
                            ^^^^^^^^^^^
                         これがプロジェクトID
```

### Step 2: パスワードを確認
- プロジェクト作成時に設定したパスワード
- もし忘れた場合は、パスワードリセットが必要

### Step 3: 接続文字列を組み立て
```
postgresql://postgres:[パスワード]@db.[プロジェクトID].supabase.co:5432/postgres
```

## 🔄 **パスワードを忘れた場合**

### パスワードリセット方法
1. **Settings** → **Database**
2. **「Reset database password」**ボタンを探す
3. 新しいパスワードを設定

または

1. **Settings** → **General**
2. **「Project Settings」**で**「Reset password」**を探す

## 💡 **簡単な確認方法**

現在の画面で以下を試してください：

1. **Ctrl+F（Mac: Cmd+F）**で「postgresql」を検索
2. **Ctrl+F**で「5432」を検索  
3. **Ctrl+F**で「Connection」を検索

これで画面内に接続情報があるかすぐに分かります。

## 🆘 **それでも見つからない場合**

Google Sheetsベースの共有データベースに切り替えることをお勧めします：

1. **設定が5分で完了**
2. **Connection string不要**
3. **すぐに使い始められる**

詳細は `ALTERNATIVE_SHARED_STORAGE.md` を参照してください。 