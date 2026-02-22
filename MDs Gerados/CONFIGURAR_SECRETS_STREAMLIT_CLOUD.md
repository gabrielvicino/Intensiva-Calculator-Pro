# 🔐 Configurar API Key no Streamlit Cloud

## 🎯 Problema
O app está online mas dá erro: "API Key não configurada!"

---

## ✅ **SOLUÇÃO: Configurar Secrets**

### **PASSO 1: Acessar o Dashboard**

1. Acesse: https://share.streamlit.io/
2. Faça login com sua conta
3. Veja lista de apps

---

### **PASSO 2: Abrir Configurações do App**

1. Localize seu app **"Intensiva Calculator"**
2. Clique nos **3 pontinhos (⋮)** ao lado do app
3. Selecione **"Settings"** ou **"⚙️ Manage app"**

**Ou:**
- Se já estiver com o app aberto
- Clique em **"Manage app"** (canto inferior direito)

---

### **PASSO 3: Configurar Secrets**

1. No painel lateral, clique em **"Secrets"**
2. Você verá um editor de texto
3. Cole este código:

```toml
# OpenAI API Key
OPENAI_API_KEY = "sk-proj-SUBSTITUA_AQUI_PELA_SUA_CHAVE_REAL_DA_OPENAI"
```

**⚠️ IMPORTANTE:** Use SUA chave real da OpenAI!

4. Clique em **"Save"** (botão no canto inferior direito)

---

### **PASSO 4: Reiniciar App**

Após salvar:

1. O app reiniciará automaticamente (15-30 segundos)
2. Aguarde a mensagem: **"Your app is live!"**
3. Recarregue a página do app

---

## 🎉 **PRONTO!**

Agora seu app deve funcionar perfeitamente!

---

## 🔍 **COMO VERIFICAR SE FUNCIONOU**

1. Abra seu app no Streamlit Cloud
2. Vá na aba **"🧪 Exames"**
3. Cole dados de exames
4. Clique em **"✨ Processar"**

**✅ Se processar normalmente = Configurado!**
**❌ Se der erro = Reveja os passos acima**

---

## 📋 **FORMATO CORRETO DOS SECRETS**

### **✅ CERTO:**
```toml
OPENAI_API_KEY = "sk-proj-..."
```

### **❌ ERRADO:**
```toml
# Sem aspas
OPENAI_API_KEY = sk-proj-...

# Formato Python (não é TOML)
OPENAI_API_KEY="sk-proj-..."

# Com espaços extras
OPENAI_API_KEY =    "sk-proj-..."    
```

---

## 🚨 **TROUBLESHOOTING**

### **Erro persiste após configurar**

**Solução:**
1. Vá em Settings > Secrets
2. Verifique se está exatamente assim:
   ```toml
   OPENAI_API_KEY = "sua-chave-aqui"
   ```
3. Salve novamente
4. Aguarde 30 segundos
5. Recarregue a página

---

### **"Invalid TOML"**

**Causa:** Erro de sintaxe no formato TOML

**Solução:**
- Use o formato exato do exemplo
- Aspas duplas obrigatórias: `"..."`
- Espaços ao redor do `=`
- Sem vírgulas ou ponto-e-vírgula no final

---

### **App não reinicia**

**Solução:**
1. Feche a aba do app
2. Vá no Dashboard (share.streamlit.io)
3. Clique em "⋮" → "Reboot app"
4. Aguarde reiniciar
5. Abra novamente

---

### **"Secret not found"**

**Causa:** Nome da variável errado

**Solução:**
- Verifique que está escrito **exatamente**:
  ```toml
  OPENAI_API_KEY
  ```
- Não pode ser `openai_api_key` (minúsculas)
- Não pode ter espaços extras

---

## 🔐 **SEGURANÇA**

### **✅ Secrets são seguros?**
Sim! Streamlit Cloud:
- Criptografa seus secrets
- Não exibe em logs
- Não compartilha entre apps
- Não aparece no código-fonte público

### **⚠️ NUNCA:**
- Commitar secrets no GitHub
- Compartilhar sua API key
- Expor secrets em prints/vídeos

---

## 📊 **VERIFICAÇÃO NO CÓDIGO**

O código agora detecta automaticamente:

```python
# Prioridade 1: Streamlit Secrets (Cloud)
if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Prioridade 2: Arquivo .env (Local)
if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
```

**Funciona em ambos os ambientes:**
- ✅ Local: Lê do `.env`
- ✅ Cloud: Lê do Streamlit Secrets

---

## 📱 **PASSO A PASSO VISUAL**

### **1. Dashboard**
```
https://share.streamlit.io/
│
├─ [Seu App: Intensiva Calculator]
│  └─ ⋮ (3 pontinhos) → Settings
```

### **2. Painel de Settings**
```
Settings
├─ General
├─ 🔐 Secrets ← CLIQUE AQUI
├─ Advanced
└─ Danger Zone
```

### **3. Editor de Secrets**
```
┌─────────────────────────────────────┐
│ # OpenAI API Key                    │
│ OPENAI_API_KEY = "sk-proj-..."      │
│                                     │
│                                     │
│                                     │
│                                     │
│                  [Save]             │
└─────────────────────────────────────┘
```

### **4. Salvar e Aguardar**
```
Saving... → Restarting... → ✅ Your app is live!
```

---

## 💡 **DICAS**

### **Adicionar Múltiplos Secrets**

Se tiver outras APIs:

```toml
# OpenAI
OPENAI_API_KEY = "sk-proj-..."

# Google Gemini (se usar)
GOOGLE_API_KEY = "AIza..."

# Outras configurações
DATABASE_URL = "postgresql://..."
```

### **Comentários no TOML**

Use `#` para comentários:

```toml
# Produção
OPENAI_API_KEY = "sk-proj-..."

# Staging (desabilitado)
# OPENAI_API_KEY = "sk-proj-staging..."
```

---

## 🔗 **LINKS ÚTEIS**

- **Dashboard:** https://share.streamlit.io/
- **Docs Secrets:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- **Formato TOML:** https://toml.io/en/

---

## ✅ **CHECKLIST**

- [ ] Acessar Dashboard Streamlit Cloud
- [ ] Clicar em Settings do app
- [ ] Abrir seção "Secrets"
- [ ] Colar configuração TOML
- [ ] Verificar formato correto
- [ ] Clicar em "Save"
- [ ] Aguardar reinício (30s)
- [ ] Testar app processando exames
- [ ] Confirmar funcionamento ✅

---

## 🎯 **RESUMO**

1. **Acesse:** https://share.streamlit.io/
2. **Vá em:** Seu App → Settings → Secrets
3. **Cole:**
   ```toml
   OPENAI_API_KEY = "sua-chave-aqui"
   ```
4. **Save** e aguarde reiniciar
5. **Teste** o app

**Tempo:** 2 minutos
**Dificuldade:** Fácil ⭐

---

**🚀 Configuração completa! Seu app funcionará perfeitamente no Streamlit Cloud.**
