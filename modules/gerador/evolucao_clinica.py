from ._base import *
import streamlit as st

def _secao_evolucao_clinica() -> list[str]:
    """
    Gera a seção '# Evolução Clínica'.
    Garante bloco único — deduplica parágrafos repetidos.
    """
    texto = _get("evolucao_notas").strip()
    if not texto:
        return []

    # Deduplica parágrafos idênticos
    paragrafos = texto.split("\n\n")
    vistos = []
    for p in paragrafos:
        norm = p.strip()
        if norm and norm not in vistos:
            vistos.append(norm)
    texto_limpo = "\n\n".join(vistos)

    return ["# Evolução Clínica", texto_limpo]
