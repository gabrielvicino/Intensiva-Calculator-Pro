import streamlit as st
from modules import fichas

# Mapeamento: chave do JSON retornado pela IA → chave do session_state
_MAPA_NOTAS = {
    "identificacao": "identificacao_notas",
    "hd":            "hd_notas",
    "comorbidades":  "comorbidades_notas",
    "muc":           "muc_notas",
    "hmpa":          "hmpa_texto",
    "dispositivos":  "dispositivos_notas",
    "culturas":      "culturas_notas",
    "antibioticos":  "antibioticos_notas",
    "complementares":"complementares_notas",
    "laboratoriais": "laboratoriais_notas",
    "controles":     "controles_notas",
    "evolucao":      "evolucao_notas",
    "sistemas":      "sistemas_notas",
    "conduta":       "conduta_final_lista",
}

def atualizar_notas_ia(dados: dict):
    """Recebe o JSON do ia_extrator e preenche os campos _notas de cada seção."""
    if not dados:
        return

    erro = dados.get("_erro")
    if erro:
        st.error(f"Erro na extração: {erro}")
        return

    preenchidos = 0
    for chave_json, chave_estado in _MAPA_NOTAS.items():
        valor = dados.get(chave_json, "")
        if valor and valor.strip():
            st.session_state[chave_estado] = valor.strip()
            preenchidos += 1

    if preenchidos:
        st.toast(f"✅ {preenchidos} seções preenchidas com sucesso!", icon="🧬")
    else:
        st.warning("A IA não encontrou dados para preencher. Verifique o texto colado.")

def limpar_tudo():
    """Reseta TODOS os campos do formulário para o estado inicial."""
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
    st.session_state["hd_ordem"] = list(range(1, 9))
    st.session_state["cult_ordem"] = list(range(1, 9))
    st.session_state["disp_ordem"] = list(range(1, 9))
    st.session_state["comp_ordem"] = list(range(1, 9))
    st.session_state["muc_ordem"] = list(range(1, 21))
    st.session_state["atb_curr_ordem"] = list(range(1, 6))
    st.session_state["atb_prev_ordem"] = list(range(1, 6))
    st.toast("✅ Todos os campos foram limpos.", icon="🗑️")
    st.rerun()
