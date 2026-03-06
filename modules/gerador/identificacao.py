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
    equipe = _get("equipe")
    interconsultora = _get("interconsultora")
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

    # 9. SAPS 3
    saps3 = _get("saps3")
    if saps3:
        corpo.append(f"SAPS 3: {saps3}")

    # 10. SOFA admissão
    sofa_adm = _get("sofa_adm", 0)
    try:
        sofa_adm = int(sofa_adm)
    except (ValueError, TypeError):
        sofa_adm = 0
    if sofa_adm:
        corpo.append(f"SOFA admissão: {sofa_adm}")

    # 11. PPS
    pps = _get("pps")
    if pps:
        corpo.append(f"PPS: {pps}")

    # 12. mRS prévio
    mrs = _get("mrs")
    if mrs:
        corpo.append(f"mRS prévio: {mrs}")

    # 13. CFS
    cfs = _get("cfs")
    if cfs:
        corpo.append(f"CFS: {cfs}")

    # 14. Paliativo — somente se True, em caixa alta, sem espaço extra
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
    return header + ["# Identificação & Scores"] + corpo


# _obs_para_linhas está em _base.py (compartilhada com diagnosticos.py e outros)
