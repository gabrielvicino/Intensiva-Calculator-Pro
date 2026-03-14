"""
Pacote agentes_secoes — cada agente em seu próprio módulo.
Interface pública idêntica ao arquivo original.
"""
import streamlit as st
from ._base import _chamar_ia, _REGRA_DATA

from .identificacao import preencher_identificacao
from .scores import preencher_scores
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
    "scores":         preencher_scores,
    "hd":             preencher_hd,
    "comorbidades":   preencher_comorbidades,
    "muc":            preencher_muc,
    "hmpa":           preencher_hmpa,
    "dispositivos":   preencher_dispositivos,
    "culturas":       preencher_culturas,
    "antibioticos":   preencher_antibioticos,
    "complementares": preencher_complementares,
    "evolucao":       preencher_evolucao,
}

_NOTAS_MAP = {
    "identificacao":  "identificacao_notas",
    "scores":         "scores_notas",
    "hd":             "hd_notas",
    "comorbidades":   "comorbidades_notas",
    "muc":            "muc_notas",
    "hmpa":           "hmpa_texto",
    "dispositivos":   "dispositivos_notas",
    "culturas":       "culturas_notas",
    "antibioticos":   "antibioticos_notas",
    "complementares": "complementares_notas",
    "evolucao":       "evolucao_notas",
}

NOMES_SECOES = {
    "identificacao":   "1. Identificação",
    "scores":          "2. Scores Clínicos",
    "hd":              "3. Diagnósticos",
    "comorbidades":    "4. Comorbidades",
    "muc":             "5. MUC",
    "hmpa":            "6. HMPA",
    "intraoperatorio": "7. Intraoperatório",
    "dispositivos":    "8. Dispositivos",
    "culturas":        "9. Culturas",
    "antibioticos":    "10. Antibióticos",
    "complementares":  "11. Complementares",
    "evolucao":        "12. Evolução Clínica",
    "condutas":        "15. Condutas",
    "prescricao":      "16. Prescrição",
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
