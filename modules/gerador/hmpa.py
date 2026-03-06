from ._base import *
import streamlit as st

def _secao_hmpa() -> list[str]:
    """
    Gera as linhas da seção '# História da Moléstia Pregressa Atual'.
    Prioriza o texto reescrito pelo agente; se vazio, usa o texto bruto.
    """
    texto = _get("hmpa_reescrito") or _get("hmpa_texto")
    if not texto or not texto.strip():
        return []
    return ["# História da Moléstia Pregressa Atual"] + texto.strip().splitlines()
