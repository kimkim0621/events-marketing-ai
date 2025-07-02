#!/bin/bash

# イベント集客AI - サーバー起動スクリプト
# ターミナルが切れても継続実行されます

echo "🚀 イベント集客AIサーバーを起動中..."

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ログディレクトリを作成
mkdir -p logs

# 既存のプロセスをチェック
if pgrep -f "streamlit run streamlit_app.py" > /dev/null; then
    echo "⚠️  既存のStreamlitプロセスが実行中です"
    echo "プロセスを停止しますか？ (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🔄 既存プロセスを停止中..."
        pkill -f "streamlit run streamlit_app.py"
        sleep 2
    else
        echo "❌ 起動をキャンセルしました"
        exit 1
    fi
fi

# ポート確認
PORT=8501
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "⚠️  ポート $PORT は既に使用中です"
    PORT=8502
    echo "📍 ポート $PORT を使用します"
fi

# nohupでバックグラウンド起動
echo "🌐 サーバーをバックグラウンドで起動中..."
nohup python3 -m streamlit run streamlit_app.py \
    --server.address 0.0.0.0 \
    --server.port $PORT \
    --server.headless true \
    > logs/streamlit.log 2>&1 &

# プロセスIDを保存
echo $! > logs/streamlit.pid

# 起動確認
sleep 3

if pgrep -f "streamlit run streamlit_app.py" > /dev/null; then
    echo "✅ サーバーが正常に起動しました！"
    echo ""
    echo "📱 アクセス情報:"
    echo "  ローカル: http://localhost:$PORT"
    echo "  ネットワーク: http://$(ipconfig getifaddr en0):$PORT"
    echo ""
    echo "📋 管理コマンド:"
    echo "  停止: ./stop_server.sh"
    echo "  ログ確認: tail -f logs/streamlit.log"
    echo "  プロセス確認: ps aux | grep streamlit"
    echo ""
    echo "💡 ターミナルを閉じてもサーバーは継続動作します"
else
    echo "❌ サーバーの起動に失敗しました"
    echo "📋 ログを確認してください: cat logs/streamlit.log"
    exit 1
fi 