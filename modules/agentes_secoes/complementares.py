from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

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

# EXEMPLO DE SAÍDA PERFEITA
{
  "comp_1_exame": "Tomografia Computadorizada de Tórax com Contraste",
  "comp_2_exame": "Ecocardiograma Transtorácico",
  "comp_3_exame": "Eletrocardiograma",
  "comp_4_exame": "Radiografia de Tórax Portátil",
  "comp_5_exame": "",
  "comp_6_exame": "",
  "comp_7_exame": "",
  "comp_8_exame": "",
  "comp_1_data": "23/02/2026",
  "comp_2_data": "22/02/2026",
  "comp_3_data": "21/02/2026",
  "comp_4_data": "25/02/2026",
  "comp_5_data": "",
  "comp_6_data": "",
  "comp_7_data": "",
  "comp_8_data": "",
  "comp_1_laudo": "Consolidação em lobo inferior direito com broncograma aéreo. Derrame pleural bilateral de pequeno volume. Sem tromboembolismo pulmonar.",
  "comp_2_laudo": "Função ventricular esquerda preservada (FE 62%). Hipertrofia concêntrica VE leve. Derrame pericárdico ausente. Pressão de VD estimada 38 mmHg.",
  "comp_3_laudo": "Ritmo sinusal, FC 88 bpm. Ondas T invertidas em V1-V3. Sem critérios de isquemia aguda.",
  "comp_4_laudo": "Piora do padrão de consolidação pulmonar bilateral difuso em relação ao exame anterior.",
  "comp_5_laudo": "",
  "comp_6_laudo": "",
  "comp_7_laudo": "",
  "comp_8_laudo": "",
  "comp_1_conduta": "",
  "comp_2_conduta": "",
  "comp_3_conduta": "",
  "comp_4_conduta": "",
  "comp_5_conduta": "",
  "comp_6_conduta": "",
  "comp_7_conduta": "",
  "comp_8_conduta": "",
  "complementares_notas": ""
}
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
