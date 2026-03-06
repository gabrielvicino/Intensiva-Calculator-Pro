import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_pele_pocus": "", "sis_pele_obs": "", "sis_pele_conduta": "",
        "sis_pele_edema": None, "sis_pele_edema_cruzes": "",
        "sis_pele_lpp": None,
        "sis_pele_lpp_local_1": "", "sis_pele_lpp_grau_1": "",
        "sis_pele_lpp_local_2": "", "sis_pele_lpp_grau_2": "",
        "sis_pele_lpp_local_3": "", "sis_pele_lpp_grau_3": "",
        "sis_pele_polineuropatia": None,
        "sis_pele_cpk_ant5": "", "sis_pele_cpk_ant4": "", "sis_pele_cpk_antepen": "",
        "sis_pele_cpk_ult": "", "sis_pele_cpk_hoje": "", "sis_pele_cpk_show": False,
    }


def render():
    with st.container(border=True):
        st.markdown("**Pele e musculoesquelético**")

        ed_col1, ed_col2 = st.columns(2)
        with ed_col1:
            st.markdown("**Edema**")
            st.pills("Edema", ["Presente", "Ausente"], key="sis_pele_edema", label_visibility="collapsed")
        with ed_col2:
            st.markdown("**Cacifo**")
            st.text_input("Cruzes", key="sis_pele_edema_cruzes", placeholder="Nº de cruzes", label_visibility="collapsed")

        st.markdown("**Lesão por Pressão**")
        lpp_cols = st.columns([1, 2, 1])
        with lpp_cols[0]:
            st.pills("LPP", ["Sim", "Não"], key="sis_pele_lpp", label_visibility="collapsed")
        for i in range(1, 4):
            l1, l2 = st.columns([3, 1])
            with l1: st.text_input(f"Local {i}", key=f"sis_pele_lpp_local_{i}", placeholder=f"Local {i}", label_visibility="collapsed")
            with l2: st.text_input(f"Grau {i}", key=f"sis_pele_lpp_grau_{i}", placeholder=f"Grau {i}", label_visibility="collapsed")

        st.markdown("**Polineuropatia**")
        st.pills("Polineuropatia", ["Sim", "Não"], key="sis_pele_polineuropatia", label_visibility="collapsed")

        st.markdown("**Pocus Pele e musculoesquelético**")
        st.text_input("Pocus Pele", key="sis_pele_pocus", placeholder="Ex: Edema em membros inferiores...", label_visibility="collapsed")

        st.markdown("**Evolução CPK**")
        _evo_header()
        _evo_row("CPK", "sis_pele_cpk")

        st.markdown("**Demais pele e musculoesquelético**")
        st.text_input("Demais", key="sis_pele_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_pele_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
