import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_cardio_pocus": "", "sis_cardio_obs": "", "sis_cardio_conduta": "",
        "sis_cardio_fc": "",
        "sis_cardio_exame_cardio": "2BNRF, não ausculto sopros significativos",
        "sis_cardio_cardioscopia": "", "sis_cardio_pam": "",
        "sis_cardio_perfusao": None, "sis_cardio_tec": "",
        "sis_cardio_fluido_responsivo": None, "sis_cardio_fluido_tolerante": None,
        "sis_cardio_lac_ant5": "", "sis_cardio_lac_ant4": "", "sis_cardio_lac_antepen": "",
        "sis_cardio_lac_ult": "", "sis_cardio_lac_hoje": "", "sis_cardio_lac_show": False,
        "sis_cardio_trop_ant5": "", "sis_cardio_trop_ant4": "", "sis_cardio_trop_antepen": "",
        "sis_cardio_trop_ult": "", "sis_cardio_trop_hoje": "", "sis_cardio_trop_show": False,
        "sis_cardio_dva_1_med": "", "sis_cardio_dva_1_dose": "",
        "sis_cardio_dva_2_med": "", "sis_cardio_dva_2_dose": "",
        "sis_cardio_dva_3_med": "", "sis_cardio_dva_3_dose": "",
        "sis_cardio_dva_4_med": "", "sis_cardio_dva_4_dose": "",
    }


def render():
    with st.container(border=True):
        st.markdown("**Cardiovascular**")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown("**Frequência**")
            st.text_input("FC", key="sis_cardio_fc", placeholder="Frequência", label_visibility="collapsed")
        with r2:
            st.markdown("**Cardioscopia**")
            st.text_input("Cardioscopia", key="sis_cardio_cardioscopia", placeholder="Sinusal, Fibrilação Atrial...", label_visibility="collapsed")
        with r3:
            st.markdown("**PAM**")
            st.text_input("PAM", key="sis_cardio_pam", placeholder="PAM", label_visibility="collapsed")

        st.markdown("**Exame Cardiológico**")
        st.text_input("Exame Cardiológico", key="sis_cardio_exame_cardio", placeholder="2BNRF, não ausculto sopros significativos", label_visibility="collapsed")

        perf_tit, tec_tit = st.columns([2, 1])
        with perf_tit: st.markdown("**Perfusão periférica**")
        with tec_tit:  st.markdown("**Tempo de Enchimento Capilar**")
        perf_col, tec_col = st.columns([2, 1])
        with perf_col:
            st.pills("Perfusão", ["Normal", "Lentificada", "Flush"], key="sis_cardio_perfusao", label_visibility="collapsed")
        with tec_col:
            st.text_input("TEC", key="sis_cardio_tec", placeholder="Ex: 3 seg.", label_visibility="collapsed")

        f1, f2 = st.columns(2)
        with f1:
            st.markdown("**Fluido responsivo**")
            st.pills("Fluido responsivo", ["Sim", "Não"], key="sis_cardio_fluido_responsivo", label_visibility="collapsed")
        with f2:
            st.markdown("**Fluido tolerante**")
            st.pills("Fluido tolerante", ["Sim", "Não"], key="sis_cardio_fluido_tolerante", label_visibility="collapsed")

        st.markdown("**Drogas Vasoativas**")
        for i in range(1, 5):
            d1, d2 = st.columns(2)
            with d1: st.text_input(f"Medicamento {i}", key=f"sis_cardio_dva_{i}_med", placeholder="Medicamento", label_visibility="collapsed")
            with d2: st.text_input(f"Dose {i}", key=f"sis_cardio_dva_{i}_dose", placeholder="Dose", label_visibility="collapsed")

        st.markdown("**Exames Cardiovasculares**")
        _evo_header()
        _evo_row("Lactato",   "sis_cardio_lac")
        _evo_row("Troponina", "sis_cardio_trop")

        st.markdown("**Pocus Cardiovascular**")
        st.text_input("Pocus Cardiovascular", key="sis_cardio_pocus", placeholder="Ex: Função ventricular preservada...", label_visibility="collapsed")
        st.markdown("**Demais cardiovascular**")
        st.text_input("Demais cardiovascular", key="sis_cardio_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_cardio_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
