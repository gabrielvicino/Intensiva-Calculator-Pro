from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 2: HD - DIAGNÓSTICOS ATUAIS E PRÉVIOS
# ==============================================================================
_PROMPT_HD = """# CONTEXTO
Você é uma ferramenta avançada usada para análise e extração de dados estruturados de textos clínicos hospitalares em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair as hipóteses diagnósticas (Atuais e Resolvidas), respeitando rigorosamente a ordem em que aparecem no texto original.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ORDEM DE LEITURA: Siga a exata ordem em que os diagnósticos aparecem no texto. O primeiro diagnóstico lido deve ser o número 1, o segundo lido o número 2, etc.
2. PASSO A PASSO: Extraia PRIMEIRO todos os Nomes. Só depois extraia todas as Classificações. Depois todas as Datas. E, por fim, todas as Observações.
3. PREENCHIMENTO VAZIO: Se a informação não constar explicitamente ou se o paciente tiver menos de 4 diagnósticos, retorne estritamente `""` (string vazia). Não use `null` ou "Não encontrado".
4. NÃO invente diagnósticos ou datas para preencher lacunas.
5. CUIDADO COM SIGLAS AMBÍGUAS: Analise o contexto clínico antes de expandir siglas (ex: "IRA").
6. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown (como ```json).

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- DIAGNÓSTICOS ATUAIS ---
# 1. NOMES (Respeitando a ordem do texto original, em Title Case, sem siglas)
- diag_atual_1_nome (string): Nome do 1º diagnóstico citado no texto.
- diag_atual_2_nome (string): Nome do 2º diagnóstico citado no texto.
- diag_atual_3_nome (string): Nome do 3º diagnóstico citado no texto.
- diag_atual_4_nome (string): Nome do 4º diagnóstico citado no texto.

# 2. CLASSIFICAÇÕES (Referentes aos diagnósticos mapeados acima)
- diag_atual_1_class (string): Estadiamento/classificação do diag 1 (ex: KDIGO 3). Se ausente, "".
- diag_atual_2_class (string): Estadiamento/classificação do diag 2.
- diag_atual_3_class (string): Estadiamento/classificação do diag 3.
- diag_atual_4_class (string): Estadiamento/classificação do diag 4.

# 3. DATAS (Referentes aos diagnósticos mapeados acima)
- diag_atual_1_data (string): Data ou tempo de início do diag 1. Se ausente, "".
- diag_atual_2_data (string): Data ou tempo de início do diag 2.
- diag_atual_3_data (string): Data ou tempo de início do diag 3.
- diag_atual_4_data (string): Data ou tempo de início do diag 4.

# 4. OBSERVAÇÕES (Referentes aos diagnósticos mapeados acima)
- diag_atual_1_obs (string): Resumo clínico objetivo da evolução do diag 1. Sem condutas. Se ausente, "".
- diag_atual_2_obs (string): Resumo clínico do diag 2.
- diag_atual_3_obs (string): Resumo clínico do diag 3.
- diag_atual_4_obs (string): Resumo clínico do diag 4.

# --- DIAGNÓSTICOS RESOLVIDOS / PASSADOS ---
# 1. NOMES DOS RESOLVIDOS
- diag_resolv_1_nome (string): Nome do 1º evento passado citado no texto.
- diag_resolv_2_nome (string): Nome do 2º evento passado citado no texto.
- diag_resolv_3_nome (string): Nome do 3º evento passado citado no texto.
- diag_resolv_4_nome (string): Nome do 4º evento passado citado no texto.

# 2. CLASSIFICAÇÕES DOS RESOLVIDOS
- diag_resolv_1_class (string): Estadiamento/classificação do resolvido 1.
- diag_resolv_2_class (string): Estadiamento/classificação do resolvido 2.
- diag_resolv_3_class (string): Estadiamento/classificação do resolvido 3.
- diag_resolv_4_class (string): Estadiamento/classificação do resolvido 4.

# 3. DATAS DOS RESOLVIDOS
- diag_resolv_1_data_inicio (string): Data de início do resolvido 1.
- diag_resolv_1_data_fim (string): Data de resolução/alta do resolvido 1.
- diag_resolv_2_data_inicio (string): Data de início do resolvido 2.
- diag_resolv_2_data_fim (string): Data de resolução do resolvido 2.
- diag_resolv_3_data_inicio (string): Data de início do resolvido 3.
- diag_resolv_3_data_fim (string): Data de resolução do resolvido 3.
- diag_resolv_4_data_inicio (string): Data de início do resolvido 4.
- diag_resolv_4_data_fim (string): Data de resolução do resolvido 4.

# 4. OBSERVAÇÕES DOS RESOLVIDOS
- diag_resolv_1_obs (string): Resumo do desfecho do resolvido 1.
- diag_resolv_2_obs (string): Resumo do desfecho do resolvido 2.
- diag_resolv_3_obs (string): Resumo do desfecho do resolvido 3.
- diag_resolv_4_obs (string): Resumo do desfecho do resolvido 4.

# EXEMPLO DE SAÍDA PERFEITA
{
  "diag_atual_1_nome": "Choque Séptico",
  "diag_atual_2_nome": "Pneumonia Associada à Ventilação Mecânica",
  "diag_atual_3_nome": "Lesão Renal Aguda",
  "diag_atual_4_nome": "Fibrilação Atrial com Alta Resposta Ventricular",
  "diag_atual_1_class": "Foco Pulmonar",
  "diag_atual_2_class": "HAPV",
  "diag_atual_3_class": "KDIGO 2",
  "diag_atual_4_class": "",
  "diag_atual_1_data": "21/02/2026",
  "diag_atual_2_data": "23/02/2026",
  "diag_atual_3_data": "21/02/2026",
  "diag_atual_4_data": "22/02/2026",
  "diag_atual_1_obs": "Admitida em choque séptico com foco pulmonar provável. Iniciado suporte vasopressor e antibioticoterapia empírica. Evolução com melhora parcial do vasopressor após 48h.",
  "diag_atual_2_obs": "Critério radiológico e microbiológico. Cultura de aspirado traqueal coletada em 23/02/2026 com isolamento de K. pneumoniae KPC+.",
  "diag_atual_3_obs": "Oligúria nas primeiras 24h. Creatinina de base 1.1, pico de 3.4. Em acompanhamento com nefrologia.",
  "diag_atual_4_obs": "Revertida com amiodarona IV. Mantém ritmo sinusal desde 22/02/2026.",
  "diag_resolv_1_nome": "Hipopotassemia",
  "diag_resolv_2_nome": "Hipotermia",
  "diag_resolv_3_nome": "",
  "diag_resolv_4_nome": "",
  "diag_resolv_1_class": "",
  "diag_resolv_2_class": "",
  "diag_resolv_3_class": "",
  "diag_resolv_4_class": "",
  "diag_resolv_1_data_inicio": "20/02/2026",
  "diag_resolv_1_data_fim": "22/02/2026",
  "diag_resolv_2_data_inicio": "20/02/2026",
  "diag_resolv_2_data_fim": "21/02/2026",
  "diag_resolv_3_data_inicio": "",
  "diag_resolv_3_data_fim": "",
  "diag_resolv_4_data_inicio": "",
  "diag_resolv_4_data_fim": "",
  "diag_resolv_1_obs": "Reposta 120 mEq IV. Corrigida.",
  "diag_resolv_2_obs": "Temperatura mínima de 34.8°C na admissão. Reaquecimento com manta térmica.",
  "diag_resolv_3_obs": "",
  "diag_resolv_4_obs": ""
}
</VARIAVEIS>"""


def preencher_hd(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_HD, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}

    # Atuais → hd_1..hd_4
    for i in range(1, 5):
        nome = _s(f"diag_atual_{i}_nome")
        resultado[f"hd_{i}_nome"]          = nome
        resultado[f"hd_{i}_class"]         = _s(f"diag_atual_{i}_class")
        resultado[f"hd_{i}_data_inicio"]   = _s(f"diag_atual_{i}_data")
        resultado[f"hd_{i}_data_resolvido"]= ""
        resultado[f"hd_{i}_status"]        = "Atual" if nome else None
        resultado[f"hd_{i}_obs"]           = _s(f"diag_atual_{i}_obs")

    # Resolvidos → hd_5..hd_8
    for i in range(1, 5):
        nome = _s(f"diag_resolv_{i}_nome")
        slot = i + 4
        resultado[f"hd_{slot}_nome"]          = nome
        resultado[f"hd_{slot}_class"]         = _s(f"diag_resolv_{i}_class")
        resultado[f"hd_{slot}_data_inicio"]   = _s(f"diag_resolv_{i}_data_inicio")
        resultado[f"hd_{slot}_data_resolvido"]= _s(f"diag_resolv_{i}_data_fim")
        resultado[f"hd_{slot}_status"]        = "Resolvida" if nome else None
        resultado[f"hd_{slot}_obs"]           = _s(f"diag_resolv_{i}_obs")

    return resultado
