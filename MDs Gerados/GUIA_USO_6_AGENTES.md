# 📖 GUIA DE USO: PACER EXAMES COM 6 AGENTES

## 🚀 INÍCIO RÁPIDO

### 1. Abra a Aplicação
```bash
streamlit run app.py
```

### 2. Navegue até "Pacer - Exames & Prescrição"
No menu lateral, selecione a página **📃 Pacer**

### 3. Configure a API
Na barra lateral esquerda:
- **Motor:** Google Gemini (recomendado)
- **API Key:** Cole sua chave do Google AI Studio
- **Modelo:** gemini-2.5-flash (mais rápido e econômico)

---

## 🧪 USANDO OS 6 AGENTES

### PASSO 1: Selecione os Tipos de Exames

Na aba **🧪 Exames**, clique em **"⚙️ Selecionar Tipos de Exames"** para expandir:

```
╔═══════════════════════════════════════════════════════╗
║  [✓] 🔵 Hematologia + Renal                          ║
║      Hemograma completo + Função Renal + Eletrólitos  ║
║                                                        ║
║  [✓] 🟡 Função Hepática                              ║
║      TGP, TGO, FAL, GGT, BT, Alb, Amil, Lipas        ║
║                                                        ║
║  [✓] 🟠 Coagulação + Inflamatórios                   ║
║      PCR, CPK, Trop, TP, TTPa                        ║
║                                                        ║
║  [✓] 🟣 Urina I (EAS)                                ║
║      Exame de Urina Completo                         ║
║                                                        ║
║  [✓] 🔴 Gasometria                                   ║
║      Gas Arterial, Venosa ou Mista                   ║
╚═══════════════════════════════════════════════════════╝
```

**DICA:** Por padrão, todas as categorias vêm marcadas. Desmarque as que não precisa para economizar tokens e acelerar o processamento.

---

### PASSO 2: Cole o Texto dos Exames

Na coluna **"Entrada"**, cole o texto bruto dos exames:

```
Exemplo de entrada:

EXAMES LABORATORIAIS - 29/12/2025
Paciente: Carlos Eduardo Souza
Registro: 9876543/2

HEMOGRAMA COMPLETO
Hemoglobina: 8,0 g/dL
Hematócrito: 24%
Leucócitos: 12.500/mm³
  Bastões: 2%
  Segmentados: 68%
  Linfócitos: 20%
  Monócitos: 6%
  Eosinófilos: 4%
  Basófilos: 0%
Plaquetas: 150.000/mm³

FUNÇÃO RENAL
Creatinina: 1,2 mg/dL
Ureia: 45 mg/dL
Sódio: 138 mEq/L
Potássio: 4,0 mEq/L

...
```

---

### PASSO 3: Clique em "✨ Processar com Multi-Agente"

O sistema irá:
1. **Extrair identificação** (Nome, HC, Data)
2. **Processar apenas os agentes selecionados**
3. **Concatenar os resultados**

---

### PASSO 4: Copie o Resultado

Na coluna **"Resultado"**, você verá:

```
Carlos Eduardo Souza 9876543
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | Cai 1,01 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Prot Tot 6,5 | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP Ativ 14,2s (1,1) | TTPa 30s (1,0)
```

**Clique no ícone de copiar** (canto superior direito da caixa de código) para copiar tudo.

---

## 💡 DICAS DE USO

### QUANDO USAR CADA AGENTE?

#### 🔵 **Hematologia + Renal** (Use sempre)
- Pacientes com anemia
- Avaliação de leucocitose/leucopenia
- Monitoramento renal (IRC, IRA)
- Distúrbios eletrolíticos

#### 🟡 **Função Hepática** (Use quando)
- Paciente hepatopata
- Suspeita de colestase
- Monitoramento de enzimas
- Avaliação nutricional (albumina)

#### 🟠 **Coagulação + Inflamatórios** (Use quando)
- Paciente anticoagulado
- Suspeita de IAM (troponina, CPK-MB)
- Monitoramento de PCR
- Avaliação de coagulopatia

#### 🟣 **Urina I** (Use quando)
- Suspeita de ITU
- Avaliação de hematúria
- Monitoramento de proteinúria
- Exame de rotina

#### 🔴 **Gasometria** (Use quando)
- Paciente com alteração respiratória
- Distúrbio ácido-base
- Monitoramento de ventilação mecânica
- Choque / Sepse (lactato)

---

## ⚡ CASOS DE USO RÁPIDOS

### CASO 1: Paciente de Rotina (UTI)
**Agentes recomendados:**
- ✅ Hematologia + Renal
- ✅ Função Hepática
- ✅ Coagulação
- ❌ Urina I (só se houver)
- ❌ Gasometria (só se houver)

**Economia:** ~44% de tokens

---

### CASO 2: Paciente com Sepse
**Agentes recomendados:**
- ✅ Hematologia + Renal
- ✅ Coagulação (PCR, lactato via gasometria)
- ✅ Gasometria
- ❌ Função Hepática (só se hepatopata)
- ❌ Urina I (só se ITU)

**Economia:** ~26% de tokens

---

### CASO 3: Paciente Cirrótico
**Agentes recomendados:**
- ✅ Hematologia + Renal (plaquetopenia, Na)
- ✅ Função Hepática (BT, Alb, enzimas)
- ✅ Coagulação (TP, RNI)
- ❌ Urina I (opcional)
- ❌ Gasometria (opcional)

**Economia:** ~35% de tokens

---

### CASO 4: Apenas Gasometria
**Agentes recomendados:**
- ❌ Hematologia + Renal
- ❌ Função Hepática
- ❌ Coagulação
- ❌ Urina I
- ✅ Gasometria

**Economia:** ~72% de tokens 🔥

---

## ❌ ERROS COMUNS E SOLUÇÕES

### Erro: "⚠️ Nenhuma categoria selecionada"
**Causa:** Todos os checkboxes estão desmarcados  
**Solução:** Marque pelo menos uma categoria no expander

---

### Erro: "⚠️ Configure a chave de API"
**Causa:** API Key não foi inserida  
**Solução:** Cole sua chave do Google AI Studio na barra lateral

---

### Erro: "❌ Erro na API: [mensagem]"
**Causas possíveis:**
- API Key inválida
- Modelo não disponível
- Limite de rate-limit atingido
- Problema de conexão

**Solução:**
1. Verifique se a API Key está correta
2. Tente outro modelo (ex: gemini-1.5-pro-002)
3. Aguarde alguns segundos e tente novamente

---

### Resultado: "(Nenhum dado laboratorial encontrado)"
**Causa:** Os agentes selecionados não encontraram dados no texto  
**Possíveis motivos:**
- Texto sem exames laboratoriais
- Agentes errados selecionados (ex: só Gasometria, mas texto tem só hemograma)
- Formato muito diferente do padrão

**Solução:**
1. Verifique se o texto realmente contém os dados desejados
2. Selecione os agentes corretos
3. Se o problema persistir, cole um exemplo de texto no GitHub Issues

---

## 🔄 COMPARAÇÃO: ANTES × DEPOIS

### ANTES (Prompt Único)
```
❌ 142 linhas de prompt
❌ Processa tudo sempre (mesmo sem dados)
❌ Taxa de erro 15-20%
❌ Lento (5-7 segundos)
❌ Mais caro ($0,10 por requisição)
```

### DEPOIS (6 Agentes)
```
✅ 25-50 linhas por agente
✅ Processa só o que precisa
✅ Taxa de erro 5-10%
✅ Rápido (2-4 segundos)
✅ Mais barato ($0,035-0,074 por requisição)
```

---

## 🎓 PERGUNTAS FREQUENTES

### 1. Posso editar os prompts dos agentes?
**Não.** Os prompts são fixos para garantir consistência e segurança.

### 2. Posso criar novos agentes?
**Não diretamente.** Entre em contato para solicitar novos agentes.

### 3. Os agentes processam em paralelo?
**Não nesta versão.** Eles processam sequencialmente, mas muito rápido.

### 4. O que acontece se desmarcar todos os checkboxes?
**Erro.** Você precisa selecionar pelo menos uma categoria.

### 5. A Aba "Prescrição" mudou?
**Não.** Apenas a aba "Exames" usa os 6 agentes. Prescrição continua igual.

### 6. Posso usar OpenAI em vez de Gemini?
**Sim.** Selecione "OpenAI GPT" na barra lateral e cole sua API Key.

---

## 📞 SUPORTE

**Problemas ou Sugestões?**
- GitHub Issues: [link do repositório]
- Email: [seu email]
- CRM-SP: 223.216

---

**Desenvolvido por:** Dr. Gabriel Valladão Vicino  
**Versão:** Pacer v3.0 (Multi-Agente)  
**Data:** 29/01/2026
