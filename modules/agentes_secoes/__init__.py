"""
Pacote agentes_secoes — cada agente em seu próprio módulo.
Interface pública idêntica ao arquivo original.
"""
import streamlit as st
from ._base import _chamar_ia, _REGRA_DATA

from .identificacao import preencher_identificacao
from .hd import preencher_hd
from .comorbidades import preencher_comorbidades
from .muc import preencher_muc
from .hmpa import preencher_hmpa
from .dispositivos import preencher_dispositivos
from .culturas import preencher_culturas
from .antibioticos import preencher_antibioticos
from .complementares import preencher_complementares
from .laboratoriais import preencher_laboratoriais
from .evolucao import preencher_evolucao
from .sistemas import preencher_sistemas
from .controles import preencher_controles

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
    "condutas":       "14. Condutas",
    "prescricao":     "15. Prescrição",
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
