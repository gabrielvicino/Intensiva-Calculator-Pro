from ._base import *
import streamlit as st

def _secao_prescricao() -> list[str]:
    """
    Gera a seção '# Prescrição' com o conteúdo formatado pela IA (bloco 14).
    Aparece abaixo de Condutas no prontuário completo.
    """
    texto = _get("prescricao_formatada").strip()
    if not texto:
        return []
    return ["===", "# Prescrição", "", texto]
