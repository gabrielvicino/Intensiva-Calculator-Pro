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
echo === Sincronizando com Área de Trabalho ===
set "DESTINO=%USERPROFILE%\OneDrive\Área de Trabalho\Intensiva Calculator\Intensiva Calculator"
if exist "%DESTINO%" (
    robocopy "%~dp0" "%DESTINO%" /E /XD .git .venv venv __pycache__ .streamlit /XF .env /NFL /NDL /NJH /NJS /NC /NS >nul 2>&1
    echo Pasta da Área de Trabalho atualizada.
) else (
    echo Pasta da Área de Trabalho não encontrada. Execute sincronizar_pastas.bat manualmente.
)

echo.
echo Concluido com sucesso!
goto fim

:erro
echo.
echo Ocorreu um erro. Verifique as mensagens acima.

:fim
echo.
pause
