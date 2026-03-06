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

    partes = []
    for label, key, obs_key in [
        ("Etilismo", "cmd_etilismo", "cmd_etilismo_obs"),
        ("Tabagismo", "cmd_tabagismo", "cmd_tabagismo_obs"),
        ("SPA", "cmd_spa", "cmd_spa_obs"),
    ]:
        p = _etil_tbg_spa(label, key, obs_key)
        if p:
            partes.append(p)
    if partes:
        corpo.append(" | ".join(partes))

    # Lista de comorbidades
    linhas = []
    for i in range(1, 11):
        nome = _get(f"cmd_{i}_nome")
        if not nome:
            continue
        linha = nome
        classif = _get(f"cmd_{i}_class")
        if classif:
            linha += f"; {classif}"
        linhas.append(f"{len(linhas)+1}- {linha}")

    corpo.extend(linhas)

    if not corpo:
        return []
    return ["# Comorbidades"] + corpo


def _calcular_dias(data_ini: str, data_fim: str) -> str:
    """Calcula diferença em dias entre duas datas DD/MM/AAAA. Retorna '' se não for possível."""
    try:
        d1 = datetime.strptime(data_ini.strip(), "%d/%m/%Y")
        d2 = datetime.strptime(data_fim.strip(), "%d/%m/%Y")
        dias = (d2 - d1).days
        if dias > 0:
            return f"{dias} dias"
    except Exception:
        pass
    return ""
