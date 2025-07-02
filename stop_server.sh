#!/bin/bash

# イベント集客AI - サーバー停止スクリプト

echo "🛑 イベント集客AIサーバーを停止中..."

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# PIDファイルから停止
if [ -f "logs/streamlit.pid" ]; then
    PID=$(cat logs/streamlit.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔄 プロセス $PID を停止中..."
        kill $PID
        sleep 2
        
        # 強制停止が必要な場合
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚡ 強制停止中..."
            kill -9 $PID
        fi
        
        echo "✅ プロセス $PID を停止しました"
    else
        echo "⚠️  プロセス $PID は既に停止しています"
    fi
    rm -f logs/streamlit.pid
fi

# 残存プロセスをチェックして停止
if pgrep -f "streamlit run streamlit_app.py" > /dev/null; then
    echo "🔍 残存プロセスを検出、停止中..."
    pkill -f "streamlit run streamlit_app.py"
    sleep 2
fi

# 最終確認
if pgrep -f "streamlit run streamlit_app.py" > /dev/null; then
    echo "❌ 一部プロセスが残存しています"
    echo "📋 手動での確認をお勧めします:"
    echo "   ps aux | grep streamlit"
    echo "   pkill -f streamlit"
else
    echo "✅ 全てのStreamlitプロセスが停止しました"
fi

echo "📊 ログファイル: logs/streamlit.log" 