#!/bin/bash

set -euo pipefail

SERVICE_NAME="com.marsyuan.convexopt"
PLIST_PATH="$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist"
PORT=8501

echo "正在启动 OPT Convex Strategy..."

if [ ! -f "$PLIST_PATH" ]; then
    echo "未找到服务配置，请先运行安装脚本"
    exit 1
fi

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"
sleep 2
open "http://localhost:${PORT}" >/dev/null 2>&1 || true
echo "服务已启动: http://localhost:${PORT}"