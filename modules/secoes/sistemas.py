import streamlit as st

# Campos com esquema anteontem → ontem → hoje (para deslocar em "Evolução Hoje")
_CAMPOS_ANTE_ONTEM_HOJE = [
    ("sis_renal_cr", "antepen", "ult", "hoje"),
    ("sis_renal_ur", "antepen", "ult", "hoje"),
    ("sis_infec_pcr", "antepen", "ult", "hoje"),
    ("sis_infec_leuc", "antepen", "ult", "hoje"),
    ("sis_hemato_hb", "antepen", "ult", "hoje"),
    ("sis_hemato_plaq", "antepen", "ult", "hoje"),
    ("sis_hemato_inr", "antepen", "ult", "hoje"),
]


def _deslocar_sistemas():
    """
    Desloca os dias nos campos de laboratório: anteontem some, ontem→anteontem, hoje→ontem, hoje fica vazio.
    Prepara os campos para preencher os dados de hoje. Preserva todos os dados preenchidos (apenas desloca).
    """
    for prefix, suf_a, suf_u, suf_h in _CAMPOS_ANTE_ONTEM_HOJE:
        key_a = f"{prefix}_{suf_a}"
        key_u = f"{prefix}_{suf_u}"
        key_h = f"{prefix}_{suf_h}"
        # Lê primeiro para não sobrescrever antes de usar
        val_ontem = st.session_state.get(key_u, "") or ""
        val_hoje = st.session_state.get(key_h, "") or ""
        st.session_state[key_a] = val_ontem
        st.session_state[key_u] = val_hoje
        st.session_state[key_h] = ""


def get_campos():
    campos = {}
    
    # Lista de prefixos para facilitar a criação
    sistemas = [
        'neuro', 'resp', 'cardio', 'renal', 'metab', 
        'infec', 'gastro', 'nutri', 'hemato', 'pele'
    ]
    
    # Campo livre abaixo do título
    campos['sistemas_notas'] = ''
    
    # Cria campos genéricos para Pocus, Obs e Conduta de cada sistema
    for s in sistemas:
        campos[f'sis_{s}_pocus'] = ''
        campos[f'sis_{s}_obs'] = ''
        campos[f'sis_{s}_conduta'] = ''

    # --- CAMPOS ESPECÍFICOS ---
    
    # 1. Neuro
    campos.update({
        'sis_neuro_ecg': '',      # GCS 3-15
        'sis_neuro_ecg_ao': '',   # Abertura Ocular 1-4
        'sis_neuro_ecg_rv': '',   # Resposta Verbal 1-5
        'sis_neuro_ecg_rm': '',   # Resposta Motora 1-6
        'sis_neuro_ecg_p': '',    # ECG-P 1-15
        'sis_neuro_rass': '',     # RASS -5 a +5
        'sis_neuro_delirium': None,
        'sis_neuro_delirium_tipo': None,
        'sis_neuro_cam_icu': None,
        'sis_neuro_pupilas_tam': None,
        'sis_neuro_pupilas_simetria': None,
        'sis_neuro_pupilas_foto': None,
        'sis_neuro_analgesico_adequado': None,
        'sis_neuro_deficits_focais': '',
        'sis_neuro_deficits_ausente': None,
        'sis_neuro_analgesia_1_tipo': None,
        'sis_neuro_analgesia_1_drogas': '',
        'sis_neuro_analgesia_1_dose': '',
        'sis_neuro_analgesia_1_freq': '',
        'sis_neuro_analgesia_2_tipo': None,
        'sis_neuro_analgesia_2_drogas': '',
        'sis_neuro_analgesia_2_dose': '',
        'sis_neuro_analgesia_2_freq': '',
        'sis_neuro_analgesia_3_tipo': None,
        'sis_neuro_analgesia_3_drogas': '',
        'sis_neuro_analgesia_3_dose': '',
        'sis_neuro_analgesia_3_freq': '',
        'sis_neuro_sedacao_meta': '',
        'sis_neuro_sedacao_1_drogas': '',
        'sis_neuro_sedacao_1_dose': '',
        'sis_neuro_sedacao_2_drogas': '',
        'sis_neuro_sedacao_2_dose': '',
        'sis_neuro_sedacao_3_drogas': '',
        'sis_neuro_sedacao_3_dose': '',
        'sis_neuro_bloqueador_med': '',
        'sis_neuro_bloqueador_dose': ''
    })

    # 2. Respiratório
    campos.update({
        'sis_resp_ausculta': '',
        'sis_resp_modo': None,
        'sis_resp_modo_vent': None,
        'sis_resp_oxigenio_modo': '',
        'sis_resp_oxigenio_fluxo': '',
        'sis_resp_pressao': '',
        'sis_resp_volume': '',
        'sis_resp_fio2': '',
        'sis_resp_peep': '',
        'sis_resp_freq': '',
        'sis_resp_vent_protetora': None,
        'sis_resp_sincronico': None,
        'sis_resp_assincronia': '',
        'sis_resp_complacencia': '',
        'sis_resp_resistencia': '',
        'sis_resp_dp': '',
        'sis_resp_plato': '',
        'sis_resp_pico': '',
        'sis_resp_dreno_1': '',
        'sis_resp_dreno_1_debito': '',
        'sis_resp_dreno_2': '',
        'sis_resp_dreno_2_debito': '',
        'sis_resp_dreno_3': '',
        'sis_resp_dreno_3_debito': '',
    })

    # 3. Cardio
    campos.update({
        'sis_cardio_fc': '',
        'sis_cardio_cardioscopia': '',
        'sis_cardio_pam': '',
        'sis_cardio_perfusao': None,
        'sis_cardio_tec': '',
        'sis_cardio_fluido_responsivo': None,
        'sis_cardio_fluido_tolerante': None,
        'sis_cardio_dva_1_med': '',
        'sis_cardio_dva_1_dose': '',
        'sis_cardio_dva_2_med': '',
        'sis_cardio_dva_2_dose': '',
        'sis_cardio_dva_3_med': '',
        'sis_cardio_dva_3_dose': '',
        'sis_cardio_dva_4_med': '',
        'sis_cardio_dva_4_dose': '',
    })

    # 4. Renal
    campos.update({
        'sis_renal_diurese': '',
        'sis_renal_balanco': '',
        'sis_renal_balanco_acum': '',
        'sis_renal_volemia': None,
        'sis_renal_cr_antepen': '',
        'sis_renal_cr_ult': '',
        'sis_renal_cr_hoje': '',
        'sis_renal_ur_antepen': '',
        'sis_renal_ur_ult': '',
        'sis_renal_ur_hoje': '',
        'sis_renal_sodio': None,
        'sis_renal_potassio': None,
        'sis_renal_magnesio': None,
        'sis_renal_fosforo': None,
        'sis_renal_calcio': None,
        'sis_renal_trs': None,
        'sis_renal_trs_via': '',
        'sis_renal_trs_ultima': '',
        'sis_renal_trs_proxima': '',
    })

    # 5. Infeccioso
    campos.update({
        'sis_infec_febre': None,
        'sis_infec_febre_vezes': '',
        'sis_infec_febre_ultima': '',
        'sis_infec_atb': None,
        'sis_infec_atb_1': '',
        'sis_infec_atb_2': '',
        'sis_infec_atb_3': '',
        'sis_infec_atb_guiado': None,
        'sis_infec_culturas_and': None,
        'sis_infec_cult_1_sitio': '',
        'sis_infec_cult_1_data': '',
        'sis_infec_cult_2_sitio': '',
        'sis_infec_cult_2_data': '',
        'sis_infec_cult_3_sitio': '',
        'sis_infec_cult_3_data': '',
        'sis_infec_cult_4_sitio': '',
        'sis_infec_cult_4_data': '',
        'sis_infec_pcr_hoje': '',
        'sis_infec_pcr_ult': '',
        'sis_infec_pcr_antepen': '',
        'sis_infec_leuc_antepen': '',
        'sis_infec_leuc_ult': '',
        'sis_infec_leuc_hoje': '',
        'sis_infec_isolamento': None,
        'sis_infec_isolamento_tipo': '',
        'sis_infec_isolamento_motivo': '',
        'sis_infec_patogenos': '',
    })

    # 7. Gastro
    campos.update({
        'sis_gastro_exame_fisico': '',
        'sis_gastro_ictericia_presente': None,
        'sis_gastro_ictericia_cruzes': '',
        'sis_gastro_dieta_oral': '',
        'sis_gastro_dieta_enteral': '',
        'sis_gastro_dieta_enteral_vol': '',
        'sis_gastro_dieta_parenteral': '',
        'sis_gastro_dieta_parenteral_vol': '',
        'sis_gastro_meta_calorica': '',
        'sis_gastro_na_meta': None,
        'sis_gastro_ingestao_quanto': '',
        'sis_gastro_escape_glicemico': None,
        'sis_gastro_escape_vezes': '',
        'sis_gastro_escape_manha': False,
        'sis_gastro_escape_tarde': False,
        'sis_gastro_escape_noite': False,
        'sis_gastro_insulino': None,
        'sis_gastro_insulino_dose_manha': '',
        'sis_gastro_insulino_dose_tarde': '',
        'sis_gastro_insulino_dose_noite': '',
        'sis_gastro_evacuacao': None,
        'sis_gastro_evacuacao_data': '',
        'sis_gastro_laxativo': '',
    })

    # 8. Hemato
    campos.update({
        'sis_hemato_anticoag': None,
        'sis_hemato_anticoag_motivo': '',
        'sis_hemato_anticoag_tipo': None,
        'sis_hemato_sangramento': None,
        'sis_hemato_sangramento_via': '',
        'sis_hemato_sangramento_data': '',
        'sis_hemato_transf_data': '',
        'sis_hemato_transf_1_comp': '',
        'sis_hemato_transf_1_bolsas': '',
        'sis_hemato_transf_2_comp': '',
        'sis_hemato_transf_2_bolsas': '',
        'sis_hemato_transf_3_comp': '',
        'sis_hemato_transf_3_bolsas': '',
        'sis_hemato_hb_antepen': '',
        'sis_hemato_hb_ult': '',
        'sis_hemato_hb_hoje': '',
        'sis_hemato_plaq_antepen': '',
        'sis_hemato_plaq_ult': '',
        'sis_hemato_plaq_hoje': '',
        'sis_hemato_inr_antepen': '',
        'sis_hemato_inr_ult': '',
        'sis_hemato_inr_hoje': '',
    })

    # 10. Pele e musculoesquelético
    campos.update({
        'sis_pele_edema': None,           # Presente / Ausente
        'sis_pele_edema_cruzes': '',      # Número de cruzes (cacifo)
        'sis_pele_lpp': None,
        'sis_pele_lpp_local_1': '',
        'sis_pele_lpp_grau_1': '',
        'sis_pele_lpp_local_2': '',
        'sis_pele_lpp_grau_2': '',
        'sis_pele_lpp_local_3': '',
        'sis_pele_lpp_grau_3': '',
        'sis_pele_polineuropatia': None,
    })

    return campos

# --- FUNÇÃO DE RENDERIZAÇÃO ---
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-13"></span>', unsafe_allow_html=True)
    st.markdown("##### 13. Evolução por Sistemas")
    
    st.text_area("Notas", key="sistemas_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    col_evo, col_puxar, col_ag, _ = st.columns([1, 1.7, 1, 6])
    with col_evo:
        evo_clicked = st.form_submit_button(
            "Evolução Hoje",
            key="btn_evolucao_hoje_sistemas",
            use_container_width=True,
            help="Anteontem some; ontem vira anteontem; hoje vira ontem; hoje fica vazio. Para preencher os dados de hoje.",
        )
        if evo_clicked:
            _deslocar_sistemas()
            st.toast("✅ Dados deslocados. Ontem → anteontem, hoje → ontem. Campos de hoje prontos para preenchimento.", icon="✅")
    with col_puxar:
        if st.form_submit_button(
            "Completar Blocos Anteriores",
            key="btn_completar_blocos_sistemas",
            help="Preenche campos da Seção 13 com dados já preenchidos: Controles (diurese, balanço), Lab (Cr, Ur, PCR, Leuco, Hb, Plaq, INR), Antibióticos e Culturas",
            use_container_width=True,
        ):
            st.session_state["_completar_blocos_sistemas"] = True
    with col_ag:
        if _agent_btn_callback:
            _agent_btn_callback()
    
    # NEUROLÓGICO
    with st.container(border=True):
        st.markdown("**Neurológico**")
        
        # Linha 1: ECG total + componentes AO / RV / RM (text_input como FC, PAM, laboratoriais)
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

        # Linha 1b: ECG-P e RASS
        ecgp_col, rass_col, _, _ = st.columns(4)
        with ecgp_col:
            st.markdown("**ECG-P (1-15)**")
            st.text_input("ECG-P", key="sis_neuro_ecg_p", placeholder="1-15", label_visibility="collapsed")
        with rass_col:
            st.markdown("**RASS (-5 a +5)**")
            st.text_input("RASS", key="sis_neuro_rass", placeholder="-5 a +5", label_visibility="collapsed")
        
        # Linha 2: Delirium, Tipo de Delirium e CAM-ICU
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
        
        # Linha 3: Pupilas, Simetria e Fotoreatividade lado a lado
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
        
        # Linha 4: Déficits focais (campo + pill Ausente no estilo Miótica/Normal)
        st.markdown("**Déficits focais**")
        df_col, df_pill = st.columns([4, 1])
        with df_col:
            st.text_input("Déficits focais", key="sis_neuro_deficits_focais", placeholder="Ex: Hemiparesia D, afasia...", label_visibility="collapsed")
        with df_pill:
            st.pills("Ausente", ["Ausente"], key="sis_neuro_deficits_ausente", label_visibility="collapsed")
        st.markdown("**Controle analgésico adequado**")
        st.pills("Analgésico", ["Sim", "Não"], key="sis_neuro_analgesico_adequado", label_visibility="collapsed")
        
        # Linha 5: Analgesia - 3 conjuntos (Fixa/Se necessário + Drogas, Dose, Frequência)
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
        
        # Linha 6: Sedação - meta única + 3 conjuntos (Drogas, Dose)
        st.markdown("**Sedação**")
        sed_meta_col, _ = st.columns([1, 3])
        with sed_meta_col:
            st.text_input("Meta RASS", key="sis_neuro_sedacao_meta",
                          placeholder="Ex: RASS -2", label_visibility="visible")
        for i in range(1, 4):
            s1, s2 = st.columns(2)
            with s1:
                st.text_input("Drogas", key=f"sis_neuro_sedacao_{i}_drogas", placeholder="Drogas", label_visibility="collapsed")
            with s2:
                st.text_input("Dose", key=f"sis_neuro_sedacao_{i}_dose", placeholder="Dose", label_visibility="collapsed")
        
        # Bloqueador neuromuscular
        st.markdown("**Bloqueador neuromuscular**")
        bnm_col1, bnm_col2 = st.columns([2, 1])
        with bnm_col1:
            st.text_input("Medicamento", key="sis_neuro_bloqueador_med", placeholder="Ex: Rocurônio", label_visibility="collapsed")
        with bnm_col2:
            st.text_input("Dose", key="sis_neuro_bloqueador_dose", placeholder="Ex: 15 ml/h", label_visibility="collapsed")
        
        # Pocus Neurológico
        st.markdown("**Pocus Neurológico**")
        st.text_input("Pocus Neurológico", key="sis_neuro_pocus", placeholder="Ex: Padrão de linhas A...", label_visibility="collapsed")

        # Demais neurologia
        st.markdown("**Demais neurologia**")
        st.text_input("Demais neurologia", key="sis_neuro_obs", placeholder="Outros achados...", label_visibility="collapsed")
        
        # Conduta (por último)
        st.text_input("Conduta", key="sis_neuro_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

    # RESPIRATÓRIO
    with st.container(border=True):
        st.markdown("**Respiratório**")
        
        # Ausculta
        st.markdown("**Ausculta**")
        st.text_input("Ausculta", key="sis_resp_ausculta", placeholder="Ex: MV+ bilateral, sem sibilos...", label_visibility="collapsed")
        
        # Suporte Ventilatório — títulos na mesma linha, mesmo design
        tit1, tit2, tit3, tit4 = st.columns([2, 1, 1.5, 1])
        with tit1:
            st.markdown("**Suporte Ventilatório**")
        with tit2:
            st.markdown("<span style='white-space: nowrap'>**Modo Ventilatório**</span>", unsafe_allow_html=True)
        with tit3:
            st.markdown("**Modo O₂**")
        with tit4:
            st.markdown("**Fluxo**")
        mv1, mv2, mv3, mv4 = st.columns([2, 1, 1.5, 1])
        with mv1:
            st.pills("Modo", ["Ar Ambiente", "Oxigenoterapia", "VNI", "Cateter de Alto Fluxo", "Ventilação Mecânica"],
                     key="sis_resp_modo", label_visibility="collapsed")
        with mv2:
            st.pills("Modalidade VM", ["VCV", "PCV", "PSV"],
                     key="sis_resp_modo_vent", label_visibility="collapsed")
        with mv3:
            st.text_input("Modo O₂", key="sis_resp_oxigenio_modo", placeholder="Ex: Cateter Nasal", label_visibility="collapsed")
        with mv4:
            st.text_input("Fluxo", key="sis_resp_oxigenio_fluxo", placeholder="Ex: 2 L/min", label_visibility="collapsed")
        
        # Parâmetros
        st.markdown("**Parâmetros**")
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1:
            st.text_input("Pressão", key="sis_resp_pressao", placeholder="Pressão", label_visibility="collapsed")
        with p2:
            st.text_input("Volume", key="sis_resp_volume", placeholder="Volume", label_visibility="collapsed")
        with p3:
            st.text_input("FiO2", key="sis_resp_fio2", placeholder="FiO2", label_visibility="collapsed")
        with p4:
            st.text_input("PEEP", key="sis_resp_peep", placeholder="PEEP", label_visibility="collapsed")
        with p5:
            st.text_input("Frequência Respiratória", key="sis_resp_freq", placeholder="Frequência Respiratória", label_visibility="collapsed")
        
        # Ventilação protetora, Sincrônico, Assincronia (no lugar de desmame)
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
        
        # Mecânica respiratória
        st.markdown("**Mecânica respiratória**")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.text_input("Complacência", key="sis_resp_complacencia", placeholder="Complacência", label_visibility="collapsed")
        with m2:
            st.text_input("Resistência", key="sis_resp_resistencia", placeholder="Resistência", label_visibility="collapsed")
        with m3:
            st.text_input("Driving Pressure", key="sis_resp_dp", placeholder="Driving Pressure", label_visibility="collapsed")
        with m4:
            st.text_input("Pressão de Platô", key="sis_resp_plato", placeholder="Pressão de Platô", label_visibility="collapsed")
        with m5:
            st.text_input("Pressão de Pico", key="sis_resp_pico", placeholder="Pressão de Pico", label_visibility="collapsed")
        
        # Drenos: 3 pares (campo + débito)
        st.markdown("**Drenos**")
        for i in range(1, 4):
            d1, d2 = st.columns([2, 1])
            with d1:
                st.text_input(f"Dreno {i}", key=f"sis_resp_dreno_{i}", placeholder="Ex: Pleural D, mediastinal...", label_visibility="collapsed")
            with d2:
                st.text_input(f"Débito {i}", key=f"sis_resp_dreno_{i}_debito", placeholder="mL/dia", label_visibility="collapsed")
        
        # Pocus Respiratório
        st.markdown("**Pocus Respiratório**")
        st.text_input("Pocus Respiratório", key="sis_resp_pocus", placeholder="Ex: Padrão de linhas B...", label_visibility="collapsed")

        # Demais respiratório
        st.markdown("**Demais respiratório**")
        st.text_input("Demais respiratório", key="sis_resp_obs", placeholder="Outros achados...", label_visibility="collapsed")

        # Conduta
        st.text_input("Conduta", key="sis_resp_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

    # CARDIOVASCULAR
    with st.container(border=True):
        st.markdown("**Cardiovascular**")

        # Frequência, Cardioscopia, PAM
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

        # Perfusão periférica — títulos na mesma linha
        perf_tit, tec_tit = st.columns([2, 1])
        with perf_tit:
            st.markdown("**Perfusão periférica**")
        with tec_tit:
            st.markdown("**Tempo de Enchimento Capilar**")
        perf_col, tec_col = st.columns([2, 1])
        with perf_col:
            st.pills("Perfusão", ["Normal", "Lentificada", "Flush"], key="sis_cardio_perfusao", label_visibility="collapsed")
        with tec_col:
            st.text_input("TEC", key="sis_cardio_tec", placeholder="Ex: 3 seg.", label_visibility="collapsed")

        # Fluido responsivo / Fluido tolerante
        f1, f2 = st.columns(2)
        with f1:
            st.markdown("**Fluido responsivo**")
            st.pills("Fluido responsivo", ["Sim", "Não"], key="sis_cardio_fluido_responsivo", label_visibility="collapsed")
        with f2:
            st.markdown("**Fluido tolerante**")
            st.pills("Fluido tolerante", ["Sim", "Não"], key="sis_cardio_fluido_tolerante", label_visibility="collapsed")

        # Drogas Vasoativas: 4 pares Medicamento / Dose
        st.markdown("**Drogas Vasoativas**")
        for i in range(1, 5):
            d1, d2 = st.columns(2)
            with d1:
                st.text_input(f"Medicamento {i}", key=f"sis_cardio_dva_{i}_med", placeholder="Medicamento", label_visibility="collapsed")
            with d2:
                st.text_input(f"Dose {i}", key=f"sis_cardio_dva_{i}_dose", placeholder="Dose", label_visibility="collapsed")

        # Pocus Cardiovascular
        st.markdown("**Pocus Cardiovascular**")
        st.text_input("Pocus Cardiovascular", key="sis_cardio_pocus", placeholder="Ex: Função ventricular preservada...", label_visibility="collapsed")

        # Demais cardio e Conduta
        st.markdown("**Demais cardiovascular**")
        st.text_input("Demais cardiovascular", key="sis_cardio_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_cardio_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

    # GASTROINTESTINAL
    with st.container(border=True):
        st.markdown("**Trato Gastrointestinal**")

        # Exame Físico (coluna 1) | Icterícia Presente + Cruzes (coluna 2)
        ef_col, icter_col = st.columns([3, 1])
        with ef_col:
            st.markdown("**Exame Físico**")
            st.text_input("Exame Físico", key="sis_gastro_exame_fisico", placeholder="Abdome distendido, timpânico, DB negativo...", label_visibility="collapsed")
        with icter_col:
            st.markdown("**Icterícia**")
            pills_col, cruzes_col = st.columns([1, 1])
            with pills_col:
                st.pills("Icterícia", ["Presente", "Ausente"], key="sis_gastro_ictericia_presente", label_visibility="collapsed")
            with cruzes_col:
                st.text_input("Quantas cruzes", key="sis_gastro_ictericia_cruzes", placeholder="1 a 4", label_visibility="collapsed")

        # Dieta
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

        # Todas as linhas usam total=7, pills sempre=1 (1/7 da largura) → alinhamento vertical
        _ing1, _ing2 = st.columns([1, 6])
        with _ing1:
            st.markdown("**Ingestão na Meta**")
            st.pills("Na meta", ["Sim", "Não"], key="sis_gastro_na_meta", label_visibility="collapsed")
        with _ing2:
            st.markdown("**Quanto**")
            st.text_input("Quanto", key="sis_gastro_ingestao_quanto", placeholder="Ex: 1200 kcal", label_visibility="collapsed")

        st.markdown("**Escape glicêmico**")
        _esc1, _esc2, _esc3, _esc4, _esc5 = st.columns([1, 3, 1, 1, 1])
        with _esc1:
            st.pills("Escape", ["Sim", "Não"], key="sis_gastro_escape_glicemico", label_visibility="collapsed")
        with _esc2:
            st.text_input("Nº vezes", key="sis_gastro_escape_vezes", placeholder="Nº vezes", label_visibility="collapsed")
        with _esc3:
            st.checkbox("Manhã", key="sis_gastro_escape_manha")
        with _esc4:
            st.checkbox("Tarde", key="sis_gastro_escape_tarde")
        with _esc5:
            st.checkbox("Noite", key="sis_gastro_escape_noite")

        st.markdown("**Insulinoterapia**")
        _ins1, _ins2, _ins3, _ins4 = st.columns([1, 2, 2, 2])
        with _ins1:
            st.pills("Insulino", ["Sim", "Não"], key="sis_gastro_insulino", label_visibility="collapsed")
        with _ins2:
            st.text_input("Dose manhã", key="sis_gastro_insulino_dose_manha", placeholder="Dose manhã", label_visibility="collapsed")
        with _ins3:
            st.text_input("Dose tarde", key="sis_gastro_insulino_dose_tarde", placeholder="Dose tarde", label_visibility="collapsed")
        with _ins4:
            st.text_input("Dose noite", key="sis_gastro_insulino_dose_noite", placeholder="Dose noite", label_visibility="collapsed")

        st.markdown("**Evacuação**")
        _ev1, _ev2, _ev3 = st.columns([1, 3, 3])
        with _ev1:
            st.pills("Evacuação", ["Sim", "Não"], key="sis_gastro_evacuacao", label_visibility="collapsed")
        with _ev2:
            st.text_input("Última evacuação", key="sis_gastro_evacuacao_data", placeholder="Data da última", label_visibility="collapsed")
        with _ev3:
            st.text_input("Laxativo", key="sis_gastro_laxativo", placeholder="Laxativo", label_visibility="collapsed")

        # Pocus Trato Gastrointestinal
        st.markdown("**Pocus Trato Gastrointestinal**")
        st.text_input("Pocus Trato Gastrointestinal", key="sis_gastro_pocus", placeholder="Ex: Ascite leve...", label_visibility="collapsed")

        # Demais gastro e Conduta
        st.markdown("**Demais gastrointestinal**")
        st.text_input("Demais gastrointestinal", key="sis_gastro_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_gastro_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

    # RENAL
    with st.container(border=True):
        st.markdown("**Renal**")

        # Diurese, Balanço, Balanço Acumulado
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

        # Volemia
        st.markdown("**Volemia**")
        st.pills("Volemia", ["Hipovolêmico", "Euvolêmico", "Hipervolêmico"], key="sis_renal_volemia", label_visibility="collapsed")

        # Creatinina e Ureia (hoje, ontem, anteontem)
        st.markdown("**Função Renal**")
        cr1, cr2, cr3 = st.columns(3)
        with cr1:
            st.markdown("**Hoje**")
            st.text_input("Creatinina hoje", key="sis_renal_cr_hoje", placeholder="Creatinina hoje", label_visibility="collapsed")
        with cr2:
            st.markdown("**Ontem**")
            st.text_input("Creatinina ontem", key="sis_renal_cr_ult", placeholder="Creatinina ontem", label_visibility="collapsed")
        with cr3:
            st.markdown("**Anteontem**")
            st.text_input("Creatinina anteontem", key="sis_renal_cr_antepen", placeholder="Creatinina anteontem", label_visibility="collapsed")
        ur1, ur2, ur3 = st.columns(3)
        with ur1:
            st.text_input("Ureia hoje", key="sis_renal_ur_hoje", placeholder="Ureia hoje", label_visibility="collapsed")
        with ur2:
            st.text_input("Ureia ontem", key="sis_renal_ur_ult", placeholder="Ureia ontem", label_visibility="collapsed")
        with ur3:
            st.text_input("Ureia anteontem", key="sis_renal_ur_antepen", placeholder="Ureia anteontem", label_visibility="collapsed")

        # Distúrbios hidroeletrolíticos
        st.markdown("**Distúrbio hidroeletrolítico**")
        e1, e2, e3, e4, e5 = st.columns(5)
        with e1:
            st.markdown("**Sódio**")
            st.pills("Sódio", ["Normal", "Hiponatremia", "Hipernatremia"], key="sis_renal_sodio", label_visibility="collapsed")
        with e2:
            st.markdown("**Potássio**")
            st.pills("Potássio", ["Normal", "Hipocalemia", "Hipercalemia"], key="sis_renal_potassio", label_visibility="collapsed")
        with e3:
            st.markdown("**Magnésio**")
            st.pills("Magnésio", ["Normal", "Hipomagnesemia", "Hipermagnesemia"], key="sis_renal_magnesio", label_visibility="collapsed")
        with e4:
            st.markdown("**Fósforo**")
            st.pills("Fósforo", ["Normal", "Hipofosfatemia", "Hiperfosfatemia"], key="sis_renal_fosforo", label_visibility="collapsed")
        with e5:
            st.markdown("**Cálcio**")
            st.pills("Cálcio", ["Normal", "Hipocalcemia", "Hipercalcemia"], key="sis_renal_calcio", label_visibility="collapsed")

        # TRS
        st.markdown("**Terapia de Substituição Renal (TRS)**")
        t1, t2, t3, t4 = st.columns(4)
        with t1:
            st.pills("TRS", ["Sim", "Não"], key="sis_renal_trs", label_visibility="collapsed")
        with t2:
            st.text_input("Via", key="sis_renal_trs_via", placeholder="Via", label_visibility="collapsed")
        with t3:
            st.text_input("Última diálise", key="sis_renal_trs_ultima", placeholder="Data última diálise", label_visibility="collapsed")
        with t4:
            st.text_input("Próxima TRS", key="sis_renal_trs_proxima", placeholder="Programação próxima TRS", label_visibility="collapsed")

        # Pocus Renal
        st.markdown("**Pocus Renal**")
        st.text_input("Pocus Renal", key="sis_renal_pocus", placeholder="Ex: Rins com dimensões preservadas...", label_visibility="collapsed")

        # Demais renal e Conduta
        st.markdown("**Demais renal**")
        st.text_input("Demais renal", key="sis_renal_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_renal_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

    # INFECCIOSO
    with st.container(border=True):
        st.markdown("**Infeccioso**")

        # Febre 24h
        st.markdown("**Febre nas últimas 24h**")
        f1, f2, f3 = st.columns(3)
        with f1:
            st.pills("Febre", ["Sim", "Não"], key="sis_infec_febre", label_visibility="collapsed")
        with f2:
            st.text_input("Quantas vezes", key="sis_infec_febre_vezes", placeholder="Quantas vezes", label_visibility="collapsed")
        with f3:
            st.text_input("Data da última febre", key="sis_infec_febre_ultima", placeholder="Data da última febre", label_visibility="collapsed")

        # Antibioticoterapia
        st.markdown("**Uso de Antibioticoterapia**")
        a1, a2 = st.columns([1, 2])
        with a1:
            st.markdown("**Em uso**")
            st.pills("ATB", ["Sim", "Não"], key="sis_infec_atb", label_visibility="collapsed")
        with a2:
            st.markdown("**Guiado por cultura**")
            st.pills("Guiado", ["Sim", "Não"], key="sis_infec_atb_guiado", label_visibility="collapsed")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.text_input("Medicamento 1", key="sis_infec_atb_1", placeholder="Medicamento 1", label_visibility="collapsed")
        with m2:
            st.text_input("Medicamento 2", key="sis_infec_atb_2", placeholder="Medicamento 2", label_visibility="collapsed")
        with m3:
            st.text_input("Medicamento 3", key="sis_infec_atb_3", placeholder="Medicamento 3", label_visibility="collapsed")

        # Culturas em andamento
        st.markdown("**Culturas em andamento**")
        st.pills("Culturas", ["Sim", "Não"], key="sis_infec_culturas_and", label_visibility="collapsed")
        for i in range(1, 5):
            cs1, cs2 = st.columns([3, 1])
            with cs1:
                st.text_input(f"Sítio {i}", key=f"sis_infec_cult_{i}_sitio", placeholder=f"Sítio {i}", label_visibility="collapsed")
            with cs2:
                st.text_input(f"Coleta {i}", key=f"sis_infec_cult_{i}_data", placeholder="Data coleta", label_visibility="collapsed")

        # PCR e Leucócitos (hoje, ontem, anteontem)
        st.markdown("**Marcadores inflamatórios**")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("**Hoje**")
            st.text_input("PCR hoje", key="sis_infec_pcr_hoje", placeholder="PCR hoje", label_visibility="collapsed")
        with m2:
            st.markdown("**Ontem**")
            st.text_input("PCR ontem", key="sis_infec_pcr_ult", placeholder="PCR ontem", label_visibility="collapsed")
        with m3:
            st.markdown("**Anteontem**")
            st.text_input("PCR anteontem", key="sis_infec_pcr_antepen", placeholder="PCR anteontem", label_visibility="collapsed")
        l1, l2, l3 = st.columns(3)
        with l1:
            st.text_input("Leucócitos hoje", key="sis_infec_leuc_hoje", placeholder="Leucócitos hoje", label_visibility="collapsed")
        with l2:
            st.text_input("Leucócitos ontem", key="sis_infec_leuc_ult", placeholder="Leucócitos ontem", label_visibility="collapsed")
        with l3:
            st.text_input("Leucócitos anteontem", key="sis_infec_leuc_antepen", placeholder="Leucócitos anteontem", label_visibility="collapsed")

        # Isolamento
        st.markdown("**Isolamento**")
        i1, i2, i3 = st.columns(3)
        with i1:
            st.pills("Isolamento", ["Sim", "Não"], key="sis_infec_isolamento", label_visibility="collapsed")
        with i2:
            st.text_input("Tipo", key="sis_infec_isolamento_tipo", placeholder="Tipo", label_visibility="collapsed")
        with i3:
            st.text_input("Motivo", key="sis_infec_isolamento_motivo", placeholder="Motivo", label_visibility="collapsed")

        # Patógenos isolados
        st.markdown("**Patógenos isolados**")
        st.text_input("Patógenos", key="sis_infec_patogenos", placeholder="Ex: K. pneumoniae KPC+, MRSA...", label_visibility="collapsed")

        # Pocus Infeccioso
        st.markdown("**Pocus Infeccioso**")
        st.text_input("Pocus Infeccioso", key="sis_infec_pocus", placeholder="Ex: Coleção...", label_visibility="collapsed")

        # Demais infeccioso e Conduta
        st.markdown("**Demais infeccioso**")
        st.text_input("Demais infeccioso", key="sis_infec_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_infec_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

    # HEMATOLÓGICO
    with st.container(border=True):
        st.markdown("**Hematológico**")

        # Anticoagulação
        st.markdown("**Anticoagulação**")
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            st.pills("Anticoag", ["Sim", "Não"], key="sis_hemato_anticoag", label_visibility="collapsed")
        with ac2:
            st.pills("Tipo", ["Profilática", "Plena"], key="sis_hemato_anticoag_tipo", label_visibility="collapsed")
        with ac3:
            st.text_input("Motivo", key="sis_hemato_anticoag_motivo", placeholder="Motivo", label_visibility="collapsed")

        # Sangramento
        st.markdown("**Sangramento**")
        s1, s2, s3 = st.columns(3)
        with s1:
            st.pills("Sangramento", ["Sim", "Não"], key="sis_hemato_sangramento", label_visibility="collapsed")
        with s2:
            st.text_input("Via", key="sis_hemato_sangramento_via", placeholder="Via", label_visibility="collapsed")
        with s3:
            st.text_input("Data último sangramento", key="sis_hemato_sangramento_data", placeholder="Data último sangramento", label_visibility="collapsed")

        # Transfusão
        st.markdown("**Transfusão sanguínea**")
        st.text_input("Data última transfusão", key="sis_hemato_transf_data", placeholder="Data última transfusão", label_visibility="collapsed")
        for i in range(1, 4):
            t1, t2 = st.columns([3, 1])
            with t1:
                st.text_input(f"Componente {i}", key=f"sis_hemato_transf_{i}_comp", placeholder=f"Componente {i}", label_visibility="collapsed")
            with t2:
                st.text_input(f"Nº bolsas {i}", key=f"sis_hemato_transf_{i}_bolsas", placeholder="Nº bolsas", label_visibility="collapsed")

        # Hb, Plaquetas e INR (hoje, ontem, anteontem)
        st.markdown("**Hemograma**")
        h1, h2, h3 = st.columns(3)
        with h1:
            st.markdown("**Hoje**")
            st.text_input("Hb hoje", key="sis_hemato_hb_hoje", placeholder="Hb hoje", label_visibility="collapsed")
        with h2:
            st.markdown("**Ontem**")
            st.text_input("Hb ontem", key="sis_hemato_hb_ult", placeholder="Hb ontem", label_visibility="collapsed")
        with h3:
            st.markdown("**Anteontem**")
            st.text_input("Hb anteontem", key="sis_hemato_hb_antepen", placeholder="Hb anteontem", label_visibility="collapsed")
        p1, p2, p3 = st.columns(3)
        with p1:
            st.text_input("Plaquetas hoje", key="sis_hemato_plaq_hoje", placeholder="Plaquetas hoje", label_visibility="collapsed")
        with p2:
            st.text_input("Plaquetas ontem", key="sis_hemato_plaq_ult", placeholder="Plaquetas ontem", label_visibility="collapsed")
        with p3:
            st.text_input("Plaquetas anteontem", key="sis_hemato_plaq_antepen", placeholder="Plaquetas anteontem", label_visibility="collapsed")

        # Coagulograma
        st.markdown("**Coagulograma**")
        inr1, inr2, inr3 = st.columns(3)
        with inr1:
            st.text_input("INR hoje", key="sis_hemato_inr_hoje", placeholder="INR hoje", label_visibility="collapsed")
        with inr2:
            st.text_input("INR ontem", key="sis_hemato_inr_ult", placeholder="INR ontem", label_visibility="collapsed")
        with inr3:
            st.text_input("INR anteontem", key="sis_hemato_inr_antepen", placeholder="INR anteontem", label_visibility="collapsed")

        # Pocus Hematológico
        st.markdown("**Pocus Hematológico**")
        st.text_input("Pocus Hematológico", key="sis_hemato_pocus", placeholder="Ex: Derrame pleural...", label_visibility="collapsed")

        # Demais hemato e Conduta
        st.markdown("**Demais hematológico**")
        st.text_input("Demais hemato", key="sis_hemato_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_hemato_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

    # PELE E MUSCULOESQUELÉTICO
    with st.container(border=True):
        st.markdown("**Pele e musculoesquelético**")

        # Edema e Cacifo
        ed_col1, ed_col2 = st.columns(2)
        with ed_col1:
            st.markdown("**Edema**")
            st.pills("Edema", ["Presente", "Ausente"], key="sis_pele_edema", label_visibility="collapsed")
        with ed_col2:
            st.markdown("**Cacifo**")
            st.text_input("Cruzes", key="sis_pele_edema_cruzes", placeholder="Nº de cruzes", label_visibility="collapsed")

        # Lesão por Pressão
        st.markdown("**Lesão por Pressão**")
        lpp_cols = st.columns([1, 2, 1])
        with lpp_cols[0]:
            st.pills("LPP", ["Sim", "Não"], key="sis_pele_lpp", label_visibility="collapsed")
        for i in range(1, 4):
            l1, l2 = st.columns([3, 1])
            with l1:
                st.text_input(f"Local {i}", key=f"sis_pele_lpp_local_{i}", placeholder=f"Local {i}", label_visibility="collapsed")
            with l2:
                st.text_input(f"Grau {i}", key=f"sis_pele_lpp_grau_{i}", placeholder=f"Grau {i}", label_visibility="collapsed")

        # Polineuropatia
        st.markdown("**Polineuropatia**")
        st.pills("Polineuropatia", ["Sim", "Não"], key="sis_pele_polineuropatia", label_visibility="collapsed")

        # Pocus Pele e musculoesquelético
        st.markdown("**Pocus Pele e musculoesquelético**")
        st.text_input("Pocus Pele", key="sis_pele_pocus", placeholder="Ex: Edema em membros inferiores...", label_visibility="collapsed")

        # Demais e Conduta
        st.markdown("**Demais pele e musculoesquelético**")
        st.text_input("Demais", key="sis_pele_obs", placeholder="Outros achados...", label_visibility="collapsed")
        st.text_input("Conduta", key="sis_pele_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")