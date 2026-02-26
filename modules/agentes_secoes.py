"""
12 agentes de IA para preencher os campos estruturados de cada seção
a partir do texto já fatiado pelo ia_extrator.
"""
import json
import re
import streamlit as st
from openai import OpenAI
import google.generativeai as genai


def _extrair_json(texto: str) -> dict | None:
    """Extrai JSON de texto que pode conter markdown ou explicações."""
    if not texto or not texto.strip():
        return None
    txt = texto.strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```\s*$", "", txt)
    txt = txt.strip()
    match = re.search(r"\{[\s\S]*\}", txt)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return None


def _chamar_ia(prompt_system: str, texto: str, api_key: str, provider: str, modelo: str) -> dict:
    """Helper: envia texto para a IA e retorna JSON parseado."""
    try:
        if "OpenAI" in provider or "GPT" in provider:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=modelo if modelo.startswith("gpt") else "gpt-4o",
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user",   "content": f"TEXTO DA SEÇÃO:\n\n{texto}"}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=modelo if modelo.startswith("gemini") else "gemini-2.5-flash",
                system_instruction=prompt_system
            )
            resp = model.generate_content(f"TEXTO DA SEÇÃO:\n\n{texto}")
            txt = (resp.text or "").replace("```json", "").replace("```", "").strip()
            parsed = _extrair_json(txt)
            if parsed is not None:
                return parsed
            return json.loads(txt)
    except json.JSONDecodeError as e:
        return {"_erro": f"JSON inválido: {e}"}
    except Exception as e:
        return {"_erro": str(e)}


# ==============================================================================
# AGENTE 1: IDENTIFICAÇÃO
# ==============================================================================
_PROMPT_IDENTIFICACAO = """# CONTEXTO
Você é uma ferramenta usada para análise e extração de dados estruturados de textos clínicos hospitalares.

# OBJETIVO
Ler o texto fornecido pelo usuário e extrair as respostas exatas para as informações solicitadas na tag <VARIAVEIS>.

# REGRAS DE EXTRAÇÃO E FORMATAÇÃO
1. Responda de forma direta, concisa e objetiva.
2. Se a informação não constar explicitamente no texto, retorne estritamente o valor `null` no JSON. Não use variações como "Não encontrado", "Vazio" ou "".
3. Para perguntas de Sim ou Não, utilize valores booleanos padronizados: `true` para Sim e `false` para Não. Caso não encontre, retorne `null`.
4. Não faça presunções ou deduções além do que está escrito no texto.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem textos introdutórios, explicações ou blocos de código markdown ao redor.

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico será fornecido na mensagem do usuário]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON:

- nome (string): Nome completo do paciente conforme escrito no texto.
- idade (number): Idade do paciente em anos. Retornar apenas o valor numérico inteiro (ex: 65). Ignorar meses ou dias — retornar somente os anos completos. Não incluir a palavra "anos" ou qualquer texto adicional.
- sexo (string): Sexo do paciente. Retornar EXATAMENTE "Masculino" ou "Feminino", mapeando automaticamente abreviações textuais (ex: "M", "Masc", "masc." → "Masculino"; "F", "Fem", "fem." → "Feminino"). Se não encontrado, null.
- prontuario (string): Número do prontuário ou número de registro hospitalar (HC). Retornar apenas o número como string.
- leito (string): Número ou identificação do leito do paciente (ex: "206A", "UTI-05", "Leito 3").
- origem (string): Procedência ou origem do paciente antes da internação atual (ex: "PS", "UPA", "Enfermaria", "Transferência hospitalar", "CC"). Texto literal do documento.
- equipe (string): Equipe médica responsável pelo paciente (ex: "Clínica Médica", "Cirurgia Geral", "Intensivismo"). Texto literal do documento.
- di_hosp (string): Data de internação hospitalar. Manter o formato original do texto (DD/MM/AAAA, MM/AAAA ou MM/AA). Se ausente, null.
- di_uti (string): Data de entrada na UTI. Manter o formato original do texto. Se ausente, null.
- di_enf (string): Data de entrada na enfermaria. Manter o formato original do texto. Se ausente, null.
- saps3 (number): Valor do escore SAPS 3. Retornar apenas o valor numérico inteiro (ex: 55). Se ausente, null.
- sofa_adm (number): Valor do escore SOFA na admissão. Retornar apenas o valor numérico inteiro (ex: 8). Se ausente, null.
- sofa_atual (number): Valor do escore SOFA atual ou mais recente. Retornar apenas o valor numérico inteiro. Se ausente, null.
- mrs (string): Valor da Escala de Rankin Modificada (mRS). Retornar apenas o número como string (ex: "2"). Se ausente, null.
- pps (string): Valor do Palliative Performance Scale (PPS). Retornar o valor como string (ex: "80%", "80"). Se ausente, null.
- cfs (string): Valor da Clinical Frailty Scale (Escala de Fragilidade Clínica). Retornar o valor como string (ex: "3", "5 - Levemente frágil"). Se ausente, null.
- paliativo (boolean): O paciente está em cuidados paliativos, conforto ou sem medidas de ressuscitação? true se mencionado explicitamente, false se explicitamente negado, null se não mencionado.
</VARIAVEIS>"""

def preencher_identificacao(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_IDENTIFICACAO, texto, api_key, provider, modelo)
    r.pop("_erro", None)
    # Campos numéricos inteiros: null/None → 0, converte string → int
    for k in ["sofa_adm", "sofa_atual"]:
        if k in r:
            try: r[k] = int(r[k]) if r[k] not in (None, "", "null") else 0
            except: r[k] = 0
    if "idade" in r:
        try: r["idade"] = int(r["idade"]) if r["idade"] not in (None, "", "null") else 0
        except: r["idade"] = 0
    # saps3: a IA retorna number, mas o widget é text_input → converte para string
    if "saps3" in r:
        r["saps3"] = str(int(r["saps3"])) if r["saps3"] not in (None, "", "null") else ""
    # Campos string: null/None → "" (campos de texto do formulário esperam string)
    for k in ["nome", "sexo", "prontuario", "leito", "origem", "equipe",
              "di_hosp", "di_uti", "di_enf", "mrs", "pps", "cfs"]:
        if r.get(k) is None:
            r[k] = ""
    # Booleano paliativo: null/None → False
    if "paliativo" in r:
        if r["paliativo"] is None:
            r["paliativo"] = False
        elif isinstance(r["paliativo"], str):
            r["paliativo"] = r["paliativo"].lower() in ("true", "sim", "yes", "1")
    return r


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
- NÃO considerar tabagismo isolado.

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

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
</VARIAVEIS>"""


def preencher_comorbidades(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_COMORBIDADES, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}
    for i in range(1, 11):
        resultado[f"cmd_{i}_nome"]  = _s(f"comorbidade_{i}_nome")
        resultado[f"cmd_{i}_class"] = _s(f"comorbidade_{i}_class")
    return resultado


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
- adesao_global (string): Relato sobre a adesão do paciente ao tratamento domiciliar (ex: "regular", "irregular"). Se ausente, "".

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
</VARIAVEIS>"""


def preencher_muc(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_MUC, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}

    resultado["muc_adesao_global"] = _s("adesao_global") or None

    for i in range(1, 21):
        resultado[f"muc_{i}_nome"] = _s(f"med_dom_{i}_nome")
        resultado[f"muc_{i}_dose"] = _s(f"med_dom_{i}_dose")
        resultado[f"muc_{i}_freq"] = _s(f"med_dom_{i}_freq")

    return resultado


# ==============================================================================
# AGENTE 5: HMPA — reescreve a HMA/HMP mantendo fidelidade absoluta
# ==============================================================================
_PROMPT_HMPA = """Você é um Especialista em Redação Médica e Comunicação Clínica de Alta Complexidade.

Sua tarefa é reescrever a História da Moléstia Atual (HMA) e História Patológica Pregressa (HMP) fornecidas, otimizando clareza, organização lógica e precisão técnica para leitura por outro médico intensivista.

════════════════════════════
REGRAS ABSOLUTAS (INVIOLÁVEIS)

FIDELIDADE INTEGRAL
- É terminantemente proibido adicionar, inferir, interpretar ou omitir qualquer dado factual.
- Não completar lacunas.
- Não reorganizar eventos de forma que altere significado clínico.
- Se o texto estiver ambíguo, manter a ambiguidade.

PROIBIÇÃO DE ALUCINAÇÃO
- Não introduzir hipóteses diagnósticas.
- Não introduzir exames ou condutas não descritas.
- Não melhorar o raciocínio clínico, apenas a redação.

INTEGRIDADE DO CONTEÚDO
- Todos os dados presentes devem permanecer na versão final.
- Nenhuma informação pode ser removida.

════════════════════════════
OBJETIVOS DA REESCRITA

ORGANIZAÇÃO CRONOLÓGICA
Sempre que possível, organizar na seguinte sequência lógica:
1. Antecedentes relevantes
2. Início dos sintomas
3. Evolução temporal
4. Atendimentos prévios
5. Admissão atual
6. Evolução até o momento descrito

Se a cronologia não estiver clara, reorganizar apenas com base nas informações explicitamente fornecidas.

MELHORIA DE CLAREZA
- Corrigir erros gramaticais e ortográficos.
- Corrigir concordância verbal e nominal.
- Transformar frases telegráficas em períodos médicos claros e objetivos.
- Eliminar repetições desnecessárias mantendo todo o conteúdo factual.

DENSIDADE INFORMATIVA
- Agrupar informações correlatas no mesmo parágrafo.
- Evitar fragmentação excessiva.
- Manter linguagem técnica adequada ao ambiente de terapia intensiva.

════════════════════════════
PADRONIZAÇÃO LINGUÍSTICA
- Utilizar português formal técnico.
- Manter terminologia médica adequada para comunicação médico-médico.
- Evitar siglas médicas incomuns ou regionais.
- Manter siglas amplamente reconhecidas (ex: UTI, IAM, AVC, PCR, DPOC, HAS).
- Corrigir erros grosseiros: "PACIEWNTE COMPARECEU A UPA." → "Paciente compareceu à UPA."

════════════════════════════
FORMATO DE SAÍDA
- Retornar apenas o texto reescrito.
- Não incluir comentários, explicações ou títulos adicionais.
- Texto contínuo, pronto para colar no prontuário."""

def preencher_hmpa(texto, api_key, provider, modelo):
    if not texto or not texto.strip():
        return {}

    try:
        if "OpenAI" in provider or "GPT" in provider:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=modelo if modelo.startswith("gpt") else "gpt-4o",
                messages=[
                    {"role": "system", "content": _PROMPT_HMPA},
                    {"role": "user",   "content": f"Texto Original:\n\n{texto}"}
                ]
            )
            reescrito = resp.choices[0].message.content.strip()
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=modelo if modelo.startswith("gemini") else "gemini-2.5-flash",
                system_instruction=_PROMPT_HMPA
            )
            resp = model.generate_content(f"Texto Original:\n\n{texto}")
            reescrito = resp.text.strip()

        return {"hmpa_reescrito": reescrito}

    except Exception as e:
        return {"_erro": str(e)}


# ==============================================================================
# AGENTE 6: DISPOSITIVOS INVASIVOS
# ==============================================================================
_PROMPT_DISPOSITIVOS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair exclusivamente os dispositivos invasivos, respeitando rigorosamente a ordem arquitetural e de leitura.

# DEFINIÇÃO OPERACIONAL
Dispositivo invasivo = qualquer dispositivo inserido com permanência para monitorização, terapia ou suporte.
Exemplos válidos: CVC, PICC, TOT, TQT, SVD, SNE, SNG, PAM, PIC, Cateter Arterial, Cateter de Hemodiálise, Dreno Torácico.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ORDEM DE LEITURA E PREENCHIMENTO: Você DEVE preencher o JSON na exata ordem das chaves solicitadas abaixo. Primeiro todos os Nomes, depois todos os Locais, Datas e Status.
2. CRONOLOGIA DO TEXTO: Liste os dispositivos na mesma ordem em que aparecem no texto fonte. NÃO reordene separando ativos de removidos.
3. PREENCHIMENTO VAZIO: O limite é de 8 dispositivos. Se a informação não constar explicitamente ou o paciente tiver menos dispositivos, retorne estritamente `""` (string vazia) para os slots sobressalentes. Não use `null`.
4. NÃO inferir. NÃO criar dispositivos não mencionados. NÃO preencher condutas.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# REGRAS DE EXCLUSÃO
- NÃO incluir dispositivos de oxigênio não invasivos (Cateter nasal, Máscara de Venturi, VNI).
- NÃO incluir dispositivos externos ou procedimentos sem permanência.

# PADRONIZAÇÕES OBRIGATÓRIAS
- NOME: Apenas a sigla padronizada (ex: CVC, TOT, SVD, PAM). Sem local, calibre ou data.
- LOCAL: Local anatômico (ex: "Jugular Direita", "Vesical"). Se não mencionado, "".
- STATUS: EXATAMENTE "Ativo" ou "Removido". Se o slot estiver preenchido com um dispositivo, este campo nunca pode estar vazio. Se o slot for sobressalente, preencha com "".

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico com os dispositivos será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- DISPOSITIVOS INVASIVOS (MÁXIMO 8) ---
# 1. NOMES DOS DISPOSITIVOS (Ordem do texto original. Apenas sigla padronizada)
- disp_1_nome (string): Sigla do 1º dispositivo.
- disp_2_nome (string): Sigla do 2º dispositivo.
- disp_3_nome (string): Sigla do 3º dispositivo.
- disp_4_nome (string): Sigla do 4º dispositivo.
- disp_5_nome (string): Sigla do 5º dispositivo.
- disp_6_nome (string): Sigla do 6º dispositivo.
- disp_7_nome (string): Sigla do 7º dispositivo.
- disp_8_nome (string): Sigla do 8º dispositivo.

# 2. LOCAIS ANATÔMICOS (Referentes aos dispositivos acima)
- disp_1_local (string): Local do 1º dispositivo.
- disp_2_local (string): Local do 2º dispositivo.
- disp_3_local (string): Local do 3º dispositivo.
- disp_4_local (string): Local do 4º dispositivo.
- disp_5_local (string): Local do 5º dispositivo.
- disp_6_local (string): Local do 6º dispositivo.
- disp_7_local (string): Local do 7º dispositivo.
- disp_8_local (string): Local do 8º dispositivo.

# 3. DATAS DE INSERÇÃO (Manter formato original do texto)
- disp_1_data_in (string): Data de inserção do 1º dispositivo.
- disp_2_data_in (string): Data de inserção do 2º dispositivo.
- disp_3_data_in (string): Data de inserção do 3º dispositivo.
- disp_4_data_in (string): Data de inserção do 4º dispositivo.
- disp_5_data_in (string): Data de inserção do 5º dispositivo.
- disp_6_data_in (string): Data de inserção do 6º dispositivo.
- disp_7_data_in (string): Data de inserção do 7º dispositivo.
- disp_8_data_in (string): Data de inserção do 8º dispositivo.

# 4. DATAS DE RETIRADA (Preencher apenas se a retirada for explícita. Senão, "")
- disp_1_data_out (string): Data de retirada do 1º dispositivo.
- disp_2_data_out (string): Data de retirada do 2º dispositivo.
- disp_3_data_out (string): Data de retirada do 3º dispositivo.
- disp_4_data_out (string): Data de retirada do 4º dispositivo.
- disp_5_data_out (string): Data de retirada do 5º dispositivo.
- disp_6_data_out (string): Data de retirada do 6º dispositivo.
- disp_7_data_out (string): Data de retirada do 7º dispositivo.
- disp_8_data_out (string): Data de retirada do 8º dispositivo.

# 5. STATUS (Estritamente "Ativo" ou "Removido")
- disp_1_status (string): Status do 1º dispositivo.
- disp_2_status (string): Status do 2º dispositivo.
- disp_3_status (string): Status do 3º dispositivo.
- disp_4_status (string): Status do 4º dispositivo.
- disp_5_status (string): Status do 5º dispositivo.
- disp_6_status (string): Status do 6º dispositivo.
- disp_7_status (string): Status do 7º dispositivo.
- disp_8_status (string): Status do 8º dispositivo.
</VARIAVEIS>"""


def preencher_dispositivos(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_DISPOSITIVOS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}
    for i in range(1, 9):
        nome   = _s(f"disp_{i}_nome")
        status = _s(f"disp_{i}_status")
        resultado[f"disp_{i}_nome"]          = nome
        resultado[f"disp_{i}_local"]         = _s(f"disp_{i}_local")
        resultado[f"disp_{i}_data_insercao"] = _s(f"disp_{i}_data_in")
        resultado[f"disp_{i}_data_retirada"] = _s(f"disp_{i}_data_out")
        resultado[f"disp_{i}_status"]        = status if nome else None
    return resultado


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


# ==============================================================================
# AGENTE 8: ANTIBIÓTICOS
# ==============================================================================
_PROMPT_ANTIBIOTICOS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair os agentes antimicrobianos (Atuais e Prévios), respeitando rigorosamente a ordem arquitetural e de leitura do texto.

# CLASSIFICAÇÃO
- ATUAIS: Em uso no momento, sem suspensão documentada.
- PRÉVIOS: Suspensos, eventos passados com data de término ou suspensão explícita.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ORDEM DE LEITURA E PREENCHIMENTO: Você DEVE preencher o JSON na exata ordem das chaves solicitadas abaixo. Preencha todos os blocos de "Atuais" primeiro (Nomes, Focos, Tipos, Datas), depois os blocos de "Prévios".
2. CRONOLOGIA DO TEXTO: Liste os antibióticos na mesma ordem em que aparecem no texto fonte.
3. PREENCHIMENTO VAZIO: O limite é de 5 atuais e 5 prévios. Se a informação não constar explicitamente ou o paciente tiver menos itens, retorne estritamente `""` (string vazia) para os slots sobressalentes. Não use `null`.
4. CONDUTAS: O campo de conduta ("_conduta") e notas ("_notas") é de preenchimento manual do médico. A IA deve preenchê-los SEMPRE com `""`.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# PADRONIZAÇÕES OBRIGATÓRIAS
- NOME: DCI (Denominação Comum Internacional), Title Case. Sem dose ou frequência. Ex: "Meropenem", "Fluconazol".
- FOCO: Title Case. Ex: "PAV", "ITU", "Bacteremia". Se ausente, "".
- TIPO: Deve ser EXATAMENTE "Empírico", "Guiado por Cultura", ou "".
- OBSERVAÇÕES (Apenas para Prévios): Motivo da suspensão. Sem condutas. Se ausente, "".
- DATAS: Manter o formato original do texto.

# ENTRADAS
<TEXTO_ALVO>
[O texto limpo com os antibióticos será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- ANTIBIÓTICOS ATUAIS (MÁXIMO 5) ---
# 1. NOMES DOS ATUAIS (Ordem do texto original. DCI, Title Case)
- atb_curr_1_nome (string): Nome do 1º ATB atual.
- atb_curr_2_nome (string): Nome do 2º ATB atual.
- atb_curr_3_nome (string): Nome do 3º ATB atual.
- atb_curr_4_nome (string): Nome do 4º ATB atual.
- atb_curr_5_nome (string): Nome do 5º ATB atual.

# 2. FOCOS DOS ATUAIS (Title Case. Ex: PAV, ITU. Se ausente, "")
- atb_curr_1_foco (string): Foco do 1º ATB atual.
- atb_curr_2_foco (string): Foco do 2º ATB atual.
- atb_curr_3_foco (string): Foco do 3º ATB atual.
- atb_curr_4_foco (string): Foco do 4º ATB atual.
- atb_curr_5_foco (string): Foco do 5º ATB atual.

# 3. TIPOS DOS ATUAIS (Exatamente "Empírico", "Guiado por Cultura" ou "")
- atb_curr_1_tipo (string): Tipo do 1º ATB atual.
- atb_curr_2_tipo (string): Tipo do 2º ATB atual.
- atb_curr_3_tipo (string): Tipo do 3º ATB atual.
- atb_curr_4_tipo (string): Tipo do 4º ATB atual.
- atb_curr_5_tipo (string): Tipo do 5º ATB atual.

# 4. DATAS DE INÍCIO DOS ATUAIS (Formato original)
- atb_curr_1_data_ini (string): Data início do 1º ATB atual.
- atb_curr_2_data_ini (string): Data início do 2º ATB atual.
- atb_curr_3_data_ini (string): Data início do 3º ATB atual.
- atb_curr_4_data_ini (string): Data início do 4º ATB atual.
- atb_curr_5_data_ini (string): Data início do 5º ATB atual.

# 5. DATAS DE FIM DOS ATUAIS (Geralmente "" se está ativo, ou data programada)
- atb_curr_1_data_fim (string): Data fim do 1º ATB atual.
- atb_curr_2_data_fim (string): Data fim do 2º ATB atual.
- atb_curr_3_data_fim (string): Data fim do 3º ATB atual.
- atb_curr_4_data_fim (string): Data fim do 4º ATB atual.
- atb_curr_5_data_fim (string): Data fim do 5º ATB atual.

# 6. CONDUTAS DOS ATUAIS (Sempre "")
- atb_curr_1_conduta (string): "".
- atb_curr_2_conduta (string): "".
- atb_curr_3_conduta (string): "".
- atb_curr_4_conduta (string): "".
- atb_curr_5_conduta (string): "".

# --- ANTIBIÓTICOS PRÉVIOS (MÁXIMO 5) ---
# 1. NOMES DOS PRÉVIOS
- atb_prev_1_nome (string): Nome do 1º ATB prévio.
- atb_prev_2_nome (string): Nome do 2º ATB prévio.
- atb_prev_3_nome (string): Nome do 3º ATB prévio.
- atb_prev_4_nome (string): Nome do 4º ATB prévio.
- atb_prev_5_nome (string): Nome do 5º ATB prévio.

# 2. FOCOS DOS PRÉVIOS
- atb_prev_1_foco (string): Foco do 1º ATB prévio.
- atb_prev_2_foco (string): Foco do 2º ATB prévio.
- atb_prev_3_foco (string): Foco do 3º ATB prévio.
- atb_prev_4_foco (string): Foco do 4º ATB prévio.
- atb_prev_5_foco (string): Foco do 5º ATB prévio.

# 3. TIPOS DOS PRÉVIOS
- atb_prev_1_tipo (string): Tipo do 1º ATB prévio.
- atb_prev_2_tipo (string): Tipo do 2º ATB prévio.
- atb_prev_3_tipo (string): Tipo do 3º ATB prévio.
- atb_prev_4_tipo (string): Tipo do 4º ATB prévio.
- atb_prev_5_tipo (string): Tipo do 5º ATB prévio.

# 4. DATAS DE INÍCIO DOS PRÉVIOS
- atb_prev_1_data_ini (string): Data início do 1º ATB prévio.
- atb_prev_2_data_ini (string): Data início do 2º ATB prévio.
- atb_prev_3_data_ini (string): Data início do 3º ATB prévio.
- atb_prev_4_data_ini (string): Data início do 4º ATB prévio.
- atb_prev_5_data_ini (string): Data início do 5º ATB prévio.

# 5. DATAS DE FIM DOS PRÉVIOS
- atb_prev_1_data_fim (string): Data fim do 1º ATB prévio.
- atb_prev_2_data_fim (string): Data fim do 2º ATB prévio.
- atb_prev_3_data_fim (string): Data fim do 3º ATB prévio.
- atb_prev_4_data_fim (string): Data fim do 4º ATB prévio.
- atb_prev_5_data_fim (string): Data fim do 5º ATB prévio.

# 6. OBSERVAÇÕES DOS PRÉVIOS (Motivo da suspensão/desfecho)
- atb_prev_1_obs (string): Observação do 1º ATB prévio.
- atb_prev_2_obs (string): Observação do 2º ATB prévio.
- atb_prev_3_obs (string): Observação do 3º ATB prévio.
- atb_prev_4_obs (string): Observação do 4º ATB prévio.
- atb_prev_5_obs (string): Observação do 5º ATB prévio.

# 7. CONDUTAS DOS PRÉVIOS (Sempre "")
- atb_prev_1_conduta (string): "".
- atb_prev_2_conduta (string): "".
- atb_prev_3_conduta (string): "".
- atb_prev_4_conduta (string): "".
- atb_prev_5_conduta (string): "".

# --- NOTAS GERAIS ---
- antibioticos_notas (string): "".
</VARIAVEIS>"""


_TIPO_ATB = {"Empírico", "Guiado por Cultura"}


def preencher_antibioticos(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_ANTIBIOTICOS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}

    for i in range(1, 6):
        nome = _s(f"atb_curr_{i}_nome")
        tipo = _s(f"atb_curr_{i}_tipo")
        resultado[f"atb_curr_{i}_nome"]     = nome
        resultado[f"atb_curr_{i}_foco"]     = _s(f"atb_curr_{i}_foco")
        resultado[f"atb_curr_{i}_tipo"]     = tipo if tipo in _TIPO_ATB else (None if not nome else "")
        resultado[f"atb_curr_{i}_data_ini"] = _s(f"atb_curr_{i}_data_ini")
        resultado[f"atb_curr_{i}_data_fim"] = _s(f"atb_curr_{i}_data_fim")

    for i in range(1, 6):
        nome = _s(f"atb_prev_{i}_nome")
        tipo = _s(f"atb_prev_{i}_tipo")
        resultado[f"atb_prev_{i}_nome"]     = nome
        resultado[f"atb_prev_{i}_foco"]     = _s(f"atb_prev_{i}_foco")
        resultado[f"atb_prev_{i}_tipo"]     = tipo if tipo in _TIPO_ATB else (None if not nome else "")
        resultado[f"atb_prev_{i}_data_ini"] = _s(f"atb_prev_{i}_data_ini")
        resultado[f"atb_prev_{i}_data_fim"] = _s(f"atb_prev_{i}_data_fim")
        resultado[f"atb_prev_{i}_obs"]      = _s(f"atb_prev_{i}_obs")

    return resultado


# ==============================================================================
# AGENTE 9: COMPLEMENTARES
# ==============================================================================
_PROMPT_COMPLEMENTARES = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair EXCLUSIVAMENTE os Exames Complementares, respeitando rigorosamente a ordem arquitetural e de leitura do texto.

# DEFINIÇÃO OPERACIONAL E FILTRO DE RUÍDO
- VÁLIDOS: Exames não laboratoriais com laudo descritivo/interpretativo. Exemplos: TC, RX, RNM, USG, PET-CT, Ecocardiograma, ECG, Holter, Endoscopia e Pareceres.
- FILTRO DE LAUDO (RUÍDO): O texto pode conter laudos extensos com descrições de estruturas normais (ex: "vesícula normal", "fígado de dimensões conservadas"). IGNORE completamente essas normalidades irrelevantes.
- FOCO DE EXTRAÇÃO: Extraia EXCLUSIVAMENTE achados clinicamente relevantes, alterações patológicas e a conclusão principal do exame.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ORDEM DE LEITURA E PREENCHIMENTO: Você DEVE preencher o JSON na exata ordem das chaves solicitadas abaixo. Primeiro todos os Nomes, depois Datas, Laudos/Conclusões e Condutas.
2. CRONOLOGIA DO TEXTO: Liste os exames na exata ordem em que aparecem no texto fonte. NÃO tente reordenar por data.
3. PREENCHIMENTO VAZIO: O limite é de 8 exames. Se o paciente tiver menos itens ou a informação faltar, retorne estritamente `""` (string vazia) para os slots sobressalentes. Não use `null`.
4. CONDUTAS E NOTAS: Os campos "_conduta" e "_notas" são de entrada manual do médico. A IA deve preenchê-los SEMPRE com `""`.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# PADRONIZAÇÕES OBRIGATÓRIAS
- NOME: Nome completo do exame, em Title Case. Ex: "Tomografia Computadorizada de Crânio Sem Contraste", "Ecocardiograma Transtorácico".
- DATA: Manter o formato original do texto (preferencialmente DD/MM/AAAA). Se ausente, "".
- LAUDO (CONCLUSÕES): Sintetize as alterações e a conclusão de forma objetiva, direta e sem enrolação estrutural.

# ENTRADAS
<TEXTO_ALVO>
[O texto contendo os exames complementares será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- EXAMES COMPLEMENTARES (MÁXIMO 8) ---
# 1. NOME DOS EXAMES (Ordem do texto original. Title Case)
- comp_1_exame (string): Nome do 1º exame citado.
- comp_2_exame (string): Nome do 2º exame citado.
- comp_3_exame (string): Nome do 3º exame citado.
- comp_4_exame (string): Nome do 4º exame citado.
- comp_5_exame (string): Nome do 5º exame citado.
- comp_6_exame (string): Nome do 6º exame citado.
- comp_7_exame (string): Nome do 7º exame citado.
- comp_8_exame (string): Nome do 8º exame citado.

# 2. DATAS DOS EXAMES
- comp_1_data (string): Data do 1º exame.
- comp_2_data (string): Data do 2º exame.
- comp_3_data (string): Data do 3º exame.
- comp_4_data (string): Data do 4º exame.
- comp_5_data (string): Data do 5º exame.
- comp_6_data (string): Data do 6º exame.
- comp_7_data (string): Data do 7º exame.
- comp_8_data (string): Data do 8º exame.

# 3. LAUDOS / CONCLUSÕES (Apenas alterações e conclusão. Excluir normalidades)
- comp_1_laudo (string): Conclusão/Achados do 1º exame.
- comp_2_laudo (string): Conclusão/Achados do 2º exame.
- comp_3_laudo (string): Conclusão/Achados do 3º exame.
- comp_4_laudo (string): Conclusão/Achados do 4º exame.
- comp_5_laudo (string): Conclusão/Achados do 5º exame.
- comp_6_laudo (string): Conclusão/Achados do 6º exame.
- comp_7_laudo (string): Conclusão/Achados do 7º exame.
- comp_8_laudo (string): Conclusão/Achados do 8º exame.

# 4. CONDUTAS (Sempre "")
- comp_1_conduta (string): "".
- comp_2_conduta (string): "".
- comp_3_conduta (string): "".
- comp_4_conduta (string): "".
- comp_5_conduta (string): "".
- comp_6_conduta (string): "".
- comp_7_conduta (string): "".
- comp_8_conduta (string): "".

# --- NOTAS GERAIS ---
- complementares_notas (string): "".
</VARIAVEIS>"""


def preencher_complementares(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_COMPLEMENTARES, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}
    for i in range(1, 9):
        resultado[f"comp_{i}_exame"] = _s(f"comp_{i}_exame")
        resultado[f"comp_{i}_data"]  = _s(f"comp_{i}_data")
        resultado[f"comp_{i}_laudo"] = _s(f"comp_{i}_laudo")

    return resultado


# ==============================================================================
# AGENTE 10: LABORATORIAIS
# ==============================================================================
_PROMPT_LABORATORIAIS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair os valores laboratoriais e gasométricos. Você deve preencher EXCLUSIVAMENTE três blocos:
- lab_1: conjunto de exames mais recente (pela data).
- lab_2: conjunto de exames imediatamente anterior (se disponível).
- lab_3: conjunto de exames terceiro mais recente (se disponível).

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ESTRUTURA PLANA: Preencha o JSON sequencialmente. Não utilize arrays ou listas aninhadas.
2. PREENCHIMENTO VAZIO: Se não houver exames suficientes para preencher os 3 blocos, retorne estritamente `""` (string vazia) para todos os campos dos blocos não utilizados. Não use `null` em hipótese alguma.
3. FIDELIDADE DOS DADOS: Mantenha o formato original das datas (DD/MM/AAAA ou DD/MM). Não calcule médias, não interprete valores, não infira unidades e não reorganize valores entre datas diferentes.
4. CONDUTAS E NOTAS: Os campos de conduta e notas laboratoriais são de entrada manual do médico. A IA deve preenchê-los SEMPRE com `""`.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# REGRAS DE MAPEAMENTO CLÍNICO
- HEMOGRAMA: Leuco deve incluir o diferencial se houver (Ex: "12500 (Seg 75% / Linf 15%)").
- RENAL E ELETRÓLITOS:
  - CaT (Cálcio Total) e CaI (Cálcio Iônico) são campos distintos.
  - O Cálcio Iônico extraído da gasometria deve ir OBRIGATORIAMENTE para a chave `cai` ou `gas_cai`, NUNCA para `cat`.
- HEPÁTICO:
  - Se o texto mostrar "BT 1,0 (0,3)", separe: `bt` = "1,0" e `bd` = "0,3".
- COAGULAÇÃO: Manter strings literais. Ex: `tp` = "14,2s (1,10)" ou "Ativ 60% (RNI 1,5)"; `ttpa` = "30,0s (1,00)".
- GASOMETRIA:
  - `gas_tipo`: "Arterial" ou "Venosa".
  - MISTA (Art + Ven na mesma data): `gas_tipo` = "Arterial". Preencha os campos arteriais normalmente. Jogue o pCO2 venoso para `gasv_pco2` e o SvO2 para `svo2`. NÃO duplique o lactato.
- OUTROS: Valores não mapeados nas chaves específicas (ex: PTH, TSH) devem ser concatenados na chave `outros` no formato "Exame Valor | Exame Valor".

# ENTRADAS
<TEXTO_ALVO>
[O texto com os exames laboratoriais será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- NOTAS GERAIS ---
- laboratoriais_notas (string): "".

# --- BLOCO LAB 1 (EXAMES MAIS RECENTES) ---
- lab_1_data (string): Data do conjunto mais recente.
- lab_1_hb (string): Hemoglobina.
- lab_1_ht (string): Hematócrito.
- lab_1_vcm (string): VCM.
- lab_1_hcm (string): HCM.
- lab_1_rdw (string): RDW.
- lab_1_leuco (string): Leucócitos (com diferencial, se houver).
- lab_1_plaq (string): Plaquetas.
- lab_1_cr (string): Creatinina.
- lab_1_ur (string): Ureia.
- lab_1_na (string): Sódio.
- lab_1_k (string): Potássio.
- lab_1_mg (string): Magnésio.
- lab_1_pi (string): Fósforo.
- lab_1_cat (string): Cálcio Total.
- lab_1_cai (string): Cálcio Iônico (sérico).
- lab_1_tgp (string): TGP / ALT.
- lab_1_tgo (string): TGO / AST.
- lab_1_fal (string): Fosfatase Alcalina.
- lab_1_ggt (string): GGT.
- lab_1_bt (string): Bilirrubina Total.
- lab_1_bd (string): Bilirrubina Direta.
- lab_1_prot_tot (string): Proteínas Totais.
- lab_1_alb (string): Albumina.
- lab_1_amil (string): Amilase.
- lab_1_lipas (string): Lipase.
- lab_1_cpk (string): CPK.
- lab_1_cpk_mb (string): CK-MB.
- lab_1_bnp (string): BNP / NT-proBNP.
- lab_1_trop (string): Troponina.
- lab_1_pcr (string): PCR.
- lab_1_vhs (string): VHS.
- lab_1_tp (string): Tempo de Protrombina (TAP / RNI).
- lab_1_ttpa (string): Tempo de Tromboplastina Parcial ativada.
- lab_1_gas_tipo (string): "Arterial", "Venosa" ou "".
- lab_1_gas_ph (string): pH da gasometria principal.
- lab_1_gas_pco2 (string): pCO2 da gasometria principal.
- lab_1_gas_po2 (string): pO2.
- lab_1_gas_hco3 (string): HCO3.
- lab_1_gas_be (string): Base Excess.
- lab_1_gas_sat (string): SatO2.
- lab_1_gas_lac (string): Lactato.
- lab_1_gas_ag (string): Anion Gap.
- lab_1_gas_cl (string): Cloreto da gasometria.
- lab_1_gas_na (string): Sódio da gasometria.
- lab_1_gas_k (string): Potássio da gasometria.
- lab_1_gas_cai (string): Cálcio Iônico da gasometria.
- lab_1_gasv_pco2 (string): pCO2 venoso (se gasometria mista).
- lab_1_svo2 (string): SvO2 (se gasometria mista).
- lab_1_ur_dens (string): Urina - Densidade.
- lab_1_ur_le (string): Urina - Esterase Leucocitária.
- lab_1_ur_nit (string): Urina - Nitrito.
- lab_1_ur_leu (string): Urina - Leucócitos.
- lab_1_ur_hm (string): Urina - Hemácias.
- lab_1_ur_prot (string): Urina - Proteínas.
- lab_1_ur_cet (string): Urina - Cetonas.
- lab_1_ur_glic (string): Urina - Glicose.
- lab_1_outros (string): Outros exames concatenados.
- lab_1_conduta (string): "".

# --- BLOCO LAB 2 (EXAMES ANTERIORES) ---
- lab_2_data (string): Data do conjunto anterior.
- lab_2_hb (string): Hemoglobina.
- lab_2_ht (string): Hematócrito.
- lab_2_vcm (string): VCM.
- lab_2_hcm (string): HCM.
- lab_2_rdw (string): RDW.
- lab_2_leuco (string): Leucócitos (com diferencial, se houver).
- lab_2_plaq (string): Plaquetas.
- lab_2_cr (string): Creatinina.
- lab_2_ur (string): Ureia.
- lab_2_na (string): Sódio.
- lab_2_k (string): Potássio.
- lab_2_mg (string): Magnésio.
- lab_2_pi (string): Fósforo.
- lab_2_cat (string): Cálcio Total.
- lab_2_cai (string): Cálcio Iônico (sérico).
- lab_2_tgp (string): TGP / ALT.
- lab_2_tgo (string): TGO / AST.
- lab_2_fal (string): Fosfatase Alcalina.
- lab_2_ggt (string): GGT.
- lab_2_bt (string): Bilirrubina Total.
- lab_2_bd (string): Bilirrubina Direta.
- lab_2_prot_tot (string): Proteínas Totais.
- lab_2_alb (string): Albumina.
- lab_2_amil (string): Amilase.
- lab_2_lipas (string): Lipase.
- lab_2_cpk (string): CPK.
- lab_2_cpk_mb (string): CK-MB.
- lab_2_bnp (string): BNP / NT-proBNP.
- lab_2_trop (string): Troponina.
- lab_2_pcr (string): PCR.
- lab_2_vhs (string): VHS.
- lab_2_tp (string): Tempo de Protrombina (TAP / RNI).
- lab_2_ttpa (string): Tempo de Tromboplastina Parcial ativada.
- lab_2_gas_tipo (string): "Arterial", "Venosa" ou "".
- lab_2_gas_ph (string): pH da gasometria principal.
- lab_2_gas_pco2 (string): pCO2 da gasometria principal.
- lab_2_gas_po2 (string): pO2.
- lab_2_gas_hco3 (string): HCO3.
- lab_2_gas_be (string): Base Excess.
- lab_2_gas_sat (string): SatO2.
- lab_2_gas_lac (string): Lactato.
- lab_2_gas_ag (string): Anion Gap.
- lab_2_gas_cl (string): Cloreto da gasometria.
- lab_2_gas_na (string): Sódio da gasometria.
- lab_2_gas_k (string): Potássio da gasometria.
- lab_2_gas_cai (string): Cálcio Iônico da gasometria.
- lab_2_gasv_pco2 (string): pCO2 venoso (se gasometria mista).
- lab_2_svo2 (string): SvO2 (se gasometria mista).
- lab_2_ur_dens (string): Urina - Densidade.
- lab_2_ur_le (string): Urina - Esterase Leucocitária.
- lab_2_ur_nit (string): Urina - Nitrito.
- lab_2_ur_leu (string): Urina - Leucócitos.
- lab_2_ur_hm (string): Urina - Hemácias.
- lab_2_ur_prot (string): Urina - Proteínas.
- lab_2_ur_cet (string): Urina - Cetonas.
- lab_2_ur_glic (string): Urina - Glicose.
- lab_2_outros (string): Outros exames concatenados.
- lab_2_conduta (string): "".

# --- BLOCO LAB 3 (EXAMES TERCEIRO MAIS RECENTES) ---
- lab_3_data (string): Data do 3º conjunto mais recente.
- lab_3_hb (string): Hemoglobina.
- lab_3_ht (string): Hematócrito.
- lab_3_vcm (string): VCM.
- lab_3_hcm (string): HCM.
- lab_3_rdw (string): RDW.
- lab_3_leuco (string): Leucócitos (com diferencial, se houver).
- lab_3_plaq (string): Plaquetas.
- lab_3_cr (string): Creatinina.
- lab_3_ur (string): Ureia.
- lab_3_na (string): Sódio.
- lab_3_k (string): Potássio.
- lab_3_mg (string): Magnésio.
- lab_3_pi (string): Fósforo.
- lab_3_cat (string): Cálcio Total.
- lab_3_cai (string): Cálcio Iônico (sérico).
- lab_3_tgp (string): TGP / ALT.
- lab_3_tgo (string): TGO / AST.
- lab_3_fal (string): Fosfatase Alcalina.
- lab_3_ggt (string): GGT.
- lab_3_bt (string): Bilirrubina Total.
- lab_3_bd (string): Bilirrubina Direta.
- lab_3_prot_tot (string): Proteínas Totais.
- lab_3_alb (string): Albumina.
- lab_3_amil (string): Amilase.
- lab_3_lipas (string): Lipase.
- lab_3_cpk (string): CPK.
- lab_3_cpk_mb (string): CK-MB.
- lab_3_bnp (string): BNP / NT-proBNP.
- lab_3_trop (string): Troponina.
- lab_3_pcr (string): PCR.
- lab_3_vhs (string): VHS.
- lab_3_tp (string): Tempo de Protrombina (TAP / RNI).
- lab_3_ttpa (string): Tempo de Tromboplastina Parcial ativada.
- lab_3_gas_tipo (string): "Arterial", "Venosa" ou "".
- lab_3_gas_ph (string): pH da gasometria principal.
- lab_3_gas_pco2 (string): pCO2 da gasometria principal.
- lab_3_gas_po2 (string): pO2.
- lab_3_gas_hco3 (string): HCO3.
- lab_3_gas_be (string): Base Excess.
- lab_3_gas_sat (string): SatO2.
- lab_3_gas_lac (string): Lactato.
- lab_3_gas_ag (string): Anion Gap.
- lab_3_gas_cl (string): Cloreto da gasometria.
- lab_3_gas_na (string): Sódio da gasometria.
- lab_3_gas_k (string): Potássio da gasometria.
- lab_3_gas_cai (string): Cálcio Iônico da gasometria.
- lab_3_gasv_pco2 (string): pCO2 venoso (se gasometria mista).
- lab_3_svo2 (string): SvO2 (se gasometria mista).
- lab_3_ur_dens (string): Urina - Densidade.
- lab_3_ur_le (string): Urina - Esterase Leucocitária.
- lab_3_ur_nit (string): Urina - Nitrito.
- lab_3_ur_leu (string): Urina - Leucócitos.
- lab_3_ur_hm (string): Urina - Hemácias.
- lab_3_ur_prot (string): Urina - Proteínas.
- lab_3_ur_cet (string): Urina - Cetonas.
- lab_3_ur_glic (string): Urina - Glicose.
- lab_3_outros (string): Outros exames concatenados.
- lab_3_conduta (string): "".
</VARIAVEIS>"""


def preencher_laboratoriais(texto, api_key, provider, modelo):
    if not texto or not str(texto).strip():
        return {"_erro": "Nenhum texto de exames fornecido. Cole os exames no campo de notas do Bloco 10."}
    r = _chamar_ia(_PROMPT_LABORATORIAIS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r
    r.pop("_erro", None)
    for i in (1, 2, 3):
        k = f"lab_{i}_gas_tipo"
        if k in r and r[k] in ("", None):
            r[k] = None
    return r


# ==============================================================================
# AGENTE 11: EVOLUÇÃO CLÍNICA (texto livre — passa direto)
# ==============================================================================
def preencher_evolucao(texto, api_key, provider, modelo):
    return {"evolucao_notas": texto.strip()} if texto and texto.strip() else {}


# ==============================================================================
# AGENTE 12: SISTEMAS
# ==============================================================================
_PROMPT_SISTEMAS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair os dados da Evolução por Sistemas, preenchendo o JSON de forma plana e sequencial.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ESTRUTURA PLANA: Preencha o JSON sequencialmente por blocos de sistema. Não utilize arrays.
2. REGRA PRIORITÁRIA (AUSÊNCIA ≠ NEGAÇÃO):
   - PRESENTE: Informação está no texto → Extraia o valor.
   - NEGADO: O texto diz explicitamente que não tem (ex: "sem febre") → "Não".
   - AUSENTE: O texto não menciona o parâmetro → Retorne o valor padrão (geralmente "" ou false).
3. PADRÕES DE DADOS:
   - Texto/Geral: ausente = "".
   - Sim/Não: ausente = ""; negado = "Não"; confirmado = "Sim".
   - Inteiros (Escalas/Escore): ausente = null.
   - Booleanos (Escapes): ausente = false.
4. CONDUTAS: Os campos `sis_{s}_conduta` são manuais. A IA deve preencher SEMPRE com `""`.
5. POCUS: Extraia achados de ultrassonografia à beira-leito mencionados em cada sistema específico.
6. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown.

# ENTRADAS
<TEXTO_ALVO>
[O texto da evolução clínica será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- 1. NEUROLÓGICO ---
- sis_neuro_ecg (string): Escala de Coma de Glasgow total.
- sis_neuro_ecg_ao (string): Glasgow - Abertura Ocular.
- sis_neuro_ecg_rv (string): Glasgow - Resposta Verbal.
- sis_neuro_ecg_rm (string): Glasgow - Resposta Motora.
- sis_neuro_ecg_p (string): Glasgow - Reatividade Pupilar.
- sis_neuro_rass (number): Escala de RASS (inteiro -5 a +5). null se ausente.
- sis_neuro_delirium (string): Presença de delirium (Sim/Não/"").
- sis_neuro_delirium_tipo (string): Tipo (Hiperativo/Hipoativo/Misto). "" se delirium ausente.
- sis_neuro_cam_icu (string): Resultado do CAM-ICU (Positivo/Negativo/"").
- sis_neuro_pupilas_tam (string): Tamanho das pupilas (Miótica/Normal/Midríase/"").
- sis_neuro_pupilas_simetria (string): Simetria (Simétricas/Anisocoria/"").
- sis_neuro_pupilas_foto (string): Fotorreatividade (Fotoreagente/Não fotoreagente/"").
- sis_neuro_analgesico_adequado (string): Dor controlada (Sim/Não/"").
- sis_neuro_deficits_focais (string): Descrição literal do déficit focal. "" se ausente.
- sis_neuro_deficits_ausente (string): "Ausente" se texto confirmar ausência de déficits. "" caso contrário.
- sis_neuro_analgesia_1_tipo (string): Tipo de analgesia (Fixa/Se necessário/"").
- sis_neuro_analgesia_1_drogas (string): Fármaco analgésico 1.
- sis_neuro_analgesia_1_dose (string): Dose (ex: "4mg IV").
- sis_neuro_analgesia_1_freq (string): Frequência (ex: "4/4h", "BIC", "ACM").
- sis_neuro_analgesia_2_tipo (string): Tipo de analgesia 2.
- sis_neuro_analgesia_2_drogas (string): Fármaco analgésico 2.
- sis_neuro_analgesia_2_dose (string): Dose 2.
- sis_neuro_analgesia_2_freq (string): Frequência 2.
- sis_neuro_analgesia_3_tipo (string): Tipo de analgesia 3.
- sis_neuro_analgesia_3_drogas (string): Fármaco analgésico 3.
- sis_neuro_analgesia_3_dose (string): Dose 3.
- sis_neuro_analgesia_3_freq (string): Frequência 3.
- sis_neuro_sedacao_meta (string): Alvo de RASS (ex: "RASS -2"). "" se ausente.
- sis_neuro_sedacao_1_drogas (string): Fármaco sedativo 1.
- sis_neuro_sedacao_1_dose (string): Dose sedativo 1.
- sis_neuro_sedacao_2_drogas (string): Fármaco sedativo 2.
- sis_neuro_sedacao_2_dose (string): Dose sedativo 2.
- sis_neuro_sedacao_3_drogas (string): Fármaco sedativo 3.
- sis_neuro_sedacao_3_dose (string): Dose sedativo 3.
- sis_neuro_bloqueador_med (string): Bloqueador neuromuscular (BNM). "" se ausente.
- sis_neuro_bloqueador_dose (string): Dose do BNM.
- sis_neuro_pocus (string): POCUS neuro (ex: diâmetro bainha nervo óptico). "" se ausente.
- sis_neuro_obs (string): Observações neurológicas livres.
- sis_neuro_conduta (string): "".

# --- 2. RESPIRATÓRIO ---
- sis_resp_ausculta (string): Descrição da ausculta pulmonar.
- sis_resp_modo (string): Tipo de suporte (Ar Ambiente/Oxigenoterapia/VNI/Cateter de Alto Fluxo/Ventilação Mecânica/"").
- sis_resp_modo_vent (string): Modo ventilatório (VCV/PCV/PSV/""). Preencher só se em VM.
- sis_resp_oxigenio_modo (string): Interface O2 (ex: Cateter Nasal, Máscara Venturi). Só se Oxigenoterapia.
- sis_resp_oxigenio_fluxo (string): Fluxo em L/min. Só se Oxigenoterapia.
- sis_resp_pressao (string): Pressão inspiratória ou suporte (ex: "18").
- sis_resp_volume (string): Volume corrente (ex: "480").
- sis_resp_fio2 (string): FiO2 em % (ex: "45").
- sis_resp_peep (string): PEEP (ex: "8").
- sis_resp_freq (string): Frequência respiratória total (ex: "16").
- sis_resp_vent_protetora (string): Ventilação protetora (Sim/Não/"").
- sis_resp_sincronico (string): Paciente sincrônico (Sim/Não/"").
- sis_resp_assincronia (string): Tipo de assincronia (ex: "Double trigger"). "" se sincrônico.
- sis_resp_complacencia (string): Complacência estática.
- sis_resp_resistencia (string): Resistência de vias aéreas.
- sis_resp_dp (string): Driving Pressure.
- sis_resp_plato (string): Pressão de Platô.
- sis_resp_pico (string): Pressão de Pico.
- sis_resp_dreno_1 (string): Localização do dreno 1 (ex: "Pleural D").
- sis_resp_dreno_1_debito (string): Débito/Aspecto do dreno 1 (ex: "180mL/dia").
- sis_resp_dreno_2 (string): Localização do dreno 2.
- sis_resp_dreno_2_debito (string): Débito dreno 2.
- sis_resp_dreno_3 (string): Localização do dreno 3.
- sis_resp_dreno_3_debito (string): Débito dreno 3.
- sis_resp_pocus (string): POCUS pulmonar (Linhas A/B, Consolidação, Derrame). "" se ausente.
- sis_resp_obs (string): Observações respiratórias livres.
- sis_resp_conduta (string): "".

# --- 3. CARDIOVASCULAR ---
- sis_cardio_fc (string): Frequência cardíaca em bpm.
- sis_cardio_cardioscopia (string): Ritmo na cardioscopia (ex: Sinusal, FA, BAVT).
- sis_cardio_pam (string): Pressão arterial média em mmHg.
- sis_cardio_perfusao (string): Perfusão periférica (Normal/Lentificada/Flush/"").
- sis_cardio_tec (string): Tempo de enchimento capilar (ex: "3 seg.").
- sis_cardio_fluido_responsivo (string): Fluido-responsividade (Sim/Não/"").
- sis_cardio_fluido_tolerante (string): Fluido-tolerância (Sim/Não/"").
- sis_cardio_dva_1_med (string): DVA 1 (ex: Noradrenalina).
- sis_cardio_dva_1_dose (string): Dose DVA 1 (ex: "0.12 mcg/kg/min").
- sis_cardio_dva_2_med (string): DVA 2.
- sis_cardio_dva_2_dose (string): Dose DVA 2.
- sis_cardio_dva_3_med (string): DVA 3.
- sis_cardio_dva_3_dose (string): Dose DVA 3.
- sis_cardio_dva_4_med (string): DVA 4.
- sis_cardio_dva_4_dose (string): Dose DVA 4.
- sis_cardio_pocus (string): POCUS cardíaco/VCI (ex: Função ventricular preservada). "" se ausente.
- sis_cardio_obs (string): Observações cardiovasculares livres.
- sis_cardio_conduta (string): "".

# --- 4. RENAL / METABÓLICO / NUTRIÇÃO ---
- sis_renal_diurese (string): Diurese das últimas 24h (ex: "1800mL").
- sis_renal_balanco (string): Balanço hídrico diário com sinal (ex: "+350mL").
- sis_renal_balanco_acum (string): Balanço hídrico acumulado (ex: "+2300mL").
- sis_renal_volemia (string): Status volêmico (Hipovolêmico/Euvolêmico/Hipervolêmico/"").
- sis_renal_cr_antepen (string): Creatinina anteontem.
- sis_renal_cr_ult (string): Creatinina ontem.
- sis_renal_cr_hoje (string): Creatinina atual.
- sis_renal_ur_antepen (string): Ureia anteontem.
- sis_renal_ur_ult (string): Ureia ontem.
- sis_renal_ur_hoje (string): Ureia atual.
- sis_renal_sodio (string): Distúrbio do sódio (Normal/Hiponatremia/Hipernatremia/""). "" se não mencionado.
- sis_renal_potassio (string): Distúrbio do potássio (Normal/Hipocalemia/Hipercalemia/""). "" se não mencionado.
- sis_renal_magnesio (string): Distúrbio do magnésio (Normal/Hipomagnesemia/""). "" se não mencionado.
- sis_renal_fosforo (string): Distúrbio do fósforo (Normal/Hipofosfatemia/""). "" se não mencionado.
- sis_renal_calcio (string): Distúrbio do cálcio (Normal/Hipocalcemia/Hipercalcemia/""). "" se não mencionado.
- sis_renal_trs (string): Em hemodiálise/TRS (Sim/Não/"").
- sis_renal_trs_via (string): Acesso da TRS (ex: "Cateter femoral D").
- sis_renal_trs_ultima (string): Data/Hora da última sessão.
- sis_renal_trs_proxima (string): Programação da próxima sessão.
- sis_renal_pocus (string): POCUS renal/bexiga. "" se ausente.
- sis_renal_obs (string): Observações renais livres.
- sis_renal_conduta (string): "".
- sis_metab_obs (string): Observações metabólicas (glicemia, ácido-base, eletrólitos).
- sis_metab_pocus (string): POCUS metabólico. "" se ausente.
- sis_metab_conduta (string): "".
- sis_nutri_obs (string): Observações nutricionais (tipo de dieta, tolerância, meta calórica).
- sis_nutri_pocus (string): POCUS gástrico (ex: antro). "" se ausente.
- sis_nutri_conduta (string): "".

# --- 5. INFECCIOSO ---
- sis_infec_febre (string): Presença de febre (Sim/Não/"").
- sis_infec_febre_vezes (string): Quantos picos febrís nas últimas 24h (ex: "2").
- sis_infec_febre_ultima (string): Horário/Data do último pico.
- sis_infec_atb (string): Em uso de antimicrobiano (Sim/Não/"").
- sis_infec_atb_guiado (string): ATB guiado por cultura (Sim/Não/"").
- sis_infec_atb_1 (string): Nome do ATB 1.
- sis_infec_atb_2 (string): Nome do ATB 2.
- sis_infec_atb_3 (string): Nome do ATB 3.
- sis_infec_culturas_and (string): Culturas em andamento (Sim/Não/"").
- sis_infec_cult_1_sitio (string): Sítio da cultura 1 (ex: "Hemocultura central").
- sis_infec_cult_1_data (string): Data da coleta 1.
- sis_infec_cult_2_sitio (string): Sítio da cultura 2.
- sis_infec_cult_2_data (string): Data da coleta 2.
- sis_infec_cult_3_sitio (string): Sítio da cultura 3.
- sis_infec_cult_3_data (string): Data da coleta 3.
- sis_infec_cult_4_sitio (string): Sítio da cultura 4.
- sis_infec_cult_4_data (string): Data da coleta 4.
- sis_infec_pcr_hoje (string): Valor da PCR atual.
- sis_infec_pcr_ult (string): PCR anterior.
- sis_infec_pcr_antepen (string): PCR antepenúltima.
- sis_infec_leuc_antepen (string): Leucócitos anteontem.
- sis_infec_leuc_ult (string): Leucócitos ontem.
- sis_infec_leuc_hoje (string): Leucócitos atual.
- sis_infec_isolamento (string): Em isolamento (Sim/Não/"").
- sis_infec_isolamento_tipo (string): Tipo (Contato/Aerossol/Gotícula/Reverso/"").
- sis_infec_isolamento_motivo (string): Germe ou suspeita (ex: "K. pneumoniae KPC+").
- sis_infec_patogenos (string): Lista de germes isolados — texto literal.
- sis_infec_pocus (string): POCUS infeccioso (ex: pesquisa de coleções). "" se ausente.
- sis_infec_obs (string): Observações infecciosas livres.
- sis_infec_conduta (string): "".

# --- 6. GASTROINTESTINAL ---
- sis_gastro_exame_fisico (string): Descrição literal do exame físico abdominal.
- sis_gastro_ictericia_presente (string): Icterícia (Presente/Ausente/"").
- sis_gastro_ictericia_cruzes (string): Intensidade da icterícia (ex: "1", "2", "3", "4"). "" se ausente.
- sis_gastro_dieta_oral (string): Tipo de dieta oral (ex: "Pastosa", "Completa"). "" se ausente.
- sis_gastro_dieta_enteral (string): Fórmula enteral (ex: "Peptamen", "Fresubin"). "" se ausente.
- sis_gastro_dieta_enteral_vol (string): Volume/kcal enteral (ex: "1200 kcal"). "" se ausente.
- sis_gastro_dieta_parenteral (string): Tipo NPT (ex: "NPT", "NPP"). "" se ausente.
- sis_gastro_dieta_parenteral_vol (string): Volume/kcal NPT. "" se ausente.
- sis_gastro_meta_calorica (string): Meta calórica em kcal — somente número (ex: "1800"). "" se ausente.
- sis_gastro_na_meta (string): Atingindo meta calórica (Sim/Não/"").
- sis_gastro_ingestao_quanto (string): Ingestão real descrita (ex: "800 kcal").
- sis_gastro_escape_glicemico (string): Escape glicêmico (Sim/Não/"").
- sis_gastro_escape_vezes (string): Quantos episódios de escape.
- sis_gastro_escape_manha (boolean): Escape de manhã (true/false).
- sis_gastro_escape_tarde (boolean): Escape à tarde (true/false).
- sis_gastro_escape_noite (boolean): Escape à noite (true/false).
- sis_gastro_insulino (string): Em insulinoterapia (Sim/Não/"").
- sis_gastro_insulino_dose_manha (string): Dose de insulina manhã (ex: "10 Un").
- sis_gastro_insulino_dose_tarde (string): Dose de insulina tarde.
- sis_gastro_insulino_dose_noite (string): Dose de insulina noite.
- sis_gastro_evacuacao (string): Evacuação presente (Sim/Não/"").
- sis_gastro_evacuacao_data (string): Data da última evacuação.
- sis_gastro_evacuacao_laxativo (string): Laxativo em uso (ex: "Lactulose 10mL 8/8h"). "" se ausente.
- sis_gastro_pocus (string): POCUS abdome (ex: Ascite leve, POCUS gástrico). "" se ausente.
- sis_gastro_obs (string): Observações gastrointestinais livres.
- sis_gastro_conduta (string): "".

# --- 7. HEMATOLÓGICO ---
- sis_hemato_anticoag (string): Em anticoagulação (Sim/Não/"").
- sis_hemato_anticoag_tipo (string): Profilática ou Plena. "" se ausente.
- sis_hemato_anticoag_motivo (string): Indicação (ex: "TVP", "FA", "TEP"). "" se ausente.
- sis_hemato_sangramento (string): Sangramento ativo (Sim/Não/"").
- sis_hemato_sangramento_via (string): Sítio do sangramento (ex: "Digestiva alta"). "" se ausente.
- sis_hemato_sangramento_data (string): Data/hora do episódio. "" se ausente.
- sis_hemato_transf_data (string): Data da última transfusão.
- sis_hemato_transf_1_comp (string): Componente transfundido 1 (ex: "Concentrado de hemácias").
- sis_hemato_transf_1_bolsas (string): Quantidade 1 (ex: "2 bolsas").
- sis_hemato_transf_2_comp (string): Componente 2.
- sis_hemato_transf_2_bolsas (string): Quantidade 2.
- sis_hemato_transf_3_comp (string): Componente 3.
- sis_hemato_transf_3_bolsas (string): Quantidade 3.
- sis_hemato_hb_antepen (string): Hb anteontem.
- sis_hemato_hb_ult (string): Hb ontem.
- sis_hemato_hb_hoje (string): Hb atual.
- sis_hemato_plaq_antepen (string): Plaquetas anteontem.
- sis_hemato_plaq_ult (string): Plaquetas ontem.
- sis_hemato_plaq_hoje (string): Plaquetas atual.
- sis_hemato_inr_antepen (string): INR anteontem.
- sis_hemato_inr_ult (string): INR ontem.
- sis_hemato_inr_hoje (string): INR atual.
- sis_hemato_pocus (string): POCUS hematológico (ex: TVP, Derrame pleural). "" se ausente.
- sis_hemato_obs (string): Observações hematológicas livres.
- sis_hemato_conduta (string): "".

# --- 8. PELE / MUSCULOESQUELÉTICO ---
- sis_pele_edema (string): Presença de edema (Presente/Ausente/"").
- sis_pele_edema_cruzes (string): Intensidade do edema em cruzes (ex: "1", "2", "3"). "" se ausente.
- sis_pele_lpp (string): Lesão por Pressão (Sim/Não/"").
- sis_pele_lpp_local_1 (string): Local da lesão 1 (ex: "Sacro").
- sis_pele_lpp_grau_1 (string): Grau da lesão 1 (ex: "Grau II").
- sis_pele_lpp_local_2 (string): Local da lesão 2.
- sis_pele_lpp_grau_2 (string): Grau da lesão 2.
- sis_pele_lpp_local_3 (string): Local da lesão 3.
- sis_pele_lpp_grau_3 (string): Grau da lesão 3.
- sis_pele_polineuropatia (string): Polineuropatia do doente crítico (Sim/Não/"").
- sis_pele_pocus (string): POCUS tecidos moles. "" se ausente.
- sis_pele_obs (string): Observações de feridas/curativos livres.
- sis_pele_conduta (string): "".
</VARIAVEIS>

# ESTRUTURA DE SAÍDA OBRIGATÓRIA
Retorne EXATAMENTE este JSON com todos os campos. Campos ausentes = "". Inteiros ausentes = null. Booleanos ausentes = false.

{
  "sis_neuro_ecg": "", "sis_neuro_ecg_ao": "", "sis_neuro_ecg_rv": "", "sis_neuro_ecg_rm": "",
  "sis_neuro_ecg_p": "", "sis_neuro_rass": null,
  "sis_neuro_delirium": "", "sis_neuro_delirium_tipo": "", "sis_neuro_cam_icu": "",
  "sis_neuro_pupilas_tam": "", "sis_neuro_pupilas_simetria": "", "sis_neuro_pupilas_foto": "",
  "sis_neuro_analgesico_adequado": "", "sis_neuro_deficits_focais": "", "sis_neuro_deficits_ausente": "",
  "sis_neuro_analgesia_1_tipo": "", "sis_neuro_analgesia_1_drogas": "", "sis_neuro_analgesia_1_dose": "", "sis_neuro_analgesia_1_freq": "",
  "sis_neuro_analgesia_2_tipo": "", "sis_neuro_analgesia_2_drogas": "", "sis_neuro_analgesia_2_dose": "", "sis_neuro_analgesia_2_freq": "",
  "sis_neuro_analgesia_3_tipo": "", "sis_neuro_analgesia_3_drogas": "", "sis_neuro_analgesia_3_dose": "", "sis_neuro_analgesia_3_freq": "",
  "sis_neuro_sedacao_meta": "",
  "sis_neuro_sedacao_1_drogas": "", "sis_neuro_sedacao_1_dose": "",
  "sis_neuro_sedacao_2_drogas": "", "sis_neuro_sedacao_2_dose": "",
  "sis_neuro_sedacao_3_drogas": "", "sis_neuro_sedacao_3_dose": "",
  "sis_neuro_bloqueador_med": "", "sis_neuro_bloqueador_dose": "",
  "sis_neuro_pocus": "", "sis_neuro_obs": "", "sis_neuro_conduta": "",

  "sis_resp_ausculta": "", "sis_resp_modo": "", "sis_resp_modo_vent": "",
  "sis_resp_oxigenio_modo": "", "sis_resp_oxigenio_fluxo": "",
  "sis_resp_pressao": "", "sis_resp_volume": "", "sis_resp_fio2": "", "sis_resp_peep": "", "sis_resp_freq": "",
  "sis_resp_vent_protetora": "", "sis_resp_sincronico": "", "sis_resp_assincronia": "",
  "sis_resp_complacencia": "", "sis_resp_resistencia": "", "sis_resp_dp": "", "sis_resp_plato": "", "sis_resp_pico": "",
  "sis_resp_dreno_1": "", "sis_resp_dreno_1_debito": "",
  "sis_resp_dreno_2": "", "sis_resp_dreno_2_debito": "",
  "sis_resp_dreno_3": "", "sis_resp_dreno_3_debito": "",
  "sis_resp_pocus": "", "sis_resp_obs": "", "sis_resp_conduta": "",

  "sis_cardio_fc": "", "sis_cardio_cardioscopia": "", "sis_cardio_pam": "",
  "sis_cardio_perfusao": "", "sis_cardio_tec": "", "sis_cardio_fluido_responsivo": "", "sis_cardio_fluido_tolerante": "",
  "sis_cardio_dva_1_med": "", "sis_cardio_dva_1_dose": "",
  "sis_cardio_dva_2_med": "", "sis_cardio_dva_2_dose": "",
  "sis_cardio_dva_3_med": "", "sis_cardio_dva_3_dose": "",
  "sis_cardio_dva_4_med": "", "sis_cardio_dva_4_dose": "",
  "sis_cardio_pocus": "", "sis_cardio_obs": "", "sis_cardio_conduta": "",

  "sis_renal_diurese": "", "sis_renal_balanco": "", "sis_renal_balanco_acum": "", "sis_renal_volemia": "",
  "sis_renal_cr_antepen": "", "sis_renal_cr_ult": "", "sis_renal_cr_hoje": "",
  "sis_renal_ur_antepen": "", "sis_renal_ur_ult": "", "sis_renal_ur_hoje": "",
  "sis_renal_sodio": "", "sis_renal_potassio": "", "sis_renal_magnesio": "", "sis_renal_fosforo": "", "sis_renal_calcio": "",
  "sis_renal_trs": "", "sis_renal_trs_via": "", "sis_renal_trs_ultima": "", "sis_renal_trs_proxima": "",
  "sis_renal_pocus": "", "sis_renal_obs": "", "sis_renal_conduta": "",
  "sis_metab_obs": "", "sis_metab_pocus": "", "sis_metab_conduta": "",
  "sis_nutri_obs": "", "sis_nutri_pocus": "", "sis_nutri_conduta": "",

  "sis_infec_febre": "", "sis_infec_febre_vezes": "", "sis_infec_febre_ultima": "",
  "sis_infec_atb": "", "sis_infec_atb_guiado": "",
  "sis_infec_atb_1": "", "sis_infec_atb_2": "", "sis_infec_atb_3": "",
  "sis_infec_culturas_and": "",
  "sis_infec_cult_1_sitio": "", "sis_infec_cult_1_data": "",
  "sis_infec_cult_2_sitio": "", "sis_infec_cult_2_data": "",
  "sis_infec_cult_3_sitio": "", "sis_infec_cult_3_data": "",
  "sis_infec_cult_4_sitio": "", "sis_infec_cult_4_data": "",
  "sis_infec_pcr_hoje": "", "sis_infec_pcr_ult": "", "sis_infec_pcr_antepen": "",
  "sis_infec_leuc_antepen": "", "sis_infec_leuc_ult": "", "sis_infec_leuc_hoje": "",
  "sis_infec_isolamento": "", "sis_infec_isolamento_tipo": "", "sis_infec_isolamento_motivo": "",
  "sis_infec_patogenos": "", "sis_infec_pocus": "", "sis_infec_obs": "", "sis_infec_conduta": "",

  "sis_gastro_exame_fisico": "", "sis_gastro_ictericia_presente": "", "sis_gastro_ictericia_cruzes": "",
  "sis_gastro_dieta_oral": "", "sis_gastro_dieta_enteral": "", "sis_gastro_dieta_enteral_vol": "",
  "sis_gastro_dieta_parenteral": "", "sis_gastro_dieta_parenteral_vol": "", "sis_gastro_meta_calorica": "",
  "sis_gastro_na_meta": "", "sis_gastro_ingestao_quanto": "",
  "sis_gastro_escape_glicemico": "", "sis_gastro_escape_vezes": "",
  "sis_gastro_escape_manha": false, "sis_gastro_escape_tarde": false, "sis_gastro_escape_noite": false,
  "sis_gastro_insulino": "",
  "sis_gastro_insulino_dose_manha": "", "sis_gastro_insulino_dose_tarde": "", "sis_gastro_insulino_dose_noite": "",
  "sis_gastro_evacuacao": "", "sis_gastro_evacuacao_data": "", "sis_gastro_evacuacao_laxativo": "",
  "sis_gastro_pocus": "", "sis_gastro_obs": "", "sis_gastro_conduta": "",

  "sis_hemato_anticoag": "", "sis_hemato_anticoag_tipo": "", "sis_hemato_anticoag_motivo": "",
  "sis_hemato_sangramento": "", "sis_hemato_sangramento_via": "", "sis_hemato_sangramento_data": "",
  "sis_hemato_transf_data": "",
  "sis_hemato_transf_1_comp": "", "sis_hemato_transf_1_bolsas": "",
  "sis_hemato_transf_2_comp": "", "sis_hemato_transf_2_bolsas": "",
  "sis_hemato_transf_3_comp": "", "sis_hemato_transf_3_bolsas": "",
  "sis_hemato_hb_antepen": "", "sis_hemato_hb_ult": "", "sis_hemato_hb_hoje": "",
  "sis_hemato_plaq_antepen": "", "sis_hemato_plaq_ult": "", "sis_hemato_plaq_hoje": "",
  "sis_hemato_inr_antepen": "", "sis_hemato_inr_ult": "", "sis_hemato_inr_hoje": "",
  "sis_hemato_pocus": "", "sis_hemato_obs": "", "sis_hemato_conduta": "",

  "sis_pele_edema": "", "sis_pele_edema_cruzes": "",
  "sis_pele_lpp": "",
  "sis_pele_lpp_local_1": "", "sis_pele_lpp_grau_1": "",
  "sis_pele_lpp_local_2": "", "sis_pele_lpp_grau_2": "",
  "sis_pele_lpp_local_3": "", "sis_pele_lpp_grau_3": "",
  "sis_pele_polineuropatia": "", "sis_pele_pocus": "", "sis_pele_obs": "", "sis_pele_conduta": ""
}"""

def preencher_sistemas(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_SISTEMAS, texto, api_key, provider, modelo)
    r.pop("_erro", None)

    # Campos neurológicos numéricos: inteiros → string para text_input (como FC, PAM)
    for k, default in [("sis_neuro_ecg", 15), ("sis_neuro_ecg_p", 15)]:
        if k in r:
            try: v = int(r[k]) if r[k] not in ("", None) else default
            except: v = default
            r[k] = str(v) if v is not None else ""

    if "sis_neuro_rass" in r:
        try: v = int(r["sis_neuro_rass"]) if r["sis_neuro_rass"] not in ("", None) else 0
        except: v = 0
        r["sis_neuro_rass"] = str(v)

    for k in ["sis_neuro_ecg_ao", "sis_neuro_ecg_rv", "sis_neuro_ecg_rm"]:
        if k in r:
            try: v = int(r[k]) if r[k] not in ("", None) else None
            except: v = None
            r[k] = str(v) if v is not None else ""

    # Booleanos do escape glicêmico
    for k in ["sis_gastro_escape_manha", "sis_gastro_escape_tarde", "sis_gastro_escape_noite"]:
        if k in r and isinstance(r[k], str):
            r[k] = r[k].lower() in ("true", "sim", "yes", "1")

    # Icterícia: normaliza Sim/Não → Presente/Ausente (compatível com pills)
    if "sis_gastro_ictericia_presente" in r:
        v = r["sis_gastro_ictericia_presente"]
        if isinstance(v, str) and v.strip():
            if v.strip().lower() in ("sim", "yes", "1", "presente"):
                r["sis_gastro_ictericia_presente"] = "Presente"
            elif v.strip().lower() in ("não", "nao", "no", "0", "ausente"):
                r["sis_gastro_ictericia_presente"] = "Ausente"
        else:
            r["sis_gastro_ictericia_presente"] = ""

    # Edema: normaliza Sim/Não → Presente/Ausente (compatível com pills)
    if "sis_pele_edema" in r:
        v = r["sis_pele_edema"]
        if isinstance(v, str) and v.strip():
            if v.strip().lower() in ("sim", "yes", "1", "presente"):
                r["sis_pele_edema"] = "Presente"
            elif v.strip().lower() in ("não", "nao", "no", "0", "ausente"):
                r["sis_pele_edema"] = "Ausente"
        else:
            r["sis_pele_edema"] = ""

    # Déficit focal ausente: converte para "Ausente" ou None (compatível com pills)
    if "sis_neuro_deficits_ausente" in r:
        v = r["sis_neuro_deficits_ausente"]
        if v == "Ausente" or v is True or (isinstance(v, str) and v.strip().lower() in ("true", "sim", "yes", "1", "ausente")):
            r["sis_neuro_deficits_ausente"] = "Ausente"
        else:
            r["sis_neuro_deficits_ausente"] = None

    # Renomeia sis_gastro_evacuacao_laxativo → sis_gastro_laxativo (chave do formulário)
    if "sis_gastro_evacuacao_laxativo" in r:
        r["sis_gastro_laxativo"] = r.pop("sis_gastro_evacuacao_laxativo")

    return r


# ==============================================================================
# AGENTE 13: CONTROLES & BALANÇO HÍDRICO
# ==============================================================================
_PROMPT_CONTROLES = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair os Sinais Vitais, Glicemia, Diurese e Balanço Hídrico. Você deve preencher EXCLUSIVAMENTE até 3 dias (blocos):
- ctrl_hoje: conjunto mais recente (pela data).
- ctrl_ontem: conjunto imediatamente anterior (se disponível).
- ctrl_anteontem: conjunto anterior a ontem (se disponível).

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ESTRUTURA PLANA: Preencha o JSON sequencialmente. Não utilize arrays ou listas aninhadas.
2. PREENCHIMENTO VAZIO: Se houver menos de 3 dias no texto, retorne estritamente `""` (string vazia) para todos os campos dos dias faltantes. Não use `null` em hipótese alguma.
3. DATA E AGRUPAMENTO: Nunca misture valores de datas diferentes. Se a mesma data aparecer repetida, consolide os dados em um único dia.
4. CONDUTAS E NOTAS: Os campos `controles_notas` e `ctrl_conduta` são de entrada manual do médico. A IA deve preenchê-los SEMPRE com `""`.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# REGRAS DE MAPEAMENTO CLÍNICO E VALORES
- INTERVALOS (MIN/MAX):
  - Textos no formato "81-181": extraia o primeiro valor para a chave `_min` ("81") e o segundo para a chave `_max` ("181").
  - Valor único isolado: preencha apenas o `_min` e deixe o `_max` como `""`.
  - Múltiplos valores soltos no dia: encontre o menor (`_min`) e o maior (`_max`).
- VALORES ÚNICOS (Diurese/Balanço): Copie o texto literal com a unidade, sinal ou descrição. Ex: "+350mL", "-100", "1800ml", "Presente", "Não Quantificado".
- PERÍODO: O campo `ctrl_periodo` deve ser "24 horas" como padrão. Mude para "12 horas" APENAS se o texto descrever explicitamente que o balanço/controle é de 12 horas.

# ENTRADAS
<TEXTO_ALVO>
[O texto com os controles e balanço hídrico será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- CAMPOS GERAIS E MANUAIS ---
- controles_notas (string): "".
- ctrl_conduta (string): "".
- ctrl_periodo (string): "24 horas" (padrão) ou "12 horas".

# --- BLOCO 1: HOJE (Mais Recente) ---
- ctrl_hoje_data (string): Data do registro mais recente.
- ctrl_hoje_pas_min (string): Pressão Arterial Sistólica mínima.
- ctrl_hoje_pas_max (string): Pressão Arterial Sistólica máxima.
- ctrl_hoje_pad_min (string): Pressão Arterial Diastólica mínima.
- ctrl_hoje_pad_max (string): Pressão Arterial Diastólica máxima.
- ctrl_hoje_pam_min (string): Pressão Arterial Média mínima.
- ctrl_hoje_pam_max (string): Pressão Arterial Média máxima.
- ctrl_hoje_fc_min (string): Frequência Cardíaca mínima.
- ctrl_hoje_fc_max (string): Frequência Cardíaca máxima.
- ctrl_hoje_fr_min (string): Frequência Respiratória mínima.
- ctrl_hoje_fr_max (string): Frequência Respiratória máxima.
- ctrl_hoje_sato2_min (string): Saturação de O2 mínima.
- ctrl_hoje_sato2_max (string): Saturação de O2 máxima.
- ctrl_hoje_temp_min (string): Temperatura mínima.
- ctrl_hoje_temp_max (string): Temperatura máxima.
- ctrl_hoje_glic_min (string): Glicemia capilar mínima.
- ctrl_hoje_glic_max (string): Glicemia capilar máxima.
- ctrl_hoje_diurese (string): Volume ou aspecto da diurese.
- ctrl_hoje_balanco (string): Valor do balanço hídrico.

# --- BLOCO 2: ONTEM (Imediatamente Anterior) ---
- ctrl_ontem_data (string): Data do registro anterior.
- ctrl_ontem_pas_min (string): Pressão Arterial Sistólica mínima.
- ctrl_ontem_pas_max (string): Pressão Arterial Sistólica máxima.
- ctrl_ontem_pad_min (string): Pressão Arterial Diastólica mínima.
- ctrl_ontem_pad_max (string): Pressão Arterial Diastólica máxima.
- ctrl_ontem_pam_min (string): Pressão Arterial Média mínima.
- ctrl_ontem_pam_max (string): Pressão Arterial Média máxima.
- ctrl_ontem_fc_min (string): Frequência Cardíaca mínima.
- ctrl_ontem_fc_max (string): Frequência Cardíaca máxima.
- ctrl_ontem_fr_min (string): Frequência Respiratória mínima.
- ctrl_ontem_fr_max (string): Frequência Respiratória máxima.
- ctrl_ontem_sato2_min (string): Saturação de O2 mínima.
- ctrl_ontem_sato2_max (string): Saturação de O2 máxima.
- ctrl_ontem_temp_min (string): Temperatura mínima.
- ctrl_ontem_temp_max (string): Temperatura máxima.
- ctrl_ontem_glic_min (string): Glicemia capilar mínima.
- ctrl_ontem_glic_max (string): Glicemia capilar máxima.
- ctrl_ontem_diurese (string): Volume ou aspecto da diurese.
- ctrl_ontem_balanco (string): Valor do balanço hídrico.

# --- BLOCO 3: ANTEONTEM (Anterior a Ontem) ---
- ctrl_anteontem_data (string): Data do registro de anteontem.
- ctrl_anteontem_pas_min (string): Pressão Arterial Sistólica mínima.
- ctrl_anteontem_pas_max (string): Pressão Arterial Sistólica máxima.
- ctrl_anteontem_pad_min (string): Pressão Arterial Diastólica mínima.
- ctrl_anteontem_pad_max (string): Pressão Arterial Diastólica máxima.
- ctrl_anteontem_pam_min (string): Pressão Arterial Média mínima.
- ctrl_anteontem_pam_max (string): Pressão Arterial Média máxima.
- ctrl_anteontem_fc_min (string): Frequência Cardíaca mínima.
- ctrl_anteontem_fc_max (string): Frequência Cardíaca máxima.
- ctrl_anteontem_fr_min (string): Frequência Respiratória mínima.
- ctrl_anteontem_fr_max (string): Frequência Respiratória máxima.
- ctrl_anteontem_sato2_min (string): Saturação de O2 mínima.
- ctrl_anteontem_sato2_max (string): Saturação de O2 máxima.
- ctrl_anteontem_temp_min (string): Temperatura mínima.
- ctrl_anteontem_temp_max (string): Temperatura máxima.
- ctrl_anteontem_glic_min (string): Glicemia capilar mínima.
- ctrl_anteontem_glic_max (string): Glicemia capilar máxima.
- ctrl_anteontem_diurese (string): Volume ou aspecto da diurese.
- ctrl_anteontem_balanco (string): Valor do balanço hídrico.
</VARIAVEIS>"""

def preencher_controles(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_CONTROLES, texto, api_key, provider, modelo)
    r.pop("_erro", None)
    return r


# ==============================================================================
# MAPEAMENTO: seção → função agente e campo _notas
# ==============================================================================
_AGENTES = {
    "identificacao":  preencher_identificacao,
    "hd":             preencher_hd,
    "comorbidades":   preencher_comorbidades,
    "muc":            preencher_muc,
    "hmpa":           preencher_hmpa,
    "dispositivos":   preencher_dispositivos,
    "culturas":       preencher_culturas,
    "antibioticos":   preencher_antibioticos,
    "complementares": preencher_complementares,
    "laboratoriais":  preencher_laboratoriais,
    "controles":      preencher_controles,
    "evolucao":       preencher_evolucao,
    "sistemas":       preencher_sistemas,
}

_NOTAS_MAP = {
    "identificacao":  "identificacao_notas",
    "hd":             "hd_notas",
    "comorbidades":   "comorbidades_notas",
    "muc":            "muc_notas",
    "hmpa":           "hmpa_texto",
    "dispositivos":   "dispositivos_notas",
    "culturas":       "culturas_notas",
    "antibioticos":   "antibioticos_notas",
    "complementares": "complementares_notas",
    "laboratoriais":  "laboratoriais_notas",
    "controles":      "controles_notas",
    "evolucao":       "evolucao_notas",
    "sistemas":       "sistemas_notas",
}

NOMES_SECOES = {
    "identificacao":  "1. Identificação",
    "hd":             "2. Diagnósticos",
    "comorbidades":   "3. Comorbidades",
    "muc":            "4. MUC",
    "hmpa":           "5. HMPA",
    "dispositivos":   "6. Dispositivos",
    "culturas":       "7. Culturas",
    "antibioticos":   "8. Antibióticos",
    "complementares": "9. Complementares",
    "laboratoriais":  "10. Exames Laboratoriais",
    "controles":      "11. Controles & Balanço",
    "evolucao":       "12. Evolução Clínica",
    "sistemas":       "13. Sistemas",
}


def preencher_todas_secoes(api_key: str, provider: str, modelo: str):
    """
    Lê os campos _notas já preenchidos pelo ia_extrator,
    roda cada um dos 12 agentes e retorna (resultado_dict, lista_erros).
    """
    resultado = {}
    erros = []

    for secao, fn_agente in _AGENTES.items():
        chave_notas = _NOTAS_MAP[secao]
        texto = st.session_state.get(chave_notas, "").strip()

        if not texto:
            continue

        dados = fn_agente(texto, api_key, provider, modelo)

        if "_erro" in dados:
            erros.append(f"{NOMES_SECOES[secao]}: {dados['_erro']}")
        else:
            resultado.update(dados)

    return resultado, erros
