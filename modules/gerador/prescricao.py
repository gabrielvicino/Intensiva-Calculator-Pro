from ._base import *
import streamlit as st

def _secao_prescricao() -> list[str]:
    """
    Gera a seção '# Prescrição' ao final do prontuário.
    Usa a versão formatada pela IA se disponível; senão usa a bruta colada.
    """
    texto = _get("prescricao_formatada").strip() or _get("prescricao_bruta").strip()
    if not texto:
        return []
    return ["===", "# Prescrição", "", texto]
