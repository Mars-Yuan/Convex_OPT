$ErrorActionPreference = "SilentlyContinue"

$TaskName = "Convex_OPT"

Write-Host "正在停止 OPT Convex Strategy..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task -and $task.State -eq "Running") {
    Stop-ScheduledTask -TaskName $TaskName
}

Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "python|streamlit" -and $_.CommandLine -match "ocm_streamlit_Streamlit.py"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "服务已停止" -ForegroundColor Green