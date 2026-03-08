from ._base import *
import streamlit as st

def _secao_antibioticos() -> list[str]:
    """
    Gera as linhas da seção Antibióticos.
    Lista única com status Atual/Prévio. Saída:
    # Antibiótico Atual
    1- {nome}[; Foco {foco}][; {tipo}][; {data_ini} → {data_fim}[ (X dias)]]
    # Antibióticos Prévios
    1- {nome}[; Foco {foco}][; {tipo}][; {data_ini} - {data_fim}]
    """
    _TIPO_EXPANDIDO = {"Empírico": "Empírico", "Guiado por Cultura": "Guiado por Cultura"}

    def _linhas_atual(i, idx):
        """Retorna lista de strings: linha principal + linha > foco."""
        nome     = _get(f"atb_{idx}_nome")
        foco     = _sigla_upper(_get(f"atb_{idx}_foco"))
        tipo     = _get(f"atb_{idx}_tipo") or ""
        data_ini = _get(f"atb_{idx}_data_ini")
        data_fim = _get(f"atb_{idx}_data_fim")
        num_dias = _get(f"atb_{idx}_num_dias")
        if not nome:
            return []
        # Linha principal: nome; tipo
        cabecalho = [nome]
        if tipo in _TIPO_EXPANDIDO:
            cabecalho.append(_TIPO_EXPANDIDO[tipo])
        resultado_linhas = [f"{i}- " + "; ".join(cabecalho)]
        # Linha > foco + datas
        if foco or data_ini:
            foco_partes = []
            if foco:
                foco_partes.append(f"Foco {foco}")
            if data_ini and data_fim:
                prog = num_dias.strip() if num_dias else _calcular_dias(data_ini, data_fim)
                datas = f"{data_ini} → {data_fim}"
                if prog:
                    suf = prog if "dia" in str(prog).lower() else f"{prog} dias"
                    datas += f" (Programado {suf})"
                foco_partes.append(datas)
            elif data_ini:
                foco_partes.append(data_ini)
            resultado_linhas.append("> " + "; ".join(foco_partes))
        return resultado_linhas

    def _linhas_previo(i, idx):
        """Retorna lista de strings: linha principal + linha > foco."""
        nome     = _get(f"atb_{idx}_nome")
        foco     = _sigla_upper(_get(f"atb_{idx}_foco"))
        tipo     = _get(f"atb_{idx}_tipo") or ""
        data_ini = _get(f"atb_{idx}_data_ini")
        data_fim = _get(f"atb_{idx}_data_fim")
        if not nome:
            return []
        # Linha principal: nome; tipo; datas
        cabecalho = [nome]
        if tipo in _TIPO_EXPANDIDO:
            cabecalho.append(_TIPO_EXPANDIDO[tipo])
        if data_ini and data_fim:
            dias_uso = _calcular_dias(data_ini, data_fim)
            if dias_uso:
                n = dias_uso.split()[0]
                cabecalho.append(f"{data_ini} - {data_fim} (Uso por {n} dias)")
            else:
                cabecalho.append(f"{data_ini} - {data_fim}")
        elif data_ini:
            cabecalho.append(data_ini)
        elif data_fim:
            cabecalho.append(data_fim)
        resultado_linhas = [f"{i}- " + "; ".join(cabecalho)]
        # Linha > foco
        if foco:
            resultado_linhas.append(f"> Foco {foco}")
        return resultado_linhas

    ordem = st.session_state.get("atb_ordem", list(range(1, 9)))

    atuais = []
    previos = []
    for idx in ordem:
        status = _get(f"atb_{idx}_status")
        if status == "Atual":
            linhas = _linhas_atual(len(atuais) + 1, idx)
            if linhas:
                atuais.extend(linhas)
        elif status == "Prévio":
            linhas = _linhas_previo(len(previos) + 1, idx)
            if linhas:
                previos.extend(linhas)

    if not atuais and not previos:
        return []

    resultado = []
    if atuais:
        resultado.append("# Antibiótico Atual")
        resultado.extend(atuais)
    if previos:
        if resultado:
            resultado.append("")
        resultado.append("# Antibióticos Prévios")
        resultado.extend(previos)

    return resultado
