from ._base import *
import streamlit as st

def _secao_diagnosticos() -> list[str]:
    """
    Gera as linhas da seção '# Diagnósticos'.
    Mesmo modelo de dispositivos: agrupa por status (Atual / Resolvida).
    Campos: hd_{1..8}_nome, _class, _data_inicio, _data_resolvido, _status, _obs.
    Formato:
      # Diagnósticos Atuais
      {i}- {nome}[; {classif}][; {início}]
      # Diagnósticos Resolvidos
      {i}- {nome}[; {classif}][; {início} - {resolvido}]
    A conduta NUNCA aparece aqui — vai para Condutas Registradas.
    """
    ordem = st.session_state.get("hd_ordem", list(range(1, 9)))
    atuais = []
    resolvidos = []

    for id_real in ordem:
        nome = _get(f"hd_{id_real}_nome")
        if not nome:
            continue

        status = _get(f"hd_{id_real}_status")
        classif = _get(f"hd_{id_real}_class")
        data_ini = _get(f"hd_{id_real}_data_inicio")
        data_res = _get(f"hd_{id_real}_data_resolvido")

        partes = [nome]
        if classif:
            partes.append(classif)
        if data_ini:
            partes.append(data_ini)
        if status == "Resolvida" and data_res:
            if data_ini:
                partes[-1] = f"{data_ini} - {data_res}"
            else:
                partes.append(data_res)

        bloco = ["; ".join(partes)]
        bloco += _obs_para_linhas(st.session_state.get(f"hd_{id_real}_obs", ""), excluir_conduta=True)

        if status == "Resolvida":
            resolvidos.append(bloco)
        else:
            atuais.append(bloco)

    corpo = []
    if atuais:
        corpo.append("# Diagnósticos Atuais")
        for i, bloco in enumerate(atuais, 1):
            corpo.append(f"{i}- {bloco[0]}")
            corpo.extend(bloco[1:])

    if resolvidos:
        corpo.append("")
        corpo.append("# Diagnósticos Resolvidos")
        for i, bloco in enumerate(resolvidos, 1):
            corpo.append(f"{i}- {bloco[0]}")
            corpo.extend(bloco[1:])

    while corpo and corpo[-1] == "":
        corpo.pop()

    if not corpo:
        return []
    return corpo
