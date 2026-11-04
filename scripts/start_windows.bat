@echo off
setlocal
set "PROJECT_ROOT=%~dp0.."
pushd "%PROJECT_ROOT%"

if not exist ".venv\Scripts\python.exe" (
    echo [!] Environment not found. Run:
    echo     powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
    popd
    exit /b 1
)

".venv\Scripts\python.exe" -m bt_sentinel
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
