@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Corrigindo arquivo exclude...
git config --unset core.excludesFile 2>nul

REM Criar exclude com encoding ASCII (sem BOM) via Python
python -c "open('.git/info/exclude','w',encoding='ascii').write('#\n')"

echo.
echo Execute git_commit.bat novamente.
pause
