#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DISPLAY_NAME="OPT Convex Strategy"
SERVICE_NAME="com.marsyuan.convexopt"
INSTALL_DIR="$HOME/.convex_opt"
LOG_DIR="$INSTALL_DIR/logs"
PLIST_PATH="$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist"
PORT=8501
PYTHON_CMD=""

get_project_dir() {
    local source="${BASH_SOURCE[0]}"
    while [ -h "$source" ]; do
        local dir
        dir="$(cd -P "$(dirname "$source")" && pwd)"
        source="$(readlink "$source")"
        [[ $source != /* ]] && source="$dir/$source"
    done
    cd -P "$(dirname "$source")/.." && pwd
}

PROJECT_DIR="$(get_project_dir)"

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         OPT Convex Strategy - macOS 安装程序              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_os() {
    if [[ "$OSTYPE" != darwin* ]]; then
        echo -e "${RED}错误: 此脚本仅支持 macOS${NC}"
        exit 1
    fi
}

check_python() {
    if command -v python3 >/dev/null 2>&1; then
        local version
        version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
        local major minor
        major="${version%%.*}"
        minor="${version##*.}"
        if [[ "$major" -ge 3 && "$minor" -ge 9 ]]; then
            PYTHON_CMD="python3"
            echo -e "${GREEN}✓ Python ${version}${NC}"
            return
        fi
    fi

    echo -e "${YELLOW}未检测到 Python 3.9+，尝试通过 Homebrew 安装${NC}"
    if ! command -v brew >/dev/null 2>&1; then
        echo -e "${RED}错误: 请先安装 Homebrew，再重新运行安装脚本${NC}"
        exit 1
    fi
    brew install python@3.11
    PYTHON_CMD="python3"
}

create_directories() {
    mkdir -p "$INSTALL_DIR" "$INSTALL_DIR/scripts" "$LOG_DIR" "$HOME/Library/LaunchAgents"
}

copy_project_files() {
    cp "$PROJECT_DIR/ocm_streamlit_Streamlit.py" "$INSTALL_DIR/"
    cp "$PROJECT_DIR/Streamlit_data.json" "$INSTALL_DIR/"
    cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"
    cp "$PROJECT_DIR/README.md" "$INSTALL_DIR/"
    cp "$PROJECT_DIR/LICENSE" "$INSTALL_DIR/"
    cp "$PROJECT_DIR/scripts/"*.sh "$INSTALL_DIR/scripts/"
    chmod +x "$INSTALL_DIR/scripts/"*.sh
}

setup_venv() {
    cd "$INSTALL_DIR"
    rm -rf venv
    "$PYTHON_CMD" -m venv venv
    source "$INSTALL_DIR/venv/bin/activate"
    python -m pip install --upgrade pip
    python -m pip install -r "$INSTALL_DIR/requirements.txt"
    deactivate
}

write_launch_agent() {
    launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
    cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${SERVICE_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/venv/bin/streamlit</string>
        <string>run</string>
        <string>${INSTALL_DIR}/ocm_streamlit_Streamlit.py</string>
        <string>--server.port</string>
        <string>${PORT}</string>
        <string>--server.headless</string>
        <string>true</string>
        <string>--server.address</string>
        <string>localhost</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${INSTALL_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/streamlit_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/streamlit_stderr.log</string>
</dict>
</plist>
EOF
}

start_service() {
    launchctl load "$PLIST_PATH"
    sleep 3
}

open_browser() {
    for _ in {1..15}; do
        if curl -fsS "http://localhost:${PORT}" >/dev/null 2>&1; then
            open "http://localhost:${PORT}"
            return
        fi
        sleep 1
    done
    echo -e "${YELLOW}请手动访问 http://localhost:${PORT}${NC}"
}

print_summary() {
    echo -e "${GREEN}安装完成${NC}"
    echo -e "${BLUE}程序目录:${NC} $INSTALL_DIR"
    echo -e "${BLUE}启动命令:${NC} ~/.convex_opt/scripts/start_mac.sh"
    echo -e "${BLUE}停止命令:${NC} ~/.convex_opt/scripts/stop_mac.sh"
    echo -e "${BLUE}升级命令:${NC} ~/.convex_opt/scripts/upgrade_mac.sh"
    echo -e "${BLUE}卸载命令:${NC} ~/.convex_opt/scripts/uninstall_mac.sh"
}

main() {
    print_header
    check_os
    check_python
    create_directories
    copy_project_files
    setup_venv
    write_launch_agent
    start_service
    open_browser
    print_summary
}

main "$@"