from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 2: SCORES CLÍNICOS
# ==============================================================================
_PROMPT_SCORES = """# CONTEXTO
Você é uma ferramenta de extração de dados estruturados de textos clínicos hospitalares.

# OBJETIVO
Ler o texto fornecido e extrair os valores dos scores clínicos listados em <VARIAVEIS>.

# REGRAS
1. Responda de forma direta, concisa e objetiva.
2. Se a informação não constar explicitamente, retorne `null`. Não invente valores.
3. Para scores numéricos, retorne apenas o número inteiro.
4. Para SOFA, atenção especial:
   - `sofa_adm` = valor de admissão (o mais antigo mencionado ou explicitamente identificado como admissão).
   - `sofa_d1..d4` = valores de evolução diária em ordem cronológica (do mais antigo ao mais recente),
     excluindo o de admissão. Preencha apenas os slots necessários, deixe os demais como null.
     Máximo 4 valores de evolução.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem textos extras.

<VARIAVEIS>
- saps3 (number): Valor do escore SAPS 3. Apenas número inteiro. Se ausente, null.
- saps2 (number): Valor do escore SAPS 2. Apenas número inteiro. Se ausente, null.
- apache3 (number): Valor do escore APACHE 3. Apenas número inteiro. Se ausente, null.
- apache2 (number): Valor do escore APACHE 2. Apenas número inteiro. Se ausente, null.
- apache4 (number): Valor do escore APACHE 4 (APACHE IV). Apenas número inteiro. Se ausente, null.
- sofa_adm (number): Valor do SOFA na admissão. Apenas número inteiro. Se ausente, null.
- sofa_d1 (number): 1º valor de evolução do SOFA (mais antigo após admissão). Se ausente, null.
- sofa_d2 (number): 2º valor de evolução do SOFA. Se ausente, null.
- sofa_d3 (number): 3º valor de evolução do SOFA. Se ausente, null.
- sofa_d4 (number): 4º valor de evolução do SOFA (mais recente). Se ausente, null.
- pps (string): Palliative Performance Scale (PPS). Como string (ex: "80%", "80"). Se ausente, null.
- mrs (string): Escala de Rankin Modificada (mRS). Apenas o número como string (ex: "2"). Se ausente, null.
- cfs (string): Clinical Frailty Scale. Como string (ex: "3", "5 - Levemente frágil"). Se ausente, null.
</VARIAVEIS>

# EXEMPLO DE SAÍDA PERFEITA
{
  "saps3": 72,
  "saps2": 38,
  "apache3": 60,
  "apache2": 18,
  "apache4": null,
  "sofa_adm": 10,
  "sofa_d1": 9,
  "sofa_d2": 8,
  "sofa_d3": null,
  "sofa_d4": null,
  "pps": "60%",
  "mrs": "2",
  "cfs": "4 - Vulnerável"
}"""


def preencher_scores(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_SCORES, texto, api_key, provider, modelo)
    r.pop("_erro", None)

    # saps3, saps2, apache3, apache2, apache4: IA retorna number, widget é text_input → string
    for k in ["saps3", "saps2", "apache3", "apache2", "apache4"]:
        if k in r:
            try:
                r[k] = str(int(r[k])) if r[k] not in (None, "", "null") else ""
            except (ValueError, TypeError):
                r[k] = ""

    # sofa_adm e sofa_d1..d4: null/None → 0
    for k in ["sofa_adm", "sofa_d1", "sofa_d2", "sofa_d3", "sofa_d4"]:
        if k in r:
            try:
                r[k] = int(r[k]) if r[k] not in (None, "", "null") else 0
            except (ValueError, TypeError):
                r[k] = 0

    # pps, mrs, cfs: null → ""
    for k in ["pps", "mrs", "cfs"]:
        if r.get(k) is None:
            r[k] = ""

    # Garantir que sofa_d5 e scores_novo_sofa não sejam sobrescritos (campos removidos)
    r.pop("sofa_d5", None)
    r.pop("scores_novo_sofa", None)

    return r
