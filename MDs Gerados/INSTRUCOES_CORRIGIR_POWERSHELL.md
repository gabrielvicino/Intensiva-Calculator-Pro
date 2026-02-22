# Como Corrigir o Erro do PowerShell

## 📋 Sobre o Erro

O erro que você está vendo:
```
The predictive suggestion feature cannot be enabled because the console output doesn't support virtual terminal processing or it's redirected.
```

**Não é grave!** É apenas um aviso de que o terminal não suporta sugestões preditivas.

---

## ✅ Solução Automática (Recomendada)

### Opção 1: Executar o script de correção

1. **Clique com botão direito** no arquivo `fix_powershell_profile.ps1`
2. Selecione **"Executar com PowerShell"**
3. Se pedir permissão, clique em **"Sim"**
4. **Reinicie o PowerShell**

---

### Opção 2: Executar manualmente no PowerShell

Abra o PowerShell e execute:

```powershell
# Navegar para a pasta do projeto
cd "C:\Users\gabri\OneDrive\Área de Trabalho\Intensiva Calculator\Intensiva Calculator"

# Executar o script
.\fix_powershell_profile.ps1
```

---

## 🔧 Solução Manual (Se preferir)

Se preferir editar manualmente, abra o arquivo:

```
C:\Users\gabri\OneDrive\Documentos\PowerShell\Microsoft.PowerShell_profile.ps1
```

**Encontre estas linhas (por volta da linha 11):**

```powershell
# Autocomplete inteligente
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle InlineView
Set-PSReadLineOption -EditMode Windows
```

**Substitua por:**

```powershell
# Autocomplete inteligente
# Só ativa predições se o terminal suportar
try {
    if ($host.UI.SupportsVirtualTerminal) {
        Set-PSReadLineOption -PredictionSource History
        Set-PSReadLineOption -PredictionViewStyle InlineView
    }
} catch {
    # Ignora se não suportar
}
Set-PSReadLineOption -EditMode Windows
```

**Salve o arquivo e reinicie o PowerShell.**

---

## ❓ O que isso faz?

A correção adiciona uma verificação condicional que:
1. ✅ Testa se o terminal suporta recursos avançados
2. ✅ Só ativa as sugestões preditivas se suportar
3. ✅ Ignora silenciosamente se não suportar
4. ✅ Mantém todas as outras funcionalidades do seu perfil

---

## 📝 Nota

Se preferir **não ver nenhum aviso**, você também pode simplesmente comentar as linhas:

```powershell
# Autocomplete inteligente
# Set-PSReadLineOption -PredictionSource History
# Set-PSReadLineOption -PredictionViewStyle InlineView
Set-PSReadLineOption -EditMode Windows
```

Isso desabilita completamente as sugestões preditivas.

---

## 🎯 Depois de Corrigir

Após aplicar a correção e reiniciar o PowerShell, o erro não aparecerá mais nos comandos do Cursor ou no terminal! 🚀
