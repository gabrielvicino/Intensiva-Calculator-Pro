from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 12: SISTEMAS
# ==============================================================================
_PROMPT_SISTEMAS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair os dados da Evolução por Sistemas, preenchendo o JSON de forma plana e sequencial.

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ESTRUTURA PLANA: Preencha o JSON sequencialmente por blocos de sistema. Não utilize arrays.
2. REGRA PRIORITÁRIA (AUSÊNCIA ≠ NEGAÇÃO):
   - PRESENTE: Informação está no texto → Extraia o valor.
   - NEGADO: O texto diz explicitamente que não tem (ex: "sem febre") → "Não".
   - AUSENTE: O texto não menciona o parâmetro → Retorne o valor padrão (geralmente "" ou false).
3. PADRÕES DE DADOS:
   - Texto/Geral: ausente = "".
   - Sim/Não: ausente = ""; negado = "Não"; confirmado = "Sim".
   - Inteiros (Escalas/Escore): ausente = null.
   - Booleanos (Escapes): ausente = false.
4. CONDUTAS: Os campos `sis_{s}_conduta` são manuais. A IA deve preencher SEMPRE com `""`.
5. POCUS: Extraia achados de ultrassonografia à beira-leito mencionados em cada sistema específico.
6. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown.

# ENTRADAS
<TEXTO_ALVO>
[O texto da evolução clínica será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- 1. NEUROLÓGICO ---
- sis_neuro_ecg (string): Escala de Coma de Glasgow total.
- sis_neuro_ecg_ao (string): Glasgow - Abertura Ocular.
- sis_neuro_ecg_rv (string): Glasgow - Resposta Verbal.
- sis_neuro_ecg_rm (string): Glasgow - Resposta Motora.
- sis_neuro_ecg_p (string): Glasgow - Reatividade Pupilar.
- sis_neuro_rass (number): Escala de RASS (inteiro -5 a +5). null se ausente.
- sis_neuro_delirium (string): Presença de delirium (Sim/Não/"").
- sis_neuro_delirium_tipo (string): Tipo (Hiperativo/Hipoativo/Misto). "" se delirium ausente.
- sis_neuro_cam_icu (string): Resultado do CAM-ICU (Positivo/Negativo/"").
- sis_neuro_pupilas_tam (string): Tamanho das pupilas (Miótica/Normal/Midríase/"").
- sis_neuro_pupilas_simetria (string): Simetria (Simétricas/Anisocoria/"").
- sis_neuro_pupilas_foto (string): Fotorreatividade (Fotoreagente/Não fotoreagente/"").
- sis_neuro_analgesico_adequado (string): Dor controlada (Sim/Não/"").
- sis_neuro_deficits_focais (string): Descrição literal do déficit focal. "" se ausente.
- sis_neuro_deficits_ausente (string): "Ausente" se texto confirmar ausência de déficits. "" caso contrário.
- sis_neuro_analgesia_1_tipo (string): Tipo de analgesia (Fixa/Se necessário/"").
- sis_neuro_analgesia_1_drogas (string): Fármaco analgésico 1.
- sis_neuro_analgesia_1_dose (string): Dose (ex: "4mg IV").
- sis_neuro_analgesia_1_freq (string): Frequência (ex: "4/4h", "BIC", "ACM").
- sis_neuro_analgesia_2_tipo (string): Tipo de analgesia 2.
- sis_neuro_analgesia_2_drogas (string): Fármaco analgésico 2.
- sis_neuro_analgesia_2_dose (string): Dose 2.
- sis_neuro_analgesia_2_freq (string): Frequência 2.
- sis_neuro_analgesia_3_tipo (string): Tipo de analgesia 3.
- sis_neuro_analgesia_3_drogas (string): Fármaco analgésico 3.
- sis_neuro_analgesia_3_dose (string): Dose 3.
- sis_neuro_analgesia_3_freq (string): Frequência 3.
- sis_neuro_sedacao_meta (string): Alvo de RASS (ex: "RASS -2"). "" se ausente.
- sis_neuro_sedacao_1_drogas (string): Fármaco sedativo 1.
- sis_neuro_sedacao_1_dose (string): Dose sedativo 1.
- sis_neuro_sedacao_2_drogas (string): Fármaco sedativo 2.
- sis_neuro_sedacao_2_dose (string): Dose sedativo 2.
- sis_neuro_sedacao_3_drogas (string): Fármaco sedativo 3.
- sis_neuro_sedacao_3_dose (string): Dose sedativo 3.
- sis_neuro_bloqueador_med (string): Bloqueador neuromuscular (BNM). "" se ausente.
- sis_neuro_bloqueador_dose (string): Dose do BNM.
- sis_neuro_pocus (string): POCUS neuro (ex: diâmetro bainha nervo óptico). "" se ausente.
- sis_neuro_obs (string): Observações neurológicas livres.
- sis_neuro_conduta (string): "".

# --- 2. RESPIRATÓRIO ---
- sis_resp_ausculta (string): Exame Respiratório — descrição do exame físico respiratório (ex: MV+, sem ruído adventício, expansão bilateral).
- sis_resp_modo (string): Tipo de suporte (Ar Ambiente/Oxigenoterapia/VNI/Cateter de Alto Fluxo/Ventilação Mecânica/"").
- sis_resp_modo_vent (string): Modo ventilatório (VCV/PCV/PSV/""). Preencher só se em VM.
- sis_resp_oxigenio_modo (string): Interface O2 (ex: Cateter Nasal, Máscara Venturi). Só se Oxigenoterapia.
- sis_resp_oxigenio_fluxo (string): Fluxo em L/min. Só se Oxigenoterapia.
- sis_resp_pressao (string): Pressão inspiratória ou suporte (ex: "18").
- sis_resp_volume (string): Volume corrente (ex: "480").
- sis_resp_fio2 (string): FiO2 em % (ex: "45").
- sis_resp_peep (string): PEEP (ex: "8").
- sis_resp_freq (string): Frequência respiratória total (ex: "16").
- sis_resp_vent_protetora (string): Ventilação protetora (Sim/Não/"").
- sis_resp_sincronico (string): Paciente sincrônico (Sim/Não/"").
- sis_resp_assincronia (string): Tipo de assincronia (ex: "Double trigger"). "" se sincrônico.
- sis_resp_complacencia (string): Complacência estática.
- sis_resp_resistencia (string): Resistência de vias aéreas.
- sis_resp_dp (string): Driving Pressure.
- sis_resp_plato (string): Pressão de Platô.
- sis_resp_pico (string): Pressão de Pico.
- sis_resp_dreno_1 (string): Localização do dreno 1 (ex: "Pleural D").
- sis_resp_dreno_1_debito (string): Débito/Aspecto do dreno 1 (ex: "180mL/dia").
- sis_resp_dreno_2 (string): Localização do dreno 2.
- sis_resp_dreno_2_debito (string): Débito dreno 2.
- sis_resp_dreno_3 (string): Localização do dreno 3.
- sis_resp_dreno_3_debito (string): Débito dreno 3.
- sis_resp_pocus (string): POCUS pulmonar (Linhas A/B, Consolidação, Derrame). "" se ausente.
- sis_resp_obs (string): Observações respiratórias livres.
- sis_resp_conduta (string): "".

# --- 3. CARDIOVASCULAR ---
- sis_cardio_fc (string): Frequência cardíaca em bpm.
- sis_cardio_cardioscopia (string): Ritmo na cardioscopia (ex: Sinusal, FA, BAVT).
- sis_cardio_pam (string): Pressão arterial média em mmHg.
- sis_cardio_exame_cardio (string): Exame Cardiológico — bulhas, sopros (ex: 2BNRF, não ausculto sopros significativos). "" se ausente.
- sis_cardio_perfusao (string): Perfusão periférica (Normal/Lentificada/Flush/"").
- sis_cardio_tec (string): Tempo de enchimento capilar (ex: "3 seg.").
- sis_cardio_fluido_responsivo (string): Fluido-responsividade (Sim/Não/"").
- sis_cardio_fluido_tolerante (string): Fluido-tolerância (Sim/Não/"").
- sis_cardio_lac_ant5 (string): Lactato 5º mais antigo (mmol/L, evolução cronológica). "" se ausente.
- sis_cardio_lac_ant4 (string): Lactato 4º. "" se ausente.
- sis_cardio_lac_antepen (string): Lactato 3º (anteontem). "" se ausente.
- sis_cardio_lac_ult (string): Lactato 2º (ontem). "" se ausente.
- sis_cardio_lac_hoje (string): Lactato mais recente. "" se ausente.
- sis_cardio_trop_ant5 (string): Troponina 5º medição anterior (ng/L ou unidade descrita). "" se ausente.
- sis_cardio_trop_ant4 (string): Troponina 4º medição. "" se ausente.
- sis_cardio_trop_antepen (string): Troponina anteontem. "" se ausente.
- sis_cardio_trop_ult (string): Troponina ontem. "" se ausente.
- sis_cardio_trop_hoje (string): Troponina atual. "" se ausente.
- sis_cardio_dva_1_med (string): DVA 1 (ex: Noradrenalina).
- sis_cardio_dva_1_dose (string): Dose DVA 1 (ex: "0.12 mcg/kg/min").
- sis_cardio_dva_2_med (string): DVA 2.
- sis_cardio_dva_2_dose (string): Dose DVA 2.
- sis_cardio_dva_3_med (string): DVA 3.
- sis_cardio_dva_3_dose (string): Dose DVA 3.
- sis_cardio_dva_4_med (string): DVA 4.
- sis_cardio_dva_4_dose (string): Dose DVA 4.
- sis_cardio_trop_ant5 (string): Troponina 5º medição anterior (ng/L ou unidade descrita). "" se ausente.
- sis_cardio_trop_ant4 (string): Troponina 4º medição. "" se ausente.
- sis_cardio_trop_antepen (string): Troponina anteontem. "" se ausente.
- sis_cardio_trop_ult (string): Troponina ontem. "" se ausente.
- sis_cardio_trop_hoje (string): Troponina atual. "" se ausente.
- sis_cardio_pocus (string): POCUS cardíaco/VCI (ex: Função ventricular preservada). "" se ausente.
- sis_cardio_obs (string): Observações cardiovasculares livres.
- sis_cardio_conduta (string): "".

# --- 4. RENAL / METABÓLICO / NUTRIÇÃO ---
- sis_renal_diurese (string): Diurese das últimas 24h (ex: "1800mL").
- sis_renal_balanco (string): Balanço hídrico diário com sinal (ex: "+350mL").
- sis_renal_balanco_acum (string): Balanço hídrico acumulado (ex: "+2300mL").
- sis_renal_volemia (string): Status volêmico (Hipovolêmico/Euvolêmico/Hipervolêmico/"").
- sis_renal_cr_ant5 (string): Creatinina 5º dia anterior (mais antigo). "" se ausente.
- sis_renal_cr_ant4 (string): Creatinina 4º dia anterior. "" se ausente.
- sis_renal_cr_antepen (string): Creatinina anteontem. "" se ausente.
- sis_renal_cr_ult (string): Creatinina ontem. "" se ausente.
- sis_renal_cr_hoje (string): Creatinina atual. "" se ausente.
- sis_renal_ur_ant5 (string): Ureia 5º dia anterior. "" se ausente.
- sis_renal_ur_ant4 (string): Ureia 4º dia anterior. "" se ausente.
- sis_renal_ur_antepen (string): Ureia anteontem. "" se ausente.
- sis_renal_ur_ult (string): Ureia ontem. "" se ausente.
- sis_renal_ur_hoje (string): Ureia atual. "" se ausente.
- sis_renal_diu_ant5 (string): Diurese 5º dia (evolução). "" se ausente.
- sis_renal_diu_ant4 (string): Diurese 4º dia. "" se ausente.
- sis_renal_diu_antepen (string): Diurese anteontem. "" se ausente.
- sis_renal_diu_ult (string): Diurese ontem. "" se ausente.
- sis_renal_diu_hoje (string): Diurese hoje (valor numérico em mL, ex: "1800"). "" se ausente.
- sis_renal_bh_ant5 (string): Balanço hídrico 5º dia. "" se ausente.
- sis_renal_bh_ant4 (string): Balanço hídrico 4º dia. "" se ausente.
- sis_renal_bh_antepen (string): Balanço hídrico anteontem. "" se ausente.
- sis_renal_bh_ult (string): Balanço hídrico ontem. "" se ausente.
- sis_renal_bh_hoje (string): Balanço hídrico hoje (ex: "+350"). "" se ausente.
- sis_renal_na_ant5 (string): Sódio 5º dia (mmol/L numérico). "" se ausente.
- sis_renal_na_ant4 (string): Sódio 4º dia. "" se ausente.
- sis_renal_na_antepen (string): Sódio anteontem. "" se ausente.
- sis_renal_na_ult (string): Sódio ontem. "" se ausente.
- sis_renal_na_hoje (string): Sódio hoje. "" se ausente.
- sis_renal_k_ant5 (string): Potássio 5º dia. "" se ausente.
- sis_renal_k_ant4 (string): Potássio 4º dia. "" se ausente.
- sis_renal_k_antepen (string): Potássio anteontem. "" se ausente.
- sis_renal_k_ult (string): Potássio ontem. "" se ausente.
- sis_renal_k_hoje (string): Potássio hoje. "" se ausente.
- sis_renal_mg_ant5 (string): Magnésio 5º dia. "" se ausente.
- sis_renal_mg_ant4 (string): Magnésio 4º dia. "" se ausente.
- sis_renal_mg_antepen (string): Magnésio anteontem. "" se ausente.
- sis_renal_mg_ult (string): Magnésio ontem. "" se ausente.
- sis_renal_mg_hoje (string): Magnésio hoje. "" se ausente.
- sis_renal_fos_ant5 (string): Fósforo 5º dia. "" se ausente.
- sis_renal_fos_ant4 (string): Fósforo 4º dia. "" se ausente.
- sis_renal_fos_antepen (string): Fósforo anteontem. "" se ausente.
- sis_renal_fos_ult (string): Fósforo ontem. "" se ausente.
- sis_renal_fos_hoje (string): Fósforo hoje. "" se ausente.
- sis_renal_cai_ant5 (string): Cálcio ionizado 5º dia. "" se ausente.
- sis_renal_cai_ant4 (string): Cálcio ionizado 4º dia. "" se ausente.
- sis_renal_cai_antepen (string): Cálcio ionizado anteontem. "" se ausente.
- sis_renal_cai_ult (string): Cálcio ionizado ontem. "" se ausente.
- sis_renal_cai_hoje (string): Cálcio ionizado hoje. "" se ausente.
- sis_renal_trs (string): Em hemodiálise/TRS (Sim/Não/"").
- sis_renal_trs_via (string): Acesso da TRS (ex: "Cateter femoral D").
- sis_renal_trs_ultima (string): Data/Hora da última sessão.
- sis_renal_trs_proxima (string): Programação da próxima sessão.
- sis_renal_pocus (string): POCUS renal/bexiga. "" se ausente.
- sis_renal_obs (string): Observações renais livres.
- sis_renal_conduta (string): "".
- sis_metab_obs (string): Observações metabólicas (glicemia, ácido-base, eletrólitos).
- sis_metab_pocus (string): POCUS metabólico. "" se ausente.
- sis_metab_conduta (string): "".
- sis_nutri_obs (string): Observações nutricionais (tipo de dieta, tolerância, meta calórica).
- sis_nutri_pocus (string): POCUS gástrico (ex: antro). "" se ausente.
- sis_nutri_conduta (string): "".

# --- 5. INFECCIOSO ---
- sis_infec_febre (string): Presença de febre (Sim/Não/"").
- sis_infec_febre_vezes (string): Quantos picos febrís nas últimas 24h (ex: "2").
- sis_infec_febre_ultima (string): Horário/Data do último pico.
- sis_infec_atb (string): Em uso de antimicrobiano (Sim/Não/"").
- sis_infec_atb_guiado (string): ATB guiado por cultura (Sim/Não/"").
- sis_infec_atb_1 (string): Nome do ATB 1.
- sis_infec_atb_2 (string): Nome do ATB 2.
- sis_infec_atb_3 (string): Nome do ATB 3.
- sis_infec_culturas_and (string): Culturas em andamento (Sim/Não/"").
- sis_infec_cult_1_sitio (string): Sítio da cultura 1 (ex: "Hemocultura central").
- sis_infec_cult_1_data (string): Data da coleta 1.
- sis_infec_cult_2_sitio (string): Sítio da cultura 2.
- sis_infec_cult_2_data (string): Data da coleta 2.
- sis_infec_cult_3_sitio (string): Sítio da cultura 3.
- sis_infec_cult_3_data (string): Data da coleta 3.
- sis_infec_cult_4_sitio (string): Sítio da cultura 4.
- sis_infec_cult_4_data (string): Data da coleta 4.
- sis_infec_pcr_ant5 (string): PCR 5º coleta anterior. "" se ausente.
- sis_infec_pcr_ant4 (string): PCR 4º coleta. "" se ausente.
- sis_infec_pcr_antepen (string): PCR antepenúltima. "" se ausente.
- sis_infec_pcr_ult (string): PCR anterior. "" se ausente.
- sis_infec_pcr_hoje (string): PCR atual. "" se ausente.
- sis_infec_leuc_ant5 (string): Leucócitos 5º dia. "" se ausente.
- sis_infec_leuc_ant4 (string): Leucócitos 4º dia. "" se ausente.
- sis_infec_leuc_antepen (string): Leucócitos anteontem. "" se ausente.
- sis_infec_leuc_ult (string): Leucócitos ontem. "" se ausente.
- sis_infec_leuc_hoje (string): Leucócitos atual. "" se ausente.
- sis_infec_vhs_ant5 (string): VHS 5º dia (mm/h). "" se ausente.
- sis_infec_vhs_ant4 (string): VHS 4º dia. "" se ausente.
- sis_infec_vhs_antepen (string): VHS anteontem. "" se ausente.
- sis_infec_vhs_ult (string): VHS ontem. "" se ausente.
- sis_infec_vhs_hoje (string): VHS atual. "" se ausente.
- sis_infec_isolamento (string): Em isolamento (Sim/Não/"").
- sis_infec_isolamento_tipo (string): Tipo (Contato/Aerossol/Gotícula/Reverso/"").
- sis_infec_isolamento_motivo (string): Germe ou suspeita (ex: "K. pneumoniae KPC+").
- sis_infec_patogenos (string): Lista de germes isolados — texto literal.
- sis_infec_pocus (string): POCUS infeccioso (ex: pesquisa de coleções). "" se ausente.
- sis_infec_obs (string): Observações infecciosas livres.
- sis_infec_conduta (string): "".

# --- 6. EXAME ABDOMINAL ---
- sis_gastro_exame_fisico (string): Exame Abdominal — descrição literal (ex: Típico, RHA presente, indolor a palpação, sem sinais de peritonite).
- sis_gastro_ictericia_presente (string): Icterícia (Presente/Ausente/"").
- sis_gastro_ictericia_cruzes (string): Intensidade da icterícia (ex: "1", "2", "3", "4"). "" se ausente.
- sis_gastro_dieta_oral (string): Tipo de dieta oral (ex: "Pastosa", "Completa"). "" se ausente.
- sis_gastro_dieta_enteral (string): Fórmula enteral (ex: "Peptamen", "Fresubin"). "" se ausente.
- sis_gastro_dieta_enteral_vol (string): Volume/kcal enteral (ex: "1200 kcal"). "" se ausente.
- sis_gastro_dieta_parenteral (string): Tipo NPT (ex: "NPT", "NPP"). "" se ausente.
- sis_gastro_dieta_parenteral_vol (string): Volume/kcal NPT. "" se ausente.
- sis_gastro_meta_calorica (string): Meta calórica em kcal — somente número (ex: "1800"). "" se ausente.
- sis_gastro_na_meta (string): Atingindo meta calórica (Sim/Não/"").
- sis_gastro_ingestao_quanto (string): Ingestão real descrita (ex: "800 kcal").
- sis_gastro_escape_glicemico (string): Escape glicêmico (Sim/Não/"").
- sis_gastro_escape_vezes (string): Quantos episódios de escape.
- sis_gastro_escape_manha (boolean): Escape de manhã (true/false).
- sis_gastro_escape_tarde (boolean): Escape à tarde (true/false).
- sis_gastro_escape_noite (boolean): Escape à noite (true/false).
- sis_gastro_insulino (string): Em insulinoterapia (Sim/Não/"").
- sis_gastro_insulino_dose_manha (string): Dose de insulina manhã (ex: "10 Un").
- sis_gastro_insulino_dose_tarde (string): Dose de insulina tarde.
- sis_gastro_insulino_dose_noite (string): Dose de insulina noite.
- sis_gastro_evacuacao (string): Evacuação presente (Sim/Não/"").
- sis_gastro_evacuacao_data (string): Data da última evacuação.
- sis_gastro_evacuacao_laxativo (string): Laxativo em uso (ex: "Lactulose 10mL 8/8h"). "" se ausente.
- sis_gastro_tgo_ant5 (string): TGO 5º dia (U/L). "" se ausente.
- sis_gastro_tgo_ant4 (string): TGO 4º dia. "" se ausente.
- sis_gastro_tgo_antepen (string): TGO anteontem. "" se ausente.
- sis_gastro_tgo_ult (string): TGO ontem. "" se ausente.
- sis_gastro_tgo_hoje (string): TGO hoje. "" se ausente.
- sis_gastro_tgp_ant5 (string): TGP 5º dia. "" se ausente.
- sis_gastro_tgp_ant4 (string): TGP 4º dia. "" se ausente.
- sis_gastro_tgp_antepen (string): TGP anteontem. "" se ausente.
- sis_gastro_tgp_ult (string): TGP ontem. "" se ausente.
- sis_gastro_tgp_hoje (string): TGP hoje. "" se ausente.
- sis_gastro_fal_ant5 (string): FAL 5º dia. "" se ausente.
- sis_gastro_fal_ant4 (string): FAL 4º dia. "" se ausente.
- sis_gastro_fal_antepen (string): FAL anteontem. "" se ausente.
- sis_gastro_fal_ult (string): FAL ontem. "" se ausente.
- sis_gastro_fal_hoje (string): FAL hoje. "" se ausente.
- sis_gastro_ggt_ant5 (string): GGT 5º dia. "" se ausente.
- sis_gastro_ggt_ant4 (string): GGT 4º dia. "" se ausente.
- sis_gastro_ggt_antepen (string): GGT anteontem. "" se ausente.
- sis_gastro_ggt_ult (string): GGT ontem. "" se ausente.
- sis_gastro_ggt_hoje (string): GGT hoje. "" se ausente.
- sis_gastro_bt_ant5 (string): Bilirrubina Total 5º dia. "" se ausente.
- sis_gastro_bt_ant4 (string): BT 4º dia. "" se ausente.
- sis_gastro_bt_antepen (string): BT anteontem. "" se ausente.
- sis_gastro_bt_ult (string): BT ontem. "" se ausente.
- sis_gastro_bt_hoje (string): BT hoje. "" se ausente.
- sis_gastro_pocus (string): POCUS abdome (ex: Ascite leve, POCUS gástrico). "" se ausente.
- sis_gastro_obs (string): Observações gastrointestinais livres.
- sis_gastro_conduta (string): "".

# --- 7. HEMATOLÓGICO ---
- sis_hemato_anticoag (string): Em anticoagulação (Sim/Não/"").
- sis_hemato_anticoag_tipo (string): Profilática ou Plena. "" se ausente.
- sis_hemato_anticoag_motivo (string): Indicação em siglas maiúsculas (ex: "TEP", "TVP", "FA"). "" se ausente.
- sis_hemato_sangramento (string): Sangramento ativo (Sim/Não/"").
- sis_hemato_sangramento_via (string): Sítio do sangramento (ex: "Hematêmese", "Digestiva alta"). "" se ausente.
- sis_hemato_sangramento_data (string): Data/hora do episódio. "" se ausente.
- sis_hemato_transf_data (string): Data da última transfusão.
- sis_hemato_transf_1_comp (string): Componente transfundido 1 (ex: "Concentrado de hemácias").
- sis_hemato_transf_1_bolsas (string): Quantidade 1 (ex: "2 bolsas").
- sis_hemato_transf_2_comp (string): Componente 2.
- sis_hemato_transf_2_bolsas (string): Quantidade 2.
- sis_hemato_transf_3_comp (string): Componente 3.
- sis_hemato_transf_3_bolsas (string): Quantidade 3.
- sis_hemato_hb_ant5 (string): Hb 5º dia. "" se ausente.
- sis_hemato_hb_ant4 (string): Hb 4º dia. "" se ausente.
- sis_hemato_hb_antepen (string): Hb anteontem. "" se ausente.
- sis_hemato_hb_ult (string): Hb ontem. "" se ausente.
- sis_hemato_hb_hoje (string): Hb atual. "" se ausente.
- sis_hemato_plaq_ant5 (string): Plaquetas 5º dia. "" se ausente.
- sis_hemato_plaq_ant4 (string): Plaquetas 4º dia. "" se ausente.
- sis_hemato_plaq_antepen (string): Plaquetas anteontem. "" se ausente.
- sis_hemato_plaq_ult (string): Plaquetas ontem. "" se ausente.
- sis_hemato_plaq_hoje (string): Plaquetas atual. "" se ausente.
- sis_hemato_inr_ant5 (string): INR 5º dia. "" se ausente.
- sis_hemato_inr_ant4 (string): INR 4º dia. "" se ausente.
- sis_hemato_inr_antepen (string): INR anteontem. "" se ausente.
- sis_hemato_inr_ult (string): INR ontem. "" se ausente.
- sis_hemato_inr_hoje (string): INR atual. "" se ausente.
- sis_hemato_ttpa_ant5 (string): TTPa 5º dia — extrair valor do parêntese se presente (ex: "39,6s (1,41)" → "1,41"). "" se ausente.
- sis_hemato_ttpa_ant4 (string): TTPa 4º dia. "" se ausente.
- sis_hemato_ttpa_antepen (string): TTPa anteontem. "" se ausente.
- sis_hemato_ttpa_ult (string): TTPa ontem. "" se ausente.
- sis_hemato_ttpa_hoje (string): TTPa atual. "" se ausente.
- sis_hemato_pocus (string): POCUS hematológico (ex: TVP, Derrame pleural). "" se ausente.
- sis_hemato_obs (string): Observações hematológicas livres.
- sis_hemato_conduta (string): "".

# --- 8. PELE / MUSCULOESQUELÉTICO ---
- sis_pele_edema (string): Presença de edema (Presente/Ausente/"").
- sis_pele_edema_cruzes (string): Intensidade do edema em cruzes (ex: "1", "2", "3"). "" se ausente.
- sis_pele_lpp (string): Lesão por Pressão (Sim/Não/"").
- sis_pele_lpp_local_1 (string): Local da lesão 1 (ex: "Sacro").
- sis_pele_lpp_grau_1 (string): Grau da lesão 1 (ex: "Grau II").
- sis_pele_lpp_local_2 (string): Local da lesão 2.
- sis_pele_lpp_grau_2 (string): Grau da lesão 2.
- sis_pele_lpp_local_3 (string): Local da lesão 3.
- sis_pele_lpp_grau_3 (string): Grau da lesão 3.
- sis_pele_polineuropatia (string): Polineuropatia do doente crítico (Sim/Não/"").
- sis_pele_cpk_ant5 (string): CPK 5º dia (U/L). "" se ausente.
- sis_pele_cpk_ant4 (string): CPK 4º dia. "" se ausente.
- sis_pele_cpk_antepen (string): CPK anteontem. "" se ausente.
- sis_pele_cpk_ult (string): CPK ontem. "" se ausente.
- sis_pele_cpk_hoje (string): CPK atual. "" se ausente.
- sis_pele_pocus (string): POCUS tecidos moles. "" se ausente.
- sis_pele_obs (string): Observações de feridas/curativos livres.
- sis_pele_conduta (string): "".
</VARIAVEIS>

# ESTRUTURA DE SAÍDA OBRIGATÓRIA
Retorne EXATAMENTE este JSON com todos os campos. Campos ausentes = "". Inteiros ausentes = null. Booleanos ausentes = false.

{
  "sis_neuro_ecg": "", "sis_neuro_ecg_ao": "", "sis_neuro_ecg_rv": "", "sis_neuro_ecg_rm": "",
  "sis_neuro_ecg_p": "", "sis_neuro_rass": null,
  "sis_neuro_delirium": "", "sis_neuro_delirium_tipo": "", "sis_neuro_cam_icu": "",
  "sis_neuro_pupilas_tam": "", "sis_neuro_pupilas_simetria": "", "sis_neuro_pupilas_foto": "",
  "sis_neuro_analgesico_adequado": "", "sis_neuro_deficits_focais": "", "sis_neuro_deficits_ausente": "",
  "sis_neuro_analgesia_1_tipo": "", "sis_neuro_analgesia_1_drogas": "", "sis_neuro_analgesia_1_dose": "", "sis_neuro_analgesia_1_freq": "",
  "sis_neuro_analgesia_2_tipo": "", "sis_neuro_analgesia_2_drogas": "", "sis_neuro_analgesia_2_dose": "", "sis_neuro_analgesia_2_freq": "",
  "sis_neuro_analgesia_3_tipo": "", "sis_neuro_analgesia_3_drogas": "", "sis_neuro_analgesia_3_dose": "", "sis_neuro_analgesia_3_freq": "",
  "sis_neuro_sedacao_meta": "",
  "sis_neuro_sedacao_1_drogas": "", "sis_neuro_sedacao_1_dose": "",
  "sis_neuro_sedacao_2_drogas": "", "sis_neuro_sedacao_2_dose": "",
  "sis_neuro_sedacao_3_drogas": "", "sis_neuro_sedacao_3_dose": "",
  "sis_neuro_bloqueador_med": "", "sis_neuro_bloqueador_dose": "",
  "sis_neuro_pocus": "", "sis_neuro_obs": "", "sis_neuro_conduta": "",

  "sis_resp_ausculta": "", "sis_resp_modo": "", "sis_resp_modo_vent": "",
  "sis_resp_oxigenio_modo": "", "sis_resp_oxigenio_fluxo": "",
  "sis_resp_pressao": "", "sis_resp_volume": "", "sis_resp_fio2": "", "sis_resp_peep": "", "sis_resp_freq": "",
  "sis_resp_vent_protetora": "", "sis_resp_sincronico": "", "sis_resp_assincronia": "",
  "sis_resp_complacencia": "", "sis_resp_resistencia": "", "sis_resp_dp": "", "sis_resp_plato": "", "sis_resp_pico": "",
  "sis_resp_dreno_1": "", "sis_resp_dreno_1_debito": "",
  "sis_resp_dreno_2": "", "sis_resp_dreno_2_debito": "",
  "sis_resp_dreno_3": "", "sis_resp_dreno_3_debito": "",
  "sis_resp_pocus": "", "sis_resp_obs": "", "sis_resp_conduta": "",

  "sis_cardio_fc": "", "sis_cardio_cardioscopia": "", "sis_cardio_pam": "",
  "sis_cardio_exame_cardio": "", "sis_cardio_perfusao": "", "sis_cardio_tec": "",   "sis_cardio_fluido_responsivo": "", "sis_cardio_fluido_tolerante": "",
  "sis_cardio_lac_ant5": "", "sis_cardio_lac_ant4": "", "sis_cardio_lac_antepen": "", "sis_cardio_lac_ult": "", "sis_cardio_lac_hoje": "",
  "sis_cardio_trop_ant5": "", "sis_cardio_trop_ant4": "", "sis_cardio_trop_antepen": "", "sis_cardio_trop_ult": "", "sis_cardio_trop_hoje": "",
  "sis_cardio_dva_1_med": "", "sis_cardio_dva_1_dose": "",
  "sis_cardio_dva_2_med": "", "sis_cardio_dva_2_dose": "",
  "sis_cardio_dva_3_med": "", "sis_cardio_dva_3_dose": "",
  "sis_cardio_dva_4_med": "", "sis_cardio_dva_4_dose": "",
  "sis_cardio_pocus": "", "sis_cardio_obs": "", "sis_cardio_conduta": "",

  "sis_renal_diurese": "", "sis_renal_balanco": "", "sis_renal_balanco_acum": "", "sis_renal_volemia": "",
  "sis_renal_cr_ant5": "", "sis_renal_cr_ant4": "", "sis_renal_cr_antepen": "", "sis_renal_cr_ult": "", "sis_renal_cr_hoje": "",
  "sis_renal_ur_ant5": "", "sis_renal_ur_ant4": "", "sis_renal_ur_antepen": "", "sis_renal_ur_ult": "", "sis_renal_ur_hoje": "",
  "sis_renal_diu_ant5": "", "sis_renal_diu_ant4": "", "sis_renal_diu_antepen": "", "sis_renal_diu_ult": "", "sis_renal_diu_hoje": "",
  "sis_renal_bh_ant5": "", "sis_renal_bh_ant4": "", "sis_renal_bh_antepen": "", "sis_renal_bh_ult": "", "sis_renal_bh_hoje": "",
  "sis_renal_na_ant5": "", "sis_renal_na_ant4": "", "sis_renal_na_antepen": "", "sis_renal_na_ult": "", "sis_renal_na_hoje": "",
  "sis_renal_k_ant5": "", "sis_renal_k_ant4": "", "sis_renal_k_antepen": "", "sis_renal_k_ult": "", "sis_renal_k_hoje": "",
  "sis_renal_mg_ant5": "", "sis_renal_mg_ant4": "", "sis_renal_mg_antepen": "", "sis_renal_mg_ult": "", "sis_renal_mg_hoje": "",
  "sis_renal_fos_ant5": "", "sis_renal_fos_ant4": "", "sis_renal_fos_antepen": "", "sis_renal_fos_ult": "", "sis_renal_fos_hoje": "",
  "sis_renal_cai_ant5": "", "sis_renal_cai_ant4": "", "sis_renal_cai_antepen": "", "sis_renal_cai_ult": "", "sis_renal_cai_hoje": "",
  "sis_renal_trs": "", "sis_renal_trs_via": "", "sis_renal_trs_ultima": "", "sis_renal_trs_proxima": "",
  "sis_renal_pocus": "", "sis_renal_obs": "", "sis_renal_conduta": "",
  "sis_metab_obs": "", "sis_metab_pocus": "", "sis_metab_conduta": "",
  "sis_nutri_obs": "", "sis_nutri_pocus": "", "sis_nutri_conduta": "",

  "sis_infec_febre": "", "sis_infec_febre_vezes": "", "sis_infec_febre_ultima": "",
  "sis_infec_atb": "", "sis_infec_atb_guiado": "",
  "sis_infec_atb_1": "", "sis_infec_atb_2": "", "sis_infec_atb_3": "",
  "sis_infec_culturas_and": "",
  "sis_infec_cult_1_sitio": "", "sis_infec_cult_1_data": "",
  "sis_infec_cult_2_sitio": "", "sis_infec_cult_2_data": "",
  "sis_infec_cult_3_sitio": "", "sis_infec_cult_3_data": "",
  "sis_infec_cult_4_sitio": "", "sis_infec_cult_4_data": "",
  "sis_infec_pcr_ant5": "", "sis_infec_pcr_ant4": "", "sis_infec_pcr_antepen": "", "sis_infec_pcr_ult": "", "sis_infec_pcr_hoje": "",
  "sis_infec_leuc_ant5": "", "sis_infec_leuc_ant4": "", "sis_infec_leuc_antepen": "", "sis_infec_leuc_ult": "", "sis_infec_leuc_hoje": "",
  "sis_infec_vhs_ant5": "", "sis_infec_vhs_ant4": "", "sis_infec_vhs_antepen": "", "sis_infec_vhs_ult": "", "sis_infec_vhs_hoje": "",
  "sis_infec_isolamento": "", "sis_infec_isolamento_tipo": "", "sis_infec_isolamento_motivo": "",
  "sis_infec_patogenos": "", "sis_infec_pocus": "", "sis_infec_obs": "", "sis_infec_conduta": "",

  "sis_gastro_exame_fisico": "", "sis_gastro_ictericia_presente": "", "sis_gastro_ictericia_cruzes": "",
  "sis_gastro_dieta_oral": "", "sis_gastro_dieta_enteral": "", "sis_gastro_dieta_enteral_vol": "",
  "sis_gastro_dieta_parenteral": "", "sis_gastro_dieta_parenteral_vol": "", "sis_gastro_meta_calorica": "",
  "sis_gastro_na_meta": "", "sis_gastro_ingestao_quanto": "",
  "sis_gastro_escape_glicemico": "", "sis_gastro_escape_vezes": "",
  "sis_gastro_escape_manha": false, "sis_gastro_escape_tarde": false, "sis_gastro_escape_noite": false,
  "sis_gastro_insulino": "",
  "sis_gastro_insulino_dose_manha": "", "sis_gastro_insulino_dose_tarde": "", "sis_gastro_insulino_dose_noite": "",
  "sis_gastro_evacuacao": "", "sis_gastro_evacuacao_data": "", "sis_gastro_evacuacao_laxativo": "",
  "sis_gastro_tgo_ant5": "", "sis_gastro_tgo_ant4": "", "sis_gastro_tgo_antepen": "", "sis_gastro_tgo_ult": "", "sis_gastro_tgo_hoje": "",
  "sis_gastro_tgp_ant5": "", "sis_gastro_tgp_ant4": "", "sis_gastro_tgp_antepen": "", "sis_gastro_tgp_ult": "", "sis_gastro_tgp_hoje": "",
  "sis_gastro_fal_ant5": "", "sis_gastro_fal_ant4": "", "sis_gastro_fal_antepen": "", "sis_gastro_fal_ult": "", "sis_gastro_fal_hoje": "",
  "sis_gastro_ggt_ant5": "", "sis_gastro_ggt_ant4": "", "sis_gastro_ggt_antepen": "", "sis_gastro_ggt_ult": "", "sis_gastro_ggt_hoje": "",
  "sis_gastro_bt_ant5": "", "sis_gastro_bt_ant4": "", "sis_gastro_bt_antepen": "", "sis_gastro_bt_ult": "", "sis_gastro_bt_hoje": "",
  "sis_gastro_pocus": "", "sis_gastro_obs": "", "sis_gastro_conduta": "",

  "sis_hemato_anticoag": "", "sis_hemato_anticoag_tipo": "", "sis_hemato_anticoag_motivo": "",
  "sis_hemato_sangramento": "", "sis_hemato_sangramento_via": "", "sis_hemato_sangramento_data": "",
  "sis_hemato_transf_data": "",
  "sis_hemato_transf_1_comp": "", "sis_hemato_transf_1_bolsas": "",
  "sis_hemato_transf_2_comp": "", "sis_hemato_transf_2_bolsas": "",
  "sis_hemato_transf_3_comp": "", "sis_hemato_transf_3_bolsas": "",
  "sis_hemato_hb_ant5": "", "sis_hemato_hb_ant4": "", "sis_hemato_hb_antepen": "", "sis_hemato_hb_ult": "", "sis_hemato_hb_hoje": "",
  "sis_hemato_plaq_ant5": "", "sis_hemato_plaq_ant4": "", "sis_hemato_plaq_antepen": "", "sis_hemato_plaq_ult": "", "sis_hemato_plaq_hoje": "",
  "sis_hemato_inr_ant5": "", "sis_hemato_inr_ant4": "", "sis_hemato_inr_antepen": "", "sis_hemato_inr_ult": "", "sis_hemato_inr_hoje": "",
  "sis_hemato_ttpa_ant5": "", "sis_hemato_ttpa_ant4": "", "sis_hemato_ttpa_antepen": "", "sis_hemato_ttpa_ult": "", "sis_hemato_ttpa_hoje": "",
  "sis_hemato_pocus": "", "sis_hemato_obs": "", "sis_hemato_conduta": "",

  "sis_pele_edema": "", "sis_pele_edema_cruzes": "",
  "sis_pele_lpp": "",
  "sis_pele_lpp_local_1": "", "sis_pele_lpp_grau_1": "",
  "sis_pele_lpp_local_2": "", "sis_pele_lpp_grau_2": "",
  "sis_pele_lpp_local_3": "", "sis_pele_lpp_grau_3": "",
  "sis_pele_polineuropatia": "",
  "sis_pele_cpk_ant5": "", "sis_pele_cpk_ant4": "", "sis_pele_cpk_antepen": "", "sis_pele_cpk_ult": "", "sis_pele_cpk_hoje": "",
  "sis_pele_pocus": "", "sis_pele_obs": "", "sis_pele_conduta": ""
}

# EXEMPLO DE SAÍDA PERFEITA (paciente intubada, séptica, em VM, em vasopressor)
{
  "sis_neuro_ecg": "10", "sis_neuro_ecg_ao": "3", "sis_neuro_ecg_rv": "2", "sis_neuro_ecg_rm": "5",
  "sis_neuro_ecg_p": "14", "sis_neuro_rass": -2,
  "sis_neuro_delirium": "Não", "sis_neuro_delirium_tipo": "", "sis_neuro_cam_icu": "Negativo",
  "sis_neuro_pupilas_tam": "Normal", "sis_neuro_pupilas_simetria": "Simétricas", "sis_neuro_pupilas_foto": "Fotoreagente",
  "sis_neuro_analgesico_adequado": "Sim", "sis_neuro_deficits_focais": "", "sis_neuro_deficits_ausente": "Ausente",
  "sis_neuro_analgesia_1_tipo": "Fixa", "sis_neuro_analgesia_1_drogas": "Fentanil", "sis_neuro_analgesia_1_dose": "25 mcg/h", "sis_neuro_analgesia_1_freq": "BIC",
  "sis_neuro_analgesia_2_tipo": "", "sis_neuro_analgesia_2_drogas": "", "sis_neuro_analgesia_2_dose": "", "sis_neuro_analgesia_2_freq": "",
  "sis_neuro_analgesia_3_tipo": "", "sis_neuro_analgesia_3_drogas": "", "sis_neuro_analgesia_3_dose": "", "sis_neuro_analgesia_3_freq": "",
  "sis_neuro_sedacao_meta": "RASS -2",
  "sis_neuro_sedacao_1_drogas": "Midazolam", "sis_neuro_sedacao_1_dose": "5 mg/h BIC",
  "sis_neuro_sedacao_2_drogas": "", "sis_neuro_sedacao_2_dose": "",
  "sis_neuro_sedacao_3_drogas": "", "sis_neuro_sedacao_3_dose": "",
  "sis_neuro_bloqueador_med": "", "sis_neuro_bloqueador_dose": "",
  "sis_neuro_pocus": "", "sis_neuro_obs": "Paciente com resposta a comandos simples durante janela de sedação às 8h.", "sis_neuro_conduta": "",

  "sis_resp_ausculta": "MV+ reduzido em bases, subcrepitantes em base D, expansão bilateral assimétrica",
  "sis_resp_modo": "Ventilação Mecânica",
  "sis_resp_modo_vent": "PCV",
  "sis_resp_oxigenio_modo": "", "sis_resp_oxigenio_fluxo": "",
  "sis_resp_pressao": "18", "sis_resp_volume": "460", "sis_resp_fio2": "55", "sis_resp_peep": "8", "sis_resp_freq": "18",
  "sis_resp_vent_protetora": "Sim", "sis_resp_sincronico": "Sim", "sis_resp_assincronia": "",
  "sis_resp_complacencia": "38", "sis_resp_resistencia": "12", "sis_resp_dp": "10", "sis_resp_plato": "26", "sis_resp_pico": "30",
  "sis_resp_dreno_1": "", "sis_resp_dreno_1_debito": "",
  "sis_resp_dreno_2": "", "sis_resp_dreno_2_debito": "",
  "sis_resp_dreno_3": "", "sis_resp_dreno_3_debito": "",
  "sis_resp_pocus": "Padrão B bilateral em bases. Consolidação em LID com broncograma aéreo.", "sis_resp_obs": "P/F: 145. SDRA leve.", "sis_resp_conduta": "",

  "sis_cardio_fc": "98", "sis_cardio_cardioscopia": "Sinusal", "sis_cardio_pam": "72",
  "sis_cardio_exame_cardio": "2BNRF, sem sopros audíveis",
  "sis_cardio_perfusao": "Lentificada", "sis_cardio_tec": "4 seg.",
  "sis_cardio_fluido_responsivo": "Não", "sis_cardio_fluido_tolerante": "Sim",
  "sis_cardio_lac_ant5": "", "sis_cardio_lac_ant4": "7.1", "sis_cardio_lac_antepen": "5.2", "sis_cardio_lac_ult": "3.8", "sis_cardio_lac_hoje": "2.9",
  "sis_cardio_trop_ant5": "", "sis_cardio_trop_ant4": "", "sis_cardio_trop_antepen": "", "sis_cardio_trop_ult": "850", "sis_cardio_trop_hoje": "1240",
  "sis_cardio_dva_1_med": "Noradrenalina", "sis_cardio_dva_1_dose": "0.18 mcg/kg/min",
  "sis_cardio_dva_2_med": "Vasopressina", "sis_cardio_dva_2_dose": "0.03 U/min",
  "sis_cardio_dva_3_med": "", "sis_cardio_dva_3_dose": "",
  "sis_cardio_dva_4_med": "", "sis_cardio_dva_4_dose": "",
  "sis_cardio_pocus": "FVE preservada, VCI colabável > 50%, SPAP estimada 42 mmHg.", "sis_cardio_obs": "Hiperlactatemia com tendência de queda. Reduzindo vasopressina.", "sis_cardio_conduta": "",

  "sis_renal_diurese": "820mL", "sis_renal_balanco": "+620mL", "sis_renal_balanco_acum": "+4200mL", "sis_renal_volemia": "Hipervolêmico",
  "sis_renal_cr_ant5": "", "sis_renal_cr_ant4": "1.8", "sis_renal_cr_antepen": "2.2", "sis_renal_cr_ult": "3.1", "sis_renal_cr_hoje": "3.4",
  "sis_renal_ur_ant5": "", "sis_renal_ur_ant4": "82", "sis_renal_ur_antepen": "98", "sis_renal_ur_ult": "128", "sis_renal_ur_hoje": "142",
  "sis_renal_diu_ant5": "", "sis_renal_diu_ant4": "", "sis_renal_diu_antepen": "950", "sis_renal_diu_ult": "780", "sis_renal_diu_hoje": "820",
  "sis_renal_bh_ant5": "", "sis_renal_bh_ant4": "", "sis_renal_bh_antepen": "+480", "sis_renal_bh_ult": "+550", "sis_renal_bh_hoje": "+620",
  "sis_renal_na_ant5": "", "sis_renal_na_ant4": "", "sis_renal_na_antepen": "", "sis_renal_na_ult": "141", "sis_renal_na_hoje": "139",
  "sis_renal_k_ant5": "", "sis_renal_k_ant4": "", "sis_renal_k_antepen": "4.2", "sis_renal_k_ult": "4.6", "sis_renal_k_hoje": "4.8",
  "sis_renal_mg_ant5": "", "sis_renal_mg_ant4": "", "sis_renal_mg_antepen": "1.4", "sis_renal_mg_ult": "1.3", "sis_renal_mg_hoje": "1.2",
  "sis_renal_fos_ant5": "", "sis_renal_fos_ant4": "", "sis_renal_fos_antepen": "4.8", "sis_renal_fos_ult": "5.0", "sis_renal_fos_hoje": "5.2",
  "sis_renal_cai_ant5": "", "sis_renal_cai_ant4": "", "sis_renal_cai_antepen": "1.08", "sis_renal_cai_ult": "1.06", "sis_renal_cai_hoje": "1.04",
  "sis_renal_trs": "Sim", "sis_renal_trs_via": "Cateter femoral D", "sis_renal_trs_ultima": "03/03/2026 22h", "sis_renal_trs_proxima": "Dialítico — sem programação definida",
  "sis_renal_pocus": "Rins aumentados e ecogênicos bilateralmente.", "sis_renal_obs": "LRA KDIGO 2, oligúria. Indicado TRS por hipercalemia e acidose refratária.", "sis_renal_conduta": "",
  "sis_metab_obs": "Acidose metabólica com AG elevado (17.6). Hiperlactatemia em queda. Hipercalemia K 4.8. Hipomagnesemia Mg 1.2.", "sis_metab_pocus": "", "sis_metab_conduta": "",
  "sis_nutri_obs": "TNE via SNE. Peptamen 1.5 kcal/mL a 50 mL/h (1800 kcal/dia). Atingindo meta. Sem resíduo gástrico elevado.", "sis_nutri_pocus": "Antro gástrico vazio.", "sis_nutri_conduta": "",

  "sis_infec_febre": "Sim", "sis_infec_febre_vezes": "2", "sis_infec_febre_ultima": "03/03 23h",
  "sis_infec_atb": "Sim", "sis_infec_atb_guiado": "Sim",
  "sis_infec_atb_1": "Polimixina B", "sis_infec_atb_2": "Ceftazidima-Avibactam", "sis_infec_atb_3": "",
  "sis_infec_culturas_and": "Sim",
  "sis_infec_cult_1_sitio": "Urocultura", "sis_infec_cult_1_data": "23/02/2026",
  "sis_infec_cult_2_sitio": "", "sis_infec_cult_2_data": "",
  "sis_infec_cult_3_sitio": "", "sis_infec_cult_3_data": "",
  "sis_infec_cult_4_sitio": "", "sis_infec_cult_4_data": "",
  "sis_infec_pcr_ant5": "", "sis_infec_pcr_ant4": "398", "sis_infec_pcr_antepen": "312", "sis_infec_pcr_ult": "241", "sis_infec_pcr_hoje": "188",
  "sis_infec_leuc_ant5": "", "sis_infec_leuc_ant4": "32100", "sis_infec_leuc_antepen": "28600", "sis_infec_leuc_ult": "22400", "sis_infec_leuc_hoje": "18200",
  "sis_infec_vhs_ant5": "", "sis_infec_vhs_ant4": "", "sis_infec_vhs_antepen": "", "sis_infec_vhs_ult": "68", "sis_infec_vhs_hoje": "40",
  "sis_infec_isolamento": "Sim", "sis_infec_isolamento_tipo": "Contato", "sis_infec_isolamento_motivo": "K. pneumoniae KPC+",
  "sis_infec_patogenos": "Klebsiella pneumoniae KPC+ (AT 23/02/2026)", "sis_infec_pocus": "", "sis_infec_obs": "Febre persistente, sem novo foco identificado. PCR em queda. Leuco caindo.", "sis_infec_conduta": "",

  "sis_gastro_exame_fisico": "Típico, RHA presente, indolor a palpação, sem sinais de peritonite, inocente",
  "sis_gastro_ictericia_presente": "Presente", "sis_gastro_ictericia_cruzes": "2",
  "sis_gastro_dieta_oral": "", "sis_gastro_dieta_enteral": "Peptamen", "sis_gastro_dieta_enteral_vol": "1800 kcal",
  "sis_gastro_dieta_parenteral": "", "sis_gastro_dieta_parenteral_vol": "", "sis_gastro_meta_calorica": "1800",
  "sis_gastro_na_meta": "Sim", "sis_gastro_ingestao_quanto": "",
  "sis_gastro_escape_glicemico": "Sim", "sis_gastro_escape_vezes": "2",
  "sis_gastro_escape_manha": false, "sis_gastro_escape_tarde": true, "sis_gastro_escape_noite": true,
  "sis_gastro_insulino": "Sim",
  "sis_gastro_insulino_dose_manha": "8 Un", "sis_gastro_insulino_dose_tarde": "6 Un", "sis_gastro_insulino_dose_noite": "6 Un",
  "sis_gastro_evacuacao": "Sim", "sis_gastro_evacuacao_data": "04/03/2026", "sis_gastro_evacuacao_laxativo": "",
  "sis_gastro_tgo_ant5": "", "sis_gastro_tgo_ant4": "", "sis_gastro_tgo_antepen": "82", "sis_gastro_tgo_ult": "94", "sis_gastro_tgo_hoje": "88",
  "sis_gastro_tgp_ant5": "", "sis_gastro_tgp_ant4": "", "sis_gastro_tgp_antepen": "62", "sis_gastro_tgp_ult": "71", "sis_gastro_tgp_hoje": "68",
  "sis_gastro_fal_ant5": "", "sis_gastro_fal_ant4": "", "sis_gastro_fal_antepen": "", "sis_gastro_fal_ult": "", "sis_gastro_fal_hoje": "",
  "sis_gastro_ggt_ant5": "", "sis_gastro_ggt_ant4": "", "sis_gastro_ggt_antepen": "", "sis_gastro_ggt_ult": "", "sis_gastro_ggt_hoje": "",
  "sis_gastro_bt_ant5": "", "sis_gastro_bt_ant4": "1.8", "sis_gastro_bt_antepen": "2.4", "sis_gastro_bt_ult": "3.1", "sis_gastro_bt_hoje": "2.8",
  "sis_gastro_pocus": "", "sis_gastro_obs": "Icterícia 2+. Elevação de bilirrubinas associada a sepse.", "sis_gastro_conduta": "",

  "sis_hemato_anticoag": "Sim", "sis_hemato_anticoag_tipo": "Profilática", "sis_hemato_anticoag_motivo": "TEV",
  "sis_hemato_sangramento": "Não", "sis_hemato_sangramento_via": "", "sis_hemato_sangramento_data": "",
  "sis_hemato_transf_data": "02/03/2026",
  "sis_hemato_transf_1_comp": "Concentrado de Hemácias", "sis_hemato_transf_1_bolsas": "2 bolsas",
  "sis_hemato_transf_2_comp": "", "sis_hemato_transf_2_bolsas": "",
  "sis_hemato_transf_3_comp": "", "sis_hemato_transf_3_bolsas": "",
  "sis_hemato_hb_ant5": "", "sis_hemato_hb_ant4": "11.4", "sis_hemato_hb_antepen": "10.2", "sis_hemato_hb_ult": "9.1", "sis_hemato_hb_hoje": "8.4",
  "sis_hemato_plaq_ant5": "", "sis_hemato_plaq_ant4": "54000", "sis_hemato_plaq_antepen": "68000", "sis_hemato_plaq_ult": "82000", "sis_hemato_plaq_hoje": "98000",
  "sis_hemato_inr_ant5": "", "sis_hemato_inr_ant4": "", "sis_hemato_inr_antepen": "", "sis_hemato_inr_ult": "1.8", "sis_hemato_inr_hoje": "1.6",
  "sis_hemato_ttpa_ant5": "", "sis_hemato_ttpa_ant4": "", "sis_hemato_ttpa_antepen": "1.54", "sis_hemato_ttpa_ult": "1.41", "sis_hemato_ttpa_hoje": "1.37",
  "sis_hemato_pocus": "", "sis_hemato_obs": "Plaquetas em recuperação pós-nadir séptico.", "sis_hemato_conduta": "",

  "sis_pele_edema": "Presente", "sis_pele_edema_cruzes": "3",
  "sis_pele_lpp": "Sim",
  "sis_pele_lpp_local_1": "Sacro", "sis_pele_lpp_grau_1": "Grau II",
  "sis_pele_lpp_local_2": "", "sis_pele_lpp_grau_2": "",
  "sis_pele_lpp_local_3": "", "sis_pele_lpp_grau_3": "",
  "sis_pele_polineuropatia": "Sim",
  "sis_pele_cpk_ant5": "", "sis_pele_cpk_ant4": "", "sis_pele_cpk_antepen": "", "sis_pele_cpk_ult": "", "sis_pele_cpk_hoje": "",
  "sis_pele_pocus": "", "sis_pele_obs": "LPP sacral Grau II em cicatrização. Mudança de decúbito 2/2h. Colchão piramidal.", "sis_pele_conduta": ""
}"""

def preencher_sistemas(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_SISTEMAS, texto, api_key, provider, modelo)
    r.pop("_erro", None)

    # Campos neurológicos numéricos: inteiros → string para text_input (como FC, PAM)
    for k, default in [("sis_neuro_ecg", 15), ("sis_neuro_ecg_p", 15)]:
        if k in r:
            try: v = int(r[k]) if r[k] not in ("", None) else default
            except: v = default
            r[k] = str(v) if v is not None else ""

    if "sis_neuro_rass" in r:
        try: v = int(r["sis_neuro_rass"]) if r["sis_neuro_rass"] not in ("", None) else 0
        except: v = 0
        r["sis_neuro_rass"] = str(v)

    for k in ["sis_neuro_ecg_ao", "sis_neuro_ecg_rv", "sis_neuro_ecg_rm"]:
        if k in r:
            try: v = int(r[k]) if r[k] not in ("", None) else None
            except: v = None
            r[k] = str(v) if v is not None else ""

    # Booleanos do escape glicêmico
    for k in ["sis_gastro_escape_manha", "sis_gastro_escape_tarde", "sis_gastro_escape_noite"]:
        if k in r and isinstance(r[k], str):
            r[k] = r[k].lower() in ("true", "sim", "yes", "1")

    # Icterícia: normaliza Sim/Não → Presente/Ausente (compatível com pills)
    if "sis_gastro_ictericia_presente" in r:
        v = r["sis_gastro_ictericia_presente"]
        if isinstance(v, str) and v.strip():
            if v.strip().lower() in ("sim", "yes", "1", "presente"):
                r["sis_gastro_ictericia_presente"] = "Presente"
            elif v.strip().lower() in ("não", "nao", "no", "0", "ausente"):
                r["sis_gastro_ictericia_presente"] = "Ausente"
        else:
            r["sis_gastro_ictericia_presente"] = ""

    # Edema: normaliza Sim/Não → Presente/Ausente (compatível com pills)
    if "sis_pele_edema" in r:
        v = r["sis_pele_edema"]
        if isinstance(v, str) and v.strip():
            if v.strip().lower() in ("sim", "yes", "1", "presente"):
                r["sis_pele_edema"] = "Presente"
            elif v.strip().lower() in ("não", "nao", "no", "0", "ausente"):
                r["sis_pele_edema"] = "Ausente"
        else:
            r["sis_pele_edema"] = ""

    # Déficit focal ausente: converte para "Ausente" ou None (compatível com pills)
    if "sis_neuro_deficits_ausente" in r:
        v = r["sis_neuro_deficits_ausente"]
        if v == "Ausente" or v is True or (isinstance(v, str) and v.strip().lower() in ("true", "sim", "yes", "1", "ausente")):
            r["sis_neuro_deficits_ausente"] = "Ausente"
        else:
            r["sis_neuro_deficits_ausente"] = None

    # Renomeia sis_gastro_evacuacao_laxativo → sis_gastro_laxativo (chave do formulário)
    if "sis_gastro_evacuacao_laxativo" in r:
        r["sis_gastro_laxativo"] = r.pop("sis_gastro_evacuacao_laxativo")

    # Remove campos _show retornados pela IA — esses são controlados pelo usuário e devem ficar False
    for k in list(r.keys()):
        if k.endswith("_show"):
            del r[k]

    return r
