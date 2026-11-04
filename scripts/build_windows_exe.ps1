$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Ambiente virtual não encontrado. Execute primeiro scripts\setup_windows.ps1."
}
& $Python -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar PyInstaller." }
& $Python -m PyInstaller --noconfirm --clean --onefile --console --name BT-SENTINEL --collect-all bleak --collect-all rich run_bt_sentinel.py
if ($LASTEXITCODE -ne 0) { throw "A compilação do executável falhou." }
Write-Host "Executável gerado em: dist\BT-SENTINEL.exe" -ForegroundColor Cyan
