from ._base import *
import streamlit as st

def _secao_comorbidades() -> list[str]:
    """
    Gera as linhas da seção '# Comorbidades'.
    Etilismo, Tabagismo, SPA na mesma linha. Ausente→Nega, Presente→Ativo.
    Formato: Etilismo: Nega | Tabagismo: Ativo; 20 anos-maço | SPA: Nega
    """
    corpo = []

    def _etil_tbg_spa(label, key, obs_key):
        val = st.session_state.get(key)
        if not val:
            return None
        exibir = "Nega" if val == "Ausente" else ("Ativo" if val == "Presente" else val)
        obs = _get(obs_key)
        if exibir == "Ativo" and obs:
            return f"{label}: {exibir}; {obs}"
        return f"{label}: {exibir}"

    # Lista de comorbidades
    linhas_cmd = []
    for i in range(1, 11):
        nome = _get(f"cmd_{i}_nome")
        if not nome:
            continue
        linha = nome
        classif = _get(f"cmd_{i}_class")
        if classif:
            linha += f"; {classif}"
        linhas_cmd.append(f"{len(linhas_cmd)+1}- {linha}")

    # Exposições (Etilismo, Tabagismo, SPA) — seção separada
    exposicoes = []
    for label, key, obs_key in [
        ("Etilismo", "cmd_etilismo", "cmd_etilismo_obs"),
        ("Tabagismo", "cmd_tabagismo", "cmd_tabagismo_obs"),
        ("SPA", "cmd_spa", "cmd_spa_obs"),
    ]:
        p = _etil_tbg_spa(label, key, obs_key)
        if p:
            exposicoes.append(p)

    if not linhas_cmd and not exposicoes:
        return []

    resultado = []
    if linhas_cmd:
        resultado.append("# Comorbidades")
        resultado.extend(linhas_cmd)
    if exposicoes:
        if resultado:
            resultado.append("")
        resultado.append("# Exposições")
        resultado.extend(exposicoes)
    return resultado


# _calcular_dias está em _base.py (compartilhada com antibioticos.py e outros)
