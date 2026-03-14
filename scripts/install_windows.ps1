#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$DisplayName = "OPT Convex Strategy"
$TaskName = "Convex_OPT"
$InstallDir = "$env:USERPROFILE\.convex_opt"
$LogDir = "$InstallDir\logs"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$Port = 8501

function Write-Info($message) { Write-Host "-> $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "[OK] $message" -ForegroundColor Green }
function Write-Warn($message) { Write-Host "[!] $message" -ForegroundColor Yellow }

function Get-CurrentUserId {
    try {
        return [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    } catch {
        if ($env:USERDOMAIN) {
            return "$env:USERDOMAIN\$env:USERNAME"
        }
        return $env:USERNAME
    }
}

function Get-PythonCommand {
    foreach ($cmd in @("python", "py", "python3")) {
        try {
            $version = & $cmd --version 2>&1
            if ($version -match "Python (\d+)\.(\d+)") {
                if ([int]$Matches[1] -ge 3 -and [int]$Matches[2] -ge 9) {
                    return $cmd
                }
            }
        } catch {}
    }
    throw "Python 3.9+ not found. Please install Python first."
}

function Copy-ProjectFiles {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    New-Item -ItemType Directory -Path "$InstallDir\scripts" -Force | Out-Null

    Copy-Item "$ProjectDir\ocm_streamlit_Streamlit.py" "$InstallDir\" -Force
    Copy-Item "$ProjectDir\Streamlit_data.json" "$InstallDir\" -Force
    Copy-Item "$ProjectDir\requirements.txt" "$InstallDir\" -Force
    Copy-Item "$ProjectDir\README.md" "$InstallDir\" -Force
    Copy-Item "$ProjectDir\LICENSE" "$InstallDir\" -Force
    Copy-Item "$ProjectDir\scripts\*.ps1" "$InstallDir\scripts\" -Force
}

function Setup-Venv {
    param([string]$PythonCmd)

    Set-Location $InstallDir
    if (Test-Path "$InstallDir\venv") {
        Remove-Item "$InstallDir\venv" -Recurse -Force
    }
    & $PythonCmd -m venv "$InstallDir\venv"
    & "$InstallDir\venv\Scripts\python.exe" -m pip install --upgrade pip
    & "$InstallDir\venv\Scripts\python.exe" -m pip install -r "$InstallDir\requirements.txt"
}

function Write-StartupScript {
    $startupPs1 = @"
Set-Location "$InstallDir"
& "$InstallDir\venv\Scripts\streamlit.exe" run "$InstallDir\ocm_streamlit_Streamlit.py" --server.port $Port --server.headless true --server.address localhost *>> "$LogDir\streamlit.log"
"@
    $startupPs1 | Out-File -FilePath "$InstallDir\startup.ps1" -Encoding utf8
}

function Register-AppTask {
    $currentUserId = Get-CurrentUserId
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$InstallDir\startup.ps1`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUserId
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $currentUserId -LogonType Interactive -RunLevel Limited

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $DisplayName | Out-Null
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "      OPT Convex Strategy - Windows Installer               " -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host ""

$pythonCmd = Get-PythonCommand
Write-Info "Using Python: $pythonCmd"
Copy-ProjectFiles
Setup-Venv -PythonCmd $pythonCmd
Write-StartupScript
Register-AppTask

Write-Success "Installation completed"
Write-Host "Startup mode: launch in background after Windows sign-in" -ForegroundColor Cyan
Write-Host "URL: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "Browser is not opened automatically." -ForegroundColor Yellow