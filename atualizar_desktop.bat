@echo off
chcp 65001 >nul
setlocal

set "DESKTOP=%~dp0"
set "DOCUMENTOS=%USERPROFILE%\OneDrive\Documentos\Projeto\Intensiva Calculator"

echo ========================================
echo  Atualizar Área de Trabalho
echo ========================================
echo.
echo Sincronizando de Documentos para Área de Trabalho...
echo.

if exist "%DOCUMENTOS%" (
    robocopy "%DOCUMENTOS%" "%DESKTOP%" /E /XD .git .venv venv __pycache__ .streamlit /XF .env /NFL /NDL /NJH /NJS /NC /NS
    echo.
    echo Área de Trabalho atualizada com os arquivos de Documentos.
) else (
    echo Pasta Documentos não encontrada. Fazendo pull do GitHub...
    "C:\Program Files\Git\bin\git.exe" pull origin main
)

echo.
echo Concluído.
pause
