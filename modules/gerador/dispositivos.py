from ._base import *
import streamlit as st

def _secao_dispositivos() -> list[str]:
    """
    Formato:
      # Dispositivos Atuais
      {i}- {nome}[; {local}][; {data_insercao}] - Atual

      # Dispositivos Retirados
      {i}- {nome}[; {local}][; {data_insercao} - {data_retirada}]
    """
    ordem = st.session_state.get("disp_ordem", list(range(1, 9)))

    ativos = []
    retirados = []

    for id_real in ordem:
        nome = _sigla_upper(_get(f"disp_{id_real}_nome"))
        if not nome:
            continue

        status        = _get(f"disp_{id_real}_status")
        local         = _sigla_upper(_get(f"disp_{id_real}_local"))
        data_insercao = _get(f"disp_{id_real}_data_insercao")
        data_retirada = _get(f"disp_{id_real}_data_retirada")

        partes = [nome]
        if local:
            partes.append(local)

        if status == "Removido":
            datas = " - ".join(filter(None, [data_insercao, data_retirada]))
            if datas:
                partes.append(datas)
            retirados.append("; ".join(partes))
        else:
            if data_insercao:
                partes.append(data_insercao)
            ativos.append("; ".join(partes))

    if not ativos and not retirados:
        return []

    corpo = []
    if ativos:
        corpo.append("# Dispositivos Atuais")
        for i, linha in enumerate(ativos, 1):
            corpo.append(f"{i}- {linha}")

    if retirados:
        if corpo:
            corpo.append("")
        corpo.append("# Dispositivos Prévios")
        for i, linha in enumerate(retirados, 1):
            corpo.append(f"{i}- {linha}")

    return corpo
