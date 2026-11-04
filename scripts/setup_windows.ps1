$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PythonLauncher) {
    & py -3 --version
    if ($LASTEXITCODE -ne 0) { throw "Python 3 was not found. Install Python 3.10 or newer." }
    & py -3 -m venv .venv
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) { throw "Python 3.10 or newer is required. Install it and enable Add Python to PATH." }
    & python --version
    if ($LASTEXITCODE -ne 0) { throw "Python could not be started." }
    & python -m venv .venv
}

if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
& $VenvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install project dependencies." }
& $VenvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "Could not install BT SENTINEL." }

Write-Host ""
Write-Host "BT SENTINEL setup completed." -ForegroundColor Cyan
Write-Host "Start the dashboard with: .\scripts\start_windows.bat"
