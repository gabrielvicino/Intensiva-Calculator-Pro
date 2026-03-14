import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_neuro_pocus": "", "sis_neuro_obs": "", "sis_neuro_conduta": "",
        "sis_neuro_ecg": "15", "sis_neuro_ecg_ao": "", "sis_neuro_ecg_rv": "",
        "sis_neuro_ecg_rm": "", "sis_neuro_ecg_p": "15", "sis_neuro_rass": "",
        "sis_neuro_delirium": None, "sis_neuro_delirium_tipo": None,
        "sis_neuro_cam_icu": None, "sis_neuro_pupilas_tam": "Normal",
        "sis_neuro_pupilas_simetria": "Simétricas", "sis_neuro_pupilas_foto": "Fotoreagente",
        "sis_neuro_analgesico_adequado": "Sim",
        "sis_neuro_deficits_focais": "", "sis_neuro_deficits_ausente": "Ausente",
        "sis_neuro_analgesia_1_tipo": None, "sis_neuro_analgesia_1_drogas": "",
        "sis_neuro_analgesia_1_dose": "", "sis_neuro_analgesia_1_freq": "",
        "sis_neuro_analgesia_2_tipo": None, "sis_neuro_analgesia_2_drogas": "",
        "sis_neuro_analgesia_2_dose": "", "sis_neuro_analgesia_2_freq": "",
        "sis_neuro_analgesia_3_tipo": None, "sis_neuro_analgesia_3_drogas": "",
        "sis_neuro_analgesia_3_dose": "", "sis_neuro_analgesia_3_freq": "",
        "sis_neuro_sedacao_meta": "",
        "sis_neuro_sedacao_1_drogas": "", "sis_neuro_sedacao_1_dose": "",
        "sis_neuro_sedacao_2_drogas": "", "sis_neuro_sedacao_2_dose": "",
        "sis_neuro_sedacao_3_drogas": "", "sis_neuro_sedacao_3_dose": "",
        "sis_neuro_bloqueador_med": "", "sis_neuro_bloqueador_dose": "",
    }


def render():
    with st.container(border=True):
        st.markdown("**Neurológico**")
        ecg_col, ao_col, rv_col, rm_col = st.columns([1, 1, 1, 1])
        with ecg_col:
            st.markdown("**ECG — Glasgow (3-15)**")
            st.text_input("ECG", key="sis_neuro_ecg", placeholder="3-15", label_visibility="collapsed")
        with ao_col:
            st.markdown("**AO (1-4)**")
            st.text_input("AO", key="sis_neuro_ecg_ao", placeholder="1-4", label_visibility="collapsed")
        with rv_col:
            st.markdown("**RV (1-5)**")
            st.text_input("RV", key="sis_neuro_ecg_rv", placeholder="1-5", label_visibility="collapsed")
        with rm_col:
            st.markdown("**RM (1-6)**")
            st.text_input("RM", key="sis_neuro_ecg_rm", placeholder="1-6", label_visibility="collapsed")

        ecgp_col, rass_col, _, _ = st.columns(4)
        with ecgp_col:
            st.markdown("**ECG-P (1-15)**")
            st.text_input("ECG-P", key="sis_neuro_ecg_p", placeholder="1-15", label_visibility="collapsed")
        with rass_col:
            st.markdown("**RASS (-5 a +5)**")
            st.text_input("RASS", key="sis_neuro_rass", placeholder="-5 a +5", label_visibility="collapsed")

        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown("**Delirium**")
            st.pills("Delirium", ["Sim", "Não"], key="sis_neuro_delirium", label_visibility="collapsed")
        with d2:
            st.markdown("**Tipo de Delirium**")
            st.pills("Tipo de Delirium", ["Hiperativo", "Hipoativo"], key="sis_neuro_delirium_tipo", label_visibility="collapsed")
        with d3:
            st.markdown("**CAM-ICU**")
            st.pills("CAM-ICU", ["Positivo", "Negativo"], key="sis_neuro_cam_icu", label_visibility="collapsed")

        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown("**Pupilas**")
            st.pills("Pupilas", ["Miótica", "Normal", "Midríase"], key="sis_neuro_pupilas_tam", label_visibility="collapsed")
        with p2:
            st.markdown("**Simetria**")
            st.pills("Simetria", ["Simétricas", "Anisocoria"], key="sis_neuro_pupilas_simetria", label_visibility="collapsed")
        with p3:
            st.markdown("**Fotoreatividade**")
            st.pills("Fotoreatividade", ["Fotoreagente", "Não fotoreagente"], key="sis_neuro_pupilas_foto", label_visibility="collapsed")

        st.markdown("**Déficits focais**")
        df_col, df_pill = st.columns([4, 1])
        with df_col:
            st.text_input("Déficits focais", key="sis_neuro_deficits_focais", placeholder="Ex: Hemiparesia D, afasia...", label_visibility="collapsed")
        with df_pill:
            st.pills("Ausente", ["Ausente"], key="sis_neuro_deficits_ausente", label_visibility="collapsed")
        st.markdown("**Controle analgésico adequado**")
        st.pills("Analgésico", ["Sim", "Não"], key="sis_neuro_analgesico_adequado", label_visibility="collapsed")

        st.markdown("**Analgesia**")
        for i in range(1, 4):
            an_tipo, an1, an2, an3 = st.columns([1, 1, 1, 1])
            with an_tipo:
                st.pills("Fixa / Se necessário", ["Fixa", "Se necessário"], key=f"sis_neuro_analgesia_{i}_tipo", label_visibility="collapsed")
            with an1:
                st.text_input("Drogas", key=f"sis_neuro_analgesia_{i}_drogas", placeholder="Drogas", label_visibility="collapsed")
            with an2:
                st.text_input("Dose", key=f"sis_neuro_analgesia_{i}_dose", placeholder="Dose", label_visibility="collapsed")
            with an3:
                st.text_input("Frequência", key=f"sis_neuro_analgesia_{i}_freq", placeholder="Frequência", label_visibility="collapsed")

        st.markdown("**Sedação**")
        sed_meta_col, _ = st.columns([1, 3])
        with sed_meta_col:
            st.text_input("Meta RASS", key="sis_neuro_sedacao_meta", placeholder="Ex: RASS -2", label_visibility="visible")
        for i in range(1, 4):
            s1, s2 = st.columns(2)
            with s1:
                st.text_input("Drogas", key=f"sis_neuro_sedacao_{i}_drogas", placeholder="Drogas", label_visibility="collapsed")
            with s2:
                st.text_input("Dose", key=f"sis_neuro_sedacao_{i}_dose", placeholder="Dose", label_visibility="collapsed")

        st.markdown("**Bloqueador neuromuscular**")
        bnm_col1, bnm_col2 = st.columns([2, 1])
        with bnm_col1:
            st.text_input("Medicamento", key="sis_neuro_bloqueador_med", placeholder="Ex: Rocurônio", label_visibility="collapsed")
        with bnm_col2:
            st.text_input("Dose", key="sis_neuro_bloqueador_dose", placeholder="Ex: 15 ml/h", label_visibility="collapsed")

        st.markdown("**Pocus Neurológico**")
        st.text_input("Pocus Neurológico", key="sis_neuro_pocus", placeholder="Ex: Padrão de linhas A...", label_visibility="collapsed")
        st.markdown("**Demais neurologia**")
        st.text_input("Demais neurologia", key="sis_neuro_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_neuro_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
