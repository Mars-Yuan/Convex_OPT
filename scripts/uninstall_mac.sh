#!/bin/bash

set -euo pipefail

SERVICE_NAME="com.marsyuan.convexopt"
INSTALL_DIR="$HOME/.convex_opt"
PLIST_PATH="$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist"

read -r -p "确定要卸载 OPT Convex Strategy 吗？(y/N) " reply
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"
pkill -f "streamlit.*ocm_streamlit_Streamlit.py" >/dev/null 2>&1 || true
rm -rf "$INSTALL_DIR"
echo "卸载完成"