import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_infec_pocus": "", "sis_infec_obs": "", "sis_infec_conduta": "",
        "sis_infec_febre": None, "sis_infec_febre_vezes": "", "sis_infec_febre_ultima": "",
        "sis_infec_atb": None, "sis_infec_atb_1": "", "sis_infec_atb_2": "",
        "sis_infec_atb_3": "", "sis_infec_atb_guiado": None,
        "sis_infec_culturas_and": None,
        "sis_infec_cult_1_sitio": "", "sis_infec_cult_1_data": "",
        "sis_infec_cult_2_sitio": "", "sis_infec_cult_2_data": "",
        "sis_infec_cult_3_sitio": "", "sis_infec_cult_3_data": "",
        "sis_infec_cult_4_sitio": "", "sis_infec_cult_4_data": "",
        "sis_infec_pcr_ant5":  "", "sis_infec_pcr_ant4":  "", "sis_infec_pcr_antepen":  "", "sis_infec_pcr_ult":  "", "sis_infec_pcr_hoje":  "",
        "sis_infec_leuc_ant5": "", "sis_infec_leuc_ant4": "", "sis_infec_leuc_antepen": "", "sis_infec_leuc_ult": "", "sis_infec_leuc_hoje": "",
        "sis_infec_vhs_ant5":  "", "sis_infec_vhs_ant4":  "", "sis_infec_vhs_antepen":  "", "sis_infec_vhs_ult":  "", "sis_infec_vhs_hoje":  "",
        "sis_infec_pcr_show":  False, "sis_infec_leuc_show": False, "sis_infec_vhs_show": False,
        "sis_infec_isolamento": None, "sis_infec_isolamento_tipo": "",
        "sis_infec_isolamento_motivo": "", "sis_infec_patogenos": "",
    }


def render():
    with st.container(border=True):
        st.markdown("**Infeccioso**")

        if st.session_state.get("sis_infec_febre") == "Ausente":
            st.session_state["sis_infec_febre"] = "Não"
        elif st.session_state.get("sis_infec_febre") == "Presente":
            st.session_state["sis_infec_febre"] = "Sim"

        st.markdown("**Febre nas últimas 24h**")
        f1, f2, f3 = st.columns(3)
        with f1: st.pills("Febre", ["Sim", "Não"], key="sis_infec_febre", label_visibility="collapsed")
        with f2: st.text_input("Quantas vezes", key="sis_infec_febre_vezes", placeholder="Quantas vezes", label_visibility="collapsed")
        with f3: st.text_input("Data da última febre", key="sis_infec_febre_ultima", placeholder="Data da última febre", label_visibility="collapsed")

        st.markdown("**Uso de Antibioticoterapia**")
        a1, a2 = st.columns([1, 2])
        with a1:
            st.markdown("**Em uso**")
            st.pills("ATB", ["Sim", "Não"], key="sis_infec_atb", label_visibility="collapsed")
        with a2:
            st.markdown("**Guiado por cultura**")
            st.pills("Guiado", ["Sim", "Não"], key="sis_infec_atb_guiado", label_visibility="collapsed")
        m1, m2, m3 = st.columns(3)
        with m1: st.text_input("Medicamento 1", key="sis_infec_atb_1", placeholder="Medicamento 1", label_visibility="collapsed")
        with m2: st.text_input("Medicamento 2", key="sis_infec_atb_2", placeholder="Medicamento 2", label_visibility="collapsed")
        with m3: st.text_input("Medicamento 3", key="sis_infec_atb_3", placeholder="Medicamento 3", label_visibility="collapsed")

        st.markdown("**Culturas em andamento**")
        st.pills("Culturas", ["Sim", "Não"], key="sis_infec_culturas_and", label_visibility="collapsed")
        for i in range(1, 5):
            cs1, cs2 = st.columns([3, 1])
            with cs1: st.text_input(f"Sítio {i}", key=f"sis_infec_cult_{i}_sitio", placeholder=f"Sítio {i}", label_visibility="collapsed")
            with cs2: st.text_input(f"Coleta {i}", key=f"sis_infec_cult_{i}_data", placeholder="Data coleta", label_visibility="collapsed")

        st.markdown("**Exames Infecciosos**")
        _evo_header()
        _evo_row("Leucócitos", "sis_infec_leuc")
        _evo_row("PCR",        "sis_infec_pcr")
        _evo_row("VHS",        "sis_infec_vhs")

        st.markdown("**Isolamento**")
        i1, i2, i3 = st.columns(3)
        with i1: st.pills("Isolamento", ["Sim", "Não"], key="sis_infec_isolamento", label_visibility="collapsed")
        with i2: st.text_input("Tipo", key="sis_infec_isolamento_tipo", placeholder="Tipo", label_visibility="collapsed")
        with i3: st.text_input("Motivo", key="sis_infec_isolamento_motivo", placeholder="Motivo", label_visibility="collapsed")

        st.markdown("**Patógenos isolados**")
        st.text_input("Patógenos", key="sis_infec_patogenos", placeholder="Ex: K. pneumoniae KPC+, MRSA...", label_visibility="collapsed")
        st.markdown("**Pocus Infeccioso**")
        st.text_input("Pocus Infeccioso", key="sis_infec_pocus", placeholder="Ex: Coleção...", label_visibility="collapsed")
        st.markdown("**Demais infeccioso**")
        st.text_input("Demais infeccioso", key="sis_infec_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_infec_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
