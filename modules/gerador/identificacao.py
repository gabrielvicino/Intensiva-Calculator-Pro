from ._base import *
import streamlit as st

def _secao_identificacao() -> list[str]:
    """
    Gera as linhas da seção '# Identificação & Scores'.
    Regra geral: campo vazio → linha não aparece.
    O cabeçalho só aparece se ao menos uma linha de conteúdo for gerada.
    """
    corpo = []

    # 1. Nome + Idade + Sexo — todos na mesma linha
    nome  = _get("nome")
    idade = _get("idade", 0)
    sexo  = _get("sexo")
    if nome:
        linha = f"Nome: {nome}"
        if idade:
            linha += f", {idade} anos"
        if sexo:
            linha += f", {sexo}"
        corpo.append(linha)

    # 3. Prontuário + Leito
    prontuario = _get("prontuario")
    leito = _get("leito")
    if prontuario or leito:
        partes = []
        if prontuario:
            partes.append(f"Prontuário: {prontuario}")
        if leito:
            partes.append(f"Leito: {leito}")
        corpo.append(" | ".join(partes))

    # 4. Origem
    origem = _get("origem")
    if origem:
        corpo.append(f"Origem: {origem}")

    # 5. Equipe Titular e Interconsultora (linhas separadas)
    equipe = _sigla_upper(_get("equipe"))
    interconsultora = _sigla_upper(_get("interconsultora"))
    if equipe:
        corpo.append(f"Equipe Titular: {equipe}")
    if interconsultora:
        corpo.append(f"Interconsultora: {interconsultora}")

    # 6. Data Internação Hospitalar
    di_hosp = _get("di_hosp")
    if di_hosp:
        corpo.append(f"Data Internação Hospitalar: {di_hosp}")

    # 7. Data Internação UTI
    di_uti = _get("di_uti")
    if di_uti:
        corpo.append(f"Data Internação UTI: {di_uti}")

    # 8. Data Internação Enfermaria — só aparece se preenchida
    di_enf = _get("di_enf")
    if di_enf:
        corpo.append(f"Data Internação Enfermaria: {di_enf}")

    # 9. Alergias
    import streamlit as _st
    alergias_status = _st.session_state.get("alergias_status")
    alergias = _get("alergias")
    if alergias_status == "Nega":
        corpo.append("Alergias: Nega")
    elif alergias_status == "Desconhecido":
        corpo.append("Alergias: Desconhecido")
    elif alergias_status == "Presente":
        corpo.append(f"Alergias: {alergias}" if alergias else "Alergias: Presente")
    elif alergias:
        corpo.append(f"Alergias: {alergias}")

    # 10. Paliativo — somente se True, em caixa alta
    if _get("paliativo", False):
        corpo.append("PACIENTE EM CUIDADOS PROPORCIONAIS")

    # Cabeçalho só aparece se houver conteúdo
    if not corpo:
        return []
    if not corpo:
        return []

    # Departamento aparece ANTES do header de seção (sempre em MAIÚSCULO)
    departamento = _get("departamento")
    header = []
    if departamento:
        header = [f"# {str(departamento).strip().upper()} #", ""]
    return header + ["# Identificação"] + corpo


# _obs_para_linhas está em _base.py (compartilhada com diagnosticos.py e outros)
