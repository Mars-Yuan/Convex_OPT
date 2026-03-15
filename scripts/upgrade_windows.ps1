#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Mars-Yuan/Convex_OPT.git"
$ZipUrl = "https://github.com/Mars-Yuan/Convex_OPT/archive/refs/heads/main.zip"
$InstallDir = "$env:USERPROFILE\.convex_opt"
$TaskName = "Convex_OPT"
$TempDir = Join-Path $env:TEMP ("convex_opt_upgrade_" + [guid]::NewGuid().ToString("N"))
$ZipPath = Join-Path $env:TEMP ("convex_opt_upgrade_" + [guid]::NewGuid().ToString("N") + ".zip")
$BackupPath = "$env:TEMP\Streamlit_data_backup.json"

function Clear-ProblemProxySettings {
    foreach ($name in @("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy")) {
        $value = [Environment]::GetEnvironmentVariable($name, "Process")
        if ($value -and $value -match "127\.0\.0\.1|localhost") {
            [Environment]::SetEnvironmentVariable($name, $null, "Process")
        }
    }

    $env:NO_PROXY = "*"
    $env:no_proxy = "*"

    if (Get-Command git -ErrorAction SilentlyContinue) {
        foreach ($key in @("http.proxy", "https.proxy")) {
            $proxyValue = git config --global --get $key 2>$null
            if ($proxyValue -and $proxyValue -match "127\.0\.0\.1|localhost") {
                git config --global --unset $key 2>$null
            }
        }
    }
}

function Download-WithGit {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return $false
    }

    try {
        git clone --depth 1 $RepoUrl $TempDir
        return (Test-Path "$TempDir\ocm_streamlit_Streamlit.py")
    } catch {
        return $false
    }
}

function Download-WithZip {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
    Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

    $expandedDir = Join-Path $TempDir "Convex_OPT-main"
    if (-not (Test-Path "$expandedDir\ocm_streamlit_Streamlit.py")) {
        throw "ZIP download succeeded, but project files were not found"
    }

    Get-ChildItem -Path $expandedDir -Force | ForEach-Object {
        Move-Item $_.FullName $TempDir -Force
    }
    Remove-Item $expandedDir -Recurse -Force
}

function Cleanup-TempFiles {
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force
    }
    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }
}

function Assert-DownloadedFiles {
    $requiredPaths = @(
        "$TempDir\ocm_streamlit_Streamlit.py",
        "$TempDir\requirements.txt",
        "$TempDir\README.md",
        "$TempDir\LICENSE",
        "$TempDir\scripts\upgrade_windows.ps1"
    )

    foreach ($path in $requiredPaths) {
        if (-not (Test-Path $path)) {
            throw "Required file not found after download: $path"
        }
    }
}

if (-not (Test-Path $InstallDir)) {
    throw "Install directory not found. Please run the installer first."
}

Write-Host "Upgrading OPT Convex Strategy..." -ForegroundColor Cyan
if (Test-Path "$InstallDir\Streamlit_data.json") {
    Copy-Item "$InstallDir\Streamlit_data.json" $BackupPath -Force
}

try {
    Clear-ProblemProxySettings

    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task -and $task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName
    }

    Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match "python|streamlit" -and $_.CommandLine -match "ocm_streamlit_Streamlit.py"
    } | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

    if (-not (Download-WithGit)) {
        Write-Host "git clone failed, switching to ZIP download..." -ForegroundColor Yellow
        Download-WithZip
    }

    Assert-DownloadedFiles

    New-Item -ItemType Directory -Path "$InstallDir\scripts" -Force | Out-Null
    Copy-Item "$TempDir\ocm_streamlit_Streamlit.py" "$InstallDir\" -Force
    Copy-Item "$TempDir\requirements.txt" "$InstallDir\" -Force
    Copy-Item "$TempDir\README.md" "$InstallDir\" -Force
    Copy-Item "$TempDir\LICENSE" "$InstallDir\" -Force
    Copy-Item "$TempDir\scripts\*.ps1" "$InstallDir\scripts\" -Force

    if (Test-Path $BackupPath) {
        Copy-Item $BackupPath "$InstallDir\Streamlit_data.json" -Force
        Remove-Item $BackupPath -Force
    }

    if (-not (Test-Path "$InstallDir\venv\Scripts\python.exe")) {
        throw "Python virtual environment not found. Please reinstall the application first."
    }

    & "$InstallDir\venv\Scripts\python.exe" -m pip install --upgrade pip
    & "$InstallDir\venv\Scripts\python.exe" -m pip install -r "$InstallDir\requirements.txt"

    if ($task) {
        Start-ScheduledTask -TaskName $TaskName
    } else {
        Write-Host "Scheduled task not found. Please rerun the Windows installer if background startup is required." -ForegroundColor Yellow
    }

    Write-Host "Upgrade completed: http://localhost:8501" -ForegroundColor Green
}
finally {
    Cleanup-TempFiles
}