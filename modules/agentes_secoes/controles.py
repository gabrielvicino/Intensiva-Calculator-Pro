from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 13: CONTROLES & BALANÇO HÍDRICO
# ==============================================================================
#
# Responsabilidade:
#   Receber o texto colado pelo usuário no campo "controles_notas" e extrair,
#   em formato JSON estruturado, os sinais vitais (PAS, PAD, PAM, FC, FR,
#   SatO2, Temperatura, Glicemia/Dextro), Diurese e Balanço Hídrico de até
#   10 dias de evolução.
#
# Regras gerais de extração:
#   1. ORDEM DE APARIÇÃO: o 1º bloco de data encontrado → ctrl_hoje;
#      o 2º → ctrl_ontem; e assim por diante, até ctrl_ant10 (10º bloco).
#      O agente NÃO usa a data para inferir "ontem/hoje" — a ordem de
#      aparição no texto é o único critério de mapeamento.
#   2. DATAS: sempre no formato DD/MM/AAAA. Ano padrão: 2026.
#   3. INTERVALOS: para parâmetros com min/max (PAS, FC, etc.):
#        - "110-140" → _min="110", _max="140"
#        - Valor único → _min="110", _max=""
#        - Múltiplos valores soltos → menor=_min, maior=_max
#   4. VALORES ÚNICOS (Diurese, BH): copiar literal com unidade e sinal.
#      Ex: "+350mL", "-100mL", "1800ml", "Oligúria", "Não Quantificado".
#   5. NÃO PREENCHER: ctrl_conduta e controles_notas → sempre "".
#   6. ESTRUTURA PLANA: sem arrays ou objetos aninhados.
#   7. VAZIO: campos sem dado → "" (nunca null).
# ==============================================================================

def _bloco_fields(dia: str, label: str) -> str:
    """Gera o bloco de variáveis JSON para um dia específico."""
    return f"""
# --- BLOCO: {label.upper()} ---
- ctrl_{dia}_data (string): Data do registro no formato DD/MM/AAAA. Se o ano não estiver explícito, use 2026.
- ctrl_{dia}_pas_min (string): PAS mínima do período (mmHg). Só o número.
- ctrl_{dia}_pas_max (string): PAS máxima do período (mmHg). Só o número.
- ctrl_{dia}_pad_min (string): PAD mínima (mmHg). Só o número.
- ctrl_{dia}_pad_max (string): PAD máxima (mmHg). Só o número.
- ctrl_{dia}_pam_min (string): PAM mínima (mmHg). Só o número.
- ctrl_{dia}_pam_max (string): PAM máxima (mmHg). Só o número.
- ctrl_{dia}_fc_min (string): FC mínima (bpm). Só o número.
- ctrl_{dia}_fc_max (string): FC máxima (bpm). Só o número.
- ctrl_{dia}_fr_min (string): FR mínima (irpm). Só o número.
- ctrl_{dia}_fr_max (string): FR máxima (irpm). Só o número.
- ctrl_{dia}_sato2_min (string): SatO2 mínima (%). Só o número, sem "%".
- ctrl_{dia}_sato2_max (string): SatO2 máxima (%). Só o número, sem "%".
- ctrl_{dia}_temp_min (string): Temperatura mínima (°C). Só o número.
- ctrl_{dia}_temp_max (string): Temperatura máxima (°C). Só o número.
- ctrl_{dia}_glic_min (string): Dextro/Glicemia mínima (mg/dL). Só o número.
- ctrl_{dia}_glic_max (string): Dextro/Glicemia máxima (mg/dL). Só o número.
- ctrl_{dia}_diurese (string): Volume/aspecto da diurese. Ex: "1800mL", "Oligúria", "Não quantificado".
- ctrl_{dia}_evacuacao (string): Informação de evacuação, se presente. Caso contrário "".
- ctrl_{dia}_balanco (string): Balanço hídrico. Preserve sinal e unidade. Ex: "+350mL", "-1200mL"."""


_DIAS_INFO = [
    ("hoje",      "Hoje (1º bloco / mais recente)"),
    ("ontem",     "Ontem (2º bloco)"),
    ("anteontem", "Anteontem (3º bloco)"),
    ("ant4",      "4º dia (4º bloco)"),
    ("ant5",      "5º dia (5º bloco)"),
    ("ant6",      "6º dia (6º bloco)"),
    ("ant7",      "7º dia (7º bloco)"),
    ("ant8",      "8º dia (8º bloco)"),
    ("ant9",      "9º dia (9º bloco)"),
    ("ant10",     "10º dia (10º bloco / mais antigo)"),
]

_VARIAVEIS = "\n".join(_bloco_fields(dia, label) for dia, label in _DIAS_INFO)

_PROMPT_CONTROLES = f"""# CONTEXTO
Você é um extrator preciso de dados médicos para prontuário de Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido em <TEXTO_ALVO> e extrair os Sinais Vitais, Glicemia/Dextro,
Diurese, Evacuação e Balanço Hídrico de cada dia de evolução encontrado.

# REGRAS DE MAPEAMENTO DE BLOCOS
- Cada bloco de data no texto corresponde a um slot, na ORDEM DE APARIÇÃO:
  1º bloco → ctrl_hoje | 2º bloco → ctrl_ontem | ... | 10º bloco → ctrl_ant10
- A data em si NÃO determina o slot — apenas a posição no texto.
- Se houver menos de 10 blocos, os slots restantes recebem "" em todos os campos.
- Se um bloco não tiver data explícita mas tiver vitais, extraia os dados e deixe
  ctrl_X_data = "".

# REGRAS DE EXTRAÇÃO DE VALORES
## Parâmetros com intervalo (PAS, PAD, PAM, FC, FR, SatO2, Temp, Glicemia):
- Formato "110-140" ou "110 a 140": _min="110", _max="140"
- Valor único ("PAS: 120"): _min="120", _max=""
- Múltiplos valores avulsos no mesmo dia: menor=_min, maior=_max
- Extraia apenas o número, sem unidade (ex: "120", não "120mmHg")
- SatO2: sem o símbolo "%" (ex: "98", não "98%")

## Valores únicos (Diurese, Evacuação, BH):
- Copie o texto literal com unidade e sinal.
  Exemplos válidos: "+350mL", "-1200mL", "1800ml", "Oligúria",
  "Presente", "Ausente", "Não Quantificado", "Anúria"
- Para BH: preserve o sinal + ou − conforme o texto.

## Dados ausentes: retorne "" (string vazia). NUNCA use null.

# CAMPOS MANUAIS (nunca preencher):
- controles_notas → sempre ""
- ctrl_conduta     → sempre ""

# PERÍODO
- ctrl_periodo → "24 horas" por padrão.
  Mude para "12 horas" APENAS se o texto mencionar explicitamente "12 horas".

# FORMATO DE SAÍDA
Retorne EXCLUSIVAMENTE um objeto JSON válido, sem markdown, sem explicações.

<TEXTO_ALVO>
[texto será fornecido pelo usuário]
</TEXTO_ALVO>

<VARIAVEIS>
# --- CAMPOS GERAIS ---
- controles_notas (string): "".
- ctrl_conduta (string): "".
- ctrl_periodo (string): "24 horas" ou "12 horas".
{_VARIAVEIS}
</VARIAVEIS>"""


_PROMPT_DIA = """# CONTEXTO
Você é um extrator de dados médicos para prontuário de Terapia Intensiva.

# OBJETIVO
Ler o texto em <TEXTO_ALVO> e extrair os Sinais Vitais, Glicemia/Dextro,
Diurese, Evacuação e Balanço Hídrico de UM único dia de evolução.

# REGRAS
## Parâmetros com intervalo (PAS, PAD, PAM, FC, FR, SatO2, Temp, Glicemia):
- "110-140": min="110", max="140"
- Valor único "120": min="120", max=""
- Múltiplos valores avulsos: menor=min, maior=max
- Retorne só o número, sem unidade. SatO2 sem "%".

## Valores únicos (Diurese, Evacuação, BH):
- Copie literal com unidade e sinal. Ex: "+350mL", "1800ml", "Oligúria", "Ausente".
- BH: preserve sinal + ou −.

## Data: formato DD/MM/AAAA. Ano padrão 2026 se não explícito.
## Campos ausentes: "" (nunca null).

# FORMATO DE SAÍDA
JSON plano com as chaves abaixo. Sem markdown, sem explicações.

<TEXTO_ALVO>
[texto será fornecido pelo usuário]
</TEXTO_ALVO>

<VARIAVEIS>
- data (string): Data do registro em DD/MM/AAAA.
- pas_min, pas_max (string): PAS mínima e máxima (mmHg).
- pad_min, pad_max (string): PAD mínima e máxima.
- pam_min, pam_max (string): PAM mínima e máxima.
- fc_min, fc_max (string): FC mínima e máxima (bpm).
- fr_min, fr_max (string): FR mínima e máxima (irpm).
- sato2_min, sato2_max (string): SatO2 mínima e máxima (sem %).
- temp_min, temp_max (string): Temperatura mínima e máxima (°C).
- glic_min, glic_max (string): Dextro/Glicemia mínima e máxima (mg/dL).
- diurese (string): Volume/aspecto da diurese.
- evacuacao (string): Informação de evacuação, se presente.
- balanco (string): Balanço hídrico com sinal e unidade.
</VARIAVEIS>"""


def preencher_controles_dia(
    texto: str, dia: str, api_key: str, provider: str, modelo: str
) -> dict:
    """
    Extrai controles de um texto de UM único dia usando IA.
    Retorna dict com chaves ctrl_{dia}_* prontas para session_state.
    """
    resultado_bruto = _chamar_ia(_PROMPT_DIA, texto, api_key, provider, modelo)
    erro = resultado_bruto.get("_erro")
    if erro:
        return {"_erro": erro}

    mapeamento = {
        "data":      f"ctrl_{dia}_data",
        "pas_min":   f"ctrl_{dia}_pas_min",
        "pas_max":   f"ctrl_{dia}_pas_max",
        "pad_min":   f"ctrl_{dia}_pad_min",
        "pad_max":   f"ctrl_{dia}_pad_max",
        "pam_min":   f"ctrl_{dia}_pam_min",
        "pam_max":   f"ctrl_{dia}_pam_max",
        "fc_min":    f"ctrl_{dia}_fc_min",
        "fc_max":    f"ctrl_{dia}_fc_max",
        "fr_min":    f"ctrl_{dia}_fr_min",
        "fr_max":    f"ctrl_{dia}_fr_max",
        "sato2_min": f"ctrl_{dia}_sato2_min",
        "sato2_max": f"ctrl_{dia}_sato2_max",
        "temp_min":  f"ctrl_{dia}_temp_min",
        "temp_max":  f"ctrl_{dia}_temp_max",
        "glic_min":  f"ctrl_{dia}_glic_min",
        "glic_max":  f"ctrl_{dia}_glic_max",
        "diurese":   f"ctrl_{dia}_diurese",
        "evacuacao": f"ctrl_{dia}_evacuacao",
        "balanco":   f"ctrl_{dia}_balanco",
    }
    return {v: resultado_bruto.get(k, "") for k, v in mapeamento.items()}


def preencher_controles(texto: str, api_key: str, provider: str, modelo: str) -> dict:
    """
    Chama a IA e retorna um dict com as chaves ctrl_X_Y preenchidas.

    Campos que a IA deixar em "" não sobrescrevem session_state existente
    (a lógica de merge fica no caller em tab_controles.py).

    Retorna {} em caso de erro, com chave '_erro' contendo a mensagem.
    """
    resultado = _chamar_ia(_PROMPT_CONTROLES, texto, api_key, provider, modelo)

    # Remove campos manuais que a IA não deve alterar
    for campo in ("controles_notas", "ctrl_conduta"):
        resultado.pop(campo, None)

    return resultado
