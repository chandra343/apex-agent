# ==============================================================================
# Project Apex: Universal Windows PowerShell Installer
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "      PROJECT APEX: SOVEREIGN HYBRID AI AGENT       " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Starting Windows installation...`n" -ForegroundColor Green

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# 1. Detect Python
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $PythonCmd) {
    Write-Host "Error: Python >= 3.10 is required but was not found in PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://python.org and check 'Add to PATH'." -ForegroundColor Yellow
    exit 1
}

$PyVersion = & $PythonCmd.Source --version
Write-Host "Using Python: $PyVersion ($($PythonCmd.Source))"

# 2. Virtual Environment Setup
$VenvDir = Join-Path $ScriptDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python virtual environment in $VenvDir..."
    & $PythonCmd.Source -m venv $VenvDir
}

Write-Host "Upgrading pip & installing dependencies..."
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -e $ScriptDir --quiet

# 3. Create global bat wrapper in user profile
$BinDir = Join-Path $env:USERPROFILE ".apex\bin"
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

$BatWrapper = Join-Path $BinDir "apex.cmd"
$BatContent = @"
@echo off
"$VenvPython" -m apex.gateways.cli %*
"@
Set-Content -Path $BatWrapper -Value $BatContent

# 4. PATH Check
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    Write-Host "Adding $BinDir to User PATH..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("PATH", "$UserPath;$BinDir", "User")
    $env:PATH = "$env:PATH;$BinDir"
}

# 5. Config initialization
$ConfigDir = Join-Path $env:USERPROFILE ".apex"
$ConfigFile = Join-Path $ConfigDir "apex.json"
$ConfigExample = Join-Path $ScriptDir "apex.json.example"

if ((-not (Test-Path $ConfigFile)) -and (Test-Path $ConfigExample)) {
    Copy-Item $ConfigExample $ConfigFile
    Write-Host "Created default configuration template in $ConfigFile"
}

Write-Host "`n✔ Installation Successful!" -ForegroundColor Green
Write-Host "You can now run:"
Write-Host "  apex setup        -> Run the 6-stage interactive setup wizard"
Write-Host "  apex              -> Launch Pi-style interactive terminal TUI"
Write-Host "  apex gateway start-> Launch the 24/7 background messaging daemon"
