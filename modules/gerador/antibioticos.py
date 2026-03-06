from ._base import *
import streamlit as st

def _secao_antibioticos() -> list[str]:
    """
    Gera as linhas da seção Antibióticos.
    Lista única com status Atual/Prévio. Saída:
    # Antibiótico Atual
    1- {nome}[; Foco {foco}][; {tipo}][; {data_ini} → {data_fim}[ (X dias)]]
    # Antibiótico Prévio
    1- {nome}[; Foco {foco}][; {tipo}][; {data_ini} - {data_fim}]
    """
    _TIPO_EXPANDIDO = {"Empírico": "Empírico", "Guiado por Cultura": "Guiado por Cultura"}

    def _linha_atual(i, idx):
        nome     = _get(f"atb_{idx}_nome")
        foco     = _sigla_upper(_get(f"atb_{idx}_foco"))
        tipo     = _get(f"atb_{idx}_tipo") or ""
        data_ini = _get(f"atb_{idx}_data_ini")
        data_fim = _get(f"atb_{idx}_data_fim")
        num_dias = _get(f"atb_{idx}_num_dias")
        if not nome:
            return None
        partes = [nome]
        if foco:
            partes.append(f"Foco {foco}")
        if tipo in _TIPO_EXPANDIDO:
            partes.append(_TIPO_EXPANDIDO[tipo])
        if data_ini and data_fim:
            prog = num_dias.strip() if num_dias else _calcular_dias(data_ini, data_fim)
            datas = f"{data_ini} → {data_fim}"
            if prog:
                suf = prog if "dia" in str(prog).lower() else f"{prog} dias"
                datas += f" (Programado {suf})"
            partes.append(datas)
        elif data_ini:
            partes.append(data_ini)
        return f"{i}- " + "; ".join(partes)

    def _linha_previo(i, idx):
        nome     = _get(f"atb_{idx}_nome")
        foco     = _sigla_upper(_get(f"atb_{idx}_foco"))
        tipo     = _get(f"atb_{idx}_tipo") or ""
        data_ini = _get(f"atb_{idx}_data_ini")
        data_fim = _get(f"atb_{idx}_data_fim")
        if not nome:
            return None
        partes = [nome]
        if foco:
            partes.append(f"Foco {foco}")
        if tipo in _TIPO_EXPANDIDO:
            partes.append(_TIPO_EXPANDIDO[tipo])
        if data_ini and data_fim:
            dias_uso = _calcular_dias(data_ini, data_fim)
            if dias_uso:
                n = dias_uso.split()[0]
                partes.append(f"{data_ini} - {data_fim} (Uso por {n} dias)")
            else:
                partes.append(f"{data_ini} - {data_fim}")
        elif data_ini:
            partes.append(data_ini)
        elif data_fim:
            partes.append(data_fim)
        return f"{i}- " + "; ".join(partes)

    ordem = st.session_state.get("atb_ordem", list(range(1, 9)))

    atuais = []
    previos = []
    for idx in ordem:
        status = _get(f"atb_{idx}_status")
        if status == "Atual":
            linha = _linha_atual(len(atuais) + 1, idx)
            if linha:
                atuais.append(linha)
        elif status == "Prévio":
            linha = _linha_previo(len(previos) + 1, idx)
            if linha:
                previos.append(linha)

    if not atuais and not previos:
        return []

    resultado = []
    if atuais:
        resultado.append("# Antibiótico Atual")
        resultado.extend(atuais)
    if previos:
        if resultado:
            resultado.append("")
        resultado.append("# Antibiótico Prévio")
        resultado.extend(previos)

    return resultado
