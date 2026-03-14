#!/bin/bash

set -euo pipefail

REPO_URL="https://github.com/Mars-Yuan/Convex_OPT.git"
INSTALL_DIR="$HOME/.convex_opt"
PLIST_PATH="$HOME/Library/LaunchAgents/com.marsyuan.convexopt.plist"
TEMP_DIR="/tmp/convex_opt_upgrade_$$"

if [ ! -d "$INSTALL_DIR" ]; then
    echo "未检测到已安装目录，请先运行安装脚本"
    exit 1
fi

echo "正在升级 OPT Convex Strategy..."
cp "$INSTALL_DIR/Streamlit_data.json" "/tmp/Streamlit_data_backup.json" 2>/dev/null || true
launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
pkill -f "streamlit.*ocm_streamlit_Streamlit.py" >/dev/null 2>&1 || true

rm -rf "$TEMP_DIR"
git clone --depth 1 "$REPO_URL" "$TEMP_DIR"

cp "$TEMP_DIR/ocm_streamlit_Streamlit.py" "$INSTALL_DIR/"
cp "$TEMP_DIR/requirements.txt" "$INSTALL_DIR/"
cp "$TEMP_DIR/README.md" "$INSTALL_DIR/"
cp "$TEMP_DIR/LICENSE" "$INSTALL_DIR/"
cp "$TEMP_DIR/scripts/"*.sh "$INSTALL_DIR/scripts/"
chmod +x "$INSTALL_DIR/scripts/"*.sh

if [ -f "/tmp/Streamlit_data_backup.json" ]; then
    cp "/tmp/Streamlit_data_backup.json" "$INSTALL_DIR/Streamlit_data.json"
    rm -f "/tmp/Streamlit_data_backup.json"
fi

source "$INSTALL_DIR/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$INSTALL_DIR/requirements.txt"
deactivate

launchctl load "$PLIST_PATH"
rm -rf "$TEMP_DIR"
echo "升级完成: http://localhost:8501"