$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PythonLauncher) {
    & py -3 --version
    if ($LASTEXITCODE -ne 0) { throw "Python 3 não encontrado. Instale Python 3.10 ou superior." }
    & py -3 -m venv .venv
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) { throw "É necessário Python 3.10 ou superior. Instale e habilite Add Python to PATH." }
    & python --version
    if ($LASTEXITCODE -ne 0) { throw "Não foi possível iniciar o Python." }
    & python -m venv .venv
}

if ($LASTEXITCODE -ne 0) { throw "Não foi possível criar o ambiente virtual." }
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Não foi possível atualizar o pip." }
& $VenvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Não foi possível instalar as dependências." }
& $VenvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "Não foi possível instalar o BT SENTINEL." }

Write-Host ""
Write-Host "BT SENTINEL instalado com sucesso." -ForegroundColor Cyan
Write-Host "Inicie o painel com: .\scripts\start_windows.bat"
