from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 3: COMORBIDADES
# ==============================================================================
_PROMPT_COMORBIDADES = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair exclusivamente as comorbidades (doenças pré-existentes ao evento/internação atual), respeitando rigorosamente a ordem arquitetural e cronológica de leitura.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ORDEM DE LEITURA E PREENCHIMENTO: Você DEVE preencher o JSON na exata ordem das chaves solicitadas abaixo. Primeiro todos os Nomes, depois todas as Classificações.
2. CRONOLOGIA DO TEXTO: Liste as comorbidades na mesma ordem em que aparecem no texto fonte (NÃO reordene por relevância).
3. PREENCHIMENTO VAZIO: O limite é de 10 comorbidades. Se a informação não constar explicitamente ou se o paciente tiver menos itens, retorne estritamente `""` (string vazia) para os slots sobressalentes. Não use `null`.
4. NÃO inferir. NÃO criar comorbidades. NÃO preencher condutas.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# REGRAS DE EXCLUSÃO
- Dúvida atual vs comorbidade: considerar comorbidade APENAS se for um antecedente explícito.
- NÃO considerar história familiar.
- Tabagismo, etilismo e substâncias psicoativas NÃO vão na lista de comorbidades — vão nos campos dedicados abaixo.

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- ETILISMO, TABAGISMO, SUBSTÂNCIAS PSICOATIVAS ---
- etilismo (string): EXATAMENTE "Desconhecido", "Ausente", "Uso Prévio" ou "Presente". "Uso Prévio" = ex-etilista/parou. Se não mencionado, "".
- etilismo_obs (string): Observação sobre etilismo (ex: "parou há 5 anos", "em abstinência"). Se ausente, "".
- tabagismo (string): EXATAMENTE "Desconhecido", "Ausente", "Uso Prévio" ou "Presente". "Uso Prévio" = ex-tabagista/parou. Se não mencionado, "".
- tabagismo_obs (string): Observação sobre tabagismo (ex: "20 anos-maço, parou há 3 anos"). Se ausente, "".
- spa (string): EXATAMENTE "Desconhecido", "Ausente", "Uso Prévio" ou "Presente" (Substâncias Psicoativas). "Uso Prévio" = ex-usuário/parou. Se não mencionado, "".
- spa_obs (string): Observação sobre SPA (ex: "crack", "maconha, parou há 2 anos"). Se ausente, "".

# --- COMORBIDADES PRÉ-EXISTENTES ---
# 1. NOMES DOS ANTECEDENTES (Ordem do texto original. Expandir siglas: "HAS" → "Hipertensão Arterial Sistêmica", etc. Sem classificação ou datas. Title Case)
- comorbidade_1_nome (string): Nome da 1ª comorbidade citada.
- comorbidade_2_nome (string): Nome da 2ª comorbidade citada.
- comorbidade_3_nome (string): Nome da 3ª comorbidade citada.
- comorbidade_4_nome (string): Nome da 4ª comorbidade citada.
- comorbidade_5_nome (string): Nome da 5ª comorbidade citada.
- comorbidade_6_nome (string): Nome da 6ª comorbidade citada.
- comorbidade_7_nome (string): Nome da 7ª comorbidade citada.
- comorbidade_8_nome (string): Nome da 8ª comorbidade citada.
- comorbidade_9_nome (string): Nome da 9ª comorbidade citada.
- comorbidade_10_nome (string): Nome da 10ª comorbidade citada.

# 2. CLASSIFICAÇÕES (Estadiamento/gravidade formal referenciando as comorbidades acima. Ex: NYHA III, Child-Pugh B, CKD G4. Se ausente, "")
- comorbidade_1_class (string): Estadiamento da 1ª comorbidade.
- comorbidade_2_class (string): Estadiamento da 2ª comorbidade.
- comorbidade_3_class (string): Estadiamento da 3ª comorbidade.
- comorbidade_4_class (string): Estadiamento da 4ª comorbidade.
- comorbidade_5_class (string): Estadiamento da 5ª comorbidade.
- comorbidade_6_class (string): Estadiamento da 6ª comorbidade.
- comorbidade_7_class (string): Estadiamento da 7ª comorbidade.
- comorbidade_8_class (string): Estadiamento da 8ª comorbidade.
- comorbidade_9_class (string): Estadiamento da 9ª comorbidade.
- comorbidade_10_class (string): Estadiamento da 10ª comorbidade.

# EXEMPLO DE SAÍDA PERFEITA
{
  "etilismo": "Uso Prévio",
  "etilismo_obs": "parou há 10 anos",
  "tabagismo": "Uso Prévio",
  "tabagismo_obs": "40 anos-maço, parou há 5 anos",
  "spa": "Ausente",
  "spa_obs": "",
  "comorbidade_1_nome": "Hipertensão Arterial Sistêmica",
  "comorbidade_2_nome": "Diabetes Mellitus Tipo 2",
  "comorbidade_3_nome": "Doença Renal Crônica",
  "comorbidade_4_nome": "Fibrilação Atrial Crônica",
  "comorbidade_5_nome": "Insuficiência Cardíaca",
  "comorbidade_6_nome": "Hipotireoidismo",
  "comorbidade_7_nome": "Obesidade",
  "comorbidade_8_nome": "",
  "comorbidade_9_nome": "",
  "comorbidade_10_nome": "",
  "comorbidade_1_class": "Estágio 3",
  "comorbidade_2_class": "Mal controlada, HbA1c 10.2%",
  "comorbidade_3_class": "CKD G3b",
  "comorbidade_4_class": "CHADS2-VASc 5",
  "comorbidade_5_class": "NYHA II, FE 45%",
  "comorbidade_6_class": "",
  "comorbidade_7_class": "IMC 34.2 kg/m²",
  "comorbidade_8_class": "",
  "comorbidade_9_class": "",
  "comorbidade_10_class": ""
}
</VARIAVEIS>"""


def preencher_comorbidades(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_COMORBIDADES, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}

    # Etilismo, Tabagismo, SPA — só grava se valor válido (compatível com pills)
    for key_ia, key_ui, obs_key in [
        ("etilismo", "cmd_etilismo", "cmd_etilismo_obs"),
        ("tabagismo", "cmd_tabagismo", "cmd_tabagismo_obs"),
        ("spa", "cmd_spa", "cmd_spa_obs"),
    ]:
        v = _s(key_ia)
        if v in ("Desconhecido", "Ausente", "Uso Prévio", "Presente"):
            resultado[key_ui] = v
        else:
            resultado[key_ui] = None
        resultado[obs_key] = _s(f"{key_ia}_obs")

    for i in range(1, 11):
        resultado[f"cmd_{i}_nome"]  = _s(f"comorbidade_{i}_nome")
        resultado[f"cmd_{i}_class"] = _s(f"comorbidade_{i}_class")
    return resultado
