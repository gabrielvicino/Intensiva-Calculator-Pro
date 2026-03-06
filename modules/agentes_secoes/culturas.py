from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 7: CULTURAS
# ==============================================================================
_PROMPT_CULTURAS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair exclusivamente as culturas microbiológicas, respeitando rigorosamente a ordem arquitetural e de leitura do texto.

# DEFINIÇÃO OPERACIONAL E EXCLUSÕES
- Válidos: Hemocultura, Urocultura, Aspirado Traqueal, Swab Retal, Lavado Broncoalveolar, Cultura de Ponta de Cateter, Dreno, Líquor, etc.
- NÃO incluir: PCR viral isolada, sorologias, exames moleculares sem cultura, ou condutas médicas.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ORDEM DE LEITURA E PREENCHIMENTO: Você DEVE preencher o JSON na exata ordem das chaves solicitadas abaixo. Primeiro todos os Sítios, depois Datas de Coleta, Datas de Resultado, Status, Micro-organismos, Sensibilidade e Conduta.
2. CRONOLOGIA DO TEXTO: Liste as culturas na mesma ordem em que aparecem no texto fonte. NÃO reordene separando positivas de negativas.
3. PREENCHIMENTO VAZIO: O limite é de 8 culturas. Se a informação não constar explicitamente ou o paciente tiver menos culturas, retorne estritamente `""` (string vazia) para os slots sobressalentes. Não use `null`.
4. NÃO inferir dados. NÃO inventar culturas não mencionadas.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# PADRONIZAÇÕES OBRIGATÓRIAS
- SÍTIO: Title Case (ex: Hemocultura, Aspirado Traqueal). Sem datas.
- STATUS: Você deve classificar cada cultura usando EXATAMENTE UMA destas 4 opções (se o slot estiver em uso):
  - "Positivo com Antibiograma"
  - "Positivo aguarda isolamento"
  - "Pendente negativo"
  - "Negativo"
- CONDUTA: Este campo deve ser SEMPRE `""` (vazio). Nunca preencha.
- MICRO/SENSIBILIDADE: Se o status for "Negativo" ou "Pendente", estes campos devem ser `""`.

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico com as culturas será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- CULTURAS MICROBIOLÓGICAS (MÁXIMO 8) ---
# 1. SÍTIOS (Ordem do texto original. Title Case)
- cult_1_sitio (string): Sítio da 1ª cultura citada.
- cult_2_sitio (string): Sítio da 2ª cultura citada.
- cult_3_sitio (string): Sítio da 3ª cultura citada.
- cult_4_sitio (string): Sítio da 4ª cultura citada.
- cult_5_sitio (string): Sítio da 5ª cultura citada.
- cult_6_sitio (string): Sítio da 6ª cultura citada.
- cult_7_sitio (string): Sítio da 7ª cultura citada.
- cult_8_sitio (string): Sítio da 8ª cultura citada.

# 2. DATAS DE COLETA (Manter formato original do texto)
- cult_1_data_coleta (string): Data de coleta da 1ª cultura.
- cult_2_data_coleta (string): Data de coleta da 2ª cultura.
- cult_3_data_coleta (string): Data de coleta da 3ª cultura.
- cult_4_data_coleta (string): Data de coleta da 4ª cultura.
- cult_5_data_coleta (string): Data de coleta da 5ª cultura.
- cult_6_data_coleta (string): Data de coleta da 6ª cultura.
- cult_7_data_coleta (string): Data de coleta da 7ª cultura.
- cult_8_data_coleta (string): Data de coleta da 8ª cultura.

# 3. DATAS DE RESULTADO (Apenas se explícito)
- cult_1_data_resultado (string): Data do resultado da 1ª cultura.
- cult_2_data_resultado (string): Data do resultado da 2ª cultura.
- cult_3_data_resultado (string): Data do resultado da 3ª cultura.
- cult_4_data_resultado (string): Data do resultado da 4ª cultura.
- cult_5_data_resultado (string): Data do resultado da 5ª cultura.
- cult_6_data_resultado (string): Data do resultado da 6ª cultura.
- cult_7_data_resultado (string): Data do resultado da 7ª cultura.
- cult_8_data_resultado (string): Data do resultado da 8ª cultura.

# 4. STATUS (Estritamente uma das 4 opções permitidas)
- cult_1_status (string): Status da 1ª cultura.
- cult_2_status (string): Status da 2ª cultura.
- cult_3_status (string): Status da 3ª cultura.
- cult_4_status (string): Status da 4ª cultura.
- cult_5_status (string): Status da 5ª cultura.
- cult_6_status (string): Status da 6ª cultura.
- cult_7_status (string): Status da 7ª cultura.
- cult_8_status (string): Status da 8ª cultura.

# 5. MICRO-ORGANISMOS ISOLADOS (Se negativo/pendente, "")
- cult_1_micro (string): Bactéria/fungo da 1ª cultura.
- cult_2_micro (string): Bactéria/fungo da 2ª cultura.
- cult_3_micro (string): Bactéria/fungo da 3ª cultura.
- cult_4_micro (string): Bactéria/fungo da 4ª cultura.
- cult_5_micro (string): Bactéria/fungo da 5ª cultura.
- cult_6_micro (string): Bactéria/fungo da 6ª cultura.
- cult_7_micro (string): Bactéria/fungo da 7ª cultura.
- cult_8_micro (string): Bactéria/fungo da 8ª cultura.

# 6. PERFIL DE SENSIBILIDADE / ANTIBIOGRAMA (Se aguarda/negativo/pendente, "")
- cult_1_sensib (string): Sensibilidade/resistência da 1ª cultura.
- cult_2_sensib (string): Sensibilidade/resistência da 2ª cultura.
- cult_3_sensib (string): Sensibilidade/resistência da 3ª cultura.
- cult_4_sensib (string): Sensibilidade/resistência da 4ª cultura.
- cult_5_sensib (string): Sensibilidade/resistência da 5ª cultura.
- cult_6_sensib (string): Sensibilidade/resistência da 6ª cultura.
- cult_7_sensib (string): Sensibilidade/resistência da 7ª cultura.
- cult_8_sensib (string): Sensibilidade/resistência da 8ª cultura.

# 7. CONDUTAS (Obrigatoriamente "")
- cult_1_conduta (string): "".
- cult_2_conduta (string): "".
- cult_3_conduta (string): "".
- cult_4_conduta (string): "".
- cult_5_conduta (string): "".
- cult_6_conduta (string): "".
- cult_7_conduta (string): "".
- cult_8_conduta (string): "".

# --- NOTAS ADICIONAIS ---
- culturas_notas (string): Qualquer observação relevante geral sobre as culturas que não coube nos campos acima. Se não houver, "".

# EXEMPLO DE SAÍDA PERFEITA
{
  "cult_1_sitio": "Aspirado Traqueal",
  "cult_2_sitio": "Hemocultura",
  "cult_3_sitio": "Hemocultura",
  "cult_4_sitio": "Urocultura",
  "cult_5_sitio": "",
  "cult_6_sitio": "",
  "cult_7_sitio": "",
  "cult_8_sitio": "",
  "cult_1_data_coleta": "23/02/2026",
  "cult_2_data_coleta": "21/02/2026",
  "cult_3_data_coleta": "21/02/2026",
  "cult_4_data_coleta": "23/02/2026",
  "cult_5_data_coleta": "",
  "cult_6_data_coleta": "",
  "cult_7_data_coleta": "",
  "cult_8_data_coleta": "",
  "cult_1_data_resultado": "25/02/2026",
  "cult_2_data_resultado": "24/02/2026",
  "cult_3_data_resultado": "24/02/2026",
  "cult_4_data_resultado": "",
  "cult_5_data_resultado": "",
  "cult_6_data_resultado": "",
  "cult_7_data_resultado": "",
  "cult_8_data_resultado": "",
  "cult_1_status": "Positivo com Antibiograma",
  "cult_2_status": "Negativo",
  "cult_3_status": "Negativo",
  "cult_4_status": "Pendente negativo",
  "cult_5_status": "",
  "cult_6_status": "",
  "cult_7_status": "",
  "cult_8_status": "",
  "cult_1_micro": "Klebsiella pneumoniae KPC+",
  "cult_2_micro": "",
  "cult_3_micro": "",
  "cult_4_micro": "",
  "cult_5_micro": "",
  "cult_6_micro": "",
  "cult_7_micro": "",
  "cult_8_micro": "",
  "cult_1_sensib": "Sensível a Polimixina B e Ceftazidima-Avibactam. Resistente a Carbapenêmicos.",
  "cult_2_sensib": "",
  "cult_3_sensib": "",
  "cult_4_sensib": "",
  "cult_5_sensib": "",
  "cult_6_sensib": "",
  "cult_7_sensib": "",
  "cult_8_sensib": "",
  "cult_1_conduta": "",
  "cult_2_conduta": "",
  "cult_3_conduta": "",
  "cult_4_conduta": "",
  "cult_5_conduta": "",
  "cult_6_conduta": "",
  "cult_7_conduta": "",
  "cult_8_conduta": "",
  "culturas_notas": ""
}
</VARIAVEIS>"""


_STATUS_CULTURAS = {
    "Positivo com Antibiograma",
    "Positivo aguarda isolamento",
    "Pendente negativo",
    "Negativo",
}


def preencher_culturas(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_CULTURAS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}
    for i in range(1, 9):
        sitio  = _s(f"cult_{i}_sitio")
        status = _s(f"cult_{i}_status")
        resultado[f"cult_{i}_sitio"]          = sitio
        resultado[f"cult_{i}_data_coleta"]    = _s(f"cult_{i}_data_coleta")
        resultado[f"cult_{i}_data_resultado"] = _s(f"cult_{i}_data_resultado")
        resultado[f"cult_{i}_status"]         = status if status in _STATUS_CULTURAS else (None if not sitio else status)
        resultado[f"cult_{i}_micro"]          = _s(f"cult_{i}_micro")
        resultado[f"cult_{i}_sensib"]         = _s(f"cult_{i}_sensib")

    culturas_notas = _s("culturas_notas")
    if culturas_notas:
        resultado["culturas_notas"] = culturas_notas

    return resultado
