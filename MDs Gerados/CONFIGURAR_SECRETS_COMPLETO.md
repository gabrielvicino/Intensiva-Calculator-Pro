# 🔐 Configurar Secrets no Streamlit Cloud - COMPLETO

## 🎯 O que você precisa configurar

Seu app precisa de 2 secrets:
1. ✅ **OpenAI API Key** - Para processar exames e prescrições
2. ✅ **Google Sheets Credentials** - Para Infusão e IOT calculadoras

---

## 📋 **COPIE E COLE ESTE CONTEÚDO EXATO**

### **Acesse:** https://share.streamlit.io/
### **Vá em:** Seu App → Settings → Secrets
### **Cole TUDO abaixo:**

```toml
# ===========================================
# OPENAI API KEY
# ===========================================
OPENAI_API_KEY = "COLOQUE_SUA_CHAVE_OPENAI_AQUI"

# ===========================================
# GOOGLE SHEETS CREDENTIALS
# ===========================================
[connections.gsheets]
type = "service_account"
project_id = "gen-lang-client-0545395359"
private_key_id = "0ad78778a2200068b38b336bf68e5c4e8931241e"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCysoJaX1bV3HL9\nd04vNIyQgNxw0huWsoBl4ZFUNQyWS3teicdJGegqHQAVYLXkCVa6pyKCSW+trR06\n/UUpcUqCBrKCTJqLoXXtP9huTpbXvOOu6rqeZ/CHrSNWPGebPxCQXyQr755Ctp1N\nCP615EGLdaPj0y3miDW1BWmRI5dh7xe0FyV/3nU/BGnk64a/eWL8zkzH2l6nVvgi\nFgl65/wdA/Sad18BiH9PuBjkKX+VbfmOoPEEp30OuAtXpbPIbLmXx97CWCnN0CXU\njjA8uEbgmxF+SZCuRv0BRjJ7CHW0Dp5Z4+c/gTGt+kiNZzHuqDB/T+hRg/YC+43i\nzT+23fLJAgMBAAECggEABwOryzlX0sA7AUkIGCFDbT6pqIIO1C0Ajj868ae9bT7c\nQls9J9js/I4z3SL1MNTPAzehSqTwTcxwS8r6RoSsbIsvwZ6ZKGb3lo79g2LxV9mR\nxGFxXttsnR7GNtHbLURd9ZTOei0HNM4vQYFbYi9qBTviaYR2Fkj9drQWLzzK6eyk\nYnKyQ53GdMx/aNon1LtofG6P1B6lqJr1viah1l0mdGCn1EL/rGAuzgr26rw+lpCi\n/T4cG97+LwgkzGpsGl8QOoBpA5rrEpyfRixbNuSM52O+jeNAw2h664q776nXizSK\nwS3+pERi1E4Ge0IcTgOpCNraphLG6kvUFEY0b7Q5qQKBgQDWqO2Nk34ke5v+6WIk\nnPS3aG6nKluGsTZ8/xRAp+KlwHBQubS95j42gsOeyvsBbiT35M9XyatfC85kAIPD\nt2TzwHFCIh5wsAeqXBi/6nJXUxqcgG7gVZIkxJi92kD+2AcsuK2izSoluLpuQoMa\n8pqtQRy66lBZ6Nhmb/n8rZpwtQKBgQDVHJHDerorY25eNb70FVvMSS+a/7fjIbPG\n59u4tBK9dJkxPvetQoNWdholpAmXM0EW+Kx+nL9PBQUJdJEX18sPLTSG1K0XjV5p\nYRwWFkoitX3gDj5WUepNA716wiNxx5IFb5RTcnyNzg4qq/UzLzTdmaoYqWLH1M0v\nsq9dtwyKRQKBgCYM4bcD2wtagedotUXqMJLGRz8IihrRFOiJSqy/VbSt7PrSQFCd\nHJALE+P09RNm09TBUWOtUtxROm+Ni83Il3OBvFHNvHmbKnCvTI/QXh5Ok9wEBCNt\n567uzmhw5K6H2pW50sWV+o+fNCTRU24WbQajERWs7TtSw/E8jiKVH1g1AoGASzQs\nwBXUErGg5gADZbEP1vRQp1rsMmvXPC7f27s4DcFSug0la+/X1zAQJA5SEBhXNNsG\nTBvWavUzhNWsygQttSpXqejtOC18DqXlOmodOUhgpiuAlgeMLidOuz49Mc6iWea5\nKgVxrLz1RNuvyKM0/apXWyKTKD+RNO7ScbjB5R0CgYACmcwxAvvlm/VO4/Y6EHHT\nfka4ESOdcliOaGsi3B93fAJcV0BdOdL4qcMMyVIK5Ep+UEJhUDyZ7cMPaJ7TvHjC\nY+T6wHTxqA0SsmWnbGTKpZIOao+Z5ywazz3e7rtXXIePgaeuSLAouFl/e9LbOKI1\n/8Yvdk+4fsz/gMycIA8FrA==\n-----END PRIVATE KEY-----\n"
client_email = "intensiva-calculator@gen-lang-client-0545395359.iam.gserviceaccount.com"
client_id = "106445411881625584918"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/intensiva-calculator%40gen-lang-client-0545395359.iam.gserviceaccount.com"
```

---

## ⚠️ **SUBSTITUA APENAS ESTA LINHA:**

```toml
OPENAI_API_KEY = "COLOQUE_SUA_CHAVE_OPENAI_AQUI"
                  ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                  Cole sua chave real aqui!
```

**Tudo o resto mantém EXATAMENTE como está!**

---

## 📋 **PASSO A PASSO**

### **1. Copiar o Bloco Completo**
- Selecione TUDO entre as linhas `# ===` até o final
- Ctrl + C

### **2. Acessar Streamlit Cloud**
```
1. https://share.streamlit.io/
2. Login
3. Encontre "Intensiva Calculator"
4. Clique nos 3 pontinhos (⋮)
5. "Settings"
```

### **3. Abrir Secrets**
```
No menu lateral esquerdo:
├─ General
├─ 🔐 Secrets ← CLIQUE AQUI
├─ Advanced
└─ Danger Zone
```

### **4. Colar e Editar**
```
1. Cole TODO o conteúdo copiado
2. Localize a linha: OPENAI_API_KEY = "COLOQUE_SUA_CHAVE_OPENAI_AQUI"
3. Substitua apenas entre as aspas pela sua chave real
4. Exemplo: OPENAI_API_KEY = "sk-proj-abc123..."
```

### **5. Salvar**
```
1. Clique em "Save" (botão inferior direito)
2. Aguarde mensagem: "Secrets saved successfully"
3. App reiniciará automaticamente (30s)
```

---

## ✅ **RESULTADO ESPERADO**

Depois de salvar, você verá algo assim no editor de Secrets:

```toml
OPENAI_API_KEY = "sk-proj-u5A8Jyet..."  ← Sua chave real

[connections.gsheets]
type = "service_account"
project_id = "gen-lang-client-0545395359"
# ... resto das credenciais do Google ...
```

---

## 🧪 **TESTAR**

### **Teste 1: Pacer (OpenAI)**
1. Vá na aba "🧪 Exames"
2. Cole dados de exames
3. Clique "✨ Processar"
4. ✅ Deve funcionar

### **Teste 2: Infusão (Google Sheets)**
1. Vá na página "Infusão"
2. Preencha campos
3. ✅ Deve salvar no Google Sheets

---

## 🚨 **TROUBLESHOOTING**

### **Erro: "Invalid TOML format"**

**Causa:** Erro de sintaxe

**Verificar:**
```toml
# ❌ ERRADO (falta aspas)
OPENAI_API_KEY = sk-proj-...

# ✅ CERTO (com aspas duplas)
OPENAI_API_KEY = "sk-proj-..."
```

**Verificar:**
```toml
# ❌ ERRADO (quebrou a private_key em várias linhas)
private_key = "-----BEGIN PRIVATE KEY-----
MIIEvAI...
-----END PRIVATE KEY-----"

# ✅ CERTO (tudo em uma linha com \n)
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAI...\n-----END PRIVATE KEY-----\n"
```

---

### **Erro: "API Key not configured"**

**Solução:**
1. Verifique se salvou os secrets
2. Aguarde 30s para app reiniciar
3. Recarregue a página (F5)
4. Se persistir: Settings → Reboot app

---

### **Erro: Google Sheets não conecta**

**Solução:**
1. Verifique se a seção `[connections.gsheets]` está presente
2. Verifique se todos os campos estão preenchidos
3. **NÃO MODIFIQUE** nada do Google Sheets, use exatamente como fornecido

---

## 🔐 **SEGURANÇA**

### **✅ É seguro?**
Sim! Streamlit Cloud:
- Criptografa todos os secrets
- Não exibe em logs
- Não compartilha entre apps
- Acesso restrito ao owner do app

### **⚠️ NUNCA:**
- Commitar secrets no GitHub
- Compartilhar sua API key
- Expor secrets em screenshots

---

## 📊 **VERIFICAÇÃO FINAL**

Depois de configurar, verifique:

```
✅ OpenAI API Key configurada
✅ Google Sheets credentials completas
✅ Formato TOML correto
✅ Secrets salvos com sucesso
✅ App reiniciado
✅ Pacer funciona (teste com exames)
✅ Infusão/IOT conectam (teste salvando)
```

---

## 💡 **DICAS**

### **Backup dos Secrets**
Salve uma cópia local em:
```
.streamlit/secrets.toml
```
**⚠️ NUNCA commite este arquivo!** (já está no `.gitignore`)

### **Múltiplos Ambientes**
Se tiver staging e produção, cada app tem seus próprios secrets.

### **Rotação de Keys**
Se precisar trocar a API key:
1. Settings → Secrets
2. Edite apenas a linha `OPENAI_API_KEY`
3. Save
4. Pronto!

---

## 📁 **ARQUIVO EXEMPLO**

Salvei um template em:
```
.streamlit/secrets_example.toml
```

**Este arquivo é seguro para commit** - não contém chaves reais.

---

## 🎯 **RESUMO DE 3 LINHAS**

1. **Copie** o bloco completo deste documento
2. **Cole** em Settings → Secrets no Streamlit Cloud
3. **Substitua** apenas sua chave OpenAI e **Save**

**Tempo:** 2 minutos ⏱️
**Dificuldade:** Fácil ⭐

---

**✅ Pronto! Seu app funcionará 100% no Streamlit Cloud!**
