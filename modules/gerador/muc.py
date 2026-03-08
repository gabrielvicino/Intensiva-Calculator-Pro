from ._base import *
import re as _re_muc
import streamlit as st

def _secao_muc() -> list[str]:
    """
    Gera as linhas da seção '# Medicações de Uso Contínuo'.
    Formato: {i}- {nome}[; {dose}][; {freq}]
    Adesão global aparece se preenchida.
    """
    linhas = []

    ordem = st.session_state.get("muc_ordem", list(range(1, 21)))
    for id_real in ordem:
        nome = _get(f"muc_{id_real}_nome")
        if not nome:
            continue
        partes = [nome]
        dose = _get(f"muc_{id_real}_dose")
        if dose:
            partes.append(dose)
        freq = _get(f"muc_{id_real}_freq")
        if freq:
            # Remove especificações de horário entre parênteses: (manhã), (noite), (jejum), etc.
            freq_limpa = _re_muc.sub(r'\s*\([^)]*\)', '', freq).strip()
            if freq_limpa:
                partes.append(freq_limpa)
        linhas.append(f"{len(linhas)+1}- {'; '.join(partes)}")

    if not linhas:
        return []

    corpo = ["# Medicações de Uso Contínuo"]

    adesao = _get("muc_adesao_global")
    if adesao:
        corpo.append(adesao)

    corpo += linhas
    return corpo
