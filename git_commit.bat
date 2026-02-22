@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Git Add ===
"C:\Program Files\Git\bin\git.exe" add .
if errorlevel 1 goto erro

echo.
echo === Git Status ===
"C:\Program Files\Git\bin\git.exe" status
if errorlevel 1 goto erro

echo.
echo === Git Commit ===
"C:\Program Files\Git\bin\git.exe" commit -m "Remover campo PCT, adicionar unidade UI na insulinoterapia"
if errorlevel 1 (
    echo.
    echo Se pediu email/nome, execute primeiro: configurar_git.bat
    goto fim
)

echo.
echo === Git Push ===
"C:\Program Files\Git\bin\git.exe" branch -M main 2>nul
"C:\Program Files\Git\bin\git.exe" push -u origin main
if errorlevel 1 goto erro

echo.
echo Concluido com sucesso!
goto fim

:erro
echo.
echo Ocorreu um erro. Verifique as mensagens acima.

:fim
echo.
pause
