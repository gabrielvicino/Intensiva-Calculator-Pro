@echo off
chcp 65001 >nul
setlocal

set "ORIGEM=%~dp0"
set "DESTINO=C:\Projetos\Intensiva Calculator"

echo ========================================
echo  Mover projeto para fora do OneDrive
echo ========================================
echo.
echo Origem:  %ORIGEM%
echo Destino: %DESTINO%
echo.
echo O projeto sera COPIADO (nao movido).
echo Voce pode continuar editando no Cursor normalmente.
echo Para enviar ao GitHub, use a pasta em C:\Projetos
echo.
pause

if not exist "C:\Projetos" mkdir "C:\Projetos"

echo Copiando arquivos...
if exist "%DESTINO%" rmdir /s /q "%DESTINO%" 2>nul
mkdir "%DESTINO%" 2>nul
robocopy "%ORIGEM" "%DESTINO%" /E /COPY:DAT /NFL /NDL /NJH /NJS /NC /NS

echo.
echo Corrigindo arquivo exclude na nova pasta...
cd /d "%DESTINO%"
python -c "open('.git/info/exclude','w',encoding='ascii').write('#\n')" 2>nul

echo.
echo Testando git...
git add . 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCESSO! O Git funciona em: %DESTINO%
    echo.
    echo Proximos passos:
    echo 1. Abra a pasta: %DESTINO%
    echo 2. Execute configurar_git.bat ^(se ainda nao fez^)
    echo 3. Execute git_commit.bat
    echo.
) else (
    echo Ainda com erro. Tente executar manualmente:
    echo   cd "%DESTINO%"
    echo   git add .
)

echo.
explorer "%DESTINO%"
pause
