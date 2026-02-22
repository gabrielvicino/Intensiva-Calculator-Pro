# 🚀 Deploy no Streamlit Cloud - Guia Completo

## 🎯 Objetivo
Colocar o Intensiva Calculator online gratuitamente.

---

## 📋 **PRÉ-REQUISITOS**

- [x] Código no GitHub ✅ (Você já tem)
- [x] Arquivo `requirements.txt` ✅ (Você já tem)
- [ ] Conta no Streamlit Cloud

---

## 🚀 **PASSO A PASSO**

### **PASSO 1: Criar Conta Streamlit Cloud**

1. Acesse: https://share.streamlit.io/
2. Clique em **"Sign up"**
3. **Use sua conta do GitHub** (mais fácil)
4. Autorize o Streamlit a acessar seus repositórios

✅ **É 100% gratuito** para apps públicos

---

### **PASSO 2: Criar Novo App**

#### **2.1 Dashboard → New App**
Clique no botão **"New app"** (ou "+ Create app")

#### **2.2 Preencher Formulário**

```
┌─────────────────────────────────────────┐
│ Repository:                             │
│ gabrielvicino/IntensivaCalculator       │
│                                         │
│ ⚠️ Use seu usuário/repositório real     │
├─────────────────────────────────────────┤
│ Branch: main                            │
├─────────────────────────────────────────┤
│ Main file path: app.py                  │
├─────────────────────────────────────────┤
│ App URL (custom):                       │
│ intensivacalculator                     │
│                                         │
│ Resulta em:                             │
│ https://intensivacalculator.streamlit.app│
└─────────────────────────────────────────┘
```

#### **2.3 Configurações Avançadas (Opcional)**

Clique em **"Advanced settings"**:

```
Python version: 3.9 (ou 3.10)
```

**⚠️ IMPORTANTE - Secrets (Se usar API Keys):**

Se seu app usa API keys (OpenAI, etc.), adicione em **"Secrets"**:

```toml
# Formato TOML
OPENAI_API_KEY = "sk-proj-..."

# ⚠️ Use suas chaves reais
# ⚠️ NUNCA commite secrets no GitHub
```

#### **2.4 Iniciar Deploy**
```
Clique em "Deploy!"
```

---

### **PASSO 3: Aguardar Deploy (2-5 minutos)**

Você verá:

```
🔄 Building...
   └─ Installing dependencies
   └─ Starting app
   
⏱️ Tempo estimado: 2-5 minutos
```

**Enquanto isso:**
- ☕ Tome um café
- 📱 Verifique email de confirmação
- 📊 O log mostrará o progresso

---

### **PASSO 4: App Online! 🎉**

Quando terminar:

```
✅ Your app is live at:
   https://intensivacalculator.streamlit.app
   
🔗 Share this URL
📊 View analytics
⚙️ Manage app
```

**Sua URL será algo como:**
```
https://[seu-nome]-intensivacalculator.streamlit.app
ou
https://intensivacalculator.streamlit.app
```

---

## 🔧 **CONFIGURAÇÕES PÓS-DEPLOY**

### **1. Configurar Secrets (API Keys)**

Se ainda não fez:

1. Dashboard → Seu App → "⚙️ Settings"
2. Clique em **"Secrets"**
3. Cole suas variáveis:

```toml
OPENAI_API_KEY = "sk-proj-u5A8JyetS54xw6l8b9Lcn2g5OG..."
# Adicione outras keys se necessário
```

4. Clique em **"Save"**
5. App reiniciará automaticamente

---

### **2. Configurar Domínio Customizado (Opcional)**

Plano gratuito: `.streamlit.app`
Plano pago: Domínio próprio (`intensivacalculator.com`)

---

### **3. Analytics e Monitoramento**

Dashboard mostra:
- 📊 Número de visitantes
- ⏱️ Tempo de uso
- 🌍 Localização geográfica
- 📈 Picos de acesso

---

## 🔄 **AUTO-DEPLOY (ATUALIZAÇÃO AUTOMÁTICA)**

### **Como Funciona:**

Após deploy inicial:

```
Você faz commit → GitHub
         ↓
Streamlit detecta
         ↓
Auto-deploy (30-60s)
         ↓
App atualizado ✅
```

**Ou seja:** Todo `git push` atualiza o app automaticamente!

---

## 🚨 **TROUBLESHOOTING**

### **Erro: "Module not found"**

**Causa:** Dependência faltando no `requirements.txt`

**Solução:**
```bash
# No local, verificar:
pip freeze > requirements.txt

# Commit e push
git add requirements.txt
git commit -m "fix: Atualiza requirements"
git push
```

---

### **Erro: "Port already in use"**

**Causa:** Configuração de porta conflitante

**Solução:** Streamlit Cloud gerencia portas automaticamente - ignore

---

### **App muito lento no primeiro acesso**

**Causa:** App "dormiu" (sleep mode)

**Solução:** Configure UptimeRobot (Nível 3) ✅

---

### **Erro de API Key**

**Causa:** Secret não configurado

**Solução:**
1. Settings → Secrets
2. Adicionar `OPENAI_API_KEY = "..."`
3. Save

---

### **Build falha com erro de Python**

**Causa:** Versão do Python incompatível

**Solução:**
1. Settings → Advanced
2. Python version: 3.9 ou 3.10
3. Reboot app

---

## 📊 **LIMITES DO PLANO GRATUITO**

### **Community (Gratuito):**
```
✅ Apps ilimitados
✅ Repositórios públicos
✅ 1 GB RAM por app
✅ 1 CPU core por app
✅ Auto-deploy
✅ HTTPS gratuito
⚠️ Sleep após 7 dias sem uso (resolver com UptimeRobot)
❌ Secrets compartilhados
```

### **Como Evitar Sleep:**
→ **Configure UptimeRobot** (Nível 3) ✅

---

## 🔗 **RECURSOS ÚTEIS**

- **Dashboard:** https://share.streamlit.io/
- **Docs Deploy:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app
- **Secrets:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- **Status:** https://status.streamlit.io/

---

## ✅ **CHECKLIST DE DEPLOY**

### **Antes do Deploy:**
- [x] Código no GitHub
- [x] `requirements.txt` atualizado
- [x] `.streamlit/config.toml` configurado
- [x] Secrets identificados (API keys)
- [x] `app.py` funciona localmente

### **Durante Deploy:**
- [ ] Conta criada no Streamlit Cloud
- [ ] Repositório conectado
- [ ] `app.py` selecionado
- [ ] Secrets configurados (se necessário)
- [ ] Deploy iniciado

### **Após Deploy:**
- [ ] App acessível na URL
- [ ] Funcionalidades testadas
- [ ] Configurar UptimeRobot ✅
- [ ] Compartilhar URL

---

## 🎯 **RESULTADO FINAL**

### **URL do Seu App:**
```
https://intensivacalculator.streamlit.app
```

### **Características:**
- ✅ Online 24/7
- ✅ HTTPS gratuito
- ✅ Auto-deploy (git push)
- ✅ Sem servidor para gerenciar
- ✅ 100% gratuito

### **Com UptimeRobot (Nível 3):**
- ✅ Nunca dorme
- ✅ Response instantâneo
- ✅ Uptime 99.9%

---

## 💡 **DICAS PRO**

### **1. Favicon Customizado**
Adicione em `.streamlit/config.toml`:
```toml
[server]
favicon = "favicon.ico"
```

### **2. Title e Layout**
Em `app.py`:
```python
st.set_page_config(
    page_title="Intensiva Calculator",
    page_icon="🏥",
    layout="wide"
)
```

### **3. Analytics Personalizados**
Adicione Google Analytics no `config.toml`:
```toml
[browser]
gatherUsageStats = false  # Desabilita Streamlit stats
```
E adicione seu próprio tracker

---

## 🎉 **PRONTO!**

Seu app está online e acessível para todo o mundo!

**Próximos passos:**
1. ✅ Configurar UptimeRobot (Nível 3)
2. 📢 Compartilhar URL com usuários
3. 📊 Monitorar uso no dashboard
4. 🔄 Continuar desenvolvendo (auto-deploy!)

---

**🚀 Deploy completo em ~10 minutos!**
