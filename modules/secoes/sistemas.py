import streamlit as st

def get_campos():
    campos = {}
    
    # Lista de prefixos para facilitar a criação
    sistemas = [
        'neuro', 'resp', 'cardio', 'renal', 'metab', 
        'infec', 'gastro', 'nutri', 'hemato', 'pele'
    ]
    
    # Cria campos genéricos para Obs e Conduta de cada sistema
    for s in sistemas:
        campos[f'sis_{s}_obs'] = ''
        campos[f'sis_{s}_conduta'] = ''

    # --- CAMPOS ESPECÍFICOS ---
    
    # 1. Neuro
    campos.update({
        'sis_neuro_nivel': 'Acordado',
        'sis_neuro_escala': '',
        'sis_neuro_sedacao': 'Não',
        'sis_neuro_delirium': 'Não avaliável',
        'sis_neuro_dor': 'Negada/Ausente',
        'sis_neuro_focal': 'Ausente',
        'sis_neuro_convulsao': 'Não',
        'sis_neuro_basal': '',
        'sis_neuro_risco': ''
    })

    # 2. Respiratório
    campos.update({
        'sis_resp_suporte': 'O2 Baixo Fluxo',
        'sis_resp_params': '',
        'sis_resp_oxigenacao': '',
        'sis_resp_mecanica': '',
        'sis_resp_sincronia': 'Boa',
        'sis_resp_secrecao': 'Ausente',
        'sis_resp_tosse': 'Eficaz',
        'sis_resp_desmame': 'Não elegível',
        'sis_resp_diag': '',
        'sis_resp_risco': ''
    })

    # 3. Cardio
    campos.update({
        'sis_cardio_ritmo': 'Sinusal',
        'sis_cardio_fc': '',
        'sis_cardio_pam': '',
        'sis_cardio_drogas': '',
        'sis_cardio_perfusao': 'Aquecido/Corado',
        'sis_cardio_lactato': '',
        'sis_cardio_volume': 'Euvolêmico',
        'sis_cardio_disfuncao': 'Não',
        'sis_cardio_diag': '',
        'sis_cardio_risco': ''
    })

    # 4. Renal
    campos.update({
        'sis_renal_func': 'Preservada',
        'sis_renal_kdigo': '',
        'sis_renal_diurese': 'Preservada',
        'sis_renal_trs': 'Não',
        'sis_renal_cr_tend': '',
        'sis_renal_eletrolitos': '',
        'sis_renal_diag': '',
        'sis_renal_risco': ''
    })

    # 5. Metabólico
    campos.update({
        'sis_metab_glicemia': 'Controlada',
        'sis_metab_insulina': 'Não',
        'sis_metab_eletro': '', # Na/K/Mg/Ca alterados
        'sis_metab_gaso': '', # Acidose/Alcalose
        'sis_metab_corticoide': 'Não',
        'sis_metab_risco': ''
    })

    # 6. Infeccioso
    campos.update({
        'sis_infec_status': 'Sem infecção ativa',
        'sis_infec_foco': '',
        'sis_infec_evolucao': 'Estável',
        'sis_infec_culturas': '',
        'sis_infec_atb': 'Não',
        'sis_infec_tempo': '',
        'sis_infec_risco': ''
    })

    # 7. Gastro
    campos.update({
        'sis_gastro_func': 'Presente',
        'sis_gastro_distensao': 'Ausente',
        'sis_gastro_elim': 'Ausentes',
        'sis_gastro_sangra': 'Ausente',
        'sis_gastro_hep': 'Preservada',
        'sis_gastro_risco': ''
    })

    # 8. Nutri
    campos.update({
        'sis_nutri_via': 'Oral',
        'sis_nutri_tol': 'Adequada',
        'sis_nutri_meta': 'Atingida',
        'sis_nutri_risco_nutri': '',
        'sis_nutri_risco_atual': ''
    })

    # 9. Hemato
    campos.update({
        'sis_hemato_hb': 'Estável',
        'sis_hemato_plaq': 'Normais',
        'sis_hemato_coag': 'Ausente',
        'sis_hemato_anticoag': 'Profilática',
        'sis_hemato_sangra': 'Não',
        'sis_hemato_risco': ''
    })

    # 10. Pele
    campos.update({
        'sis_pele_integra': 'Preservada',
        'sis_pele_disp': 'Limbos',
        'sis_pele_iras': 'Não',
        'sis_pele_retirada': 'Não'
    })

    return campos

# --- FUNÇÃO DE RENDERIZAÇÃO ---
def render():
    st.markdown("##### 12. Evolução Detalhada por Sistemas")
    
    # 🧠 NEUROLÓGICO
    with st.container(border=True):
        st.markdown("**🧠 Neurológico**")
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Consciência", ["Acordado", "Sonolento", "Coma", "Sedado"], key="sis_neuro_nivel")
        c2.text_input("Escala (GCS/FOUR/RASS)", key="sis_neuro_escala", placeholder="Ex: GCS 15 ou RASS -2")
        c3.text_input("Sedação (Droga/Alvo)", key="sis_neuro_sedacao", placeholder="Ex: Precedex, alvo 0")
        
        c4, c5, c6 = st.columns(3)
        c4.selectbox("Delirium (CAM-ICU)", ["Negativo", "Positivo", "Não avaliável"], key="sis_neuro_delirium")
        c5.text_input("Dor / Déficits", key="sis_neuro_dor", placeholder="Ex: Hemiparesia D")
        c6.selectbox("Convulsão?", ["Não", "Sim"], key="sis_neuro_convulsao")

        st.text_input("Basal / Risco Atual", key="sis_neuro_risco", placeholder="Ex: AVC prévio / Risco de abstinência")
        
        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Neuro", key="sis_neuro_obs", placeholder="Outros achados...")
        with c:
            st.text_input("👉 Conduta Neuro", key="sis_neuro_conduta", placeholder="Ex: Desligar sedação, TC crânio...")

    # 🫁 RESPIRATÓRIO
    with st.container(border=True):
        st.markdown("**🫁 Respiratório**")
        c1, c2 = st.columns([1, 2])
        c1.selectbox("Suporte", ["AA", "CNAF", "VNI", "IOT (VM)", "TQT"], key="sis_resp_suporte")
        c2.text_input("Parâmetros (Modo/PEEP/FiO2/Vt)", key="sis_resp_params", placeholder="PCV 14 | PEEP 8 | FiO2 40%")
        
        c3, c4, c5 = st.columns(3)
        c3.text_input("Oxigenação (P/F)", key="sis_resp_oxigenacao", placeholder="Ex: P/F 250")
        c4.text_input("Mecânica (Platô/DP)", key="sis_resp_mecanica")
        c5.selectbox("Sincronia", ["Boa", "Assincronia Leve", "Grave"], key="sis_resp_sincronia")
        
        c6, c7, c8 = st.columns(3)
        c6.selectbox("Secreções", ["Ausentes", "Moderadas", "Abundantes"], key="sis_resp_secrecao")
        c7.selectbox("Tosse/Desmame", ["Eficaz/Elegível", "Ineficaz/Não elegível"], key="sis_resp_tosse")
        c8.text_input("Diagnóstico Ativo", key="sis_resp_diag", placeholder="Ex: PAV, SDRA")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Resp", key="sis_resp_obs")
        with c:
            st.text_input("👉 Conduta Resp", key="sis_resp_conduta", placeholder="Ex: TRE amanhã, Aspirar SN...")

    # ❤️ CARDIOVASCULAR
    with st.container(border=True):
        st.markdown("**❤️ Cardiovascular**")
        c1, c2, c3 = st.columns(3)
        c1.text_input("Ritmo", key="sis_cardio_ritmo", placeholder="Sinusal, FA")
        c2.text_input("FC / PA", key="sis_cardio_fc", placeholder="80 bpm / 65 mmHg (média)")
        c3.text_input("Perfusão/Lactato", key="sis_cardio_perfusao", placeholder="TEC < 3s, Lac em queda")
        
        c4, c5 = st.columns([2, 1])
        c4.text_input("Drogas Vasoativas (Tendência)", key="sis_cardio_drogas", placeholder="Nora 0.1 (estável)")
        c5.selectbox("Volume/Disfunção", ["Euvolêmico", "Hipovolêmico", "Congesto", "Disfunção VE/VD"], key="sis_cardio_volume")
        
        st.text_input("Diagnóstico / Risco", key="sis_cardio_diag", placeholder="Ex: Choque Séptico / Risco de FA")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Cardio", key="sis_cardio_obs")
        with c:
            st.text_input("👉 Conduta Cardio", key="sis_cardio_conduta", placeholder="Ex: Desmame de DVA, EcoTT...")

    # 💧 RENAL
    with st.container(border=True):
        st.markdown("**💧 Renal**")
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Função/KDIGO", ["Preservada", "IRA KDIGO 1", "IRA KDIGO 2", "IRA KDIGO 3"], key="sis_renal_func")
        c2.selectbox("Diurese", ["Preservada", "Oligúria", "Anúria", "Poliúria"], key="sis_renal_diurese")
        c3.selectbox("Diálise (TRS)", ["Não", "HD Intermitente", "SLED", "CVVHDF"], key="sis_renal_trs")
        
        st.text_input("Tendência Cr / Eletrolitos", key="sis_renal_cr_tend", placeholder="Cr estável (1.2) / K+ 5.5")
        
        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Renal", key="sis_renal_obs", placeholder="Diagnóstico/Risco")
        with c:
            st.text_input("👉 Conduta Renal", key="sis_renal_conduta", placeholder="Ex: Ajustar dose ATB, Repor K...")

    # 🍬 METABÓLICO
    with st.container(border=True):
        st.markdown("**🍬 Metabólico / Endócrino**")
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Glicemia", ["Controlada", "Hiperglicemia", "Hipoglicemia"], key="sis_metab_glicemia")
        c2.selectbox("Insulina", ["Não", "SC Check", "Bomba Contínua"], key="sis_metab_insulina")
        c3.selectbox("Corticoide", ["Não", "Estresse (Hidrocort)", "Crônico"], key="sis_metab_corticoide")
        
        st.text_input("Distúrbios (Na, Ca, Mg, Acidose)", key="sis_metab_eletro")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Metab", key="sis_metab_obs")
        with c:
            st.text_input("👉 Conduta Metab", key="sis_metab_conduta", placeholder="Ex: Correção de acidose...")

    # 🦠 INFECCIOSO
    with st.container(border=True):
        st.markdown("**🦠 Infeccioso**")
        c1, c2 = st.columns([1, 2])
        c1.selectbox("Síndrome", ["Sem infecção", "Sepse", "Choque Séptico", "Inf. Localizada"], key="sis_infec_status")
        c2.text_input("Foco / Estado", key="sis_infec_foco", placeholder="Pulmonar / Em melhora")
        
        c3, c4 = st.columns(2)
        c3.text_input("Culturas (Resumo)", key="sis_infec_culturas", placeholder="Hemocultura pendente...")
        c4.text_input("Antibiótico / Dia", key="sis_infec_atb", placeholder="Mero (D3) - Empírico")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Infec", key="sis_infec_obs", placeholder="Risco de multirresistência...")
        with c:
            st.text_input("👉 Conduta Infec", key="sis_infec_conduta", placeholder="Ex: Escalonar, manter ou suspender...")

    # 🍏 GASTROINTESTINAL
    with st.container(border=True):
        st.markdown("**🍏 Gastrointestinal**")
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Função/Trânsito", ["Presente", "Íleo", "Intolerância"], key="sis_gastro_func")
        c2.selectbox("Abdome/Distensão", ["Flácido/Ausente", "Distendido", "Tenso"], key="sis_gastro_distensao")
        c3.selectbox("Eliminações", ["Normais", "Diarreia", "Constipação", "Melena"], key="sis_gastro_elim")
        
        st.text_input("Fígado / Risco Sangramento", key="sis_gastro_hep", placeholder="Função hepática preservada")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Gastro", key="sis_gastro_obs")
        with c:
            st.text_input("👉 Conduta Gastro", key="sis_gastro_conduta", placeholder="Ex: Procinético, Laxante...")

    # 🥗 NUTRICIONAL
    with st.container(border=True):
        st.markdown("**🥗 Nutricional**")
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Via", ["Oral (VO)", "SNE/SNG", "Parenteral (NPT)", "Oral + Enteral"], key="sis_nutri_via")
        c2.selectbox("Tolerância", ["Adequada", "Resíduo alto", "Vômitos"], key="sis_nutri_tol")
        c3.selectbox("Meta Calórica", ["Atingida", "Não atingida", "Em progressão"], key="sis_nutri_meta")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Nutri", key="sis_nutri_obs", placeholder="Risco broncoaspiração...")
        with c:
            st.text_input("👉 Conduta Nutri", key="sis_nutri_conduta", placeholder="Ex: Progredir dieta, Jejum...")

    # 🩸 HEMATOLÓGICO
    with st.container(border=True):
        st.markdown("**🩸 Hematológico**")
        c1, c2, c3 = st.columns(3)
        c1.text_input("Hb / Plaq", key="sis_hemato_hb", placeholder="Hb 8.0 / Plaq 150k")
        c2.selectbox("Coagulopatia", ["Ausente", "Presente (INR/TTPA alt)", "CIVD"], key="sis_hemato_coag")
        c3.selectbox("Sangramento Ativo", ["Não", "Sim (Localizado)", "Sim (Maciço)"], key="sis_hemato_sangra")
        
        st.text_input("Anticoagulação", key="sis_hemato_anticoag", placeholder="Ex: Enoxa 40mg SC (Profilática)")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Hemato", key="sis_hemato_obs")
        with c:
            st.text_input("👉 Conduta Hemato", key="sis_hemato_conduta", placeholder="Ex: Transfundir, Suspender Enoxa...")

    # 🛡️ PELE & DISPOSITIVOS
    with st.container(border=True):
        st.markdown("**🛡️ Pele / Dispositivos / IRAS**")
        c1, c2 = st.columns(2)
        c1.selectbox("Pele / LPP", ["Íntegra", "LPP Estágio 1/2", "LPP Grave"], key="sis_pele_integra")
        c2.selectbox("Dispositivos/Infecção", ["Limpos/Sem sinais", "Sinais flogisticos", "Secreção purulenta"], key="sis_pele_disp")
        
        st.text_input("Necessidade de Retirada / Risco IRAS", key="sis_pele_retirada", placeholder="Avaliar retirada de CVC...")

        # Obs e Conduta
        st.markdown("---")
        o, c = st.columns([1, 1])
        o.text_input("➕ Obs. Pele", key="sis_pele_obs")
        with c:
            st.text_input("👉 Conduta Pele", key="sis_pele_conduta", placeholder="Ex: Curativo, Mudança de decúbito...")