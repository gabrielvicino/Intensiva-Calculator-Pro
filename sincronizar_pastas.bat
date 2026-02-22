@echo off
chcp 65001 >nul
setlocal

set "ORIGEM=%~dp0"
set "DESTINO=%USERPROFILE%\OneDrive\Área de Trabalho\Intensiva Calculator\Intensiva Calculator"

echo ========================================
echo  Sincronizar: Documentos -^> Área de Trabalho
echo ========================================
echo.
echo Origem:  %ORIGEM%
echo Destino: %DESTINO%
echo.

if not exist "%DESTINO%" (
    echo Criando pasta de destino...
    mkdir "%DESTINO%" 2>nul
)

echo Sincronizando arquivos...
robocopy "%ORIGEM%" "%DESTINO%" /E /XD .git .venv venv __pycache__ .streamlit /XF .env /NFL /NDL /NJH /NJS /NC /NS

if %ERRORLEVEL% LSS 8 (
    echo.
    echo Sincronização concluída com sucesso!
) else (
    echo.
    echo Aviso: Alguns arquivos podem não ter sido copiados. Código: %ERRORLEVEL%
)

echo.
pause
