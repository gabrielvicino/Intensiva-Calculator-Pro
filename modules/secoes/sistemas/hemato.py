import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_hemato_pocus": "", "sis_hemato_obs": "", "sis_hemato_conduta": "",
        "sis_hemato_anticoag": None, "sis_hemato_anticoag_motivo": "",
        "sis_hemato_anticoag_tipo": None, "sis_hemato_sangramento": None,
        "sis_hemato_sangramento_via": "", "sis_hemato_sangramento_data": "",
        "sis_hemato_transf_data": "",
        "sis_hemato_transf_1_comp": "", "sis_hemato_transf_1_bolsas": "",
        "sis_hemato_transf_2_comp": "", "sis_hemato_transf_2_bolsas": "",
        "sis_hemato_transf_3_comp": "", "sis_hemato_transf_3_bolsas": "",
        "sis_hemato_hb_ant5":   "", "sis_hemato_hb_ant4":   "", "sis_hemato_hb_antepen":   "", "sis_hemato_hb_ult":   "", "sis_hemato_hb_hoje":   "",
        "sis_hemato_plaq_ant5": "", "sis_hemato_plaq_ant4": "", "sis_hemato_plaq_antepen": "", "sis_hemato_plaq_ult": "", "sis_hemato_plaq_hoje": "",
        "sis_hemato_inr_ant5":  "", "sis_hemato_inr_ant4":  "", "sis_hemato_inr_antepen":  "", "sis_hemato_inr_ult":  "", "sis_hemato_inr_hoje":  "",
        "sis_hemato_ttpa_ant5": "", "sis_hemato_ttpa_ant4": "", "sis_hemato_ttpa_antepen": "", "sis_hemato_ttpa_ult": "", "sis_hemato_ttpa_hoje": "",
        "sis_hemato_hb_show":   False, "sis_hemato_plaq_show": False,
        "sis_hemato_inr_show":  False, "sis_hemato_ttpa_show": False,
    }


def render():
    with st.container(border=True):
        st.markdown("**Hematológico**")

        st.markdown("**Anticoagulação**")
        ac1, ac2, ac3 = st.columns(3)
        with ac1: st.pills("Anticoag", ["Sim", "Não"], key="sis_hemato_anticoag", label_visibility="collapsed")
        with ac2: st.pills("Tipo", ["Profilática", "Plena"], key="sis_hemato_anticoag_tipo", label_visibility="collapsed")
        with ac3: st.text_input("Motivo", key="sis_hemato_anticoag_motivo", placeholder="Motivo", label_visibility="collapsed")

        st.markdown("**Sangramento**")
        s1, s2, s3 = st.columns(3)
        with s1: st.pills("Sangramento", ["Sim", "Não"], key="sis_hemato_sangramento", label_visibility="collapsed")
        with s2: st.text_input("Via", key="sis_hemato_sangramento_via", placeholder="Via", label_visibility="collapsed")
        with s3: st.text_input("Data último sangramento", key="sis_hemato_sangramento_data", placeholder="Data último sangramento", label_visibility="collapsed")

        st.markdown("**Transfusão sanguínea**")
        st.text_input("Data última transfusão", key="sis_hemato_transf_data", placeholder="Data última transfusão", label_visibility="collapsed")
        for i in range(1, 4):
            t1, t2 = st.columns([3, 1])
            with t1: st.text_input(f"Componente {i}", key=f"sis_hemato_transf_{i}_comp", placeholder=f"Componente {i}", label_visibility="collapsed")
            with t2: st.text_input(f"Nº bolsas {i}", key=f"sis_hemato_transf_{i}_bolsas", placeholder="Nº bolsas", label_visibility="collapsed")

        st.markdown("**Exames Hematológicos**")
        _evo_header()
        _evo_row("Hb",   "sis_hemato_hb")
        _evo_row("Plaq", "sis_hemato_plaq")
        _evo_row("INR",  "sis_hemato_inr")
        _evo_row("TTPa", "sis_hemato_ttpa")

        st.markdown("**Pocus Hematológico**")
        st.text_input("Pocus Hematológico", key="sis_hemato_pocus", placeholder="Ex: Derrame pleural...", label_visibility="collapsed")
        st.markdown("**Demais hematológico**")
        st.text_input("Demais hemato", key="sis_hemato_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_hemato_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
