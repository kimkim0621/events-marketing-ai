# ⚡ 共有データベース 5分セットアップ

## 🎯 目的
ローカルDBから → チーム共有DBへ **5分で**移行

## ✅ 手順（5分）

### 1. Supabase無料アカウント作成 (2分)
1. https://supabase.com → 「Start your project」
2. GitHubでサインイン
3. プロジェクト作成:
   - 名前: `findy-events-ai`
   - パスワード: **強力なもの**（メモ）
   - Region: `Tokyo`

### 2. 接続情報コピー (1分)
1. Settings → Database
2. **Connection string**をコピー
3. パスワード部分を実際のパスワードに置換

### 3. 設定ファイル更新 (1分)
`.streamlit/secrets.toml`を編集:
```toml
[database]
connection_string = "postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.xxxxx.supabase.co:5432/postgres"
```

### 4. パッケージインストール (1分)
```bash
pip install psycopg2-binary toml
```

### 5. 動作確認 (30秒)
```bash
python3 -m streamlit run streamlit_app.py
```

## 🎉 完了！

これで**全メンバー**が同じデータを見れます！

---

**📞 困ったら**: 詳細は `SHARED_DATABASE_SETUP.md` を参照 