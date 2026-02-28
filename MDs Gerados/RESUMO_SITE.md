# Resumo Completo — Intensiva Calculator

**Sistema de Apoio à Decisão Clínica** para Terapia Intensiva e Medicina de Emergência.

---

## 1. Visão Geral

O **Intensiva Calculator** é uma aplicação web em **Streamlit** (Python) que oferece ferramentas clínicas para médicos intensivistas. Opera com **autenticação por PIN** (opcional), **dados em Google Sheets** e **IA** (OpenAI GPT / Google Gemini) para extração e estruturação de textos clínicos.

---

## 2. Arquitetura

```
app.py                    ← Ponto de entrada (router + autenticação)
├── views/
│   ├── home.py           ← Página inicial
│   ├── evolucao.py       ← Evolução Diária (principal)
│   ├── infusao.py        ← Calculadora de Infusão Contínua
│   ├── intubacao.py      ← Guia Intubação Orotraqueal
│   ├── conversao.py      ← Conversor Universal de Unidades
│   ├── pacer.py          ← Pacer (Exames + Prescrição via IA)
│   └── calculadoras.py  ← Calculadoras Médicas (renal, etc.)
├── modules/
│   ├── fichas.py         ← Formulários e seções
│   ├── fluxo.py          ← Fluxo de dados (IA → session_state)
│   ├── gerador.py        ← Geração do texto prontuário
│   ├── ia_extrator.py    ← Recorte de texto em seções
│   ├── agentes_secoes.py ← 12 agentes IA por seção
│   ├── extrator_exames.py← 6 agentes exames + 3 prescrição
│   ├── parser_*.py       ← Parsers determinísticos
│   └── ui.py             ← Componentes UI reutilizáveis
├── utils.py              ← Google Sheets, load/save, rodapé
└── calculos/             ← Cálculos especializados (renal, etc.)
```

---

## 3. Páginas e Funcionalidades

### 3.1 Home
- **Descrição:** Página inicial com apresentação do sistema e links para os módulos.
- **Conteúdo:** Texto sobre módulos disponíveis (Pacer, Evolução, Infusão, IOT, etc.).

### 3.2 Evolução Diária
- **Objetivo:** Gerar evolução clínica estruturada completa.

**Fluxo:**
1. **Busca de paciente:** Número de prontuário → carregar ou criar novo.
2. **Card do paciente:** Nome, Prontuário, Leito, Dias internados.
3. **Bloco 1 — Prontuário:**
   - Colar texto bruto da evolução.
   - **Extrair Seções:** IA (`ia_extrator`) recorta o texto em 14 seções JSON.
   - **Completar Campos:** 12 agentes (`agentes_secoes`) preenchem formulários.
4. **Bloco 2 — Dados Clínicos:**
   - Formulário com 15 seções (Identificação, Diagnósticos, Comorbidades, MUC, HMPA, Dispositivos, Culturas, Antibióticos, Complementares, Laboratoriais, Controles, Evolução Clínica, Sistemas, Prescrição, Condutas).
   - Parsers determinísticos para laboratoriais, controles e sistemas.
   - Botão **Prontuário Completo** gera o texto final via `gerador.py`.
5. **Bloco 3 — Saída:** Prontuário formatado, copiável e download.

### 3.3 Infusão Contínua
- **Objetivo:** Calcular doses de drogas vasoativas, sedativos e analgésicos.
- **Dados:** Google Sheets (aba `DB_INFUSAO`).
- **Funcionalidades:** Concentração, cálculo reverso, limites de segurança.

### 3.4 Intubação Orotraqueal (IOT)
- **Objetivo:** Guia rápido para sequência rápida com doses sugeridas por peso.

### 3.5 Conversor Universal
- **Objetivo:** Conversão entre unidades farmacológicas (mcg, mg, g, UI) e taxas de infusão.

### 3.6 Pacer (Exames & Prescrição)
- **Objetivo:** Extração estruturada de laudos e prescrições via IA.

**Fluxo:**
1. **Aba Exames:** 6 agentes IA em paralelo (Hematologia/Renal, Hepático, Coagulação, Urinálise, Gasometria, Identificação).
2. **Aba Prescrição:** 3 agentes sequenciais (Identificação, Medicamentos, Análise).
3. **Saída:** Texto formatado e padronizado.

### 3.7 Calculadoras Médicas
- **Objetivo:** Calculadoras especializadas (renal, hemodinâmica, etc.).
- **Atual:** `calculos/renal.py` — Clearance de Creatinina, TFG, RIFLE, AKIN, KDIGO.

---

## 4. Fluxo de Dados (Evolução Diária)

```
Texto bruto
    ↓
ia_extrator.extrair_dados_prontuario()  → JSON com 14 seções
    ↓
fluxo.atualizar_notas_ia()  → preenche campos *_notas
    ↓
Usuário clica "Completar Campos"
    ↓
agentes_secoes (12 agentes em paralelo)  → preenchem formulários
    ↓
session_state (campos estruturados)
    ↓
gerador.gerar_texto_final()  → texto prontuário completo
```

---

## 5. Regra de Novos Campos

Ao criar ou alterar um campo em qualquer seção:

1. **Formulário:** `modules/secoes/<secao>.py` → `get_campos()` + widget.
2. **Gerador:** `modules/gerador.py` → função `_secao_*` correspondente.
3. **Agente:** `modules/agentes_secoes.py` → prompt, schema e `preencher_<secao>`.

---

## 6. Arquivos Essenciais

| Arquivo | Função |
|---------|--------|
| `app.py` | Router, autenticação, páginas |
| `utils.py` | Google Sheets, load/save, rodapé |
| `views/*.py` | Páginas do app |
| `modules/fichas.py` | Orquestra formulários e seções |
| `modules/fluxo.py` | Atualiza notas da IA, limpar campos |
| `modules/gerador.py` | Gera texto prontuário |
| `modules/ia_extrator.py` | Recorta texto em seções |
| `modules/agentes_secoes.py` | 12 agentes IA por seção |
| `modules/extrator_exames.py` | 6 agentes exames + 3 prescrição |
| `modules/parser_*.py` | Parsers determinísticos |
| `modules/ui.py` | Componentes UI |
| `calculos/renal.py` | Cálculos renais |

---

## 7. Configuração

- **API Keys:** `.streamlit/secrets.toml` ou variáveis de ambiente (`OPENAI_API_KEY`, `GOOGLE_API_KEY`).
- **Google Sheets:** URL em `utils.py` (`SHEET_URL`).
- **Execução:** `streamlit run app.py` ou `executar.bat`.

---

## 8. Scripts e Pastas Auxiliares

| Pasta/Arquivo | Uso |
|---------------|-----|
| `scripts/` | `gerar_exemplo_standalone.py`, `testar_gemini.py`, `sync_infusao_sheet.py`, `iniciar.bat` |
| `MDs Gerados/` | Documentação interna |
| `.streamlit/` | `config.toml`, `keep_alive.py`, `atualizar*.py` |
| `fazer_commit.bat` | Commit e push via `fazer_commit.py` |

---

*Última atualização: Fevereiro 2026*
