# 🤖 Configuração UptimeRobot - Manter App Sempre Ativo

## 🎯 Objetivo
Configurar monitoramento externo para manter o Streamlit Cloud sempre acordado (gratuito).

---

## 📋 **Passo a Passo Completo**

### **1. Criar Conta no UptimeRobot**

1. Acesse: https://uptimerobot.com/
2. Clique em **"Sign Up"** (canto superior direito)
3. Use email ou conta Google
4. ✅ **100% Gratuito** para até 50 monitores

---

### **2. Adicionar Novo Monitor**

Após login, siga:

#### **A. Dashboard → Add New Monitor**
```
Clique no botão verde "+ Add New Monitor"
```

#### **B. Configurações Básicas**
```
Monitor Type: HTTP(s)
Friendly Name: Intensiva Calculator
URL: https://seu-app.streamlit.app
Monitoring Interval: 5 minutes (gratuito)
```

#### **C. Configurações Avançadas (Opcional)**
```
☑ Monitor Timeout: 30 seconds
☑ HTTP Method: HEAD (mais leve que GET)
☐ Follow Redirects: Sim
```

#### **D. Alertas (Opcional)**
```
☑ Alert Contacts: Seu email
☐ Alert When: Down (opcional)
```

#### **E. Finalizar**
```
Clique em "Create Monitor"
```

---

### **3. Verificar Configuração**

Após criar, você verá:

```
✅ Status: Up
⏰ Uptime: 100%
🔄 Checking Every: 5 minutes
📊 Response Time: ~200ms
```

---

## 🔍 **Como Funciona**

### **Fluxo:**
```
UptimeRobot (Servidor) 
    ↓ Ping a cada 5 min
Streamlit Cloud (Seu App)
    ↓ Responde
App Permanece Ativo ✅
```

### **Benefícios:**
- ✅ Previne sleep após 7 dias
- ✅ Monitora disponibilidade real
- ✅ Alerta se app cair
- ✅ Gratuito para sempre

---

## 📊 **Configurações Recomendadas**

### **Para Apps Críticos:**
```
Monitoring Interval: 5 minutes
Monitor Timeout: 30 seconds
HTTP Method: HEAD
Alert: Email quando Down
```

### **Para Apps Normais:**
```
Monitoring Interval: 5 minutes
Monitor Timeout: 30 seconds
HTTP Method: HEAD
Alert: Desabilitado
```

### **Para Economia Máxima (ainda efetivo):**
```
Monitoring Interval: 5 minutes
Monitor Timeout: 30 seconds
HTTP Method: HEAD
```

---

## 🛠️ **URLs para Configurar**

### **Produção (Streamlit Cloud):**
```
URL: https://intensivacalculator.streamlit.app
```

### **Staging (Se houver):**
```
URL: https://staging-intensivacalculator.streamlit.app
```

### **Múltiplos Apps:**
Você pode adicionar até **50 monitores gratuitos**:
- App Principal
- API Backend (se houver)
- Dashboard Admin (se houver)

---

## 📈 **Resultados Esperados**

### **Antes (Sem UptimeRobot):**
- 😴 App dorme após 7 dias sem acesso
- ⏱️ Wake-up time: 20-30 segundos
- 📉 Uptime: ~95%

### **Depois (Com UptimeRobot):**
- ✅ App sempre ativo
- ⚡ Response time: instantâneo
- 📈 Uptime: 99.9%

---

## 🚨 **Troubleshooting**

### **Monitor mostra "Down"**

**Possíveis causas:**
1. App realmente está offline → Verifique Streamlit Cloud
2. Deploy em andamento → Aguarde 2-3 minutos
3. Timeout muito curto → Aumente para 60s

**Solução:**
```
1. Verifique app manualmente no navegador
2. Ajuste "Monitor Timeout" para 60 seconds
3. Pause monitor durante deploys programados
```

### **App ainda dorme**

**Verificar:**
1. Monitor está ativo? (Status: Up)
2. Intervalo está correto? (5 min)
3. URL está correta?

**Teste:**
```bash
# Testar URL manualmente
curl -I https://seu-app.streamlit.app

# Deve retornar:
# HTTP/2 200
```

### **Muitos alertas falsos**

**Causa:** Deploys frequentes ou instabilidade temporária

**Solução:**
```
Alert Threshold: 2 consecutive failures
(Em vez de 1 failure)
```

---

## 💡 **Dicas Avançadas**

### **1. Monitor Customizado (Página Específica)**
```
URL: https://seu-app.streamlit.app/health
(Criar endpoint /health se possível)
```

### **2. Múltiplos Intervalos**
Plano Gratuito: 5 minutos (suficiente)
Plano Pago: 1 minuto (opcional)

### **3. Status Page Pública**
UptimeRobot oferece página de status pública:
```
https://uptimerobot.com/dashboard#PublicStatusPages
→ Create Public Status Page
→ Compartilhar com usuários
```

---

## 📊 **Dashboard e Relatórios**

### **Métricas Disponíveis:**
- ✅ Uptime % (últimos 30/60/90 dias)
- ✅ Response Time médio
- ✅ Histórico de Down/Up
- ✅ Logs de monitoramento

### **Exportar Dados:**
```
Dashboard → Monitor → Logs → Export
Formato: CSV ou JSON
```

---

## 🔗 **Recursos Úteis**

- **Dashboard:** https://dashboard.uptimerobot.com/
- **Documentação:** https://uptimerobot.com/kb/
- **API:** https://uptimerobot.com/api/ (para automação)
- **Status:** https://status.uptimerobot.com/

---

## ✅ **Checklist de Configuração**

- [ ] Conta criada no UptimeRobot
- [ ] Monitor adicionado com URL correta
- [ ] Intervalo: 5 minutos
- [ ] HTTP Method: HEAD
- [ ] Timeout: 30 segundos
- [ ] Status: Up ✅
- [ ] Testar por 24h

---

## 🎯 **Resultado Final**

Após configuração:
- ✅ App nunca mais dorme
- ✅ Monitoramento 24/7 gratuito
- ✅ Alertas automáticos (opcional)
- ✅ Relatórios de uptime profissionais

**Tempo de setup: ~3 minutos**
**Custo: $0 (gratuito para sempre)**
**Efetividade: 99.9%**

---

**🤖 Configuração completa! Seu app Streamlit ficará sempre ativo.**
