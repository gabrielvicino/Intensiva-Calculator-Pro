@echo off
chcp 65001 >nul
cls

echo.
echo ╔══════════════════════════════════════════╗
echo ║   🚀 UPLOAD RÁPIDO - GITHUB              ║
echo ╚══════════════════════════════════════════╝
echo.

REM Pede mensagem
set /p "MSG=📝 Mudança (Enter = auto): "

REM Se vazio, usa data/hora
if "%MSG%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATA=%%a/%%b
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set HORA=%%a:%%b
    set "MSG=Update !DATA! !HORA!"
)

echo.
echo ⚡ Executando...
echo.

REM 3 comandos diretos
git add . 2>nul
if errorlevel 1 goto erro

git commit -m "%MSG%" 2>nul
if errorlevel 1 (
    echo ⚠️  Nada para commitar
    goto fim
)

git push origin main 2>nul
if errorlevel 1 goto erro

echo.
echo ✅ DONE! GitHub atualizado.
goto fim

:erro
echo.
echo ❌ ERRO - Veja mensagens acima
pause
exit /b 1

:fim
echo.
pause
