"""
state.py -- gestao de estado: limpeza, mapa de notas e atualizacao pos-IA.
"""
import streamlit as st
from modules import fichas
from modules.agentes_secoes import _NOTAS_MAP

# -- Helpers de limpeza de valores (usados em bridge.py) ----------------------

def _limpar(v) -> str:
    """Remove barra e tudo apos (ex: '1.2/72s' -> '1.2')."""
    return str(v or "").split("/")[0].strip()

def _limpar_leuco(v) -> str:
    """Remove diferencial entre parenteses (ex: '12.500 (Seg 70%)' -> '12.500')."""
    return _limpar(v).split("(")[0].strip()

def _extrair_parenteses(v) -> str:
    """Extrai valor entre parenteses; se ausente, aplica _limpar.
    Ex: '14.2s (1.10)' -> '1.10'  |  '39,6s (1,41)' -> '1,41'
    """
    s = str(v or "").strip()
    if "(" in s and ")" in s:
        return s.split("(")[1].split(")")[0].strip()
    return _limpar(s)


# Mapeamento: chave do JSON retornado pela IA -> chave do session_state
# Estende _NOTAS_MAP (agentes_secoes) com a chave extra "conduta" do ia_extrator.
_MAPA_NOTAS = {**_NOTAS_MAP, "conduta": "conduta_final_lista"}


def atualizar_notas_ia(dados: dict):
    """Recebe o JSON do ia_extrator e preenche os campos _notas de cada secao."""
    if not dados:
        return

    erro = dados.get("_erro")
    if erro:
        st.error(f"Erro na extracao: {erro}")
        return

    preenchidos = 0
    for chave_json, chave_estado in _MAPA_NOTAS.items():
        valor = dados.get(chave_json, "")
        if valor and valor.strip():
            st.session_state[chave_estado] = valor.strip()
            preenchidos += 1

    if preenchidos:
        st.toast(f"Secoes preenchidas: {preenchidos}", icon="🧬")
    else:
        st.warning("A IA nao encontrou dados para preencher. Verifique o texto colado.")


def limpar_tudo():
    """Reseta TODOS os campos do formulario para o estado inicial."""
    defaults = fichas._campos_base()
    for k, v in defaults.items():
        st.session_state[k] = v
    st.session_state["idade"] = 0
    st.session_state["sofa_adm"] = 0
    st.session_state["sofa_atual"] = 0
    st.session_state["paliativo"] = False
    st.session_state["texto_final_gerado"] = ""
    st.session_state["texto_bruto_original"] = ""
    st.session_state.pop("_agent_staging", None)
    st.session_state.pop("_secoes_recortadas", None)
    st.session_state.pop("_data_hora_carregado", None)
    st.session_state["hd_ordem"] = list(range(1, 9))
    st.session_state["cult_ordem"] = list(range(1, 9))
    st.session_state["disp_ordem"] = list(range(1, 9))
    st.session_state["comp_ordem"] = list(range(1, 9))
    st.session_state["muc_ordem"] = list(range(1, 21))
    st.session_state["atb_ordem"] = list(range(1, 9))
    st.toast("Todos os campos foram limpos.", icon="🗑️")
