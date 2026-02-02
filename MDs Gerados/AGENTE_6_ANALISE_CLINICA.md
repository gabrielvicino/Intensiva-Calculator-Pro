# 🩺 AGENTE 6: ANÁLISE CLÍNICA (CDSS - Clinical Decision Support System)

## 📅 Data: 29/01/2026

---

## 🎯 OBJETIVO

Adicionar um **Sistema de Suporte à Decisão Clínica (CDSS)** que analisa os resultados dos exames e gera **hipóteses diagnósticas** baseadas em valores alterados.

---

## 🔄 ARQUITETURA DO FLUXO

```
┌──────────────────────────────────────────────────────────┐
│  INPUT DO USUÁRIO (Texto bruto dos exames)              │
└──────────────────────────────────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │  PROCESSAMENTO PARALELO      │
        │  (Agentes 0-5)               │
        ├──────────────────────────────┤
        │  • Agente 0: Identificação   │
        │  • Agente 1: Hematologia     │
        │  • Agente 2: Hepático        │
        │  • Agente 3: Coagulação      │
        │  • Agente 4: Urina           │
        │  • Agente 5: Gasometria      │
        └──────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │  RESULTADO CONSOLIDADO       │
        │  (String de exames)          │
        └──────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │  AGENTE 6: ANÁLISE CLÍNICA   │
        │  (Entrada = Output Agentes)  │
        └──────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │  DISPLAY PARA O USUÁRIO:     │
        │  1. Exames (campo 1)         │
        │  2. Análise (campo 2)        │
        └──────────────────────────────┘
```

---

## 📝 IMPLEMENTAÇÃO

### 1. PROMPT DO AGENTE 6 (Linhas 177-212)

```python
PROMPT_AGENTE_ANALISE = """
# ATUE COMO
Um Assistente de Decisão Clínica Sênior para Medicina Intensiva.
Seu usuário é um médico experiente. NÃO explique fisiopatologia básica.

# TAREFA
1. Identifique valores críticos ou alterados.
2. Gere hipóteses diagnósticas diretas.

# FORMATO DE RESPOSTA (RIGOROSO)
SEÇÃO 1: **Laboratoriais Alterados:** [Lista]
SEÇÃO 2: **Hipóteses Diagnósticas:** [Numeradas]

# REGRAS DE RACIOCÍNIO CLÍNICO
- ANEMIA: Classifique por VCM (Micro/Normo/Macro)
- LEUCOGRAMA: Desvio → Infecção; Eosinofilia → Alergia
- RIM: Cr/Ur elevadas → IRA vs DRC
- GASOMETRIA: Classifique o distúrbio
- INFLAMATÓRIOS: PCR/Leuco → SIRS/Sepse
- CARDIO: Trop → IAM vs Injúria Miocárdica
"""
```

**Características:**
- Tom técnico para médicos experientes
- Sem prolixidade ou explicações básicas
- Foco em diferenciais práticos

---

### 2. MODIFICAÇÃO NA FUNÇÃO `processar_multi_agente()` (Linhas 915-939)

**ANTES (retornava apenas string):**
```python
# PASSO 3: Montar resultado final
if exames_concatenados:
    resultado_final = f"{nome_hc}\n{data_linha} " + " | ".join(exames_concatenados)
    return resultado_final
```

**DEPOIS (retorna tupla):**
```python
# PASSO 3: Montar resultado final dos exames
if exames_concatenados:
    resultado_exames = f"{nome_hc}\n{data_linha} " + " | ".join(exames_concatenados)
else:
    resultado_exames = f"{nome_hc}\n{data_linha} (Nenhum dado encontrado)"

# PASSO 4: Análise clínica (AGENTE 6)
analise_clinica = ""
if exames_concatenados:
    try:
        analise_clinica = processar_texto(
            api_source, api_key, model_name,
            PROMPT_AGENTE_ANALISE,
            resultado_exames  # INPUT: resultado dos agentes 0-5
        )
        if "❌" in analise_clinica or "⚠️" in analise_clinica:
            analise_clinica = ""
    except Exception:
        analise_clinica = ""

# Retorna tupla: (exames, análise)
return resultado_exames, analise_clinica
```

**Mudanças:**
- ✅ Retorna tupla `(resultado_exames, analise_clinica)`
- ✅ Agente 6 processa **APÓS** os agentes 0-5
- ✅ Input do Agente 6 é o **output consolidado** dos outros
- ✅ Tolerante a falhas (se Agente 6 falhar, retorna string vazia)

---

### 3. INTERFACE COM DOIS CAMPOS (Linhas 1084-1135)

**CAMPO 1: Resultado dos Exames**
```python
st.markdown("**Resultado dos Exames**")
if processar:
    resultado_exames, analise_clinica = processar_multi_agente(...)
    st.session_state["output_exames"] = resultado_exames
    st.session_state["output_analise"] = analise_clinica

# Exibe exames
if "output_exames" in st.session_state:
    st.code(resultado_exames, language="text")
```

**CAMPO 2: Análise Clínica (Novo)**
```python
# SEÇÃO DE ANÁLISE CLÍNICA (AGENTE 6) - ABAIXO DO RESULTADO
if "output_analise" in st.session_state and st.session_state["output_analise"]:
    st.divider()
    st.markdown("**🩺 Análise Clínica (Suporte à Decisão)**")
    st.markdown(analise)  # Renderiza markdown (listas, negrito)
```

**Layout Visual:**
```
┌─────────────────────────────────────────────────────────┐
│  🧪 Extrator de Exames - Multi-Agente                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Entrada]              [Resultado dos Exames]          │
│  Cole aqui...           João Silva 123456               │
│                         29/01/2026 – Hb 8,0 | Ht 24%   │
│  [Limpar] [✨ Processar]  ...                           │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  🩺 Análise Clínica (Suporte à Decisão)                │
│                                                         │
│  **Laboratoriais Alterados:** Hb, VCM, Cr, PCR         │
│                                                         │
│  **Hipóteses Diagnósticas:**                           │
│  1- Anemia Microcítica | Ferropriva; Talassemia        │
│  2- Injúria Renal Aguda | NTA; Pré-renal               │
│  3- Síndrome Inflamatória | Sepse; Pneumonia           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎓 REGRAS DE RACIOCÍNIO CLÍNICO DO AGENTE 6

### 1. ANEMIA
```
VCM < 80: Microcítica | Ferropriva; Talassemia; Doença Crônica
VCM 80-100: Normocítica | Hemorragia; Doença Crônica; Hemólise
VCM > 100: Macrocítica | Deficiência B12/Folato; Hipotireoidismo; Álcool
```

### 2. LEUCOGRAMA
```
Leucocitose + Desvio (Bast ↑): Infecção Bacteriana; Sepse
Leucopenia: Neutropenia; Viral; Medicamentoso
Eosinofilia: Alergia; Parasitose; Neoplasia
```

### 3. FUNÇÃO RENAL
```
Cr/Ur elevadas:
- Agudo: IRA (Pré-renal; NTA; Obstrutiva)
- Crônico: DRC (Diabetes; HAS; Glomerular)
```

### 4. GASOMETRIA
```
pH < 7,35: Acidose (Metabólica vs Respiratória)
pH > 7,45: Alcalose (Metabólica vs Respiratória)
Lac > 2: Hiperlactatemia (Choque; Tecidual; Tipo B)
AG > 12: AGMA (Cetoacidose; Uremia; Intoxicação; Lactato)
```

### 5. INFLAMATÓRIOS
```
PCR ↑ + Leuco ↑:
- Infecção: Sepse; Pneumonia; ITU
- Estéril: Pancreatite; TEP; IAM; Trauma
```

### 6. CARDÍACOS
```
Trop positiva:
- IAM: IAMCSST; IAMSSST
- Não IAM: Sepse; Insuf. Renal; TEP; Miocardite
```

---

## 📊 EXEMPLO DE USO REAL

### INPUT DO USUÁRIO:
```
JOÃO DA SILVA - HC 123456
29/01/2026

Hemograma:
Hb: 8,0 g/dL
Ht: 24%
VCM: 68 fL
Leucócitos: 18.500
Bastões: 8%
Plaquetas: 450.000

Função Renal:
Cr: 3,5 mg/dL
Ur: 120 mg/dL

Inflamatórios:
PCR: 280 mg/L

Gasometria Arterial:
pH: 7,25
pCO2: 30
HCO3: 14
Lactato: 4,5
```

### OUTPUT - CAMPO 1 (Resultado dos Exames):
```
João da Silva 123456
29/01/2026 – Hb 8,0 | Ht 24% | VCM 68 | Leuco 18.500 (Bast 8% / Seg 70% / Linf 15% / Mon 7%) | Plaq 450.000 | Cr 3,5 | Ur 120 | PCR 280 | Gas Art pH 7,25 / pCO2 30 / HCO3 14 / Lac 4,5
```

### OUTPUT - CAMPO 2 (Análise Clínica):
```
**Laboratoriais Alterados:** Hb (8,0), VCM (68), Leuco (18.500), Bastões (8%), Cr (3,5), Ur (120), PCR (280), Gasometria (Acidose Metabólica), Lactato (4,5)

**Hipóteses Diagnósticas:**
1- Anemia Microcítica Grave | Ferropriva; Talassemia; Sangramento crônico
2- Injúria Renal Aguda Grave (Cr 3,5) | NTA séptica; Choque; Nefrotóxicos
3- Síndrome Inflamatória Sistêmica | Sepse grave; Choque séptico; Foco abdominal/pulmonar
4- Acidose Metabólica Lática (AG elevado) | Choque séptico; Hipoperfusão; Lactato 4,5
5- Leucocitose com Desvio Grave | Infecção bacteriana ativa; Sepse com foco não controlado
```

---

## ✅ VANTAGENS DO AGENTE 6

### 1. SEGURANÇA JURÍDICA
- **Separação clara:** Dados objetivos (Campo 1) vs Opinião da IA (Campo 2)
- **Documento legal:** Campo 1 pode ir para prontuário sem "opinião"
- **Transparência:** Usuário sabe que Campo 2 é sugestão, não diagnóstico

### 2. SUPORTE EDUCACIONAL
- Médicos residentes aprendem raciocínio clínico
- Correlação entre achados laboratoriais e síndromes
- Diferenciais práticos e diretos

### 3. AGILIDADE
- Identifica valores críticos automaticamente
- Sugere próximos passos investigativos
- Economiza tempo de análise

### 4. REDUÇÃO DE ERROS
- Alertas para valores críticos
- Não deixa passar achados importantes
- Correlação entre múltiplos exames

---

## ⚠️ LIMITAÇÕES E AVISOS

### 1. NÃO É DIAGNÓSTICO DEFINITIVO
```
CORRETO: "Hipóteses diagnósticas sugeridas"
ERRADO: "Diagnóstico confirmado"
```

### 2. CONTEXTO CLÍNICO ESSENCIAL
- IA não conhece história clínica completa
- Não substitui exame físico
- Não considera imagem/outros exames

### 3. RESPONSABILIDADE MÉDICA
```
┌────────────────────────────────────────────┐
│  ⚠️ NOTA LEGAL (Sempre visível)           │
│                                            │
│  As hipóteses são SUGESTÕES para          │
│  auxiliar o raciocínio clínico.           │
│                                            │
│  A decisão final compete ao MÉDICO        │
│  ASSISTENTE, considerando o contexto      │
│  clínico completo do paciente.            │
└────────────────────────────────────────────┘
```

---

## 💰 IMPACTO NO CUSTO

### Custo Adicional por Exame (Gemini 2.5 Flash):

**ANTES (5 agentes):**
- Tokens: ~11.870 (input) + 520 (output)
- Custo: ~R$ 0,006/exame

**DEPOIS (6 agentes):**
- Tokens extras do Agente 6:
  - Input: ~400 tokens (string de exames)
  - Output: ~200 tokens (análise)
- Custo adicional: ~R$ 0,0001
- **TOTAL: ~R$ 0,0061/exame** (+1,7%)

**CONCLUSÃO:** 
- ✅ Aumento de custo **IRRISÓRIO** (+R$ 0,0001)
- ✅ Valor agregado **ENORME** (suporte à decisão)
- ✅ ROI positivo (economiza tempo do médico)

---

## 🧪 TESTES RECOMENDADOS

### Teste 1: Anemia Ferropriva
**Input:** Hb 7,0 / VCM 65 / Ferritina baixa  
**Esperado:** "Anemia Microcítica | Ferropriva; Sangramento"

### Teste 2: Sepse
**Input:** Leuco 22.000 / Bast 15% / PCR 300 / Lac 5,0  
**Esperado:** "Sepse grave | Choque séptico; Foco a esclarecer"

### Teste 3: IRA
**Input:** Cr 4,0 / Ur 150 / Na normal  
**Esperado:** "IRA Grave | NTA; Pré-renal; Obstrutiva"

### Teste 4: Acidose Metabólica
**Input:** pH 7,20 / HCO3 10 / Lac 8,0  
**Esperado:** "Acidose Metabólica Lática | Choque; Hipoperfusão"

---

## 📚 ARQUIVOS MODIFICADOS

1. **`views/pacer.py`** (Linhas 177-212): Novo prompt AGENTE 6
2. **`views/pacer.py`** (Linhas 915-939): Função retorna tupla
3. **`views/pacer.py`** (Linhas 1084-1135): Interface com 2 campos

---

## 🎓 PRÓXIMOS PASSOS (FUTURO)

### Fase 2: Refinamento
- [ ] Adicionar valores de referência personalizáveis
- [ ] Considerar idade/sexo do paciente
- [ ] Integrar com histórico de exames anteriores

### Fase 3: Alertas Críticos
- [ ] Destacar valores críticos em vermelho
- [ ] Notificações sonoras para valores perigosos
- [ ] Sugestões de conduta urgente

### Fase 4: Machine Learning
- [ ] Aprender com feedbacks do médico
- [ ] Melhorar acurácia das hipóteses
- [ ] Personalizar para cada serviço/hospital

---

**Desenvolvido por:** Dr. Gabriel Valladão Vicino - CRM-SP 223.216  
**Data:** 29/01/2026  
**Versão:** Pacer v3.2 (Com CDSS)
