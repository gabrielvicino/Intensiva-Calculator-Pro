import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_resp_pocus": "", "sis_resp_obs": "", "sis_resp_conduta": "",
        "sis_resp_ausculta": "MV+, sem ruído adventício, expansão bilateral, sem sinais de desconforto",
        "sis_resp_modo": None, "sis_resp_modo_vent": None,
        "sis_resp_oxigenio_modo": "", "sis_resp_oxigenio_fluxo": "",
        "sis_resp_pressao": "", "sis_resp_volume": "", "sis_resp_fio2": "",
        "sis_resp_peep": "", "sis_resp_freq": "",
        "sis_resp_vent_protetora": None, "sis_resp_sincronico": None,
        "sis_resp_assincronia": "", "sis_resp_complacencia": "",
        "sis_resp_resistencia": "", "sis_resp_dp": "",
        "sis_resp_plato": "", "sis_resp_pico": "",
        "sis_resp_dreno_1": "", "sis_resp_dreno_1_debito": "",
        "sis_resp_dreno_2": "", "sis_resp_dreno_2_debito": "",
        "sis_resp_dreno_3": "", "sis_resp_dreno_3_debito": "",
    }


def render():
    with st.container(border=True):
        st.markdown("**Respiratório**")
        st.markdown("**Exame Respiratório**")
        st.text_input("Exame Respiratório", key="sis_resp_ausculta", placeholder="MV+, sem ruído adventício, expansão bilateral, sem sinais de desconforto", label_visibility="collapsed")

        tit1, tit2, tit3, tit4 = st.columns([2, 1, 1.5, 1])
        with tit1: st.markdown("**Suporte Ventilatório**")
        with tit2: st.markdown("<span style='white-space: nowrap'>**Modo Ventilatório**</span>", unsafe_allow_html=True)
        with tit3: st.markdown("**Modo O₂**")
        with tit4: st.markdown("**Fluxo**")
        mv1, mv2, mv3, mv4 = st.columns([2, 1, 1.5, 1])
        with mv1:
            st.pills("Modo", ["Ar Ambiente", "Oxigenoterapia", "VNI", "Cateter de Alto Fluxo", "Ventilação Mecânica"], key="sis_resp_modo", label_visibility="collapsed")
        with mv2:
            st.pills("Modalidade VM", ["VCV", "PCV", "PSV"], key="sis_resp_modo_vent", label_visibility="collapsed")
        with mv3:
            st.text_input("Modo O₂", key="sis_resp_oxigenio_modo", placeholder="Ex: Cateter Nasal", label_visibility="collapsed")
        with mv4:
            st.text_input("Fluxo", key="sis_resp_oxigenio_fluxo", placeholder="Ex: 2 L/min", label_visibility="collapsed")

        st.markdown("**Parâmetros**")
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: st.text_input("Pressão", key="sis_resp_pressao", placeholder="Pressão", label_visibility="collapsed")
        with p2: st.text_input("Volume", key="sis_resp_volume", placeholder="Volume", label_visibility="collapsed")
        with p3: st.text_input("FiO2", key="sis_resp_fio2", placeholder="FiO2", label_visibility="collapsed")
        with p4: st.text_input("PEEP", key="sis_resp_peep", placeholder="PEEP", label_visibility="collapsed")
        with p5: st.text_input("Frequência Respiratória", key="sis_resp_freq", placeholder="Frequência Respiratória", label_visibility="collapsed")

        v1, v2, v3 = st.columns(3)
        with v1:
            st.markdown("**Ventilação protetora**")
            st.pills("Vent protetora", ["Sim", "Não"], key="sis_resp_vent_protetora", label_visibility="collapsed")
        with v2:
            st.markdown("**Sincrônico**")
            st.pills("Sincrônico", ["Sim", "Não"], key="sis_resp_sincronico", label_visibility="collapsed")
        with v3:
            st.markdown("**Assincronia**")
            st.text_input("Assincronia", key="sis_resp_assincronia", placeholder="Ex: Double trigger, esforço ineficaz...", label_visibility="collapsed")

        st.markdown("**Mecânica respiratória**")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.text_input("Complacência", key="sis_resp_complacencia", placeholder="Complacência", label_visibility="collapsed")
        with m2: st.text_input("Resistência", key="sis_resp_resistencia", placeholder="Resistência", label_visibility="collapsed")
        with m3: st.text_input("Driving Pressure", key="sis_resp_dp", placeholder="Driving Pressure", label_visibility="collapsed")
        with m4: st.text_input("Pressão de Platô", key="sis_resp_plato", placeholder="Pressão de Platô", label_visibility="collapsed")
        with m5: st.text_input("Pressão de Pico", key="sis_resp_pico", placeholder="Pressão de Pico", label_visibility="collapsed")

        st.markdown("**Drenos**")
        for i in range(1, 4):
            d1, d2 = st.columns([2, 1])
            with d1: st.text_input(f"Dreno {i}", key=f"sis_resp_dreno_{i}", placeholder="Ex: Pleural D, mediastinal...", label_visibility="collapsed")
            with d2: st.text_input(f"Débito {i}", key=f"sis_resp_dreno_{i}_debito", placeholder="mL/dia", label_visibility="collapsed")

        st.markdown("**Pocus Respiratório**")
        st.text_input("Pocus Respiratório", key="sis_resp_pocus", placeholder="Ex: Padrão de linhas B...", label_visibility="collapsed")
        st.markdown("**Demais respiratório**")
        st.text_input("Demais respiratório", key="sis_resp_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_resp_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
