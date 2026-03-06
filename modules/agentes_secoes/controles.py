from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

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
- ctrl_hoje_glic_min (string): Dextro/Glicemia capilar mínima (mg/dL).
- ctrl_hoje_glic_max (string): Dextro/Glicemia capilar máxima (mg/dL).
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
- ctrl_ontem_glic_min (string): Dextro/Glicemia capilar mínima (mg/dL).
- ctrl_ontem_glic_max (string): Dextro/Glicemia capilar máxima (mg/dL).
- ctrl_ontem_diurese (string): Volume ou aspecto da diurese.
- ctrl_ontem_balanco (string): Valor do balanço hídrico.

# --- BLOCO 3: ANTEONTEM ---
- ctrl_anteontem_data (string): Data do registro de anteontem.
- ctrl_anteontem_pas_min (string): PAS mínima.
- ctrl_anteontem_pas_max (string): PAS máxima.
- ctrl_anteontem_pad_min (string): PAD mínima.
- ctrl_anteontem_pad_max (string): PAD máxima.
- ctrl_anteontem_pam_min (string): PAM mínima.
- ctrl_anteontem_pam_max (string): PAM máxima.
- ctrl_anteontem_fc_min (string): FC mínima.
- ctrl_anteontem_fc_max (string): FC máxima.
- ctrl_anteontem_fr_min (string): FR mínima.
- ctrl_anteontem_fr_max (string): FR máxima.
- ctrl_anteontem_sato2_min (string): SatO2 mínima.
- ctrl_anteontem_sato2_max (string): SatO2 máxima.
- ctrl_anteontem_temp_min (string): Temperatura mínima.
- ctrl_anteontem_temp_max (string): Temperatura máxima.
- ctrl_anteontem_glic_min (string): Glicemia mínima.
- ctrl_anteontem_glic_max (string): Glicemia máxima.
- ctrl_anteontem_diurese (string): Diurese.
- ctrl_anteontem_balanco (string): Balanço hídrico.

# --- BLOCO 4: 4º DIA ---
- ctrl_ant4_data (string): Data do 4º registro.
- ctrl_ant4_pas_min (string): PAS mínima.
- ctrl_ant4_pas_max (string): PAS máxima.
- ctrl_ant4_pad_min (string): PAD mínima.
- ctrl_ant4_pad_max (string): PAD máxima.
- ctrl_ant4_pam_min (string): PAM mínima.
- ctrl_ant4_pam_max (string): PAM máxima.
- ctrl_ant4_fc_min (string): FC mínima.
- ctrl_ant4_fc_max (string): FC máxima.
- ctrl_ant4_fr_min (string): FR mínima.
- ctrl_ant4_fr_max (string): FR máxima.
- ctrl_ant4_sato2_min (string): SatO2 mínima.
- ctrl_ant4_sato2_max (string): SatO2 máxima.
- ctrl_ant4_temp_min (string): Temperatura mínima.
- ctrl_ant4_temp_max (string): Temperatura máxima.
- ctrl_ant4_glic_min (string): Glicemia mínima.
- ctrl_ant4_glic_max (string): Glicemia máxima.
- ctrl_ant4_diurese (string): Diurese.
- ctrl_ant4_balanco (string): Balanço hídrico.

# --- BLOCO 5: 5º DIA ---
- ctrl_ant5_data (string): Data do 5º registro.
- ctrl_ant5_pas_min (string): PAS mínima.
- ctrl_ant5_pas_max (string): PAS máxima.
- ctrl_ant5_pad_min (string): PAD mínima.
- ctrl_ant5_pad_max (string): PAD máxima.
- ctrl_ant5_pam_min (string): PAM mínima.
- ctrl_ant5_pam_max (string): PAM máxima.
- ctrl_ant5_fc_min (string): FC mínima.
- ctrl_ant5_fc_max (string): FC máxima.
- ctrl_ant5_fr_min (string): FR mínima.
- ctrl_ant5_fr_max (string): FR máxima.
- ctrl_ant5_sato2_min (string): SatO2 mínima.
- ctrl_ant5_sato2_max (string): SatO2 máxima.
- ctrl_ant5_temp_min (string): Temperatura mínima.
- ctrl_ant5_temp_max (string): Temperatura máxima.
- ctrl_ant5_glic_min (string): Glicemia mínima.
- ctrl_ant5_glic_max (string): Glicemia máxima.
- ctrl_ant5_diurese (string): Diurese.
- ctrl_ant5_balanco (string): Balanço hídrico.
</VARIAVEIS>"""

def preencher_controles(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_CONTROLES, texto, api_key, provider, modelo)
    r.pop("_erro", None)
    return r


# ==============================================================================
# MAPEAMENTO: seção → função agente e campo _notas
# ==============================================================================
