#Requires -RunAsAdministrator

$ErrorActionPreference = "SilentlyContinue"

$TaskName = "Convex_OPT"
$InstallDir = "$env:USERPROFILE\.convex_opt"

$reply = Read-Host "Confirm uninstall OPT Convex Strategy? (Y/N)"
if ($reply -notin @("Y", "y")) {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    if ($task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "python|streamlit" -and $_.CommandLine -match "ocm_streamlit_Streamlit.py"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

if (Test-Path $InstallDir) {
    Remove-Item $InstallDir -Recurse -Force
}

Write-Host "Uninstall completed" -ForegroundColor Green