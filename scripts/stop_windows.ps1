$ErrorActionPreference = "SilentlyContinue"

$TaskName = "Convex_OPT"

Write-Host "Stopping OPT Convex Strategy..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task -and $task.State -eq "Running") {
    Stop-ScheduledTask -TaskName $TaskName
}

Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "python|streamlit" -and $_.CommandLine -match "ocm_streamlit_Streamlit.py"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Service stopped" -ForegroundColor Green