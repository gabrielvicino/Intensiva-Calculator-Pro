@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Atualizando projeto do GitHub ===
"C:\Program Files\Git\bin\git.exe" pull origin main

echo.
echo Concluído.
pause
