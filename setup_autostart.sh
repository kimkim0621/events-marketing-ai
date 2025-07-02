#!/bin/bash

# macOS自動起動設定スクリプト

echo "🔧 macOS自動起動を設定中..."

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR"

# ユーザー名を取得
USERNAME=$(whoami)

# launchdファイルの作成
PLIST_FILE="$HOME/Library/LaunchAgents/com.events-marketing-ai.plist"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.events-marketing-ai</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$APP_PATH/start_server.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$APP_PATH</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>$APP_PATH/logs/autostart.log</string>
    
    <key>StandardErrorPath</key>
    <string>$APP_PATH/logs/autostart.error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ launchdファイルを作成しました: $PLIST_FILE"

# 権限設定
chmod 644 "$PLIST_FILE"

echo "🚀 自動起動を有効化しますか？ (y/N): "
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    # 既存のサービスを停止（存在する場合）
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    
    # サービスを読み込み
    launchctl load "$PLIST_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ 自動起動が有効になりました"
        echo ""
        echo "📋 管理コマンド:"
        echo "  手動開始: launchctl start com.events-marketing-ai"
        echo "  手動停止: launchctl stop com.events-marketing-ai"
        echo "  自動起動無効化: launchctl unload $PLIST_FILE"
        echo "  自動起動再有効化: launchctl load $PLIST_FILE"
        echo ""
        echo "💡 システム再起動時に自動的にサーバーが起動します"
    else
        echo "❌ 自動起動の設定に失敗しました"
    fi
else
    echo "⏸️  自動起動設定をスキップしました"
    echo "💡 後で有効化する場合:"
    echo "   launchctl load $PLIST_FILE"
fi

echo ""
echo "📁 設定ファイル: $PLIST_FILE" 