#!/bin/bash

set -euo pipefail

SERVICE_NAME="com.marsyuan.convexopt"
PLIST_PATH="$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist"

echo "正在停止 OPT Convex Strategy..."
launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
pkill -f "streamlit.*ocm_streamlit_Streamlit.py" >/dev/null 2>&1 || true
echo "服务已停止"