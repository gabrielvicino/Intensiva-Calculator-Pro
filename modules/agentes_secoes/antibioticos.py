from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 8: ANTIBIÓTICOS
# ==============================================================================
_PROMPT_ANTIBIOTICOS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair os agentes antimicrobianos, respeitando a ordem de leitura do texto. Cada antibiótico tem status "Atual" ou "Prévio".

# CLASSIFICAÇÃO
- ATUAIS: Em uso no momento, sem suspensão documentada.
- PRÉVIOS: Suspensos, eventos passados com data de término ou suspensão explícita.

# REGRAS DE EXTRAÇÃO
1. ORDEM: Preencha atb_1..atb_8 na ordem em que os antibióticos aparecem no texto. Atuais primeiro, depois Prévios.
2. LIMITE: Máximo 8 antibióticos. Slots vazios: nome="", status="".
3. CONDUTAS E NOTAS: _conduta e antibioticos_notas sempre "".
4. Saída: EXCLUSIVAMENTE objeto JSON válido, sem markdown.

# PADRONIZAÇÕES
- NOME: DCI, Title Case. Ex: "Meropenem", "Fluconazol".
- FOCO: Title Case. Ex: "PAV", "ITU". Se ausente, "".
- TIPO: EXATAMENTE "Empírico", "Guiado por Cultura" ou "".
- STATUS: EXATAMENTE "Atual" ou "Prévio".
- num_dias: Número de dias de tratamento se explícito no texto. Ex: "7". Se ausente, "".
- OBS (Prévios): Motivo da suspensão. Se ausente, "".
- DATAS: Formato original do texto.

# ENTRADAS
<TEXTO_ALVO>
[O texto com os antibióticos será fornecido aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia as chaves JSON nesta ordem. Para cada antibiótico de 1 a 8, use atb_1, atb_2, ... atb_8:

- atb_1_nome, atb_1_foco, atb_1_tipo, atb_1_data_ini, atb_1_data_fim, atb_1_num_dias, atb_1_status ("Atual"|"Prévio"), atb_1_obs, atb_1_conduta (sempre "")
- atb_2_nome, atb_2_foco, atb_2_tipo, atb_2_data_ini, atb_2_data_fim, atb_2_num_dias, atb_2_status, atb_2_obs, atb_2_conduta
- ... (atb_3 a atb_8, mesma estrutura)
- antibioticos_notas (string): "".

Slots sem antibiótico: nome="", status="", demais campos "".

# EXEMPLO DE SAÍDA PERFEITA
{
  "atb_1_nome": "Polimixina B",
  "atb_1_foco": "PAV",
  "atb_1_tipo": "Guiado por Cultura",
  "atb_1_data_ini": "25/02/2026",
  "atb_1_data_fim": "",
  "atb_1_num_dias": "7",
  "atb_1_status": "Atual",
  "atb_1_obs": "",
  "atb_1_conduta": "",
  "atb_2_nome": "Ceftazidima-Avibactam",
  "atb_2_foco": "PAV",
  "atb_2_tipo": "Guiado por Cultura",
  "atb_2_data_ini": "25/02/2026",
  "atb_2_data_fim": "",
  "atb_2_num_dias": "7",
  "atb_2_status": "Atual",
  "atb_2_obs": "",
  "atb_2_conduta": "",
  "atb_3_nome": "Meropenem",
  "atb_3_foco": "PAV",
  "atb_3_tipo": "Empírico",
  "atb_3_data_ini": "21/02/2026",
  "atb_3_data_fim": "24/02/2026",
  "atb_3_num_dias": "4",
  "atb_3_status": "Prévio",
  "atb_3_obs": "Suspenso após antibiograma com resistência a carbapenêmicos.",
  "atb_3_conduta": "",
  "atb_4_nome": "",
  "atb_4_foco": "",
  "atb_4_tipo": "",
  "atb_4_data_ini": "",
  "atb_4_data_fim": "",
  "atb_4_num_dias": "",
  "atb_4_status": "",
  "atb_4_obs": "",
  "atb_4_conduta": "",
  "atb_5_nome": "",
  "atb_5_foco": "",
  "atb_5_tipo": "",
  "atb_5_data_ini": "",
  "atb_5_data_fim": "",
  "atb_5_num_dias": "",
  "atb_5_status": "",
  "atb_5_obs": "",
  "atb_5_conduta": "",
  "atb_6_nome": "",
  "atb_6_foco": "",
  "atb_6_tipo": "",
  "atb_6_data_ini": "",
  "atb_6_data_fim": "",
  "atb_6_num_dias": "",
  "atb_6_status": "",
  "atb_6_obs": "",
  "atb_6_conduta": "",
  "atb_7_nome": "",
  "atb_7_foco": "",
  "atb_7_tipo": "",
  "atb_7_data_ini": "",
  "atb_7_data_fim": "",
  "atb_7_num_dias": "",
  "atb_7_status": "",
  "atb_7_obs": "",
  "atb_7_conduta": "",
  "atb_8_nome": "",
  "atb_8_foco": "",
  "atb_8_tipo": "",
  "atb_8_data_ini": "",
  "atb_8_data_fim": "",
  "atb_8_num_dias": "",
  "atb_8_status": "",
  "atb_8_obs": "",
  "atb_8_conduta": "",
  "antibioticos_notas": ""
}
</VARIAVEIS>"""


_TIPO_ATB = {"Empírico", "Guiado por Cultura"}
_STATUS_ATB = {"Atual", "Prévio"}


def preencher_antibioticos(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_ANTIBIOTICOS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}
    for i in range(1, 9):
        nome = _s(f"atb_{i}_nome")
        tipo = _s(f"atb_{i}_tipo")
        status = _s(f"atb_{i}_status")
        resultado[f"atb_{i}_nome"]     = nome
        resultado[f"atb_{i}_foco"]     = _s(f"atb_{i}_foco")
        resultado[f"atb_{i}_tipo"]     = tipo if tipo in _TIPO_ATB else (None if not nome else "")
        resultado[f"atb_{i}_data_ini"] = _s(f"atb_{i}_data_ini")
        resultado[f"atb_{i}_data_fim"] = _s(f"atb_{i}_data_fim")
        resultado[f"atb_{i}_num_dias"] = _s(f"atb_{i}_num_dias")
        resultado[f"atb_{i}_status"]   = status if status in _STATUS_ATB else (None if not nome else "")
        resultado[f"atb_{i}_obs"]      = _s(f"atb_{i}_obs")
    return resultado
