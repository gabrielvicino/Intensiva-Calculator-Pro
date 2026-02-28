import streamlit as st
from utils import mostrar_rodape
import google.generativeai as genai
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ==============================================================================
# 1. CONFIGURAÇÕES VISUAIS
# ==============================================================================
# st.set_page_config já é definido em app.py (router). Evita erro "can only be called once".

# CSS para ajustar botões e fonte
st.markdown("""
<style>
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #1a73e8;
        border-color: #1a73e8;
        color: white;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #1557b0;
        border-color: #1557b0;
    }
    /* Aumenta a fonte do código para facilitar leitura */
    code {
        font-size: 1.1em !important;
        font-family: 'Courier New', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. PROMPTS DOS 6 AGENTES ESPECIALIZADOS (FIXOS - NÃO EDITÁVEIS)
# ==============================================================================

# AGENTE 0: IDENTIFICAÇÃO (Nome, HC, Data)
PROMPT_AGENTE_IDENTIFICACAO = """# ATUE COMO
Um formatador de identificação hospitalar.

# TAREFA
Extraia Nome, Registro (HC) e Data do texto.

# REGRAS DE FORMATAÇÃO (RIGOROSAS)
1. NOME: Converta OBRIGATORIAMENTE para Title Case (Apenas primeiras letras maiúsculas).
   - Entrada: "MARCOS PAULO DE GODOY" -> Saída: "Marcos Paulo de Godoy"
2. DATA: Se não houver data no texto, use a data de hoje.
3. SAÍDA: Exatamente duas linhas. Mantenha o travessão final.

# FORMATO DE RESPOSTA
Linha 1: [Nome Title Case] [HC]
Linha 2: [Data DD/MM/AAAA] –

# EXEMPLO DE SAÍDA (TEMPLATE)
João da Silva 1234567
01/02/2026 –

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 1: HEMATOLOGIA + RENAL + ELETRÓLITOS
PROMPT_AGENTE_HEMATOLOGIA_RENAL = """# ATUE COMO
Especialista em Hematologia e Nefrologia.

# TAREFA
Varra o texto buscando os dados abaixo.
Retorne APENAS os itens que possuem valor numérico, separados por " | ".

# REGRAS DE LIMPEZA (CRÍTICO)
- Se um item não tiver valor, IGNORE-O completamente.
- NÃO deixe pipes duplos "||".
- NÃO escreva o nome do exame se não houver número (Ex: Proibido retornar "Ur |").

# ORDEM DE BUSCA
1. Hb (1 casa decimal)
2. Ht (Inteiro + %)
3. [CONDICIONAL]: Se Hb < 9,0 inclua: VCM | HCM | RDW. (Se Hb >= 9,0, ignore estes 3).
4. Leuco (Se <500, converta ex: 0,4->400)
5. Fórmula (Bast X% / Seg Y% / Linf Z% / Mon W% / Eos K% / Bas H%). Use barras "/" internas.
6. Plaq
7. Cr (1 casa decimal)
8. Ur (Inteiro)
9. Na (Inteiro)
10. K (1 casa decimal)
11. Mg (1 casa decimal)
12. Pi (1 casa decimal)
13. CaT (1 casa decimal)
14. Cai (2 casas decimais)

# EXEMPLO DE SAÍDA (TEMPLATE)
Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | Cai 1,01

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 2: FUNÇÃO HEPÁTICA
PROMPT_AGENTE_HEPATICO = """# ATUE COMO
Especialista em Gastroenterologia.

# TAREFA
Extraia os dados abaixo. Se o dado não existir, PULE para o próximo.
Não deixe espaços vazios ou pipes extras.

# ORDEM DE PREFERÊNCIA
1. TGP
2. TGO
3. FAL
4. GGT
5. BT (Se houver direta: BT X,X (Y,Y))
6. Prot Tot
7. Alb
8. Amil
9. Lipas

# REGRAS DE LIMPEZA
- Retorne apenas o que tiver valor.
- Exemplo: Se só tem TGP e Amilase, retorne: "TGP 32 | Amil 65".

# EXEMPLO DE SAÍDA (TEMPLATE)
TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Prot Tot 6,5 | Alb 3,8 | Amil 65 | Lipas 40

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 3: COAGULAÇÃO + INFLAMATÓRIOS
PROMPT_AGENTE_COAGULACAO = """# ATUE COMO
Especialista em Marcadores Críticos.

# TAREFA
Extraia apenas os marcadores presentes no texto.

# LISTA ALVO
1. PCR (inteiro, sem casas decimais)
2. CPK (inteiro, sem casas decimais)
3. CK-MB (inteiro, sem casas decimais)
4. Trop (2 casas decimais)
5. TP (com RNI entre parênteses) - SEMPRE 1 casa decimal
6. TTPa (com Relação entre parênteses) - SEMPRE 1 casa decimal

# REGRAS DE PRECISÃO NUMÉRICA (RIGOROSO)
- PCR, CPK, CK-MB: INTEIROS (Ex: 89, 150, 12)
- Trop: 2 casas decimais (Ex: 0,01)
- TP: SEMPRE 1 casa decimal (Ex: 14,2s) - Sigla: "TP" (NÃO "TP Ativ")
- TTPa: SEMPRE 1 casa decimal (Ex: 69,1s)
- RNI/Relação: 2 casas decimais entre parênteses (Ex: (1,22))

# REGRA DE OURO (ANTI-ALUCINAÇÃO)
- Se o texto menciona "CPK" mas não traz o resultado numérico, NÃO inclua "CPK" na saída.
- Proibido saídas como: "CPK | CK-MB".
- Correto: "PCR 12 | Trop 0,01".

# EXEMPLOS DE SAÍDA (TEMPLATES)
Exemplo 1: PCR 89 | TP 14,2s (1,22) | TTPa 69,1s (2,49)
Exemplo 2: PCR 12 | CPK 150 | CK-MB 12 | Trop 0,01 | TP 14,2s (1,10) | TTPa 30,0s (1,00)

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 4: URINA I (EAS)
PROMPT_AGENTE_URINA = """# ATUE COMO
Especialista em Urinálise.

# TAREFA
Verifique se há exame de URINA TIPO I (EAS).
- SE SIM: Monte a string completa.
- SE NÃO: Retorne string vazia.

# ESTRUTURA
Urn: Den: [Val] / Leu Est: [Val] / Nit: [Val] / Leuco [Val] / Hm : [Val] / Prot: [Val] / Cet: [Val] / Glic: [Val]

# REGRAS
- Den (Densidade): Ex 1.020.
- Qualitativos: Use "Pos" ou "Neg".
- Quantitativos: Use números.

# EXEMPLO DE SAÍDA (TEMPLATE)
Urn: Den: 1.020 / Leu Est: Neg / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Neg / Cet: Neg / Glic: Neg

# FORMATO DE RESPOSTA
- Apenas a string formatada ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 5: GASOMETRIA
PROMPT_AGENTE_GASOMETRIA = """# ATUE COMO
Especialista em Gasometria.

# TAREFA
Identifique Gasometria (Arterial, Venosa ou Ambas).
REGRA DE DATA: Se houver múltiplas coletas, extraia APENAS a que tiver horário mais recente.

# REGRAS DE PRECISÃO NUMÉRICA (RIGOROSO)
Aplique estas regras de arredondamento/formatação para cada item:
1. INTEIROS (Sem vírgula): pCO2, pO2, HCO3, SatO2, SvO2, AG, Cl, Na.
2. 1 CASA DECIMAL: BE (Ex: -2,3), Lac (Ex: 1,5), K (Ex: 4,0).
3. 2 CASAS DECIMAIS: pH (Ex: 7,35), Cai (Ex: 1,15).

# ESTRUTURA
- Use " / " entre valores.
- Use " | " entre blocos (apenas se for mista).

# CENÁRIOS
A. ARTERIAL: pH / pCO2 / pO2 / HCO3 / BE / SatO2 / Lac / AG / Cl / Na / K / Cai
B. VENOSA: pH / pCO2 / HCO3 / BE / SvO2 / Lac / AG / Cl / Na / K / Cai

# EXEMPLOS DE SAÍDA (TEMPLATES)
Exemplo 1 (Só Arterial):
Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

Exemplo 2 (Só Venosa):
Gas Ven pH 7,31 / pCO2 48 / HCO3 24 / BE -1,5 / SvO2 70% / Lac 1,8 / AG 12 / Cl 102 / Na 137 / K 4,2 / Cai 1,10

Exemplo 3 (Mista - Arterial Completa + Venosa Resumida):
Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | Gas Ven pCO2 48 / SvO2 70%

# FORMATO DE RESPOSTA
- Escolha UM cenário. Retorne APENAS a string formatada conforme as regras de precisão.
- Se não houver dados, retorne VAZIO.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 6: ANALISTA DE HIPÓTESES DIAGNÓSTICAS
PROMPT_AGENTE_ANALISE = """# ATUE COMO
Um Assistente de Decisão Clínica Sênior para Medicina Intensiva.
Seu usuário é um médico experiente. NÃO explique fisiopatologia básica. NÃO seja prolixo.

# TAREFA
Analise a string de exames laboratoriais fornecida.
1. Identifique valores críticos ou alterados (considere valores de referência padrão para adultos).
2. Gere hipóteses diagnósticas diretas baseadas nessas alterações.

# FORMATO DE RESPOSTA (RIGOROSO)
A resposta deve conter APENAS duas seções, com quebras de linha OBRIGATÓRIAS:

SEÇÃO 1:
**Laboratoriais Alterados:** [Lista dos exames fora da faixa, separados por vírgula]

[LINHA EM BRANCO OBRIGATÓRIA]

SEÇÃO 2:
**Hipóteses Diagnósticas:**  
1- [Item 1]  
2- [Item 2]  
3- [Item 3]  
(etc.)

REGRAS DE FORMATAÇÃO:
- Coloque DOIS espaços no final de cada linha antes de quebrar (markdown)
- OU use quebra de linha dupla entre as seções
- Cada item numerado deve estar em sua própria linha

# REGRAS DE RACIOCÍNIO CLÍNICO
- ANEMIA: Classifique por VCM (Micro/Normo/Macro). Ex: "Anemia Microcítica | Ferropriva; Talassemia; Doença Crônica".
- LEUCOGRAMA: Se Leucocitose com desvio (Bast > %) -> Sugerir Infecção Bacteriana/Sepse. Se Eosinofilia -> Alergia/Parasitose.
- RIM: Se Cr/Ur elevadas -> IRA (Pré-renal vs NTA) ou DRC.
- GASOMETRIA: Classifique o distúrbio (ex: Acidose Metabólica). Se houver AG (Anion Gap) calculado, use-o.
- INFLAMATÓRIOS: PCR/Leuco altos -> SIRS/Sepse vs Inflamação estéril (Pancreatite, Trauma).
- CARDIO: Trop positiva -> IAM vs Injúria Miocárdica (Sepse/TEP/Renal).

# EXEMPLO DE SAÍDA (TEMPLATE)
**Laboratoriais Alterados:** Hb, VCM, Leuco, Cr, PCR, Gasometria (Acidose)

**Hipóteses Diagnósticas:**  
1- Anemia Microcítica | Ferropriva; Sangramento crônico; Doença Crônica  
2- Injúria Renal Aguda (Cr 3.5) | NTA; Pré-renal; Obstrutiva  
3- Síndrome Inflamatória | Sepse bacteriana; Foco abdominal; Pneumonia  
4- Acidose Metabólica | Hiperlactatemia (Perfusional); Uremia

IMPORTANTE: Cada linha numerada DEVE terminar com dois espaços OU quebra de linha real.

# INPUT PARA PROCESSAR:
{{TEXTO_CONSOLIDADO_DOS_EXAMES}}"""

# ==============================================================================
# DICIONÁRIO DE AGENTES (Configuração dos 5 Agentes de Extração)
# ==============================================================================
AGENTES_EXAMES = {
    "hematologia_renal": {
        "nome": "🔵 Hematologia + Renal",
        "descricao": "Hemograma completo + Função Renal + Eletrólitos",
        "prompt": PROMPT_AGENTE_HEMATOLOGIA_RENAL,
        "ativado_default": True
    },
    "hepatico": {
        "nome": "🟡 Função Hepática",
        "descricao": "TGP, TGO, FAL, GGT, BT, Alb, Amil, Lipas",
        "prompt": PROMPT_AGENTE_HEPATICO,
        "ativado_default": True
    },
    "coagulacao": {
        "nome": "🟠 Coagulação + Inflamatórios",
        "descricao": "PCR, CPK, Trop, TP, TTPa",
        "prompt": PROMPT_AGENTE_COAGULACAO,
        "ativado_default": True
    },
    "urina": {
        "nome": "🟣 Urina I (EAS)",
        "descricao": "Exame de Urina Completo",
        "prompt": PROMPT_AGENTE_URINA,
        "ativado_default": True
    },
    "gasometria": {
        "nome": "🔴 Gasometria",
        "descricao": "Gas Arterial, Venosa ou Mista",
        "prompt": PROMPT_AGENTE_GASOMETRIA,
        "ativado_default": True
    }
}

# ==============================================================================
# 3. PROMPTS MULTI-AGENTE - PRESCRIÇÃO (3 AGENTES)
# ==============================================================================

# AGENTE 1: IDENTIFICAÇÃO DO PACIENTE E PERÍODO
PROMPT_AGENTE_IDENTIFICACAO_PRESCRICAO = """# ROLE
Você é um Especialista em Admissão e Registro Hospitalar.

# TAREFA
Sua única função é extrair os dados de identificação do paciente e o período da prescrição a partir do texto bruto.

# REGRAS DE EXTRAÇÃO
1. NOME: Converta OBRIGATORIAMENTE para Title Case (Apenas primeiras letras maiúsculas).
2. IDADE: Extraia apenas o número.
3. DATAS: Formato DD/MM/AAAA.
4. REGISTRO/LEITO: Se não encontrar, deixe em branco, mas mantenha a estrutura.

# ESTRUTURA DE SAÍDA (FORMATO RÍGIDO)
Retorne APENAS duas linhas de texto bruto (Plaintext). Nada mais.

Linha 1: [Nome Completo], [Idade] anos - [Registro] - [Leito]
Linha 2: Prescrição: [Data Início] até [Data Fim]

# EXEMPLO DE SAÍDA
João da Silva - 74 anos - 1570869/3 - 643A
Prescrição: 09/01/2026 até 10/01/2026

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 2: DIETA, SUPLEMENTOS E HIDRATAÇÃO
PROMPT_AGENTE_DIETA = """# ROLE
Você é um Auditor de Nutrição Clínica.

# TAREFA
Extraia e organize os itens de nutrição.
Sua prioridade máxima é a CONSISTÊNCIA: Você deve gerar no máximo 1 linha para cada categoria nutricional.

# AS 6 CATEGORIAS PERMITIDAS (HIERARQUIA RÍGIDA)
1. Dieta Oral
2. Suplemento Oral
3. Hidratação (Água livre/Flush)
4. Dieta Enteral
5. Suplemento Enteral
6. Nutrição Parenteral (NPP)

# REGRAS DE PROCESSAMENTO (CRÍTICO)
1. REGRA DE FUSÃO (UNICIDADE): É estritamente PROIBIDO ter duas linhas da mesma categoria.
   - Cenário: O texto diz "Dieta branda" e depois "Dieta para diabetes".
   - Ação: Funda as características em uma única linha.
   - Resultado: "1. Dieta oral branda para diabetes".
   
2. O QUE INCLUIR:
   - Dietas, Suplementos (mesmo se estiverem em medicamentos) e NPP (mesmo se estiver em soluções).
   - Cuidados EXCLUSIVOS de hidratação.

3. LIMPEZA:
   - Troque ";" por " e ".
   - Padronize para Title Case na primeira letra.

# FORMATO DE SAÍDA
- Título: DIETA
- Lista numerada sequencial (iniciando em 1).
- Se uma categoria não existir, pule-a (não deixe linha vazia).

# EXEMPLO DE SAÍDA (CENÁRIO COMPLETO)
DIETA
1. Dieta oral liquidificada para diabetes e hepatopata
2. Suplemento oral hiperproteico 900 kcal
3. Hidratação via sonda 500ml a cada 8 horas
4. Dieta enteral oligomérica padrão 1000 kcal
5. Suplemento enteral hiperproteico 200 kcal
6. NPP individualizada oligomérica 1500 kcal

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# AGENTE 3: MEDICAÇÕES E SOLUÇÕES
PROMPT_AGENTE_MEDICACOES = """# ROLE
Você é um Farmacêutico Clínico Especialista em Segurança do Paciente.

# TAREFA
Extraia, Padronize e ORDENE as Medicações e Soluções.

# REGRAS DE PADRONIZAÇÃO
1. NOME: Fármaco + Concentração (Ex: Dipirona 1g).
2. DOSE: A quantidade final prescrita (Ex: 2 amp, 40mg). Não confunda com a concentração do frasco.
3. VIAS: Padronize para: Endovenoso, Intramuscular, Subcutâneo, Oral, Por Sonda, Inalatória, Retal.
4. FREQUÊNCIA:
   - "24/24h" -> converta para "1 vez ao dia".
   - Fixos: use separador " x " (Ex: 40 mg x 1 vez ao dia).
   - Se Necessário (ACM/SOS): use separador " ; " (Ex: Se Necessário).

# REGRAS DE SOLUÇÕES (SOROS/DILUENTES)
- Se houver dois volumes (ex: "Soro 250ml INJ 234ml"), escolha SEMPRE o volume de preparo (234ml) e ignore o nominal (250ml).
- Remova termos: "Base", "INJ", "Solução".

# O QUE IGNORAR (CRÍTICO)
- NÃO inclua Nutrição Parenteral (NPP) aqui. Isso pertence à Dieta.
- NÃO inclua Suplementos Nutricionais.

# ALGORITMO DE ORDENAÇÃO (OBRIGATÓRIO)
Processe tudo na memória e imprima nesta ordem estrita:

GRUPO 1: MEDICAMENTOS FIXOS (Horário agendado)
   Ordem: Endovenoso > Intramuscular > Subcutâneo > Oral > Sonda > Outros.

GRUPO 2: MEDICAMENTOS "SE NECESSÁRIO" (SOS/ACM)
   Ordem: Endovenoso > Intramuscular > Subcutâneo > Oral > Sonda > Outros.

GRUPO 3: SOLUÇÕES (Soros e Infusões Contínuas)
   Siga a mesma lógica (Fixos > SN).

# ESTRUTURA DE SAÍDA
Separe em dois blocos: MEDICAÇÕES e SOLUÇÕES.
Inicie a numeração em 1 para cada bloco.
Use quebra de linha dupla entre os blocos.

# FORMATO DE CADA LINHA
[Número]. [Nome]; [Dose]; [Via]; [Dose x Frequência ou Se Necessário]

# EXEMPLO DE SAÍDA
MEDICAÇÕES
1. Amicacina 500mg; 1 amp; Endovenoso; 1 amp x 1 vez ao dia
2. Sinvastatina 20mg; 40 mg; Oral; 40 mg x 1 vez ao dia
3. Dipirona 1g; 1 g; Endovenoso; Se Necessário

SOLUÇÕES
1. Norepinefrina 4 amp + Cloreto de Sodio 0,9% 234 ml; Endovenoso; A Critério Médico

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# ==============================================================================
# 4. PROMPTS E MODELOS (LEGADO - MANTER POR COMPATIBILIDADE)
# ==============================================================================

# ==============================================================================
# LISTA COMPLETA DE MODELOS CANDIDATOS (Todos os Gemini)
# ==============================================================================
CANDIDATOS_GEMINI = [
    # === GEMINI 2.5 (Janeiro 2026 - MAIS RECENTES) ===
    "gemini-2.5-flash",                    # RECOMENDADO: Mais rápido e recente
    "gemini-2.5-flash-preview-0205",       # Preview específico
    "gemini-2.5-flash-preview-01-17",      # Preview de janeiro
    "gemini-2.5-pro",                      # Máxima inteligência 2.5
    "gemini-2.5-pro-preview-0205",         # Preview Pro
    "gemini-2.5-pro-preview-01-17",        # Preview Pro janeiro
    "gemini-2.5-flash-thinking",           # Raciocínio avançado 2.5
    "gemini-2.5-flash-thinking-exp",       # Experimental thinking
    "gemini-2.5-flash-thinking-exp-01-21", # Experimental específico
    
    # === GEMINI 2.0 (Dezembro 2025 - Descontinuados em Fevereiro 2026) ===
    "gemini-2.0-flash",                    # Flash 2.0 padrão
    "gemini-2.0-flash-exp",                # Experimental 2.0
    "gemini-2.0-flash-thinking-exp",       # Thinking experimental 2.0
    "gemini-2.0-flash-thinking-exp-1219",  # Versão específica
    
    # === GEMINI 1.5 PRO (Estáveis - 2M tokens) ===
    "gemini-1.5-pro",                      # Pro sem sufixo (latest)
    "gemini-1.5-pro-latest",               # Última versão stable
    "gemini-1.5-pro-002",                  # Versão stable 002
    "gemini-1.5-pro-001",                  # Versão stable 001
    "gemini-1.5-pro-exp-0827",             # Experimental agosto
    "gemini-1.5-pro-exp-0801",             # Experimental agosto
    
    # === GEMINI 1.5 FLASH (Estáveis - Rápidos) ===
    "gemini-1.5-flash",                    # Flash sem sufixo (latest)
    "gemini-1.5-flash-latest",             # Última versão stable
    "gemini-1.5-flash-002",                # Versão stable 002
    "gemini-1.5-flash-001",                # Versão stable 001
    "gemini-1.5-flash-8b",                 # Versão 8B (mais leve)
    "gemini-1.5-flash-8b-latest",          # 8B latest
    "gemini-1.5-flash-8b-001",             # 8B versão 001
    "gemini-1.5-flash-8b-exp-0827",        # 8B experimental agosto
    "gemini-1.5-flash-8b-exp-0924",        # 8B experimental setembro
    "gemini-1.5-flash-exp-0827",           # Experimental agosto
    
    # === GEMINI EXPERIMENTAL (Previews e Testes) ===
    "gemini-exp-1206",                     # Experimental dezembro 2024
    "gemini-exp-1121",                     # Experimental novembro 2024
    "gemini-exp-1114",                     # Experimental novembro 2024
    "gemini-exp-1005",                     # Experimental outubro 2024
    
    # === GEMINI 1.0 (Legado - Descontinuados) ===
    "gemini-pro",                          # Pro 1.0 (legado)
    "gemini-pro-vision",                   # Vision 1.0 (legado)
    "gemini-1.0-pro",                      # 1.0 Pro explícito
    "gemini-1.0-pro-latest",               # 1.0 Pro latest
    "gemini-1.0-pro-001",                  # 1.0 Pro versão 001
    "gemini-1.0-pro-vision",               # 1.0 Vision
    "gemini-1.0-pro-vision-latest",        # 1.0 Vision latest
]

# --- PROMPT EXAMES (Lista Limpa) ---
PROMPT_EXAMES_PADRAO = """
# PROMPT MESTRE - EXTRAÇÃO DE DADOS LABORATORIAIS

ATUE COMO:
Um Pacer Especialista em Extração de Dados Laboratoriais.
Seu objetivo é processar texto bruto (PDF, OCR, fragmentos) e transformá-lo em um registro de evolução médica padronizado e conciso.

---

### 1. DIRETRIZES DE SEGURANÇA (CRÍTICO)
1. PROIBIDO INVENTAR VALORES: Se o dado não consta no texto, não o invente. Não calcule nada (exceto conversão de Leucócitos < 500).
2. IGNORAR AUSENTES (TRAVA DE SEGURANÇA): Se um biomarcador não existir no texto, ELE DEVE DESAPARECER COMPLETAMENTE DA SAÍDA.
   - REGRA DE OURO: **Sem valor = Sem Sigla.** (Ex: Se não tem CaT, não escreva "CaT". Pule direto para o próximo).
   - Não deixe espaços vazios ou pipes duplos consecutivos (ex: Errado: `Pi 3,2 | CaT | TGP`. Certo: `Pi 3,2 | TGP`).
3. FIDELIDADE: Apenas extraia números e resultados. Não copie textos descritivos ou diagnósticos.

---

### 2. ESTRUTURA DE SAÍDA (LAYOUT RÍGIDO)

A resposta deve ter exatamente duas partes:

PARTE 1: BLOCO DE CÓPIA
IMPORTANTE: O conteúdo deve ter obrigatoriamente DUAS LINHAS distintas (use `Enter` / quebra de linha):

Linha 1: [Nome do Paciente] [HC (se disponível)]
Linha 2: [Data DD/MM/AAAA] – [Sequência de Exames]

PARTE 2: LISTA DE EXCLUSÃO
Texto simples listando os nomes dos exames presentes no original que foram ignorados por não estarem na lista alvo (ex: TSH, Colesterol, Sorologias, VPM).

---

### 3. REGRAS DE FORMATAÇÃO E SEPARADORES

1. SEPARADOR PADRÃO ( | ): Use Pipe com espaços (" | ") para separar TODOS os exames individuais e grupos.
2. SEPARADOR INTERNO ( / ): Use Barra com espaços (" / ") EXCLUSIVAMENTE dentro de: Fórmula Leucocitária, URINA I e GASOMETRIA.
3. DECIMAIS: Use Vírgula (padrão PT-BR).
4. UNIDADES: Remova todas (mg/dL, U/L, etc). Mantenha apenas:
   - "%" para: Ht, Fórmula Leucocitária, SatO2, SvO2 e TP Atividade.
   - "s" para: TTPa.
5. LIMPEZA FINAL: Antes de entregar a resposta, verifique se existe alguma sigla sem número ao lado. Se houver, apague a sigla.

---

### 4. SEQUÊNCIA DE EXTRAÇÃO (ORDEM RÍGIDA)

Extraia os dados na ordem abaixo. **ATENÇÃO:** A lista abaixo é uma ordem de prioridade. Você só deve incluir o item se encontrar um valor numérico para ele.

Extraia os dados na ordem abaixo. Use " | " para separar os itens.

GRUPO 1: HEMATOLOGIA
Ordem: Hb | Ht | [Se Hb < 9,0: VCM | HCM | RDW] | Leuco (Fórmula) | Plaq
- Hb: 1 casa decimal.
- Ht: inteiro + %.
- REGRA CONDICIONAL: Se e somente se Hb < 9,0, inclua VCM, HCM e RDW (inteiros) logo após o Ht. Caso contrário, omita-os.
- Leuco: Ponto para milhar. (Se < 500, multiplique por 1.000).
- Fórmula: ([Se >0: Mielo A% / Meta B% /] Bast X% / Seg Y% / Linf Z% / Mon W% / Eos K% / Bas J%)
  * ATENÇÃO: Se houver Mielócitos ou Metamielócitos positivos (>0), insira-os no início da fórmula (antes de Bastões). Se forem zero ou não citados, omita-os.
- Plaq: Ponto para milhar.

GRUPO 2: RENAL / ELETRÓLITOS
Ordem: Cr | Ur | Na | K | Mg | Pi | CaT
- Cr: 1 casa decimal.
- Ur, Na: Inteiros.
- K, Mg, Pi, CaT: 1 casa decimal.
- **Nota:** Se faltar algum (ex: CaT), pule-o e não escreva a sigla.

GRUPO 3: HEPÁTICO
Ordem: TGP | TGO | FAL | GGT | BT (BD) | Alb | Amil | Lipas
- Enzimas: Inteiros.
- BT (BD): 1 casa decimal. Formato: Total (Direta).
- Alb: 1 casa decimal.

GRUPO 4: INFLAMATÓRIOS
Ordem: PCR | Trop
- PCR: Inteiro.
- Trop: 2 casas decimais.

GRUPO 5: COAGULAÇÃO
Ordem: TP (RNI) | TTPa (rel)
- TP: Número + s. (RNI: 1 casa decimal). Ex TP 12,2s (1,4)
- TTPa: Número + s. (rel: 1 casa decimal). Ex TTPA 10,3s (0,9)

GRUPO 6: URINA I (EAS)
Se houver dados, use esta string fixa exata com barras internas:
Urn: Leu Est: [Val] / Nit: [Val] / Leuco [Val] / Hm : [Val] / Prot: [Val] / Cet: [Val] / Glic: [Val]
- Use "Pos" (com cruzes se houver, ex: "Pos ++") ou "Neg".

GRUPO 7: GASOMETRIA 
Identifique se a gasometria é ARTERIAL, VENOSA ou MISTA (Ambas). Use barras "/" para separar os itens DENTRO do bloco da gasometria.

A. SE ARTERIAL: Prefixo: "Gas Art" Ordem: pH / pCO2 / pO2 / HCO3 / BE / SatO2 / Lac / AG / Cl / Na / K / Cai

Formatação:
pH, Cai: 2 casas decimais.

pCO2, pO2, HCO3, AG, Cl, Na: Inteiros.

BE: 1 casa decimal (Obrigatório manter sinal positivo "+" ou negativo "-").

SatO2: Inteiro + %.

Lac, K: 1 casa decimal.

B. SE VENOSA: Prefixo: "Gas Ven" Ordem: pH / pCO2 / HCO3 / BE / SvO2 / Lac / AG / Cl / Na / K / Cai

Nota: Substitua SatO2 por SvO2. Omita pO2.

Formatação: Idêntica à arterial.

C. SE MISTA (Duas gasometrias no mesmo input): Ordem: [Bloco Arterial Completo] | Gas Ven pCO2 / SvO2 
Separe os dois blocos com o pipe " | "

---

### 5. GABARITO DE CENÁRIOS (SIGA ESTES MODELOS)

Use os exemplos abaixo como molde estrito para a formatação final, respeitando a quebra de linha entre o Nome e a Data.

CENÁRIO A: APENAS GASOMETRIA ARTERIAL
(Exemplo: Hb < 9,0 com índices. Sem Mielo/Meta. Gaso Arterial Completa)

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP 14,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Neg / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Neg / Cet: Neg / Glic: Neg | Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina).

CENÁRIO B: APENAS GASOMETRIA VENOSA
(Exemplo: Hb < 9,0 com índices. Com Mielo/Meta. Gaso Venosa Completa)

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Mielo 1% / Meta 2% / Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP 14,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Pos +++ / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Pos + / Cet: Neg / Glic: Neg | Gas Ven pH 7,35 / pCO2 40 / HCO3 22 / BE -2,3 / SvO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina).

CENÁRIO C: GASOMETRIA ARTERIAL E VENOSA
(Exemplo: Hb < 9,0 com índices. Com Mielo/Meta. Gaso Arterial e Venosa Completa)

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Mielo 1% / Meta 2% / Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP 14,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Pos +++ / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Pos + / Cet: Neg / Glic: Neg | Gas Art pH 7,35 / pCO2 40 / HCO3 22 / BE -2,3 / SvO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | Gas Ven pCO2 40 / SvO2 96% 

LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina)."""

PROMPT_PRESCRICAO_PADRAO = """
# SYSTEM ROLE: PROCESSADOR DE DADOS CLÍNICOS (PACER v2.0)

## 1. OBJETIVO PRIMÁRIO
Converter prescrições médicas desestruturadas em um formato de lista rígido, ordenado e padronizado. O foco é precisão em Doses, Vias e Frequências.

## 2. REGRAS DE OURO (ZERO TOLERANCE)
1. **OUTPUT LIMPO:** Apenas o texto estruturado. Sem introduções, sem markdown de código (```), sem comentários finais.
2. **FIDELIDADE:** Nunca altere valores numéricos da dose prescrita.
3. **ORDENAÇÃO ABSOLUTA:** A falha na ordem das vias é considerada erro sistêmico.

---

## 3. ESTRUTURA DE RESPOSTA
1. CABEÇALHO
2. (Linha vazia)
3. DIETA
4. (Linha vazia)
5. MEDICAÇÕES
6. (Linha vazia)
7. SOLUÇÕES
8. (Linha vazia)

* **PROIBIDO** escrever itens na mesma linha.
* **OBRIGATÓRIO** usar uma quebra de linha (`\n`) após cada medicamento.
* O resultado deve parecer uma escada, não um texto corrido.

*Nota: A numeração dos itens deve ser contínua do início (Dieta) ao fim (Soluções).*

---

## 4. MOTOR DE REGRAS (LOGIC ENGINE)

### A. CABEÇALHO (Extração e Formatação Rigorosa)
**Template Obrigatório:**
`[Nome Completo Formatado] - [Idade] anos - [Registro] - [Leito]`
`Prescrição: [Data Início] até [Data Fim]`

**Regras de Limpeza e Formatação:**
1.  **Nome:** Identifique o nome do paciente e converta OBRIGATORIAMENTE para **Title Case** (Primeira Letra Maiúscula, o resto minúsculo).
    * *Input:* "MARIA APARECIDA DE LANES" -> *Output:* "Maria Aparecida De Lanes"
2.  **Idade:** Extraia apenas o número inteiro. Adicione o sufixo " anos".
3.  **Registro:** Busque o número do Atendimento ou Prontuário (geralmente formato `Número/Dígito`). Copie exatamente.
4.  **Leito:** Extraia apenas o código do leito (ex: "449B"). Remova rótulos como "Leito:", "Quarto:", "L:".
5.  **Datas:** Busque o campo "Validade" ou "Vigência".
    * Remova as horas (ex: "14:00 h"). Mantenha **apenas** as datas no formato DD/MM/AAAA.

**Exemplo de Saída (Gabarito):**
Maria Aparecida De Lanes - 75 anos - 1270983/0 - 449B
Prescrição: 04/12/2025 até 05/12/2025

### B. DIETA (Lógica de Unicidade e Extração Cruzada)
**Onde buscar:**
* Cabeçalhos: DIETA, CUIDADOS (apenas água), SOLUÇÕES (apenas NPP), MEDICAMENTOS (apenas suplementos).

**Estrutura Rígida (Máximo 1 item por categoria - Total máx 5 linhas):**
A saída deve seguir estritamente esta ordem. Se a categoria não existir, pule-a.
1. **Oral** (Ex: Dieta oral geral...)
2. **Suplemento** (Busque em todo o texto. Mova para cá.)
3. **Hidratação** (Água com volume definido, Água livre pela sonda.)
4. **Enteral** (Ex: Dieta enteral 1.5...)
5. **Parenteral** (NPP. Busque em Soluções e mova para cá.)

**Regras de Filtragem (Filtro Passa/Não-Passa):**
* **Regra da Hidratação:**
    * ✅ **MANTER:** Se tiver volume explícito para hidratar (ex: "500ml", "1000ml de água livre", "Água livre pela SNE").
    * ❌ **DESCARTAR:** "Água para lavagem", "Água para limpeza de sonda", "Água filtrada" (sem volume/contexto de lavagem).
* **Regra de Unicidade:** Se houver duas dietas enterais (ex: uma industrializada e uma fórmula), **junte as informações na mesma linha** para respeitar o limite de 1 item por categoria.
* **Formatação Visual:**
    * Primeira letra da frase Maiúscula.
    * Unidades (ml, kcal, g) sempre minúsculas.
    * Substitua `;` por ` para ` na descrição.

**Exemplo de Output Perfeito (Dieta):**
DIETA
Dieta oral branda para diabetes
Suplemento hiperproteico 200ml 1 vez ao dia
Água filtrada 1500ml via sonda nasoenteral
Dieta enteral polimérica 1500kcal
NPP sistema fechado 1500kcal

### C. MEDICAÇÕES (LÓGICA DE ORDENAÇÃO BLINDADA)

**FORMATO FINAL DE SAÍDA:**
Para MEDICAMENTOS FIXOS:
`N. [Nome]; [Dose]; [Via]; [Dose] x [Frequência]`

Para MEDICAMENTOS CONDICIONAIS (Se Necessário/ACM):
`N. [Nome]; [Dose]; [Via]; Se Necessário` (ou A Critério Médico)

---

#### REGRA 1: PADRONIZAÇÃO DE VIA (NORMALIZAÇÃO)
Converta qualquer termo encontrado para a lista oficial abaixo:
1. **Endovenoso** (IV, EV, Venosa)
2. **Intramuscular** (IM)
3. **Subcutâneo** (SC)
4. **Por Sonda** (SNE, SNG, Nasoenteral, GTT)
5. **Oral** (VO, Boca)
6. **Retal**
7. **Inalatória** (NBZ, Nebulização)
8. **Tópica**
9. **Oftálmica**
10. **Outras**

#### REGRA 2: TRATAMENTO DE FREQUÊNCIA
Converta a frequência escrita para o padrão técnico:
* **Menos de 24h:** Use horas (Ex: "3x ao dia" -> **8/8h** | "4x" -> **6/6h** | "2x" -> **12/12h**).
* **Exatamente 24h:** Use **1 vez ao dia** (Não use 24/24h).
* **Mais de 24h:** Mantenha os dias (Ex: "Segunda, Quarta e Sexta" ou "1 vez a cada 3 dias").

---

#### REGRA 3: ALGORITMO DE ORDENAÇÃO (CRÍTICO - ZERO TOLERANCE)
Você deve classificar cada item mentalmente antes de escrever a lista final. Siga esta hierarquia estrita:

**PASSO 1: SEGREGAR POR TIPO**
* **GRUPO A (FIXOS):** Tudo que tem horário definido. (VEM PRIMEIRO).
* **GRUPO B (CONDICIONAIS):** Tudo que é "Se Necessário", "ACM", "SOS", "Se Dor/Febre". (VEM POR ÚLTIMO).

**PASSO 2: ORDENAR DENTRO DOS GRUPOS (POR VIA)**
Dentro do Grupo A, ordene pela VIA. Depois, dentro do Grupo B, ordene pela mesma regra de VIA.
**Ordem de Precedência das Vias (Do topo para baixo):**
1.  **Endovenoso** (Prioridade Máxima)
2.  **Intramuscular**
3.  **Subcutâneo**
4.  **Por Sonda**
5.  **Oral**
6.  **Enteral**
7.  **Inalatória**
8.  **Outras** (Tópica, Oftálmica, etc)

**PASSO 3: DESEMPATE**
Se houver dois medicamentos com o mesmo Tipo e mesma Via (ex: dois Endovenosos Fixos), ordene alfabeticamente pelo Nome.

---

#### REGRA 4: GABARITO DE FORMATAÇÃO (CASE SENSITIVE)
* **Nomes:** `Dipirona` (1ª Maiúscula).
* **Unidades:** `mg`, `ml`, `amp`, `ui`, `gts` (Sempre minúsculas).
* **Vias:** `Endovenoso`, `Oral` (1ª Maiúscula).
* **Separador:** Ponto e vírgula seguido de espaço (`; `).

**EXEMPLO DE SAÍDA PERFEITA (Siga esta ordem):**
MEDICAÇÕES
1. Piperacilina 4g; 2,25 g; Endovenoso; 2,25 g x 8/8h
2. Furosemida 20mg; 2 amp; Endovenoso; 2 amp x 12/12h
3. Heparina 5.000ui; 5.000 ui; Subcutâneo; 5.000 ui x 12/12h
4. Ácido Acetilsalicílico 100mg; 100 mg; Por Sonda; 100 mg x 1 vez ao dia
5. Sinvastatina 20mg; 40 mg; Oral; 40 mg x 1 vez ao dia
6. Ipratrópio 0,25mg; 40 gts; Inalatória; 40 gts x 6/6h
7. Dipirona 1g; 1 g; Endovenoso; Se Necessário
8. Ondansetrona 8mg; 8 mg; Endovenoso; Se Necessário
9. Insulina Regular; 2 ui; Subcutâneo; Se Necessário
10. Bromoprida 10mg; 10 mg; Por Sonda; Se Necessário

*(Nota: Observe que Por Sonda (Fixo) vem antes de Oral (Fixo). E Endovenoso (Se Necessário) vem DEPOIS de todos os fixos, mas ANTES de Subcutâneo (Se Necessário)).*

### D. SOLUÇÕES (REGRA DE COMPOSIÇÃO RÍGIDA)
**FORMATO DE SAÍDA OBRIGATÓRIO:**
`N. [Soluto] + [Diluente]; [Via Padronizada]; [Fluxo ou Frequência]`

**REGRAS DE MONTAGEM:**
1.  **Concatenação com Espaços:** Use OBRIGATORIAMENTE espaço antes e depois do sinal de mais.
    * *Errado:* `Norepinefrina+Glicose`
    * *Correto:* `Norepinefrina + Glicose`
2.  **Ordem dos Fatores:** Sempre coloque o **Medicamento (Soluto)** primeiro e o **Soro/Diluente** depois.
    * *Ex:* `Norepinefrina 4 amp + Glicose 5% 250 ml`
3.  **Regra de Volume (Preparo vs Frasco):**
    * Se o texto informar o "Volume Total" ou "Volume Final" (ex: 234ml), use este valor.
    * Caso contrário, use o volume do frasco original (ex: 250 ml).
4.  **NPP (Nutrição Parenteral):**
    * Se encontrar NPP/Nutrição Parenteral aqui, **MOVA PARA A SEÇÃO DE DIETA**. Não liste em Soluções.

**PADRONIZAÇÃO VISUAL (CASE SENSITIVE):**
* **Via:** Primeira letra Maiúscula (ex: `Endovenoso`).
* **Unidades:** Minúsculas (ex: `ml`, `amp`).
* **Fluxo:** Se for ACM, escreva `A Critério Médico`. Se for contínuo com vazão, escreva ex: `10 ml/h` ou `Contínuo`.

**EXEMPLO DE SAÍDA PERFEITA (SOLUÇÕES):**
SOLUÇÕES
18. Norepinefrina 4 amp + Glicose 5% 250 ml; Endovenoso; A Critério Médico
19. Amiodarona 2 amp + Glicose 5% 250 ml; Endovenoso; 10 ml/h
20. Polivitamínico 1 fr + Soro Fisiológico 0,9% 100 ml; Endovenoso; 1 vez ao dia

Nota: Medicamento Proprio Do Paciente : Ornitina Sache, excluir "Medicamento Proprio Do Paciente : ", manter apenas o medicamento.

---

## 5. CASO PARA REFERÊNCIA INPUT/OUPUT DESEJADO 

INPUT
Validade: de 04/12/2025 14:00 h. a 05/12/2025 14:00 h.
PRESCRIÇÃO MÉDICA
** Reimpressão **
DIETA
DESCRIÇÃO VIA FREQUÊNCIA APRAZAMENTO
1. LIQUIDIFICADA;DIABETES Oral
CUIDADOS
DESCRIÇÃO FREQUÊNCIA APRAZAMENTO
2. CABECEIRA ELEVADA A 30 GRAUS contínuo
3. CONTROLE DE DIURESE 6/6 HORAS
4. CONTROLE DE SINAIS VITAIS 6/6 HORAS
5. GLICEMIA CAPILAR - HGT ANTES DAS
REFEIÇÕES/22 H
6. MONITORIZAÇÃO CARDÍACA CONTÍNUA contínuo
MEDICAMENTOS
DESCRIÇÃO DOSE VELOC. INF. VIA FREQUÊNCIA CONDIÇÃO APRAZAMENTO
7. Acido Acetilsalicilico CMP 100 mg 100 mg Por Sonda 24/24
HORAS;
Fixo
8. DipiRONA INJ (1g) 500 mg/mL
Obs.: Em caso de dor ou febre.
1 g Endovenosa 6/6 HORAS; Se
Necessário
9. Escopolamina INJ (Hioscina) 20
mg/mL
20 mg Endovenosa 12/12
HORAS;
Fixo
Identificação
04/12/2025,20:21:21
Leito: 449B 1270983/0
MARIA APARECIDA DE LANES
Idade:75 anos, 9 meses e 26 dias
Página 1/3
Local: Prontuário:
Paciente:
Data de Nascimento: 08/02/1950
PRESCRIÇÃO MÉDICA
Validade: de 04/12/2025 14:00 h. a 05/12/2025 14:00 h.
PRESCRIÇÃO MÉDICA
** Reimpressão **
MEDICAMENTOS
DESCRIÇÃO DOSE VELOC. INF. VIA FREQUÊNCIA CONDIÇÃO APRAZAMENTO
10. Furosemida INJ (20mg) 10 mg/mL 2 AMP Endovenosa 8/8 HORAS; Fixo
11. Glicose 50% INJ 10 mL
Obs.: SE DEXTRO < 70
20 mL Endovenosa A CRITÉRIO MÉDICO; Se Necessário
12. HEParina SC 5.000 UI 5.000 UI Subcutânea 12/12
HORAS;
Fixo
13. HidrALAZINA CMP 25 mg 25 mg Oral 8/8 HORAS; Fixo
14. Ipratropio GTS 0,25 mg/mL 40 gts Inalatória 12/12
HORAS;
Fixo
15. LevoTIROXina CMP 25 mcg
Obs.: Em jejum.
25 mcg Oral MANHÃ; Fixo
16. NOREPinefrina Base 4mg/4mL
Inj 1 mg/mL
Diluir em Glicose 5% 250mL INJ;
Obs.: ACM
4 AMP Endovenosa A CRITÉRIO MÉDICO; Se Necessário
17. Ondansetrona INJ (8mg) 2 mg/mL
Obs.: Se náusea ou vômitos.
8 mg Endovenosa 8/8 HORAS; Se
Necessário
18. Piperacilina 4g + Tazobactam 0,5g
Inj
2,25 g Endovenosa 8/8 HORAS; Fixo
19. Piperacilina 4g + Tazobactam 0,5g
Inj
Obs.: Dose pós diálise
0,75 g Endovenosa A CRITÉRIO MÉDICO; Se Necessário
Identificação
04/12/2025,20:21:21
Leito: 449B 1270983/0
MARIA APARECIDA DE LANES
Idade:75 anos, 9 meses e 26 dias
Página 2/3
Local: Prontuário:
Paciente:
Data de Nascimento: 08/02/1950
PRESCRIÇÃO MÉDICA
Validade: de 04/12/2025 14:00 h. a 05/12/2025 14:00 h.
PRESCRIÇÃO MÉDICA
** Reimpressão **
MEDICAMENTOS
DESCRIÇÃO DOSE VELOC. INF. VIA FREQUÊNCIA CONDIÇÃO APRAZAMENTO
20. Sacarato de Hidróxido Ferrico INJ
(100mg) 20 mg/mL
Obs.: Aplicações em 01/12, 03/12,
05/12, 07/12, 09/12. Após 09/12
suspender
2 AMP Endovenosa 48/48
HORAS;
Fixo
21. Simeticona GTS 75 mg/mL 40 gts Oral 8/8 HORAS; Fixo
22. Sinvastatina CMP 20 mg 40 mg Oral noite; Fixo
Dr. GABRIEL VALLADAO VICINO CRM: 223216
Identificação
04/12/2025,20:21:21
Leito: 449B 1270983/0
MARIA APARECIDA DE LANES
Idade:75 anos, 9 meses e 26 dias
Página 3/3
Local: Prontuário:
Paciente:
Data de Nascimento: 08/02/1950
PRESCRIÇÃO MÉDICA

GABARITO:

Maria Aparecida De Lanes - 75 anos - 1270983/0 - 449B
Prescrição: 04/12/2025 até 05/12/2025

DIETA
1. Dieta oral liquidificada para diabetes


MEDICAÇÕES
2. Escopolamina 20mg/ml Inj; 20 mg; Endovenoso; 20 mg x 12/12h
3. Furosemida 20mg Inj; 2 amp; Endovenoso; 2 amp x 8/8h
4. Piperacilina 4g + Tazobactam 0,5g Inj; 2,25 g; Endovenoso; 2,25 g x 8/8h
5. Sacarato de Hidróxido Férrico 100mg Inj; 2 amp; Endovenoso; 2 amp x a cada 2 dias
6. Heparina 5.000ui; 5.000 ui; Subcutâneo; 5.000 ui x 12/12h
7. Hidralazina 25mg Cp; 25 mg; Oral; 25 mg x 8/8h
8. Levotiroxina 25mcg Cp; 25 mcg; Oral; 25 mcg x 1 vez ao dia
9. Simeticona 75mg/ml Gts; 40 gts; Oral; 40 gts x 8/8h
10. Sinvastatina 20mg Cp; 40 mg; Oral; 40 mg x 1 vez ao dia
11. Ácido Acetilsalicílico 100mg Cp; 100 mg; Oral; 100 mg x 1 vez ao dia
12. Ipratrópio 0,25mg/ml Gts; 40 gts; Inalatória; 40 gts x 12/12h
13. Dipirona 1g Inj; 1 g; Endovenoso; Se Necessário
14. Glicose 50% Inj; 20 ml; Endovenoso; Se Necessário
15. Norepinefrina 4mg/4ml Inj; 4 amp; Endovenoso; Se Necessário
16. Ondansetrona 8mg Inj; 8 mg; Endovenoso; Se Necessário
17. Piperacilina 4g + Tazobactam 0,5g Inj; 0,75 g; Endovenoso; Se Necessário

SOLUÇÕES
18. Norepinefrina 4 amp + Glicose 5% 234 ml; Endovenoso; A Critério Médico
"""


# ==============================================================================
# 3. FUNÇÕES DE PROCESSAMENTO
# ==============================================================================

def processar_multi_agente(api_source, api_key, model_name, agentes_selecionados, input_text, executar_analise=True):
    """
    Processa o texto usando múltiplos agentes especializados EM PARALELO.
    
    Fluxo:
    1. Chama o agente de IDENTIFICAÇÃO (sempre, sequencial)
    2. Chama os agentes SELECIONADOS SIMULTANEAMENTE (paralelo)
    3. Concatena os resultados com " | "
    4. Opcionalmente executa análise clínica (sequencial)
    
    Args:
        api_source: "Google Gemini" ou "OpenAI GPT"
        api_key: Chave da API
        model_name: Nome do modelo (use gpt-4o para máxima precisão)
        agentes_selecionados: Lista de IDs dos agentes (ex: ["hematologia_renal", "hepatico"])
        input_text: Texto de entrada
        executar_analise: Se True, executa Agente 6 (análise clínica). Default: True
    
    Returns:
        Tupla: (resultado_exames, analise_clinica)
    """
    if not input_text:
        return "⚠️ O campo de entrada está vazio.", ""
    if not api_key:
        return f"⚠️ Configure a chave de API do {api_source}.", ""
    if not agentes_selecionados:
        return "⚠️ Selecione pelo menos um agente.", ""
    
    tempo_inicio = time.time()
    
    # PRÉ-PROCESSAMENTO CONSERVADOR (Remove apenas redundâncias)
    print("[PRÉ-PROC] Aplicando pré-processamento conservador...")
    input_text_limpo = preprocessar_texto_exames(input_text)
    
    # PASSO 1: Extrair identificação (SEMPRE - SEQUENCIAL)
    try:
        resultado_identificacao = processar_texto(
            api_source, api_key, model_name, 
            PROMPT_AGENTE_IDENTIFICACAO, 
            input_text_limpo  # Usa texto pré-processado
        )
        
        # Verifica se houve erro
        if "❌" in resultado_identificacao or "⚠️" in resultado_identificacao:
            return resultado_identificacao, ""
        
        # Parseia o resultado (2 linhas)
        linhas = resultado_identificacao.strip().split('\n')
        if len(linhas) < 2:
            return "❌ Erro ao extrair identificação. Verifique o texto de entrada.", ""
        
        nome_hc = linhas[0].strip()  # Ex: "Carlos Eduardo Souza 9876543"
        data_linha = linhas[1].strip()  # Ex: "29/12/2025 –"
        
    except Exception as e:
        return f"❌ Erro no agente de identificação: {str(e)}", ""
    
    # PASSO 2: Processar agentes selecionados EM PARALELO ⚡
    print(f"\n[PARALELO] Iniciando processamento de {len(agentes_selecionados)} agentes simultaneamente...")
    
    exames_concatenados = []
    
    def processar_agente_worker(agente_id):
        """Worker para processar um agente em thread separada"""
        if agente_id not in AGENTES_EXAMES:
            return None
        
        agente = AGENTES_EXAMES[agente_id]
        prompt = agente["prompt"]
        
        try:
            inicio_agente = time.time()
            # Usa input_text do escopo externo (já pré-processado)
            resultado = processar_texto(api_source, api_key, model_name, prompt, input_text_limpo)
            tempo_agente = time.time() - inicio_agente
            
            print(f"[PARALELO] Agente '{agente['nome']}' concluído em {tempo_agente:.1f}s")
            
            # Ignora erros, strings vazias, e palavras como "VAZIO"
            if resultado and "❌" not in resultado and "⚠️" not in resultado:
                resultado_limpo = resultado.strip()
                # Remove pontuação do final para comparação
                resultado_sem_pontuacao = resultado_limpo.rstrip('.,:;!? ')
                # Filtra strings vazias ou que contenham apenas "VAZIO" (qualquer variação)
                if resultado_limpo and resultado_sem_pontuacao.upper() != "VAZIO":
                    return resultado_limpo
        
        except Exception as e:
            print(f"[PARALELO] Erro no agente '{agente_id}': {str(e)}")
            return None
        
        return None
    
    # Executa agentes em paralelo com ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as executor:
        # Cria tarefas para todos os agentes
        future_to_agente = {
            executor.submit(processar_agente_worker, agente_id): agente_id 
            for agente_id in agentes_selecionados
        }
        
        # Coleta resultados conforme terminam (em dicionário para preservar ordem)
        resultados_dict = {}
        for future in as_completed(future_to_agente):
            agente_id = future_to_agente[future]
            try:
                resultado = future.result(timeout=60)  # Timeout de 60s por agente
                if resultado:
                    resultados_dict[agente_id] = resultado
            except Exception as e:
                print(f"[PARALELO] Exceção ao processar agente '{agente_id}': {str(e)}")
    
    # IMPORTANTE: Ordena resultados pela ordem FIXA dos agentes (não por conclusão)
    # Mantém a ordem: Hematologia/Renal > Gastro > Cardio/Coag > Urina > Gasometria
    for agente_id in agentes_selecionados:
        if agente_id in resultados_dict:
            exames_concatenados.append(resultados_dict[agente_id])
    
    tempo_extracao = time.time() - tempo_inicio
    print(f"[PARALELO] Extração completa em {tempo_extracao:.1f}s (vs ~15s sequencial)")
    print(f"[PARALELO] Agentes com dados: {len(exames_concatenados)}/{len(agentes_selecionados)}")
    
    # PASSO 3: Montar resultado final dos exames
    if exames_concatenados:
        # Filtra novamente para garantir que não há "Vazio" na concatenação final
        exames_filtrados = [
            ex for ex in exames_concatenados 
            if ex.strip().rstrip('.,:;!? ').upper() != "VAZIO"
        ]
        if exames_filtrados:
            resultado_exames = f"{nome_hc}\n{data_linha} " + " | ".join(exames_filtrados)
        else:
            resultado_exames = f"{nome_hc}\n{data_linha} (Nenhum dado laboratorial encontrado)"
    else:
        resultado_exames = f"{nome_hc}\n{data_linha} (Nenhum dado laboratorial encontrado)"
    
    # PASSO 4: Análise clínica (AGENTE 6) - OPCIONAL
    analise_clinica = ""
    if executar_analise and exames_concatenados:
        try:
            print(f"[DEBUG] Executando Agente 6 (Análise Clínica) com {model_name}...")
            
            inicio_analise = time.time()
            analise_clinica = processar_texto(
                api_source, api_key, model_name,
                PROMPT_AGENTE_ANALISE,
                resultado_exames  # INPUT: resultado dos agentes 0-5
            )
            tempo_analise = time.time() - inicio_analise
            print(f"[DEBUG] Análise concluída em {tempo_analise:.1f}s")
            
            # Debug: log do resultado
            print(f"[DEBUG] Análise Clínica retornada (primeiros 200 chars): {analise_clinica[:200] if analise_clinica else 'VAZIO'}")
            
            # Se houver erro explícito, mantém vazio
            if "❌" in analise_clinica or "⚠️" in analise_clinica:
                print(f"[DEBUG] Análise com erro, limpando: {analise_clinica}")
                analise_clinica = ""
            elif not analise_clinica or analise_clinica.strip() == "":
                print("[DEBUG] Análise retornou vazia!")
                analise_clinica = ""
        except Exception as e:
            print(f"[DEBUG] Exceção no Agente 6: {str(e)}")
            analise_clinica = ""
    elif not executar_analise:
        print("[DEBUG] Agente 6 desabilitado pelo usuário")
    else:
        print("[DEBUG] exames_concatenados está vazio, não processando Agente 6")
    
    print(f"[DEBUG] Análise final tem {len(analise_clinica)} caracteres")
    
    # Retorna tupla: (exames, análise)
    return resultado_exames, analise_clinica


def processar_multi_agente_prescricao(api_source, api_key, model_name, input_text):
    """
    Processa prescrição usando 3 agentes especializados.
    
    Fluxo:
    1. Agente 1: Identificação (Nome, Idade, Registro, Leito, Datas)
    2. Agente 2: Dieta (Oral, Enteral, Parenteral, Suplementos, Hidratação)
    3. Agente 3: Medicações e Soluções (ordenadas por via e tipo)
    
    Retorna: string completa da prescrição formatada
    """
    # Validações
    if not input_text:
        return "⚠️ O campo de entrada está vazio."
    if not api_key:
        return f"⚠️ Configure a chave de API do {api_source}."
    
    # PASSO 1: Extrair identificação (SEMPRE)
    try:
        resultado_identificacao = processar_texto(
            api_source, api_key, model_name, 
            PROMPT_AGENTE_IDENTIFICACAO_PRESCRICAO, 
            input_text
        )
        
        # Verifica se houve erro
        if "❌" in resultado_identificacao or "⚠️" in resultado_identificacao:
            return resultado_identificacao
        
        identificacao_completa = resultado_identificacao.strip()
        
    except Exception as e:
        return f"❌ Erro no agente de identificação: {str(e)}"
    
    # PASSO 2: Extrair Dieta
    resultado_dieta = ""
    try:
        dieta_raw = processar_texto(api_source, api_key, model_name, PROMPT_AGENTE_DIETA, input_text)
        
        # Ignora erros e strings vazias
        if dieta_raw and "❌" not in dieta_raw and "⚠️" not in dieta_raw:
            dieta_limpa = dieta_raw.strip()
            if dieta_limpa and dieta_limpa.upper() != "VAZIO":
                # O prompt já retorna "DIETA" no início, não precisa adicionar
                resultado_dieta = dieta_limpa
    
    except Exception:
        pass  # Ignora erros na dieta
    
    # PASSO 3: Extrair Medicações e Soluções
    resultado_medicacoes = ""
    try:
        med_raw = processar_texto(api_source, api_key, model_name, PROMPT_AGENTE_MEDICACOES, input_text)
        
        # Ignora erros e strings vazias
        if med_raw and "❌" not in med_raw and "⚠️" not in med_raw:
            med_limpa = med_raw.strip()
            if med_limpa and med_limpa.upper() != "VAZIO":
                resultado_medicacoes = med_limpa
    
    except Exception:
        pass  # Ignora erros nas medicações
    
    # PASSO 4: Montar resultado final
    partes = [identificacao_completa]
    
    if resultado_dieta:
        partes.append("\n" + resultado_dieta)
    
    if resultado_medicacoes:
        partes.append("\n" + resultado_medicacoes)
    
    # Se não houver dieta nem medicações
    if not resultado_dieta and not resultado_medicacoes:
        partes.append("\n(Nenhum dado de prescrição encontrado)")
    
    return "\n".join(partes)


def verificar_modelos_ativos(api_key):
    modelos_validos = []
    genai.configure(api_key=api_key)
    status_msg = st.empty()
    for modelo in CANDIDATOS_GEMINI:
        status_msg.text(f"Testando: {modelo}...")
        try:
            m = genai.GenerativeModel(modelo)
            m.generate_content("Oi")
            modelos_validos.append(modelo)
        except Exception:
            pass      
    status_msg.empty()
    return modelos_validos

def preprocessar_texto_exames(texto):
    """
    Pré-processamento CONSERVADOR: Remove apenas redundâncias óbvias.
    Mantém TODOS os dados clínicos intactos.
    """
    if not texto:
        return texto
    
    # Lista de padrões SEGUROS para remover (repetitivos e sem valor clínico)
    padroes_remover = [
        # Rodapés repetitivos
        '"Todo teste laboratorial deve ser correlacionado com o quadro clínico',
        'sem o qual a interpretação do resultado é apenas relativa',
        'Impressão do Laudo:',
        'Conferência por Vídeo',
        # Endereços/contatos repetitivos
        'Rua Rua Vital Brasil',
        'CIDADE UNIVERSITÁRIA',
        'Campinas, SP - Brasil',
        'CNPJ 46.068.425',
        'Telefone (55)(19)',
        'homepage: HTTPS://WWW.HC.UNICAMP.BR/',
        'email: null',
        'Caixa Postal null',
        # Cabeçalhos genéricos repetidos
        'LABORATÓRIO DE PATOLOGIA CLÍNICA',
        'Chefe de Serviço: EDER DE CARVALHO PINCINATO CRF: 23811',
    ]
    
    texto_processado = texto
    
    # Remove padrões CONSERVADORAMENTE (linha inteira se contiver)
    linhas = texto.split('\n')
    linhas_filtradas = []
    
    for linha in linhas:
        # Mantém linha se NÃO contiver nenhum padrão de remoção
        linha_limpa = linha.strip()
        
        # Se linha vazia, pula
        if not linha_limpa:
            continue
            
        # Verifica se contém padrões a remover
        deve_remover = False
        for padrao in padroes_remover:
            if padrao.lower() in linha_limpa.lower():
                deve_remover = True
                break
        
        # Mantém linha se não for para remover
        if not deve_remover:
            linhas_filtradas.append(linha)
    
    texto_processado = '\n'.join(linhas_filtradas)
    
    # Remove múltiplas linhas vazias consecutivas (mantém estrutura)
    while '\n\n\n' in texto_processado:
        texto_processado = texto_processado.replace('\n\n\n', '\n\n')
    
    # Log de redução (opcional)
    reducao = len(texto) - len(texto_processado)
    if reducao > 0:
        pct = (reducao / len(texto)) * 100
        print(f"[PRÉ-PROC] Redução: {reducao} chars ({pct:.1f}%) - DADOS CLÍNICOS INTACTOS")
    
    return texto_processado.strip()

def processar_texto(api_source, api_key, model_name, prompt_system, input_text):
    if not input_text: return "⚠️ O campo de entrada está vazio."
    if not api_key: return f"⚠️ Configure a chave de API do {api_source}."

    try:
        if api_source == "Google Gemini":
            genai.configure(api_key=api_key)
            generation_config = {"temperature": 0.0, "top_p": 1.0, "top_k": 1}
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config, system_instruction=prompt_system)
            response = model.generate_content(input_text)
            return response.text

        elif api_source == "OpenAI GPT":
            client = OpenAI(api_key=api_key)
            
            # Otimizações da API OpenAI (mantém qualidade)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": prompt_system}, 
                    {"role": "user", "content": input_text}
                ],
                temperature=0.0,        # Determinístico (já estava)
                top_p=0.1,              # Foco nas respostas mais prováveis
                frequency_penalty=0.0,  # Sem penalidade (dados médicos)
                presence_penalty=0.0,   # Sem penalidade (dados médicos)
                max_tokens=2000,        # Limite adequado para extração
                seed=42                 # Reprodutibilidade (GPT-4o suporta)
            )
            return response.choices[0].message.content
            
    except Exception as e:
        return f"❌ Erro na API: {str(e)}"

def limpar_campos(lista_chaves):
    for chave in lista_chaves:
        if chave in st.session_state: st.session_state[chave] = ""

# ==============================================================================
# 4. INTERFACE
# ==============================================================================

if "pacer_google_key" not in st.session_state: st.session_state.pacer_google_key = ""
if "pacer_openai_key" not in st.session_state: st.session_state.pacer_openai_key = ""
# Inicializa lista com modelos Gemini 2.5 (MAIS RECENTES)
if "lista_modelos_validos" not in st.session_state: 
    st.session_state.lista_modelos_validos = [
        "gemini-2.5-flash",              # RECOMENDADO: Mais rápido
        "gemini-2.5-pro",                # Máxima qualidade
        "gemini-2.5-flash-thinking",     # Raciocínio avançado
        "gemini-1.5-pro-002"             # Maior contexto
    ]

st.header("📃 Pacer - Exames & Prescrição")

# Carrega chaves do .env (local) ou Streamlit Secrets (cloud)
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass

def _carregar_chave_pacer(nome_secret: str, nome_env: str) -> str:
    try:
        if hasattr(st, "secrets") and nome_secret in st.secrets:
            return st.secrets[nome_secret]
    except Exception:
        pass
    return os.getenv(nome_env, "")

OPENAI_API_KEY = _carregar_chave_pacer("OPENAI_API_KEY", "OPENAI_API_KEY")
GOOGLE_API_KEY = _carregar_chave_pacer("GOOGLE_API_KEY", "GOOGLE_API_KEY")

MODELOS_GEMINI_PACER = ["gemini-2.5-flash", "gemini-2.5-pro"]

with st.sidebar:
    st.header("Configurações")

    provider = st.radio("IA:", ["OpenAI GPT", "Google Gemini"], index=0)

    if provider == "OpenAI GPT":
        motor_escolhido  = "OpenAI GPT"
        modelo_escolhido = "gpt-4o"
        api_key          = OPENAI_API_KEY
        st.success("IA: OpenAI - GPT-4o")
        if api_key and len(api_key) > 10:
            st.success(f"✅ API Key: ...{api_key[-8:]}")
        else:
            st.error("❌ API Key não carregada!")

    else:  # Google Gemini
        motor_escolhido  = "Google Gemini"
        api_key          = GOOGLE_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
        modelo_escolhido = st.selectbox("Modelo:", MODELOS_GEMINI_PACER, index=0)
        st.success(f"IA: Google - {modelo_escolhido}")
        if api_key and len(api_key) > 10:
            st.success(f"✅ API Key: ...{api_key[-8:]}")
        else:
            st.error("❌ API Key não carregada!")

# Função de renderização principal
def render_interface_colunas(titulo, key_input, key_output, prompt_atual, usar_markdown=True):
    st.subheader(titulo)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("**Entrada**")
        input_val = st.text_area("Cole aqui:", height=300, key=key_input, label_visibility="collapsed")
        
        c_b1, c_b2 = st.columns([1, 3])
        with c_b1: st.button("Limpar", key=f"clr_{key_input}", on_click=limpar_campos, args=([key_input, key_output],))
        with c_b2: processar = st.button("✨ Processar", key=f"proc_{key_input}", type="primary", use_container_width=True)

    with col2:
        st.markdown("**Resultado**")
        if processar:
            with st.spinner("Processando..."):
                resultado = processar_texto(
                    motor_escolhido,
                    api_key,
                    modelo_escolhido,
                    prompt_atual,
                    input_val
                )
                st.session_state[key_output] = resultado
        
        # EXIBIÇÃO DO RESULTADO
        if key_output in st.session_state and st.session_state[key_output]:
             res = st.session_state[key_output]
             if "❌" in res or "⚠️" in res:
                 st.error(res)
             else:
                 if usar_markdown:
                     # Mostra Markdown renderizado
                     st.markdown(res)
                 else:
                     # Mostra CAIXA DE CÓDIGO (Texto puro, botão de copiar)
                     st.code(res, language="text")
        else:
             st.info("Aguardando entrada...")

# Inicializa checkbox de análise no session_state (ANTES DAS TABS)
if "usar_analise" not in st.session_state:
    st.session_state.usar_analise = True

# Abas
tab1, tab2 = st.tabs(["🧪 Exames", "💊 Prescrição"])

with tab1:
    st.subheader("🧪 Pacer - Exames Laboratoriais")
    
    # TODOS OS AGENTES SEMPRE ATIVOS (SEM OPÇÃO DE SELEÇÃO)
    agentes_ativos = list(AGENTES_EXAMES.keys())
    
    # COLUNAS DE INPUT/OUTPUT
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("**Entrada**")
        input_val = st.text_area("Cole aqui:", height=300, key="input_exames", label_visibility="collapsed")
        
        c_b1, c_b2 = st.columns([1, 3])
        with c_b1:
            st.button("Limpar", key="clr_input_exames", on_click=limpar_campos, args=(["input_exames", "output_exames", "output_analise"],))
        with c_b2:
            processar = st.button("✨ Processar", key="proc_input_exames", type="primary", use_container_width=True)
    
    with col2:
        st.markdown("**Resultado dos Exames**")
        if processar:
            # Define mensagem do spinner baseado em usar_analise
            if st.session_state.usar_analise:
                msg_spinner = "Processando exames laboratoriais..."
            else:
                msg_spinner = "Processando exames laboratoriais..."
            
            with st.spinner(msg_spinner):
                # USA A NOVA FUNÇÃO MULTI-AGENTE COM TODOS OS AGENTES
                # GPT-4o para TUDO (máxima precisão, paralelização mantém velocidade)
                resultado_exames, analise_clinica = processar_multi_agente(
                    motor_escolhido,
                    api_key,
                    modelo_escolhido,
                    agentes_ativos,  # TODOS OS AGENTES SEMPRE
                    input_val,
                    executar_analise=st.session_state.usar_analise
                )
                st.session_state["output_exames"] = resultado_exames
                st.session_state["output_analise"] = analise_clinica if st.session_state.usar_analise else ""
                
                # Debug: mostra informação no terminal
                print(f"\n[INFO] Processamento concluído:")
                print(f"  - Resultado exames: {len(resultado_exames)} chars")
                print(f"  - Análise clínica: {len(analise_clinica) if analise_clinica else 0} chars")
                print(f"  - Análise ativada: {st.session_state.usar_analise}")
                print(f"  - Análise tem conteúdo: {bool(analise_clinica and len(analise_clinica.strip()) > 0)}\n")
        
        # EXIBIÇÃO DO RESULTADO DOS EXAMES
        if "output_exames" in st.session_state and st.session_state["output_exames"]:
            res = st.session_state["output_exames"]
            if "❌" in res or "⚠️" in res:
                st.error(res)
            else:
                st.code(res, language="text")
        else:
            st.info("Aguardando entrada...")
        
        # CHECKBOX DE ANÁLISE CLÍNICA - LOGO ABAIXO DO RESULTADO
        st.divider()
        st.session_state.usar_analise = st.checkbox(
            "🩺 Mostrar Análise Clínica (CDSS)", 
            value=st.session_state.usar_analise,
            help="Gera hipóteses diagnósticas baseadas nos exames alterados"
        )
        
        # SEÇÃO DE ANÁLISE CLÍNICA (AGENTE 6) - APARECE SE CHECKBOX MARCADO
        if st.session_state.usar_analise:
            if "output_analise" in st.session_state:
                analise = st.session_state["output_analise"]
                
                if analise and len(analise.strip()) > 0:
                    # Tem conteúdo
                    if "❌" in analise or "⚠️" in analise:
                        st.error(analise)
                    else:
                        # Mostra análise em markdown para formatação bonita
                        st.markdown(analise)
                else:
                    # Vazio ou não processou
                    st.info("Aguardando processamento ou sem dados alterados para análise.")
            elif "output_exames" in st.session_state and st.session_state["output_exames"]:
                # Exames foram processados mas análise não apareceu em session_state
                st.warning("⚠️ Análise clínica não foi gerada. Verifique o terminal para logs de debug.")

with tab2:
    st.subheader("💊 Pacer - Prescrição Médica")
    
    # COLUNAS DE INPUT/OUTPUT
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("**Entrada**")
        input_val = st.text_area("Cole aqui:", height=300, key="input_presc", label_visibility="collapsed")
        
        c_b1, c_b2 = st.columns([1, 3])
        with c_b1:
            st.button("Limpar", key="clr_input_presc", on_click=limpar_campos, args=(["input_presc", "output_presc"],))
        with c_b2:
            processar = st.button("✨ Processar", key="proc_input_presc", type="primary", use_container_width=True)
    
    with col2:
        st.markdown("**Resultado da Prescrição**")
        if processar:
            with st.spinner("Processando prescrição..."):
                # USA A NOVA FUNÇÃO MULTI-AGENTE COM 3 AGENTES
                resultado_prescricao = processar_multi_agente_prescricao(
                    motor_escolhido,
                    api_key,
                    modelo_escolhido,
                    input_val
                )
                st.session_state["output_presc"] = resultado_prescricao
        
        # EXIBIÇÃO DO RESULTADO DA PRESCRIÇÃO
        if "output_presc" in st.session_state and st.session_state["output_presc"]:
            res = st.session_state["output_presc"]
            if "❌" in res or "⚠️" in res:
                st.error(res)
            else:
                st.code(res, language="text")
        else:
            st.info("Aguardando entrada...")

# Rodapé com nota legal
mostrar_rodape()