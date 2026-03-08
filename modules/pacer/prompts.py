# ==============================================================================
# modules/pacer/prompts.py
# Fonte única de todos os prompts do PACER.
#
# Prompts compartilhados com o Bloco 10 (Evolução Diária) ficam em
# modules/extrator_exames.py — edite lá para refletir em ambos os lugares.
# ==============================================================================

from modules.extrator_exames import (
    PROMPT_AGENTE_IDENTIFICACAO,
    PROMPT_AGENTE_HEMATOLOGIA_RENAL,
    PROMPT_AGENTE_HEPATICO,
    PROMPT_AGENTE_COAGULACAO,
    PROMPT_AGENTE_URINA,
    PROMPT_AGENTE_GASOMETRIA,
    PROMPT_AGENTE_NAO_TRANSCRITOS,
    PROMPT_AGENTE_IDENTIFICACAO_PRESCRICAO,
    PROMPT_AGENTE_DIETA,
    PROMPT_AGENTE_MEDICACOES,
)

# ==============================================================================
# AGENTE 6 — Analista de Hipóteses Diagnósticas (exclusivo do PACER)
# ==============================================================================
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
# DICIONÁRIO DE AGENTES — configuração dos 6 agentes de extração de exames
# ==============================================================================
AGENTES_EXAMES = {
    "hematologia_renal": {
        "nome": "🔵 Hematologia + Renal",
        "descricao": "Hemograma completo + Função Renal + Eletrólitos",
        "prompt": PROMPT_AGENTE_HEMATOLOGIA_RENAL,
        "ativado_default": True,
    },
    "hepatico": {
        "nome": "🟡 Função Hepática",
        "descricao": "TGP, TGO, FAL, GGT, BT, Alb, Amil, Lipas",
        "prompt": PROMPT_AGENTE_HEPATICO,
        "ativado_default": True,
    },
    "coagulacao": {
        "nome": "🟠 Coagulação + Inflamatórios",
        "descricao": "PCR, CPK, Trop, TP, TTPa",
        "prompt": PROMPT_AGENTE_COAGULACAO,
        "ativado_default": True,
    },
    "urina": {
        "nome": "🟣 Urina I (EAS)",
        "descricao": "Exame de Urina Completo",
        "prompt": PROMPT_AGENTE_URINA,
        "ativado_default": True,
    },
    "gasometria": {
        "nome": "🔴 Gasometria",
        "descricao": "Gas Arterial, Venosa ou Mista",
        "prompt": PROMPT_AGENTE_GASOMETRIA,
        "ativado_default": True,
    },
    "nao_transcritos": {
        "nome": "🔍 Não Transcritos",
        "descricao": "Exames presentes no texto que não foram capturados pelos demais agentes",
        "prompt": PROMPT_AGENTE_NAO_TRANSCRITOS,
        "ativado_default": True,
    },
}

# ==============================================================================
# LISTA COMPLETA DE MODELOS GEMINI — usada por verificar_modelos_ativos()
# ==============================================================================
CANDIDATOS_GEMINI = [
    # === GEMINI 2.5 (Janeiro 2026 - MAIS RECENTES) ===
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-0205",
    "gemini-2.5-flash-preview-01-17",
    "gemini-2.5-pro",
    "gemini-2.5-pro-preview-0205",
    "gemini-2.5-pro-preview-01-17",
    "gemini-2.5-flash-thinking",
    "gemini-2.5-flash-thinking-exp",
    "gemini-2.5-flash-thinking-exp-01-21",
    # === GEMINI 2.0 ===
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-thinking-exp",
    "gemini-2.0-flash-thinking-exp-1219",
    # === GEMINI 1.5 PRO ===
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    "gemini-1.5-pro-002",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-exp-0827",
    "gemini-1.5-pro-exp-0801",
    # === GEMINI 1.5 FLASH ===
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash-8b-latest",
    "gemini-1.5-flash-8b-001",
    "gemini-1.5-flash-8b-exp-0827",
    "gemini-1.5-flash-8b-exp-0924",
    "gemini-1.5-flash-exp-0827",
    # === GEMINI EXPERIMENTAL ===
    "gemini-exp-1206",
    "gemini-exp-1121",
    "gemini-exp-1114",
    "gemini-exp-1005",
    # === GEMINI 1.0 (Legado) ===
    "gemini-pro",
    "gemini-pro-vision",
    "gemini-1.0-pro",
    "gemini-1.0-pro-latest",
    "gemini-1.0-pro-001",
    "gemini-1.0-pro-vision",
    "gemini-1.0-pro-vision-latest",
]

# Modelos exibidos no seletor da sidebar
MODELOS_GEMINI_PACER = ["gemini-2.5-flash", "gemini-2.5-pro"]
