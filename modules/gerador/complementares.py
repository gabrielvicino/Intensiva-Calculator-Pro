from ._base import *
import streamlit as st

def _secao_complementares() -> list[str]:
    """
    Gera as linhas da seção Exames Complementares.
    Formato por exame:
        {i}- {Nome do Exame} (data)
        Laudo
    Linha em branco entre exames.
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
        nome = exame or "Exame complementar"
        cabecalho = f"{contador}- {nome} ({data})" if data else f"{contador}- {nome}"
        bloco = [cabecalho]
        if laudo:
            bloco.append(laudo)
        blocos.append(bloco)
        contador += 1

    if not blocos:
        return []

    resultado = ["# Exames Complementares"]
    for i, bloco in enumerate(blocos):
        resultado.extend(bloco)
        if i < len(blocos) - 1:
            resultado.append("")

    return resultado
