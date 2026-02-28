# ⚙️ scripts/ - Scripts de Automação

**Propósito:** Esta pasta contém scripts executáveis e de automação do projeto.

---

## 📋 SCRIPTS DISPONÍVEIS

### **iniciar.bat** (Windows)
- **Descrição:** Inicia o aplicativo Streamlit no Windows
- **Uso:** Duplo clique ou `scripts\iniciar.bat`
- **O que faz:** `streamlit run app.py`

### **sync_infusao_sheet.py**
- **Descrição:** Sincroniza os dados padrão de infusão para a aba DB_INFUSAO no Google Sheets
- **Uso:** `streamlit run scripts/sync_infusao_sheet.py`

### **testar_gemini.py**
- **Descrição:** Verifica se a API do Google Gemini está configurada corretamente
- **Uso:** `python scripts/testar_gemini.py` (execute da raiz do projeto)

### **gerar_exemplo_completo.py**
- **Descrição:** Gera o prontuário de exemplo completo (interface Streamlit)
- **Uso:** `streamlit run scripts/gerar_exemplo_completo.py`

### **gerar_exemplo_standalone.py**
- **Descrição:** Gera PRONTUARIO_EXEMPLO_COMPLETO.txt via linha de comando (sem UI)
- **Uso:** `python scripts/gerar_exemplo_standalone.py` (da raiz do projeto)

---

## 🚀 COMO USAR

### **Windows:**
```bash
# Duplo clique em:
scripts\iniciar.bat

# Ou via linha de comando:
cd scripts
iniciar.bat
```

### **Linux/Mac:**
Se criar scripts para Linux/Mac, nomeie como:
- `iniciar.sh`
- `deploy.sh`
- etc.

---

## 📝 ADICIONAR NOVOS SCRIPTS

### **Para Windows (.bat):**
```batch
@echo off
echo Executando...
streamlit run app.py
pause
```

### **Para Linux/Mac (.sh):**
```bash
#!/bin/bash
echo "Executando..."
streamlit run app.py
```

**Não esqueça:** `chmod +x script.sh` no Linux/Mac

---

## 🎯 TIPOS DE SCRIPTS ÚTEIS

### **Pode adicionar aqui:**
- ✅ Scripts de inicialização
- ✅ Scripts de deploy
- ✅ Scripts de backup
- ✅ Scripts de atualização
- ✅ Scripts de limpeza
- ✅ Scripts de testes

### **Exemplos:**
```
scripts/
├── iniciar.bat           (Windows)
├── iniciar.sh            (Linux/Mac)
├── deploy.bat            (Deploy)
├── backup.py             (Backup de dados)
├── atualizar.bat         (Atualizar deps)
└── limpar_cache.bat      (Limpar __pycache__)
```

---

## ⚠️ IMPORTANTE

- **SIM** coloque todos os scripts aqui
- **NÃO** deixe scripts na raiz do projeto
- **SIM** documente o que cada script faz
- **NÃO** inclua credenciais nos scripts

---

## 💡 DICAS

### **Para scripts Python:**
Se criar scripts .py auxiliares, considere:
- Colocar em `scripts/` se for executável
- Colocar em `modules/` se for importável

### **Para automação:**
- Use `.bat` para Windows
- Use `.sh` para Linux/Mac
- Use `.ps1` para PowerShell

---

**Última atualização:** Fevereiro 2026
**Scripts disponíveis:** iniciar.bat, sync_infusao_sheet.py, testar_gemini.py, gerar_exemplo_completo.py, gerar_exemplo_standalone.py
