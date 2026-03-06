from ._base import *
import streamlit as st

def _secao_evolucao_clinica() -> list[str]:
    texto = _get("evolucao_notas").strip()
    if not texto:
        return []
    return ["# Evolução Clínica", texto]
