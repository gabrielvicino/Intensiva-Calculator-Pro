from ._base import *
import streamlit as st

def _secao_hmpa() -> list[str]:
    """
    Gera as linhas da seção '# História da Moléstia Pregressa Atual'.
    Prioriza o texto reescrito pelo agente; se vazio, usa o texto bruto.
    Garante bloco único — deduplica parágrafos repetidos.
    """
    texto = _get("hmpa_reescrito") or _get("hmpa_texto")
    if not texto or not texto.strip():
        return []

    # Deduplica parágrafos: remove blocos idênticos que apareçam >1 vez
    paragrafos = texto.strip().split("\n\n")
    vistos = []
    for p in paragrafos:
        norm = p.strip()
        if norm and norm not in vistos:
            vistos.append(norm)
    texto_limpo = "\n\n".join(vistos)

    return ["# História da Moléstia Pregressa Atual"] + texto_limpo.splitlines()
