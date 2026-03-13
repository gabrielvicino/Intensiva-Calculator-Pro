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

# REGRAS DE EXTRAÇÃO

## Formatação de Nomes (Title Case)
- Converta texto em CAIXA ALTA para **Title Case** (Primeira Letra Maiúscula de cada palavra significativa).
- Preposições e artigos ficam em minúsculas: de, em, com, por, para, do, da, no, na, etc.
- Siglas médicas reconhecidas PERMANECEM em maiúsculas: POT, UTI, IRA, TVP, TEP, IAM, ICC, DM, HAS, DPOC, VMI, PAV, KDIGO, KPC, MRSA, etc.
- Exemplos:
  - "POLIPOSE ADENOMATOSA FAMILIAR" → "Polipose Adenomatosa Familiar"
  - "POT DRENAGEM DE ABSCESSO PERINEAL" → "POT Drenagem de Abscesso Perineal"
  - "ADENOMA EM PÓLIPO DUODENAL DE BAIXO GRAU" → "Adenoma em Pólipo Duodenal de Baixo Grau"

## Datas — REGRA PRIORITÁRIA (sobrepõe qualquer outra regra de data)
- Mantenha as datas **EXATAMENTE** como aparecem no texto original. NÃO reformate, NÃO tente converter para DD/MM/AAAA.
- Exemplos de preservação:
  - "1999" → retorne "1999" (NÃO "19/99/" nem "01/01/1999")
  - "2019" → retorne "2019" (NÃO "20/19/")
  - "01/2022" → retorne "01/2022" (NÃO "01/20/2022")
  - "07/2022" → retorne "07/2022"
  - "27/11/21" → retorne "27/11/21"
  - "10/01/2026" → retorne "10/01/2026"
- Se a data é só um ano (ex: "- 1999"), retorne apenas "1999".
- Se a data é mês/ano (ex: "- 01/2022"), retorne "01/2022".

## Sub-itens e Observações
- Linhas que começam com ">>" ou ">" ou são sub-itens indentados de um diagnóstico são **OBSERVAÇÕES** do diagnóstico pai.
- Coloque essas linhas no campo `_obs` do diagnóstico, **separadas por \\n** (newline).
- **NÃO** crie diagnósticos separados para sub-itens. Eles NÃO são diagnósticos independentes.
- Converta os sub-itens também para Title Case (mantendo siglas em maiúsculas).
- Exemplo:
  Entrada:
    1) POLIPOSE ADENOMATOSA FAMILIAR
    >>POT RETOCOLECTOMIA TOTAL COM RESERVATORIO ILEAL -1999
    >>POT RECONSTRUÇÃO DE TRÂNSITO - 2001
  Saída:
    diag_atual_1_nome: "Polipose Adenomatosa Familiar"
    diag_atual_1_data: "1999"
    diag_atual_1_obs: "POT Retocolectomia Total com Reservatório Ileal - 1999\\nPOT Reconstrução de Trânsito - 2001"

## Classificação Atual vs Resolvida
- Classifique como "Resolvida" APENAS se o texto indicar EXPLICITAMENTE resolução (palavras: "resolvido", "resolvida", "alta de", "retirado").
- Sub-itens como "POT ...", "Pós-operatório de ..." são observações do diagnóstico pai, NÃO diagnósticos resolvidos.

## Ordem e Preenchimento
- Siga a exata ordem em que os diagnósticos aparecem no texto.
- Se não houver informação, retorne `""` (string vazia). NÃO use `null`.
- NÃO invente diagnósticos ou datas.
- A saída deve ser EXCLUSIVAMENTE um objeto JSON válido, sem markdown.

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON:

# --- DIAGNÓSTICOS ATUAIS (até 4) ---
- diag_atual_1_nome (string): Nome do 1º diagnóstico em Title Case.
- diag_atual_2_nome (string): Nome do 2º diagnóstico.
- diag_atual_3_nome (string): Nome do 3º diagnóstico.
- diag_atual_4_nome (string): Nome do 4º diagnóstico.

- diag_atual_1_class (string): Classificação do diag 1 (ex: "KDIGO 3", "Foco Pulmonar"). Se ausente, "".
- diag_atual_2_class (string): Classificação do diag 2.
- diag_atual_3_class (string): Classificação do diag 3.
- diag_atual_4_class (string): Classificação do diag 4.

- diag_atual_1_data (string): Data EXATAMENTE como no texto. Se ausente, "".
- diag_atual_2_data (string): Data do diag 2.
- diag_atual_3_data (string): Data do diag 3.
- diag_atual_4_data (string): Data do diag 4.

- diag_atual_1_obs (string): Observações e sub-itens (separados por \\n). Sem condutas. Se ausente, "".
- diag_atual_2_obs (string): Observações do diag 2.
- diag_atual_3_obs (string): Observações do diag 3.
- diag_atual_4_obs (string): Observações do diag 4.

# --- DIAGNÓSTICOS RESOLVIDOS (até 4) ---
- diag_resolv_1_nome (string): Nome do 1º evento passado/resolvido.
- diag_resolv_2_nome (string): 2º resolvido.
- diag_resolv_3_nome (string): 3º resolvido.
- diag_resolv_4_nome (string): 4º resolvido.

- diag_resolv_1_class (string): Classificação do resolvido 1.
- diag_resolv_2_class (string): Classificação do resolvido 2.
- diag_resolv_3_class (string): Classificação do resolvido 3.
- diag_resolv_4_class (string): Classificação do resolvido 4.

- diag_resolv_1_data_inicio (string): Data de início do resolvido 1 (EXATAMENTE como no texto).
- diag_resolv_1_data_fim (string): Data de resolução do resolvido 1.
- diag_resolv_2_data_inicio (string): Data de início do resolvido 2.
- diag_resolv_2_data_fim (string): Data de resolução do resolvido 2.
- diag_resolv_3_data_inicio (string): Data de início do resolvido 3.
- diag_resolv_3_data_fim (string): Data de resolução do resolvido 3.
- diag_resolv_4_data_inicio (string): Data de início do resolvido 4.
- diag_resolv_4_data_fim (string): Data de resolução do resolvido 4.

- diag_resolv_1_obs (string): Resumo do desfecho do resolvido 1.
- diag_resolv_2_obs (string): Resumo do desfecho do resolvido 2.
- diag_resolv_3_obs (string): Resumo do desfecho do resolvido 3.
- diag_resolv_4_obs (string): Resumo do desfecho do resolvido 4.

# EXEMPLO DE SAÍDA PERFEITA
Texto de entrada:
  1) POLIPOSE ADENOMATOSA FAMILIAR
  >>POT RETOCOLECTOMIA TOTAL COM RESERVATORIO ILEAL -1999
  >>POT RECONSTRUÇÃO DE TRÂNSITO - 2001
  2) ADENOMA EM PÓLIPO DUODENAL DE BAIXO GRAU - 2019
  3) ADENOMA EM PÓLIPO DUODENAL DE ALTO GRAU DE 1,2 CM EM REGIÃO PÓS BULBAR - 01/2022
  4) POT DRENAGEM DE ABSCESSO PERINEAL 27/11/21

JSON correto:
{
  "diag_atual_1_nome": "Polipose Adenomatosa Familiar",
  "diag_atual_2_nome": "Adenoma em Pólipo Duodenal de Baixo Grau",
  "diag_atual_3_nome": "Adenoma em Pólipo Duodenal de Alto Grau de 1,2 cm",
  "diag_atual_4_nome": "POT Drenagem de Abscesso Perineal",
  "diag_atual_1_class": "",
  "diag_atual_2_class": "",
  "diag_atual_3_class": "Região Pós Bulbar",
  "diag_atual_4_class": "",
  "diag_atual_1_data": "1999",
  "diag_atual_2_data": "2019",
  "diag_atual_3_data": "01/2022",
  "diag_atual_4_data": "27/11/21",
  "diag_atual_1_obs": "POT Retocolectomia Total com Reservatório Ileal - 1999\nPOT Reconstrução de Trânsito - 2001",
  "diag_atual_2_obs": "",
  "diag_atual_3_obs": "",
  "diag_atual_4_obs": "",
  "diag_resolv_1_nome": "",
  "diag_resolv_2_nome": "",
  "diag_resolv_3_nome": "",
  "diag_resolv_4_nome": "",
  "diag_resolv_1_class": "",
  "diag_resolv_2_class": "",
  "diag_resolv_3_class": "",
  "diag_resolv_4_class": "",
  "diag_resolv_1_data_inicio": "",
  "diag_resolv_1_data_fim": "",
  "diag_resolv_2_data_inicio": "",
  "diag_resolv_2_data_fim": "",
  "diag_resolv_3_data_inicio": "",
  "diag_resolv_3_data_fim": "",
  "diag_resolv_4_data_inicio": "",
  "diag_resolv_4_data_fim": "",
  "diag_resolv_1_obs": "",
  "diag_resolv_2_obs": "",
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
