$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Mars-Yuan/Convex_OPT.git"
$TempDir = Join-Path $env:TEMP ("convex_opt_quick_install_" + [guid]::NewGuid().ToString("N"))

Write-Host "正在下载 Convex_OPT 最新版本..." -ForegroundColor Cyan
git clone --depth 1 $RepoUrl $TempDir
powershell -NoProfile -ExecutionPolicy Bypass -File "$TempDir\scripts\install_windows.ps1"
Remove-Item $TempDir -Recurse -Force