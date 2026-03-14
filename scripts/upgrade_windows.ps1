#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Mars-Yuan/Convex_OPT.git"
$InstallDir = "$env:USERPROFILE\.convex_opt"
$TaskName = "Convex_OPT"
$TempDir = Join-Path $env:TEMP ("convex_opt_upgrade_" + [guid]::NewGuid().ToString("N"))

if (-not (Test-Path $InstallDir)) {
    throw "未检测到已安装目录，请先运行安装脚本。"
}

Write-Host "正在升级 OPT Convex Strategy..." -ForegroundColor Cyan
if (Test-Path "$InstallDir\Streamlit_data.json") {
    Copy-Item "$InstallDir\Streamlit_data.json" "$env:TEMP\Streamlit_data_backup.json" -Force
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task -and $task.State -eq "Running") {
    Stop-ScheduledTask -TaskName $TaskName
}

Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "python|streamlit" -and $_.CommandLine -match "ocm_streamlit_Streamlit.py"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

git clone --depth 1 $RepoUrl $TempDir

Copy-Item "$TempDir\ocm_streamlit_Streamlit.py" "$InstallDir\" -Force
Copy-Item "$TempDir\requirements.txt" "$InstallDir\" -Force
Copy-Item "$TempDir\README.md" "$InstallDir\" -Force
Copy-Item "$TempDir\LICENSE" "$InstallDir\" -Force
Copy-Item "$TempDir\scripts\*.ps1" "$InstallDir\scripts\" -Force

if (Test-Path "$env:TEMP\Streamlit_data_backup.json") {
    Copy-Item "$env:TEMP\Streamlit_data_backup.json" "$InstallDir\Streamlit_data.json" -Force
    Remove-Item "$env:TEMP\Streamlit_data_backup.json" -Force
}

& "$InstallDir\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$InstallDir\venv\Scripts\python.exe" -m pip install -r "$InstallDir\requirements.txt"

Start-ScheduledTask -TaskName $TaskName
Remove-Item $TempDir -Recurse -Force
Write-Host "升级完成: http://localhost:8501" -ForegroundColor Green