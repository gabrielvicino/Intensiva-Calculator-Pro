from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 4: MUC - MEDICAÇÕES DE USO CONTÍNUO
# ==============================================================================
_PROMPT_MUC = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair as medicações de uso domiciliar, respeitando rigorosamente a ordem arquitetural e de leitura.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ORDEM DE LEITURA E PREENCHIMENTO: Você DEVE preencher o JSON na exata ordem das chaves solicitadas abaixo. Primeiro a adesão, depois todos os Nomes, depois todas as Doses, e por fim todas as Frequências.
2. CRONOLOGIA DO TEXTO: Liste as medicações na mesma ordem em que aparecem no texto fonte.
3. PREENCHIMENTO VAZIO: O limite é de 20 medicações. Se a informação não constar explicitamente ou se o paciente usar menos fármacos, retorne estritamente `""` (string vazia) para os slots sobressalentes. Não use `null` ou "Não encontrado".
4. NÃO inferir. NÃO criar medicações.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# PADRONIZAÇÕES OBRIGATÓRIAS
- NOME: DCI (Denominação Comum Brasileira/Internacional), Title Case, sem siglas, sem dose, sem frequência. Ex: "AAS" → "Acido Acetilsalicilico".
- DOSE: Apenas valor + unidade. Ex: "20mg", "850mg". Se ausente, "".
- FREQUÊNCIA: Entenda e traduza a notação numérica que representa "[manhã]-[tarde]-[noite]":
  - "1-0-0" → "1x ao dia"
  - "1-1-1" → "1 comprimido a cada 8 horas"
  - "2-0-1" → "2 comprimidos manhã e 1 comprimido noite"
  - "0-0-2" → "2 comprimidos noite"
  - Outros formatos ("1x/dia", "ao deitar") devem ser extraídos de forma limpa. Se ausente, "".

# ENTRADAS
<TEXTO_ALVO>
[O texto limpo com as medicações será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- INFORMAÇÕES GERAIS DA TERAPIA DOMICILIAR ---
- adesao_global (string): EXATAMENTE "Uso Regular", "Uso Irregular" ou "Desconhecido". Uso Regular = paciente usa medicações conforme prescrito; Uso Irregular = não adere bem; Desconhecido = não há informação. Se ausente, "".
- alergia (string): EXATAMENTE "Desconhecido", "Nega" ou "Presente". Desconhecido = não há informação; Nega = paciente nega alergias; Presente = há alergias. Se não mencionado, "".
- alergia_obs (string): Quando alergia = "Presente", liste as alergias (ex: "Penicilina", "Dipirona"). Se ausente, "".

# --- MEDICAÇÕES DE USO CONTÍNUO (MÁXIMO 20) ---
# 1. NOMES DOS FÁRMACOS (Ordem do texto original. Apenas o princípio ativo)
- med_dom_1_nome (string): Nome da 1ª medicação.
- med_dom_2_nome (string): Nome da 2ª medicação.
- med_dom_3_nome (string): Nome da 3ª medicação.
- med_dom_4_nome (string): Nome da 4ª medicação.
- med_dom_5_nome (string): Nome da 5ª medicação.
- med_dom_6_nome (string): Nome da 6ª medicação.
- med_dom_7_nome (string): Nome da 7ª medicação.
- med_dom_8_nome (string): Nome da 8ª medicação.
- med_dom_9_nome (string): Nome da 9ª medicação.
- med_dom_10_nome (string): Nome da 10ª medicação.
- med_dom_11_nome (string): Nome da 11ª medicação.
- med_dom_12_nome (string): Nome da 12ª medicação.
- med_dom_13_nome (string): Nome da 13ª medicação.
- med_dom_14_nome (string): Nome da 14ª medicação.
- med_dom_15_nome (string): Nome da 15ª medicação.
- med_dom_16_nome (string): Nome da 16ª medicação.
- med_dom_17_nome (string): Nome da 17ª medicação.
- med_dom_18_nome (string): Nome da 18ª medicação.
- med_dom_19_nome (string): Nome da 19ª medicação.
- med_dom_20_nome (string): Nome da 20ª medicação.

# 2. DOSES DOS FÁRMACOS (Valor e unidade)
- med_dom_1_dose (string): Dose da 1ª medicação.
- med_dom_2_dose (string): Dose da 2ª medicação.
- med_dom_3_dose (string): Dose da 3ª medicação.
- med_dom_4_dose (string): Dose da 4ª medicação.
- med_dom_5_dose (string): Dose da 5ª medicação.
- med_dom_6_dose (string): Dose da 6ª medicação.
- med_dom_7_dose (string): Dose da 7ª medicação.
- med_dom_8_dose (string): Dose da 8ª medicação.
- med_dom_9_dose (string): Dose da 9ª medicação.
- med_dom_10_dose (string): Dose da 10ª medicação.
- med_dom_11_dose (string): Dose da 11ª medicação.
- med_dom_12_dose (string): Dose da 12ª medicação.
- med_dom_13_dose (string): Dose da 13ª medicação.
- med_dom_14_dose (string): Dose da 14ª medicação.
- med_dom_15_dose (string): Dose da 15ª medicação.
- med_dom_16_dose (string): Dose da 16ª medicação.
- med_dom_17_dose (string): Dose da 17ª medicação.
- med_dom_18_dose (string): Dose da 18ª medicação.
- med_dom_19_dose (string): Dose da 19ª medicação.
- med_dom_20_dose (string): Dose da 20ª medicação.

# 3. FREQUÊNCIAS / POSOLOGIAS (Padrão texto traduzido)
- med_dom_1_freq (string): Frequência da 1ª medicação.
- med_dom_2_freq (string): Frequência da 2ª medicação.
- med_dom_3_freq (string): Frequência da 3ª medicação.
- med_dom_4_freq (string): Frequência da 4ª medicação.
- med_dom_5_freq (string): Frequência da 5ª medicação.
- med_dom_6_freq (string): Frequência da 6ª medicação.
- med_dom_7_freq (string): Frequência da 7ª medicação.
- med_dom_8_freq (string): Frequência da 8ª medicação.
- med_dom_9_freq (string): Frequência da 9ª medicação.
- med_dom_10_freq (string): Frequência da 10ª medicação.
- med_dom_11_freq (string): Frequência da 11ª medicação.
- med_dom_12_freq (string): Frequência da 12ª medicação.
- med_dom_13_freq (string): Frequência da 13ª medicação.
- med_dom_14_freq (string): Frequência da 14ª medicação.
- med_dom_15_freq (string): Frequência da 15ª medicação.
- med_dom_16_freq (string): Frequência da 16ª medicação.
- med_dom_17_freq (string): Frequência da 17ª medicação.
- med_dom_18_freq (string): Frequência da 18ª medicação.
- med_dom_19_freq (string): Frequência da 19ª medicação.
- med_dom_20_freq (string): Frequência da 20ª medicação.

# EXEMPLO DE SAÍDA PERFEITA
{
  "adesao_global": "Uso Regular",
  "alergia": "Presente",
  "alergia_obs": "Penicilina, Sulfa",
  "med_dom_1_nome": "Enalapril",
  "med_dom_2_nome": "Metformina",
  "med_dom_3_nome": "Glibenclamida",
  "med_dom_4_nome": "Acido Acetilsalicilico",
  "med_dom_5_nome": "Sinvastatina",
  "med_dom_6_nome": "Levotiroxina",
  "med_dom_7_nome": "Carvedilol",
  "med_dom_8_nome": "Furosemida",
  "med_dom_9_nome": "Espironolactona",
  "med_dom_10_nome": "Apixabana",
  "med_dom_11_nome": "",
  "med_dom_12_nome": "",
  "med_dom_13_nome": "",
  "med_dom_14_nome": "",
  "med_dom_15_nome": "",
  "med_dom_16_nome": "",
  "med_dom_17_nome": "",
  "med_dom_18_nome": "",
  "med_dom_19_nome": "",
  "med_dom_20_nome": "",
  "med_dom_1_dose": "10mg",
  "med_dom_2_dose": "850mg",
  "med_dom_3_dose": "5mg",
  "med_dom_4_dose": "100mg",
  "med_dom_5_dose": "40mg",
  "med_dom_6_dose": "50mcg",
  "med_dom_7_dose": "25mg",
  "med_dom_8_dose": "40mg",
  "med_dom_9_dose": "25mg",
  "med_dom_10_dose": "2.5mg",
  "med_dom_11_dose": "",
  "med_dom_12_dose": "",
  "med_dom_13_dose": "",
  "med_dom_14_dose": "",
  "med_dom_15_dose": "",
  "med_dom_16_dose": "",
  "med_dom_17_dose": "",
  "med_dom_18_dose": "",
  "med_dom_19_dose": "",
  "med_dom_20_dose": "",
  "med_dom_1_freq": "12/12h",
  "med_dom_2_freq": "1 comprimido manhã e noite",
  "med_dom_3_freq": "1x ao dia",
  "med_dom_4_freq": "1x ao dia",
  "med_dom_5_freq": "ao deitar",
  "med_dom_6_freq": "1x ao dia (jejum)",
  "med_dom_7_freq": "12/12h",
  "med_dom_8_freq": "1x ao dia",
  "med_dom_9_freq": "1x ao dia",
  "med_dom_10_freq": "12/12h",
  "med_dom_11_freq": "",
  "med_dom_12_freq": "",
  "med_dom_13_freq": "",
  "med_dom_14_freq": "",
  "med_dom_15_freq": "",
  "med_dom_16_freq": "",
  "med_dom_17_freq": "",
  "med_dom_18_freq": "",
  "med_dom_19_freq": "",
  "med_dom_20_freq": ""
}
</VARIAVEIS>"""


def preencher_muc(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_MUC, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}

    # Adesão: mapear para pills ["Uso Regular", "Uso Irregular", "Desconhecido"]
    v_adesao = _s("adesao_global").strip().lower()
    if v_adesao in ("uso regular", "regular", "regularmente"):
        resultado["muc_adesao_global"] = "Uso Regular"
    elif v_adesao in ("uso irregular", "irregular", "irregularmente"):
        resultado["muc_adesao_global"] = "Uso Irregular"
    elif v_adesao in ("desconhecido", "desconhecida", "nao informado", "não informado"):
        resultado["muc_adesao_global"] = "Desconhecido"
    else:
        resultado["muc_adesao_global"] = None if not v_adesao else "Desconhecido"
    # Alergia: Desconhecido, Nega, Presente + obs
    v = _s("alergia")
    resultado["muc_alergia"] = v if v in ("Desconhecido", "Nega", "Presente") else None
    resultado["muc_alergia_obs"] = _s("alergia_obs")

    for i in range(1, 21):
        resultado[f"muc_{i}_nome"] = _s(f"med_dom_{i}_nome")
        resultado[f"muc_{i}_dose"] = _s(f"med_dom_{i}_dose")
        resultado[f"muc_{i}_freq"] = _s(f"med_dom_{i}_freq")

    return resultado
