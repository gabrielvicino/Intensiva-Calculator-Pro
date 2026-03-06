from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 11: EVOLUÇÃO CLÍNICA (texto livre — passa direto)
# ==============================================================================
def preencher_evolucao(texto, api_key, provider, modelo):
    return {"evolucao_notas": texto.strip()} if texto and texto.strip() else {}
