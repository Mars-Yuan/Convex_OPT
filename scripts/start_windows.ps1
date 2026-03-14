$ErrorActionPreference = "Stop"

$TaskName = "Convex_OPT"
$Port = 8501

Write-Host "Starting OPT Convex Strategy..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    throw "Scheduled task not found. Please run the installer first."
}

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 3
Start-Process "http://localhost:$Port"
Write-Host "Service started: http://localhost:$Port" -ForegroundColor Green