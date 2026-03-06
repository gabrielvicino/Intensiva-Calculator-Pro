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
    alergia = st.session_state.get("muc_alergia")
    alergia_obs = _get("muc_alergia_obs")

    # Adesão e alergia na mesma linha quando ambos existem
    partes_muc = []
    if adesao:
        partes_muc.append(adesao)  # Uso Regular / Uso Irregular / Desconhecido
    if alergia == "Presente":
        partes_muc.append(f"Alergias: {alergia_obs}" if alergia_obs else "Alergias: presente")
    elif alergia == "Nega":
        partes_muc.append("Nega alergias")
    elif alergia == "Desconhecido":
        partes_muc.append("Desconhece alergias")
    if partes_muc:
        corpo.append(" | ".join(partes_muc))

    corpo += linhas
    return corpo
