# Corrige o arquivo .git/info/exclude com encoding ASCII (sem BOM)
Set-Location $PSScriptRoot

# Reverter config se foi alterada
git config --unset core.excludesFile 2>$null

# Recriar exclude com encoding correto (UTF-8 sem BOM)
$excludePath = Join-Path $PSScriptRoot ".git\info\exclude"
$content = "# Local exclude`n"
[System.IO.File]::WriteAllText($excludePath, $content, [System.Text.UTF8Encoding]::new($false))

Write-Host "Exclude recriado. Testando git add..."
git add . 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "Sucesso! Agora execute git_commit.bat" } else { Write-Host "Ainda com erro. Tente mover o projeto para fora do OneDrive (ex: C:\Projetos)" }
