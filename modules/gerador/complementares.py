from ._base import *
import re as _re
import streamlit as st

_SIGLAS_UPPER = {
    "eda", "tc", "rm", "rx", "usg", "eco", "ecott", "ecote", "cate",
    "bnp", "pet", "eeg", "emg", "enmg", "rnm", "dvp", "pam", "bva",
}


def _normalizar_nome_exame(nome: str) -> str:
    """Converte nome de exame para formato correto: siglas em maiúsculas, resto em Title Case."""
    palavras = nome.split()
    resultado = []
    for p in palavras:
        if p.lower() in _SIGLAS_UPPER:
            resultado.append(p.upper())
        elif p.upper() == p and len(p) <= 4:
            resultado.append(p.upper())
        else:
            resultado.append(p.capitalize())
    return " ".join(resultado)


def _secao_complementares() -> list[str]:
    """
    Gera as linhas da seção Exames Complementares.
    Formato por exame (sem linha em branco entre exames):
        {i}- {Nome do Exame} (data)
        Laudo
    """
    ordem = st.session_state.get("comp_ordem", list(range(1, 9)))

    blocos = []
    contador = 1
    for idx in ordem:
        exame = _get(f"comp_{idx}_exame").strip()
        data = _get(f"comp_{idx}_data").strip()
        laudo = _get(f"comp_{idx}_laudo").strip()
        if not exame and not laudo:
            continue
        nome = _normalizar_nome_exame(exame) if exame else "Exame Complementar"
        cabecalho = f"{contador}- {nome} ({data})" if data else f"{contador}- {nome}"
        bloco = [cabecalho]
        if laudo:
            bloco.append(laudo)
        blocos.append(bloco)
        contador += 1

    if not blocos:
        return []

    resultado = ["# Exames Complementares"]
    for bloco in blocos:
        resultado.extend(bloco)

    return resultado
