#!/bin/bash

set -euo pipefail

REPO_URL="https://github.com/Mars-Yuan/Convex_OPT.git"
TEMP_DIR="/tmp/convex_opt_quick_install_$$"

echo "正在下载 Convex_OPT 最新版本..."
rm -rf "$TEMP_DIR"
git clone --depth 1 "$REPO_URL" "$TEMP_DIR"
chmod +x "$TEMP_DIR/scripts/install_mac.sh"
"$TEMP_DIR/scripts/install_mac.sh"
rm -rf "$TEMP_DIR"