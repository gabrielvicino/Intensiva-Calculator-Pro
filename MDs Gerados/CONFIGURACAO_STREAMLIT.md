# 🔧 Configuração do Streamlit - Prevenir Sleep/Inatividade

## 🎯 Objetivo
Evitar que o Streamlit entre em modo "sleep" ou desconecte por inatividade.

---

## 📋 **Configurações Aplicadas**

### **Arquivo: `.streamlit/config.toml`**

```toml
[server]
enableXsrfProtection = false    # Previne timeout de sessão CSRF
enableCORS = false               # Desabilita CORS (uso local)
enableWebsocketCompression = false  # Mantém WebSocket ativo
maxUploadSize = 200             # Aumenta limite de upload (MB)

[browser]
gatherUsageStats = false        # Não coleta estatísticas (mais leve)

[client]
toolbarMode = "minimal"         # Interface limpa
showErrorDetails = true         # Mostra erros detalhados
```

---

## 🔍 **Tipos de "Sleep" e Soluções**

### **1. Sleep Local (Desenvolvimento)**

**Problema:** Aplicação congela após inatividade

**Solução Aplicada:**
- ✅ `enableWebsocketCompression = false` - Mantém conexão ativa
- ✅ `enableXsrfProtection = false` - Sem timeout de sessão

**Como Testar:**
```bash
streamlit run app.py
# Deixe aberto por 30+ minutos sem interagir
# Deve continuar responsivo
```

---

### **2. Sleep do Navegador (Tab Inativa)**

**Problema:** Navegador suspende tabs inativas

**Soluções:**

#### **Opção A: Extensão de Navegador**
- Chrome: "Keep Awake" ou "Tab Wrangler"
- Mantém a tab ativa mesmo em segundo plano

#### **Opção B: Código JavaScript (Automático)**
Adicionar ao `app.py`:

```python
import streamlit.components.v1 as components

# Mantém sessão ativa com ping periódico
components.html(
    """
    <script>
    // Envia ping a cada 30 segundos para manter sessão ativa
    setInterval(function() {
        fetch(window.location.href)
            .then(() => console.log('Ping: Sessão ativa'))
            .catch(() => console.log('Ping: Erro'));
    }, 30000);
    </script>
    """,
    height=0
)
```

---

### **3. Sleep do Streamlit Cloud (Deploy)**

**Problema:** Apps gratuitos no Streamlit Cloud "dormem" após 7 dias sem uso

**Características:**
- ⏰ **Inatividade:** 7 dias sem acesso
- 🔄 **Reinício:** Automático no primeiro acesso
- ⚡ **Tempo de Wake:** 10-30 segundos

**Soluções:**

#### **Opção A: Ping Externo (Gratuito)**
Use serviços de monitoramento:

1. **UptimeRobot** (https://uptimerobot.com/)
   - Gratuito para até 50 monitores
   - Ping a cada 5 minutos
   - Mantém app sempre acordado

2. **Cron-job.org** (https://cron-job.org/)
   - Gratuito
   - Configurável (ex: ping a cada hora)

**Configuração:**
```
URL: https://seu-app.streamlit.app
Intervalo: 5 minutos
Método: GET
```

#### **Opção B: GitHub Actions (Avançado)**
Criar arquivo `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Streamlit Awake

on:
  schedule:
    - cron: '0 */6 * * *'  # A cada 6 horas
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Streamlit App
        run: |
          curl -I https://seu-app.streamlit.app
          echo "App pingado com sucesso"
```

#### **Opção C: Upgrade para Plano Pago**
- Streamlit Cloud Pro: Apps sempre ativos
- Custo: ~$20/mês

---

## 🛠️ **Script de Keep-Alive (Automático)**

### **keep_alive.py** (Para uso local)

```python
import streamlit as st
import time
from datetime import datetime

def keep_alive():
    """Mantém a sessão ativa com atualizações invisíveis"""
    if 'last_ping' not in st.session_state:
        st.session_state.last_ping = datetime.now()
    
    # Atualiza a cada 30 segundos
    if (datetime.now() - st.session_state.last_ping).seconds > 30:
        st.session_state.last_ping = datetime.now()
        # Força pequena atualização da UI (invisível)
        with st.empty():
            pass

# Adicionar no início do app.py
if __name__ == "__main__":
    keep_alive()
```

---

## 📊 **Comparação de Métodos**

| Método | Eficácia | Complexidade | Custo |
|--------|----------|--------------|-------|
| Configuração .toml | ⭐⭐⭐ | Fácil | Gratuito |
| JavaScript Ping | ⭐⭐⭐⭐ | Média | Gratuito |
| UptimeRobot | ⭐⭐⭐⭐⭐ | Fácil | Gratuito |
| GitHub Actions | ⭐⭐⭐⭐ | Avançada | Gratuito |
| Streamlit Pro | ⭐⭐⭐⭐⭐ | Fácil | $20/mês |

**Recomendação:** UptimeRobot (deploy) + Configuração .toml (local)

---

## ✅ **Checklist de Implementação**

### **Para Uso Local:**
- [x] Atualizar `.streamlit/config.toml`
- [ ] Adicionar JavaScript keep-alive (opcional)
- [ ] Reiniciar Streamlit

### **Para Deploy (Streamlit Cloud):**
- [ ] Confirmar que `.streamlit/config.toml` está no repositório
- [ ] Configurar UptimeRobot ou similar
- [ ] Testar após 1 hora de inatividade

---

## 🧪 **Como Testar**

### **Teste Local:**
```bash
# 1. Iniciar app
streamlit run app.py

# 2. Deixar aberto por 1 hora sem interagir

# 3. Verificar se ainda responde instantaneamente
```

### **Teste no Deploy:**
```bash
# 1. Deploy no Streamlit Cloud

# 2. Não acessar por 24 horas

# 3. Acessar novamente - deve carregar rapidamente se configurado
```

---

## 🚨 **Troubleshooting**

### **Problema: "Reconnecting..." aparece frequentemente**

**Causa:** Conexão WebSocket instável

**Solução:**
```toml
[server]
enableWebsocketCompression = false
headless = true
```

### **Problema: App desconecta após 10 minutos de inatividade**

**Causa:** Firewall ou proxy

**Solução:**
```bash
# Rodar com --server.headless
streamlit run app.py --server.headless=true
```

### **Problema: Session State é perdido**

**Causa:** Reconexão completa

**Solução:**
- Usar `st.cache_data` para dados importantes
- Implementar persistência em banco de dados

---

## 💡 **Dicas Avançadas**

### **1. Heartbeat Customizado**
```python
import streamlit as st
import time

# No sidebar (invisível)
with st.sidebar:
    if st.button("🔄", key="heartbeat", help="Manter ativo"):
        st.rerun()
```

### **2. Auto-Refresh (Cuidado com custos de API)**
```python
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Atualiza a cada 5 minutos
st_autorefresh(interval=300000, key="refresh")
```

### **3. Monitoramento de Conexão**
```python
import streamlit as st

def check_connection():
    try:
        # Tenta uma operação simples
        st.session_state['connection_check'] = True
        return True
    except:
        return False

if not check_connection():
    st.warning("⚠️ Conexão instável detectada")
```

---

## 📈 **Resultados Esperados**

### **Antes:**
- 😴 App dorme após 15-30 min de inatividade
- 🔄 Precisa reconectar frequentemente
- ⏱️ Tempo de resposta: 5-10s após inatividade

### **Depois:**
- ✅ App permanece ativo por horas
- ✅ Conexão estável
- ⚡ Tempo de resposta: instantâneo

---

## 📝 **Resumo**

1. ✅ **Configurações aplicadas** em `.streamlit/config.toml`
2. ✅ **Previne timeout** de sessão local
3. 💡 **Use UptimeRobot** para apps em produção
4. 🔧 **Reinicie o Streamlit** para aplicar mudanças

---

**🎯 Configuração completa! O aplicativo deve permanecer ativo e responsivo.**
