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

    # Remove linha de título colada pelo usuário (ex: "Evolução Clínica — 19/02/2026")
    linhas_raw = texto.splitlines()
    if linhas_raw and linhas_raw[0].strip().lower().startswith("evolução clínica"):
        linhas_raw = linhas_raw[1:]
    texto = "\n".join(linhas_raw).strip()
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
