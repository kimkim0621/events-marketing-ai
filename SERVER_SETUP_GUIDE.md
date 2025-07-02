# 🌐 イベント集客AI - サーバー運用ガイド

## ✅ **ターミナル独立実行 - 完全対応済み！**

このガイドに従って設定すれば、**ターミナルが切れてもアプリが継続動作**します。

---

## 🚀 **クイックスタート**

### **即座に開始**
```bash
# プロジェクトディレクトリに移動
cd Projects/new-products/events-marketing-ai

# サーバーをバックグラウンドで起動
./start_server.sh
```

### **アクセス**
- **ローカル**: http://localhost:8501
- **ネットワーク**: http://192.168.20.178:8501

### **停止**
```bash
./stop_server.sh
```

---

## 📋 **実行方法の選択肢**

| 方法 | 継続性 | 自動復旧 | 設定難易度 | 推奨度 |
|------|--------|----------|------------|--------|
| **nohupスクリプト** | ✅ | ❌ | ⭐ | 🥇 |
| **macOS自動起動** | ✅ | ✅ | ⭐⭐ | 🥇 |
| **Docker** | ✅ | ✅ | ⭐⭐⭐ | 🥉 |
| **手動実行** | ❌ | ❌ | ⭐ | 🥉 |

---

## 🎯 **方法1: nohupスクリプト（推奨）**

### **特徴**
- ✅ ターミナル独立
- ✅ 即座に利用可能
- ✅ ログ自動保存
- ❌ PC再起動時は手動起動が必要

### **使用方法**
```bash
# 起動
./start_server.sh

# 停止
./stop_server.sh

# ログ確認
tail -f logs/streamlit.log

# プロセス確認
ps aux | grep streamlit
```

### **起動成功の確認**
```
✅ サーバーが正常に起動しました！

📱 アクセス情報:
  ローカル: http://localhost:8501
  ネットワーク: http://192.168.20.178:8501
```

---

## 🔄 **方法2: macOS自動起動（最強）**

### **特徴**
- ✅ ターミナル独立
- ✅ PC再起動時に自動起動
- ✅ プロセス死活監視
- ✅ システムレベルの安定性

### **設定方法**
```bash
# 自動起動を設定
./setup_autostart.sh

# yを入力して有効化
🚀 自動起動を有効化しますか？ (y/N): y
```

### **管理コマンド**
```bash
# 手動開始
launchctl start com.events-marketing-ai

# 手動停止
launchctl stop com.events-marketing-ai

# 自動起動無効化
launchctl unload ~/Library/LaunchAgents/com.events-marketing-ai.plist

# 自動起動再有効化
launchctl load ~/Library/LaunchAgents/com.events-marketing-ai.plist
```

---

## 🐳 **方法3: Docker（高度）**

### **設定**
```bash
# Dockerイメージをビルド
docker build -t events-marketing-ai .

# バックグラウンドで起動
docker run -d -p 8501:8501 --name marketing-ai events-marketing-ai

# 停止
docker stop marketing-ai

# 再開
docker start marketing-ai
```

---

## 📊 **ログ・モニタリング**

### **ログファイル**
```bash
# メインログ
tail -f logs/streamlit.log

# 自動起動ログ
tail -f logs/autostart.log

# エラーログ
tail -f logs/autostart.error.log
```

### **プロセス確認**
```bash
# プロセス一覧
ps aux | grep streamlit

# ネットワーク確認
lsof -i :8501

# ポート確認
netstat -an | grep 8501
```

---

## 🔧 **トラブルシューティング**

### **問題1: ポートが使用中**
```bash
# 使用中のプロセスを確認
lsof -i :8501

# プロセスを停止
kill $(lsof -t -i:8501)

# または強制停止
pkill -f streamlit
```

### **問題2: 起動に失敗**
```bash
# ログを確認
cat logs/streamlit.log

# 手動実行でエラー確認
python3 -m streamlit run streamlit_app.py --server.address 0.0.0.0

# 依存関係確認
pip3 install -r requirements.txt
```

### **問題3: ネットワークアクセス不可**
```bash
# ファイアウォール確認
sudo pfctl -sr | grep 8501

# IPアドレス確認
ifconfig | grep inet
```

---

## 🌐 **ネットワークアクセス設定**

### **LAN内アクセス（既に設定済み）**
- アドレス: `0.0.0.0`（全てのインターフェースでリッスン）
- メンバーアクセス: `http://192.168.20.178:8501`

### **ファイアウォール設定（必要に応じて）**
```bash
# macOSファイアウォールでポート許可
sudo pfctl -f /etc/pf.conf
```

---

## 💡 **ベストプラクティス**

### **推奨運用手順**

#### **初回セットアップ**
1. `./start_server.sh` でテスト起動
2. 動作確認後に `./stop_server.sh` で停止
3. `./setup_autostart.sh` で自動起動設定
4. PC再起動でテスト

#### **日常運用**
- **確認**: ブラウザでアクセステスト
- **ログ**: 定期的な `tail -f logs/streamlit.log`
- **更新**: コード更新後は `./stop_server.sh` → `./start_server.sh`

#### **メンテナンス**
```bash
# 週次ログローテーション
mv logs/streamlit.log logs/streamlit.log.$(date +%Y%m%d)
touch logs/streamlit.log

# プロセス健全性チェック
ps aux | grep streamlit
```

---

## 📱 **メンバーアクセス方法**

### **社内メンバー向け案内**

```
🎯 イベント集客AIへのアクセス

URL: http://192.168.20.178:8501

📋 利用条件:
- 同じオフィスネットワーク内からアクセス
- ブラウザ: Chrome, Firefox, Safari 対応
- 問題があれば管理者に連絡

💡 機能:
- イベント施策提案
- データ管理・分析
- PDF/CSVインポート
```

---

## 🛡️ **セキュリティ考慮事項**

### **現在の設定**
- ✅ LAN内限定アクセス
- ✅ 社内データ保持
- ⚠️ 認証機能なし

### **セキュリティ強化オプション**
1. **認証追加**: パスワード認証の実装
2. **HTTPS化**: SSL証明書の設定
3. **VPN経由**: リモートアクセス制限

---

## 📞 **サポート情報**

### **動作確認済み環境**
- **OS**: macOS 13.6.0
- **Python**: 3.9
- **ブラウザ**: Chrome, Safari, Firefox

### **よくある質問**

**Q: ターミナルを閉じても大丈夫？**
A: はい、`./start_server.sh` で起動すればターミナル終了後も動作継続します。

**Q: PC再起動後も自動で動く？**
A: `./setup_autostart.sh` で自動起動を設定すれば、再起動後も自動で起動します。

**Q: 複数人が同時に使える？**
A: はい、Streamlitは複数ユーザーの同時アクセスに対応しています。

**Q: データは保持される？**
A: はい、SQLiteデータベースファイルで永続化されています。

---

## 🎉 **完了チェックリスト**

- [ ] `./start_server.sh` でサーバー起動
- [ ] ブラウザで http://localhost:8501 にアクセス成功
- [ ] ネットワーク経由で http://192.168.20.178:8501 にアクセス成功  
- [ ] `./stop_server.sh` で正常停止
- [ ] `./setup_autostart.sh` で自動起動設定（オプション）
- [ ] ターミナル終了後もアクセス可能を確認

**✅ 全てチェック完了 = ターミナル独立実行の完全セットアップ完了！** 