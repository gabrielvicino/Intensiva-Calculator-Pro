import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_renal_pocus": "", "sis_renal_obs": "", "sis_renal_conduta": "",
        "sis_renal_diurese": "", "sis_renal_balanco": "", "sis_renal_balanco_acum": "",
        "sis_renal_bacum_hoje": "", "sis_renal_bacum_ult": "", "sis_renal_bacum_antepen": "",
        "sis_renal_bacum_ant4": "", "sis_renal_bacum_ant5": "",
        "sis_renal_bacum_show": False,
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

        r1, r2 = st.columns(2)
        with r1:
            st.markdown("**Diurese**")
            st.text_input("Diurese", key="sis_renal_diurese", placeholder="Diurese", label_visibility="collapsed")
        with r2:
            st.markdown("**Balanço Hídrico**")
            st.text_input("Balanço", key="sis_renal_balanco", placeholder="Balanço Hídrico", label_visibility="collapsed")

        st.markdown("**Volemia**")
        st.pills("Volemia", ["Hipovolêmico", "Euvolêmico", "Hipervolêmico"], key="sis_renal_volemia", label_visibility="collapsed")

        st.markdown("**Evolução Função Renal e Eletrólitos**")
        _evo_header()
        # BH Acumulado — calculado automaticamente pelo bridge (read-only)
        _cb, _lbl, _v1, _v2, _v3, _v4, _v5 = st.columns([0.5, 1.5, 1, 1, 1, 1, 1])
        with _cb:
            st.checkbox("📋", key="sis_renal_bacum_show", help="Colocar no prontuário", label_visibility="collapsed")
        with _lbl:
            st.markdown("**BH Acumulado**")
        with _v1: st.text_input("BH Acumulado hoje",    key="sis_renal_bacum_hoje",    placeholder="Hoje",    label_visibility="collapsed", disabled=True)
        with _v2: st.text_input("BH Acumulado ontem",   key="sis_renal_bacum_ult",     placeholder="Ontem",   label_visibility="collapsed", disabled=True)
        with _v3: st.text_input("BH Acumulado antepen", key="sis_renal_bacum_antepen", placeholder="Antepen", label_visibility="collapsed", disabled=True)
        with _v4: st.text_input("BH Acumulado 4o",      key="sis_renal_bacum_ant4",    placeholder="4º",      label_visibility="collapsed", disabled=True)
        with _v5: st.text_input("BH Acumulado 5o",      key="sis_renal_bacum_ant5",    placeholder="5º",      label_visibility="collapsed", disabled=True)
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
