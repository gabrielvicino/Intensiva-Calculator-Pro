from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 2: HD - DIAGNÓSTICOS ATUAIS E PRÉVIOS
# ==============================================================================
_PROMPT_HD = """# CONTEXTO
Você é uma ferramenta de formatação e extração de diagnósticos clínicos hospitalares.

# OBJETIVO
Ler o texto fornecido e extrair até 8 diagnósticos na ordem exata do texto, formatando-os de forma limpa e profissional. NÃO classifique como "Atual" ou "Resolvida" — isso é responsabilidade do usuário.

# REGRAS

## Formatação (Title Case) — SEM PERDER DADOS
- Converta CAIXA ALTA para Title Case (Primeira Letra Maiúscula).
- Preposições/artigos em minúsculas: de, em, com, por, para, do, da, no, na, etc.
- Siglas médicas em MAIÚSCULAS: POT, UTI, IRA, TVP, TEP, IAM, ICC, DM, HAS, DPOC, VMI, PAV, KDIGO, KPC, MRSA, etc.
- Exemplos:
  "POLIPOSE ADENOMATOSA FAMILIAR" → "Polipose Adenomatosa Familiar"
  "POT DRENAGEM DE ABSCESSO PERINEAL" → "POT Drenagem de Abscesso Perineal"

## Datas — REGRA PRIORITÁRIA (sobrepõe qualquer outra regra)
- Mantenha datas **EXATAMENTE** como no texto. NÃO reformate.
- "1999" → "1999" | "01/2022" → "01/2022" | "27/11/21" → "27/11/21"

## Sub-itens (>> ou >) → campo obs
- Linhas que começam com ">>" ou ">" são OBSERVAÇÕES do diagnóstico pai.
- Cada sub-item vai em uma linha separada no campo `_obs` (separados por \\n).
- Converta sub-itens também para Title Case (siglas em maiúsculas).
- NÃO crie diagnósticos separados para sub-itens.

## Preenchimento
- Extraia na ordem exata do texto. Até 8 diagnósticos (diag_1 a diag_8).
- Se não houver informação, retorne `""`. NÃO use `null`. NÃO invente dados.
- JSON puro, sem markdown.

# ENTRADAS
<TEXTO_ALVO>
[Texto clínico]
</TEXTO_ALVO>

<VARIAVEIS>
Para cada diagnóstico i (1 a 8):
- diag_{i}_nome (string): Nome em Title Case.
- diag_{i}_class (string): Classificação/subtipo. Se ausente, "".
- diag_{i}_data (string): Data EXATAMENTE como no texto. Se ausente, "".
- diag_{i}_obs (string): Sub-itens e observações, cada um em linha separada (\\n). Sem condutas. Se ausente, "".

# EXEMPLO
Entrada:
  1) POLIPOSE ADENOMATOSA FAMILIAR
  >>POT RETOCOLECTOMIA TOTAL COM RESERVATORIO ILEAL -1999
  >>POT RECONSTRUÇÃO DE TRÂNSITO - 2001
  2) ADENOMA EM PÓLIPO DUODENAL DE BAIXO GRAU - 2019
  3) ADENOMA EM PÓLIPO DUODENAL DE ALTO GRAU DE 1,2 CM EM REGIÃO PÓS BULBAR - 01/2022
  4) ADENOMA EM PÓLIPO DUODENAL DE BAIXO GRAU DE 1,0 CM EM TERCEIRA PORÇÃO - 07/2022
  5) POT DRENAGEM DE ABSCESSO PERINEAL 27/11/21

JSON:
{
  "diag_1_nome": "Polipose Adenomatosa Familiar",
  "diag_1_class": "",
  "diag_1_data": "1999",
  "diag_1_obs": "POT Retocolectomia Total com Reservatório Ileal - 1999\\nPOT Reconstrução de Trânsito - 2001",
  "diag_2_nome": "Adenoma em Pólipo Duodenal de Baixo Grau",
  "diag_2_class": "",
  "diag_2_data": "2019",
  "diag_2_obs": "",
  "diag_3_nome": "Adenoma em Pólipo Duodenal de Alto Grau de 1,2 cm",
  "diag_3_class": "Região Pós Bulbar",
  "diag_3_data": "01/2022",
  "diag_3_obs": "",
  "diag_4_nome": "Adenoma em Pólipo Duodenal de Baixo Grau de 1,0 cm",
  "diag_4_class": "Terceira Porção",
  "diag_4_data": "07/2022",
  "diag_4_obs": "",
  "diag_5_nome": "POT Drenagem de Abscesso Perineal",
  "diag_5_class": "",
  "diag_5_data": "27/11/21",
  "diag_5_obs": "",
  "diag_6_nome": "",
  "diag_6_class": "",
  "diag_6_data": "",
  "diag_6_obs": "",
  "diag_7_nome": "",
  "diag_7_class": "",
  "diag_7_data": "",
  "diag_7_obs": "",
  "diag_8_nome": "",
  "diag_8_class": "",
  "diag_8_data": "",
  "diag_8_obs": ""
}
</VARIAVEIS>"""


def preencher_hd(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_HD, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    def _s(key): return str(r.get(key) or "").strip()

    resultado = {}

    for i in range(1, 9):
        nome = _s(f"diag_{i}_nome")
        resultado[f"hd_{i}_nome"]          = nome
        resultado[f"hd_{i}_class"]         = _s(f"diag_{i}_class")
        resultado[f"hd_{i}_data_inicio"]   = _s(f"diag_{i}_data")
        resultado[f"hd_{i}_data_resolvido"]= ""
        resultado[f"hd_{i}_status"]        = "Atual" if nome else None
        resultado[f"hd_{i}_obs"]           = _s(f"diag_{i}_obs")

    return resultado
