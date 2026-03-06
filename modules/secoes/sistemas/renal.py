import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_renal_pocus": "", "sis_renal_obs": "", "sis_renal_conduta": "",
        "sis_renal_diurese": "", "sis_renal_balanco": "", "sis_renal_balanco_acum": "",
        "sis_renal_volemia": None,
        "sis_renal_cr_ant5": "", "sis_renal_cr_ant4": "", "sis_renal_cr_antepen": "", "sis_renal_cr_ult": "", "sis_renal_cr_hoje": "",
        "sis_renal_ur_ant5": "", "sis_renal_ur_ant4": "", "sis_renal_ur_antepen": "", "sis_renal_ur_ult": "", "sis_renal_ur_hoje": "",
        "sis_renal_diu_ant5": "", "sis_renal_diu_ant4": "", "sis_renal_diu_antepen": "", "sis_renal_diu_ult": "", "sis_renal_diu_hoje": "",
        "sis_renal_bh_ant5":  "", "sis_renal_bh_ant4":  "", "sis_renal_bh_antepen":  "", "sis_renal_bh_ult":  "", "sis_renal_bh_hoje":  "",
        "sis_renal_na_ant5":  "", "sis_renal_na_ant4":  "", "sis_renal_na_antepen":  "", "sis_renal_na_ult":  "", "sis_renal_na_hoje":  "",
        "sis_renal_k_ant5":   "", "sis_renal_k_ant4":   "", "sis_renal_k_antepen":   "", "sis_renal_k_ult":   "", "sis_renal_k_hoje":   "",
        "sis_renal_mg_ant5":  "", "sis_renal_mg_ant4":  "", "sis_renal_mg_antepen":  "", "sis_renal_mg_ult":  "", "sis_renal_mg_hoje":  "",
        "sis_renal_fos_ant5": "", "sis_renal_fos_ant4": "", "sis_renal_fos_antepen": "", "sis_renal_fos_ult": "", "sis_renal_fos_hoje": "",
        "sis_renal_cai_ant5": "", "sis_renal_cai_ant4": "", "sis_renal_cai_antepen": "", "sis_renal_cai_ult": "", "sis_renal_cai_hoje": "",
        "sis_renal_cr_show":  False, "sis_renal_ur_show": False,
        "sis_renal_diu_show": False, "sis_renal_bh_show":  False,
        "sis_renal_na_show":  False, "sis_renal_k_show":   False,
        "sis_renal_mg_show":  False, "sis_renal_fos_show": False, "sis_renal_cai_show": False,
        "sis_renal_trs": None, "sis_renal_trs_via": "",
        "sis_renal_trs_ultima": "", "sis_renal_trs_proxima": "",
    }


def render():
    with st.container(border=True):
        st.markdown("**Renal**")

        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown("**Diurese**")
            st.text_input("Diurese", key="sis_renal_diurese", placeholder="Diurese", label_visibility="collapsed")
        with r2:
            st.markdown("**Balanço Hídrico**")
            st.text_input("Balanço", key="sis_renal_balanco", placeholder="Balanço Hídrico", label_visibility="collapsed")
        with r3:
            st.markdown("**Balanço Acumulado**")
            st.text_input("Balanço Acumulado", key="sis_renal_balanco_acum", placeholder="Balanço Acumulado", label_visibility="collapsed")

        st.markdown("**Volemia**")
        st.pills("Volemia", ["Hipovolêmico", "Euvolêmico", "Hipervolêmico"], key="sis_renal_volemia", label_visibility="collapsed")

        st.markdown("**Evolução Função Renal e Eletrólitos**")
        _evo_header()
        _evo_row("Bal. Hídrico", "sis_renal_bh")
        _evo_row("Diurese",      "sis_renal_diu")
        _evo_row("Cr",           "sis_renal_cr")
        _evo_row("Ur",           "sis_renal_ur")
        _evo_row("Na",           "sis_renal_na")
        _evo_row("K",            "sis_renal_k")
        _evo_row("Mg",           "sis_renal_mg")
        _evo_row("Fos",          "sis_renal_fos")
        _evo_row("CaI",          "sis_renal_cai")

        st.markdown("**Terapia de Substituição Renal (TRS)**")
        t1, t2, t3, t4 = st.columns(4)
        with t1: st.pills("TRS", ["Sim", "Não"], key="sis_renal_trs", label_visibility="collapsed")
        with t2: st.text_input("Via", key="sis_renal_trs_via", placeholder="Via", label_visibility="collapsed")
        with t3: st.text_input("Última diálise", key="sis_renal_trs_ultima", placeholder="Data última diálise", label_visibility="collapsed")
        with t4: st.text_input("Próxima TRS", key="sis_renal_trs_proxima", placeholder="Programação próxima TRS", label_visibility="collapsed")

        st.markdown("**Pocus Renal**")
        st.text_input("Pocus Renal", key="sis_renal_pocus", placeholder="Ex: Rins com dimensões preservadas...", label_visibility="collapsed")
        st.markdown("**Demais renal**")
        st.text_input("Demais renal", key="sis_renal_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_renal_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
