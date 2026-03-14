$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Mars-Yuan/Convex_OPT.git"
$ZipUrl = "https://github.com/Mars-Yuan/Convex_OPT/archive/refs/heads/main.zip"
$TempDir = Join-Path $env:TEMP ("convex_opt_quick_install_" + [guid]::NewGuid().ToString("N"))
$ZipPath = Join-Path $env:TEMP ("convex_opt_quick_install_" + [guid]::NewGuid().ToString("N") + ".zip")

function Write-Info($message) { Write-Host "-> $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "[OK] $message" -ForegroundColor Green }
function Write-Warn($message) { Write-Host "[!] $message" -ForegroundColor Yellow }

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
		return (Test-Path "$TempDir\scripts\install_windows.ps1")
	} catch {
		return $false
	}
}

function Download-WithZip {
	Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
	Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

	$expandedDir = Join-Path $TempDir "Convex_OPT-main"
	if (-not (Test-Path "$expandedDir\scripts\install_windows.ps1")) {
		throw "ZIP 下载成功，但未找到 install_windows.ps1"
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

Write-Host "正在下载 Convex_OPT 最新版本..." -ForegroundColor Cyan

try {
	Clear-ProblemProxySettings

	if (-not (Download-WithGit)) {
		Write-Warn "git clone 失败，回退到 ZIP 下载..."
		Download-WithZip
	}

	$installScript = "$TempDir\scripts\install_windows.ps1"
	if (-not (Test-Path $installScript)) {
		throw "未找到安装脚本: $installScript"
	}

	Write-Success "下载完成，开始执行安装脚本"
	powershell -NoProfile -ExecutionPolicy Bypass -File $installScript
}
finally {
	Cleanup-TempFiles
}