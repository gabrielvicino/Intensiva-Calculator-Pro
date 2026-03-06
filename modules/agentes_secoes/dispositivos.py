from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

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

# EXEMPLO DE SAÍDA PERFEITA
{
  "disp_1_nome": "TOT",
  "disp_2_nome": "CVC",
  "disp_3_nome": "PAM",
  "disp_4_nome": "SVD",
  "disp_5_nome": "SNE",
  "disp_6_nome": "CVC",
  "disp_7_nome": "",
  "disp_8_nome": "",
  "disp_1_local": "fixado em 23 cm na rima labial",
  "disp_2_local": "Jugular Interna Direita",
  "disp_3_local": "Radial Esquerda",
  "disp_4_local": "Vesical",
  "disp_5_local": "Posição confirmada por RX",
  "disp_6_local": "Femoral Esquerda (removido)",
  "disp_7_local": "",
  "disp_8_local": "",
  "disp_1_data_in": "21/02/2026",
  "disp_2_data_in": "21/02/2026",
  "disp_3_data_in": "21/02/2026",
  "disp_4_data_in": "21/02/2026",
  "disp_5_data_in": "22/02/2026",
  "disp_6_data_in": "20/02/2026",
  "disp_7_data_in": "",
  "disp_8_data_in": "",
  "disp_1_data_out": "",
  "disp_2_data_out": "",
  "disp_3_data_out": "",
  "disp_4_data_out": "",
  "disp_5_data_out": "",
  "disp_6_data_out": "22/02/2026",
  "disp_7_data_out": "",
  "disp_8_data_out": "",
  "disp_1_status": "Ativo",
  "disp_2_status": "Ativo",
  "disp_3_status": "Ativo",
  "disp_4_status": "Ativo",
  "disp_5_status": "Ativo",
  "disp_6_status": "Removido",
  "disp_7_status": "",
  "disp_8_status": ""
}
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
