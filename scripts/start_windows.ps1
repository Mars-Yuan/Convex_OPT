$ErrorActionPreference = "Stop"

$TaskName = "Convex_OPT"
$Port = 8501

Write-Host "正在启动 OPT Convex Strategy..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    throw "未找到计划任务，请先运行安装脚本。"
}

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 3
Start-Process "http://localhost:$Port"
Write-Host "服务已启动: http://localhost:$Port" -ForegroundColor Green