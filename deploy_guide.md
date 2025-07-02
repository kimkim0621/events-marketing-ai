# 🌐 イベント集客AI - デプロイメントガイド

## 📋 概要

ローカル環境からメンバー全員がアクセスできる環境へのデプロイ方法を説明します。

## 🎯 デプロイ方法の比較

| 方法 | 難易度 | コスト | セキュリティ | アクセス範囲 |
|------|--------|--------|-------------|-------------|
| LAN内共有 | ⭐ | 無料 | 社内のみ | オフィス内 |
| Streamlit Cloud | ⭐⭐ | 無料 | 公開 | 全世界 |
| Heroku | ⭐⭐⭐ | 有料 | 高 | 全世界 |
| 社内サーバー | ⭐⭐⭐⭐ | - | 最高 | 社内 |

## 🏢 Option 1: LAN内共有（実装済み）

### **起動方法**
```bash
cd Projects/new-products/events-marketing-ai
python3 -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

### **アクセス方法**
- **社内メンバー**: `http://192.168.20.178:8501`
- **利用条件**: 同じネットワーク内

### **メリット・デメリット**
✅ **メリット**:
- 即座に利用開始
- セットアップ不要
- データは社内に保持

❌ **デメリット**:
- 起動者のPCが必要
- リモートワーク時は利用不可
- PC終了時に停止

---

## ☁️ Option 2: Streamlit Cloud デプロイ

### **手順1: GitHubリポジトリ準備**

#### **1-1. requirements.txtの最適化**
```bash
# 現在のファイルを確認
cat requirements.txt

# 必要に応じて軽量化
```

#### **1-2. GitHubにプッシュ**
```bash
# Git初期化（初回のみ）
git init
git add .
git commit -m "Initial commit: Event Marketing AI"

# GitHubリポジトリ作成後
git remote add origin https://github.com/yourusername/events-marketing-ai.git
git push -u origin main
```

### **手順2: Streamlit Cloud設定**

1. [Streamlit Cloud](https://streamlit.io/cloud) にアクセス
2. GitHubアカウントでサインイン
3. 「New app」をクリック
4. リポジトリ・ブランチ・ファイルパスを指定
   - Repository: `yourusername/events-marketing-ai`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
5. 「Deploy!」をクリック

### **手順3: 環境変数設定**
データベースファイルをクラウド対応にするための設定：

```python
# streamlit_app.py の冒頭に追加
import os
if "STREAMLIT_CLOUD" in os.environ:
    # クラウド環境用の設定
    DB_PATH = "events_marketing.db"
else:
    # ローカル環境用の設定
    DB_PATH = "data/events_marketing.db"
```

### **URL例**
`https://your-app-name.streamlit.app/`

---

## 🐳 Option 3: Docker化（中級者向け）

### **Dockerファイル作成**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0"]
```

### **起動方法**
```bash
# イメージビルド
docker build -t events-marketing-ai .

# コンテナ起動
docker run -p 8501:8501 events-marketing-ai
```

---

## 🖥️ Option 4: 社内サーバーデプロイ

### **Linux サーバーでの起動**
```bash
# 依存関係インストール
sudo apt update
sudo apt install python3 python3-pip

# アプリケーション配置
git clone https://github.com/yourusername/events-marketing-ai.git
cd events-marketing-ai
pip3 install -r requirements.txt

# サービスとして起動
sudo systemctl enable events-marketing-ai
sudo systemctl start events-marketing-ai
```

### **systemdサービスファイル例**
```ini
[Unit]
Description=Events Marketing AI
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/events-marketing-ai
ExecStart=/usr/bin/python3 -m streamlit run streamlit_app.py --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🛡️ セキュリティ考慮事項

### **Option 1 (LAN内)のセキュリティ**
- ✅ データは社内サーバーに保持
- ✅ ネットワーク内のみアクセス
- ⚠️ 認証機能なし

### **Option 2 (Streamlit Cloud)のセキュリティ**
- ⚠️ パブリックアクセス
- ⚠️ データがクラウドに保存
- 💡 **対策**: 認証機能の追加

### **認証機能の追加例**
```python
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == "your_secret_password":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("パスワード", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("パスワード", type="password", on_change=password_entered, key="password")
        st.error("パスワードが間違っています")
        return False
    else:
        return True

# メイン関数の冒頭
if not check_password():
    st.stop()
```

---

## 💡 推奨デプロイメント戦略

### **段階的導入**

#### **Phase 1: 社内テスト**
- **方法**: LAN内共有
- **期間**: 1-2週間
- **目的**: 機能テスト・フィードバック収集

#### **Phase 2: 本格運用**
- **方法**: Streamlit Cloud または 社内サーバー
- **期間**: 継続利用
- **目的**: 安定した本格運用

### **組織別推奨方法**

#### **スタートアップ・小規模チーム**
→ **Streamlit Cloud** (無料、簡単)

#### **中規模企業**
→ **社内サーバー** (セキュリティ重視)

#### **大企業**
→ **エンタープライズクラウド** (AWS/Azure等)

---

## 🚀 クイックスタート

### **今すぐ始めるなら**

1. **LAN内共有**（現在実行中）
   ```
   http://192.168.20.178:8501
   ```

2. **Streamlit Cloud準備**
   ```bash
   # 1. GitHubリポジトリ作成
   # 2. コードをプッシュ
   # 3. Streamlit Cloudでデプロイ
   ```

### **必要なファイル確認**
- ✅ streamlit_app.py
- ✅ requirements.txt  
- ✅ internal_data_system.py
- ✅ data_cleaner.py
- ✅ services/ ディレクトリ

---

**💡 Tips**: まずはLAN内共有で運用を開始し、利用者の反応を見てから本格的なクラウドデプロイを検討することをお勧めします！ 