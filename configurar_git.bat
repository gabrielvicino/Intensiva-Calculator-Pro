@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Configurar identidade do Git ===
echo.
echo Digite seu email do GitHub (ex: seuemail@gmail.com):
set /p GIT_EMAIL=
echo Digite seu nome (ex: Gabriel Vicino):
set /p GIT_NAME=

"C:\Program Files\Git\bin\git.exe" config user.email "%GIT_EMAIL%"
"C:\Program Files\Git\bin\git.exe" config user.name "%GIT_NAME%"

echo.
echo Configurado com sucesso!
echo.
pause
