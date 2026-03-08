import streamlit as st
from ._base import _evo_header, _evo_row


def _campos():
    return {
        "sis_gastro_pocus": "", "sis_gastro_obs": "", "sis_gastro_conduta": "",
        "sis_gastro_exame_fisico": "Típico, RHA presente, indolor a palpação, sem sinais de peritonite, inocente",
        "sis_gastro_ictericia_presente": "Ausente", "sis_gastro_ictericia_cruzes": "",
        "sis_gastro_dieta_oral": "", "sis_gastro_dieta_enteral": "",
        "sis_gastro_dieta_enteral_vol": "", "sis_gastro_dieta_parenteral": "",
        "sis_gastro_dieta_parenteral_vol": "", "sis_gastro_meta_calorica": "",
        "sis_gastro_na_meta": None, "sis_gastro_ingestao_quanto": "",
        "sis_gastro_escape_glicemico": None, "sis_gastro_escape_vezes": "",
        "sis_gastro_escape_manha": False, "sis_gastro_escape_tarde": False,
        "sis_gastro_escape_noite": False, "sis_gastro_insulino": None,
        "sis_gastro_insulino_dose_manha": "", "sis_gastro_insulino_dose_tarde": "",
        "sis_gastro_insulino_dose_noite": "",
        "sis_gastro_evacuacao": None, "sis_gastro_evacuacao_data": "",
        "sis_gastro_laxativo": "",
        "sis_gastro_tgo_ant5": "", "sis_gastro_tgo_ant4": "", "sis_gastro_tgo_antepen": "", "sis_gastro_tgo_ult": "", "sis_gastro_tgo_hoje": "",
        "sis_gastro_tgp_ant5": "", "sis_gastro_tgp_ant4": "", "sis_gastro_tgp_antepen": "", "sis_gastro_tgp_ult": "", "sis_gastro_tgp_hoje": "",
        "sis_gastro_fal_ant5": "", "sis_gastro_fal_ant4": "", "sis_gastro_fal_antepen": "", "sis_gastro_fal_ult": "", "sis_gastro_fal_hoje": "",
        "sis_gastro_ggt_ant5": "", "sis_gastro_ggt_ant4": "", "sis_gastro_ggt_antepen": "", "sis_gastro_ggt_ult": "", "sis_gastro_ggt_hoje": "",
        "sis_gastro_bt_ant5":  "", "sis_gastro_bt_ant4":  "", "sis_gastro_bt_antepen":  "", "sis_gastro_bt_ult":  "", "sis_gastro_bt_hoje":  "",
        "sis_gastro_tgo_show": False, "sis_gastro_tgp_show": False, "sis_gastro_fal_show": False,
        "sis_gastro_ggt_show": False, "sis_gastro_bt_show":  False,
    }


def render():
    with st.container(border=True):
        st.markdown("**Exame Abdominal**")
        ef_col, icter_col = st.columns([3, 1])
        with ef_col:
            st.markdown("**Exame Abdominal**")
            st.text_input("Exame Abdominal", key="sis_gastro_exame_fisico", placeholder="Típico, RHA presente, indolor a palpação, sem sinais de peritonite, inocente", label_visibility="collapsed")
        with icter_col:
            st.markdown("**Icterícia**")
            pills_col, cruzes_col = st.columns([1, 1])
            with pills_col:
                st.pills("Icterícia", ["Presente", "Ausente"], key="sis_gastro_ictericia_presente", label_visibility="collapsed")
            with cruzes_col:
                st.text_input("Quantas cruzes", key="sis_gastro_ictericia_cruzes", placeholder="1 a 4", label_visibility="collapsed")

        d1, d2, d3, d4, d5, d6 = st.columns(6)
        with d1:
            st.markdown("**Dieta Oral**")
            st.text_input("Oral", key="sis_gastro_dieta_oral", placeholder="Oral", label_visibility="collapsed")
        with d2:
            st.markdown("**Dieta Enteral**")
            st.text_input("Enteral", key="sis_gastro_dieta_enteral", placeholder="Enteral", label_visibility="collapsed")
        with d3:
            st.markdown("**Kcal Enteral**")
            st.text_input("Kcal enteral", key="sis_gastro_dieta_enteral_vol", placeholder="Kcal enteral", label_visibility="collapsed")
        with d4:
            st.markdown("**Dieta NPP**")
            st.text_input("NPP", key="sis_gastro_dieta_parenteral", placeholder="NPP", label_visibility="collapsed")
        with d5:
            st.markdown("**Kcal NPP**")
            st.text_input("Kcal NPP", key="sis_gastro_dieta_parenteral_vol", placeholder="Kcal NPP", label_visibility="collapsed")
        with d6:
            st.markdown("**Meta Calórica**")
            st.text_input("Meta Calórica", key="sis_gastro_meta_calorica", placeholder="Meta Calórica", label_visibility="collapsed")

        _ing1, _ing2 = st.columns([1, 6])
        with _ing1:
            st.markdown("**Ingestão na Meta**")
            st.pills("Na meta", ["Sim", "Não"], key="sis_gastro_na_meta", label_visibility="collapsed")
        with _ing2:
            st.markdown("**Quanto**")
            st.text_input("Quanto", key="sis_gastro_ingestao_quanto", placeholder="Ex: 1200 kcal", label_visibility="collapsed")

        st.markdown("**Escape glicêmico**")
        _esc1, _esc2, _esc3, _esc4, _esc5 = st.columns([1, 3, 1, 1, 1])
        with _esc1: st.pills("Escape", ["Sim", "Não"], key="sis_gastro_escape_glicemico", label_visibility="collapsed")
        with _esc2: st.text_input("Nº vezes", key="sis_gastro_escape_vezes", placeholder="Nº vezes", label_visibility="collapsed")
        with _esc3: st.checkbox("Manhã", key="sis_gastro_escape_manha")
        with _esc4: st.checkbox("Tarde", key="sis_gastro_escape_tarde")
        with _esc5: st.checkbox("Noite", key="sis_gastro_escape_noite")

        st.markdown("**Insulinoterapia**")
        _ins1, _ins2, _ins3, _ins4 = st.columns([1, 2, 2, 2])
        with _ins1: st.pills("Insulino", ["Sim", "Não"], key="sis_gastro_insulino", label_visibility="collapsed")
        with _ins2: st.text_input("Dose manhã", key="sis_gastro_insulino_dose_manha", placeholder="Dose manhã", label_visibility="collapsed")
        with _ins3: st.text_input("Dose tarde", key="sis_gastro_insulino_dose_tarde", placeholder="Dose tarde", label_visibility="collapsed")
        with _ins4: st.text_input("Dose noite", key="sis_gastro_insulino_dose_noite", placeholder="Dose noite", label_visibility="collapsed")

        st.markdown("**Evacuação**")
        _ev1, _ev2, _ev3 = st.columns([1, 3, 3])
        with _ev1: st.pills("Evacuação", ["Sim", "Não"], key="sis_gastro_evacuacao", label_visibility="collapsed")
        with _ev2: st.text_input("Última evacuação", key="sis_gastro_evacuacao_data", placeholder="Data da última", label_visibility="collapsed")
        with _ev3: st.text_input("Laxativo", key="sis_gastro_laxativo", placeholder="Laxativo", label_visibility="collapsed")

        st.markdown("**Pocus Exame Abdominal**")
        st.text_input("Pocus Exame Abdominal", key="sis_gastro_pocus", placeholder="Ex: Ascite leve...", label_visibility="collapsed")

        st.markdown("**Exames Trato Gastrointestinal**")
        _evo_header()
        _evo_row("TGO", "sis_gastro_tgo")
        _evo_row("TGP", "sis_gastro_tgp")
        _evo_row("FAL", "sis_gastro_fal")
        _evo_row("GGT", "sis_gastro_ggt")
        _evo_row("BT",  "sis_gastro_bt")

        st.markdown("**Demais abdominal**")
        st.text_input("Demais gastrointestinal", key="sis_gastro_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_gastro_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")
