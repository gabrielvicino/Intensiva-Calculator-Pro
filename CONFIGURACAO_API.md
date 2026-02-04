# 🔑 Configuração da API Key OpenAI

Este guia explica como configurar sua chave de API OpenAI para usar o Intensiva Calculator.

---

## 📋 **Pré-requisitos**

1. **Chave de API OpenAI**
   - Obtenha sua chave em: https://platform.openai.com/api-keys
   - A chave começa com `sk-proj-...`

2. **Arquivo `.env` configurado**
   - O arquivo `.env` armazena sua chave localmente
   - Este arquivo **NÃO** é enviado para o GitHub (está no `.gitignore`)

---

## ⚙️ **Como Configurar**

### **Passo 1: Criar arquivo `.env`**

Na **raiz do projeto**, crie um arquivo chamado `.env` (sem extensão antes do ponto).

### **Passo 2: Adicionar sua chave**

Abra o arquivo `.env` e adicione:

```env
OPENAI_API_KEY=sk-proj-SUA_CHAVE_AQUI
```

**Substitua** `sk-proj-SUA_CHAVE_AQUI` pela sua chave real da OpenAI.

### **Passo 3: Salvar e reiniciar**

1. Salve o arquivo `.env`
2. Reinicie o Streamlit:
   ```bash
   streamlit run app.py
   ```

---

## ✅ **Verificação**

Após reiniciar, a **sidebar** do Pacer deve mostrar:

```
✅ API Key: ...últimos8caracteres
```

Se mostrar `❌ API Key não carregada!`, revise os passos acima.

---

## 🔒 **Segurança**

- ✅ O arquivo `.env` **não** é enviado para o GitHub
- ✅ Suas chaves ficam **apenas no seu computador**
- ⚠️ **NUNCA** compartilhe seu arquivo `.env` publicamente
- ⚠️ **NUNCA** coloque a chave diretamente no código

---

## 📁 **Exemplo de Estrutura**

```
Intensiva Calculator/
├── .env                  ← Sua chave aqui (NÃO commitado)
├── .env.example          ← Modelo (commitado)
├── .gitignore            ← .env está listado aqui
├── app.py
├── views/
│   └── pacer.py          ← Lê a chave do .env
└── ...
```

---

## ❓ **Problemas Comuns**

### **Erro: "API Key não configurada!"**

**Causa:** Arquivo `.env` não existe ou está vazio.

**Solução:**
1. Verifique se o arquivo `.env` existe na raiz
2. Verifique se a linha está correta: `OPENAI_API_KEY=sk-proj-...`
3. Reinicie o Streamlit (`Ctrl+C` → `streamlit run app.py`)

### **Erro: "python-dotenv não encontrado"**

**Causa:** Biblioteca não instalada.

**Solução:**
```bash
pip install python-dotenv
```

---

## 📞 **Suporte**

Se ainda tiver problemas:

1. Verifique o **terminal** para logs de debug
2. Consulte a [documentação oficial da OpenAI](https://platform.openai.com/docs)
3. Revise este guia novamente

---

**✨ Configuração completa! Agora você pode usar o Pacer com todos os 6 agentes especializados.**
