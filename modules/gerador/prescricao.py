from ._base import *
import streamlit as st

def _secao_prescricao() -> list[str]:
    """
    Gera a seção '# Prescrição' ao final do prontuário.
    Usa a prescrição formatada salva via PACER.
    """
    texto = _get("prescricao_formatada").strip()
    if not texto:
        return []
    return ["===", "# Prescrição", "", texto]
