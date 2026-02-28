"""
Script para gerar a saída determinística completa do Bloco 3 (Prontuário Completo)
com TODOS os campos preenchidos.
Execute da raiz: streamlit run scripts/gerar_exemplo_completo.py

O resultado é exibido na tela e salvo em PRONTUARIO_EXEMPLO_COMPLETO.txt (na raiz)
"""
import os
import streamlit as st
from modules.fichas import _campos_base

st.set_page_config(page_title="Exemplo Prontuário Completo", layout="wide")

# Inicializa com defaults
for k, v in _campos_base().items():
    if k not in st.session_state:
        st.session_state[k] = v

# Ordens
st.session_state["hd_ordem"] = list(range(1, 9))
st.session_state["atb_ordem"] = list(range(1, 9))
st.session_state["cult_ordem"] = list(range(1, 9))
st.session_state["disp_ordem"] = list(range(1, 9))
st.session_state["comp_ordem"] = list(range(1, 9))
st.session_state["muc_ordem"] = list(range(1, 21))

# ─── DADOS DE EXEMPLO (TODOS OS CAMPOS) ───────────────────────────────────────
EXEMPLO = {
    # Identificação
    "nome": "Maria Silva Santos",
    "idade": 62,
    "sexo": "Feminino",
    "prontuario": "12345678",
    "leito": "UTI 3 - Leito 12",
    "origem": "Enfermaria 2",
    "equipe": "Dr. João Costa",
    "di_hosp": "15/01/2026",
    "di_uti": "18/01/2026",
    "di_enf": "",
    "saps3": "58",
    "sofa_adm": 8,
    "pps": "60%",
    "mrs": "2",
    "cfs": "6",
    "departamento": "UTI",
    "paliativo": False,
    # Diagnósticos (2 Atuais, 2 Resolvidos)
    "hd_1_nome": "Lesão Renal Aguda",
    "hd_1_class": "KDIGO 3",
    "hd_1_data_inicio": "18/01/2026",
    "hd_1_data_resolvido": "",
    "hd_1_status": "Atual",
    "hd_1_obs": "Em TRS intermitente. Creatinina em queda.",
    "hd_2_nome": "Pneumonia Associada à Ventilação",
    "hd_2_class": "PAV",
    "hd_2_data_inicio": "20/01/2026",
    "hd_2_data_resolvido": "",
    "hd_2_status": "Atual",
    "hd_2_obs": "Melhora radiológica. Desmame em curso.",
    "hd_3_nome": "Sepse",
    "hd_3_class": "Choque séptico",
    "hd_3_data_inicio": "18/01/2026",
    "hd_3_data_resolvido": "25/01/2026",
    "hd_3_status": "Resolvida",
    "hd_3_obs": "Resposta adequada à antibioticoterapia.",
    "hd_4_nome": "Insuficiência Respiratória Aguda",
    "hd_4_class": "SDRA moderada",
    "hd_4_data_inicio": "18/01/2026",
    "hd_4_data_resolvido": "24/01/2026",
    "hd_4_status": "Resolvida",
    "hd_4_obs": "Desmame concluído. Extubada.",
    # Comorbidades
    "cmd_etilismo": "Ausente",
    "cmd_tabagismo": "Presente",
    "cmd_tabagismo_obs": "20 anos-maço",
    "cmd_spa": "Ausente",
    "cmd_1_nome": "Hipertensão Arterial Sistêmica",
    "cmd_1_class": "Grau 2",
    "cmd_2_nome": "Diabetes Mellitus",
    "cmd_2_class": "Tipo 2",
    "cmd_3_nome": "Doença Renal Crônica",
    "cmd_3_class": "Estádio 3b",
    # MUC
    "muc_adesao_global": "Aderente",
    "muc_alergia": "Presente",
    "muc_alergia_obs": "Penicilina - rash",
    "muc_1_nome": "Losartana",
    "muc_1_dose": "50 mg",
    "muc_1_freq": "12/12h",
    "muc_2_nome": "Metformina",
    "muc_2_dose": "850 mg",
    "muc_2_freq": "12/12h",
    # HMPA
    "hmpa_reescrito": "Paciente hipertensa e diabética em uso regular de medicações. Negava sintomas até 15/01, quando iniciou dispneia progressiva. Internada em enfermaria, evoluiu com piora e transferida para UTI em 18/01.",
    # Dispositivos (2 Atuais, 1 Retirado)
    "disp_1_nome": "Cateter Central",
    "disp_1_local": "Subclávia D",
    "disp_1_data_insercao": "18/01/2026",
    "disp_1_data_retirada": "",
    "disp_1_status": "Ativo",
    "disp_2_nome": "Sonda Vesical",
    "disp_2_local": "",
    "disp_2_data_insercao": "18/01/2026",
    "disp_2_data_retirada": "",
    "disp_2_status": "Ativo",
    "disp_3_nome": "Tubo Orotraqueal",
    "disp_3_local": "",
    "disp_3_data_insercao": "18/01/2026",
    "disp_3_data_retirada": "24/01/2026",
    "disp_3_status": "Removido",
    # Culturas (1 Positiva, 1 Andamento, 1 Negativa)
    "cult_1_sitio": "Hem cultura",
    "cult_1_data_coleta": "18/01/2026",
    "cult_1_data_resultado": "20/01/2026",
    "cult_1_status": "Positivo com Antibiograma",
    "cult_1_micro": "Klebsiella pneumoniae",
    "cult_1_sensib": "Sensível a Meropenem",
    "cult_2_sitio": "Secreção traqueal",
    "cult_2_data_coleta": "22/01/2026",
    "cult_2_data_resultado": "",
    "cult_2_status": "Pendente negativo",
    "cult_3_sitio": "Urina",
    "cult_3_data_coleta": "18/01/2026",
    "cult_3_data_resultado": "20/01/2026",
    "cult_3_status": "Negativo",
    # Antibióticos (2 Atuais, 2 Prévios)
    "atb_1_nome": "Meropenem",
    "atb_1_foco": "PAV",
    "atb_1_tipo": "Guiado por Cultura",
    "atb_1_data_ini": "20/01/2026",
    "atb_1_data_fim": "30/01/2026",
    "atb_1_num_dias": "10",
    "atb_1_status": "Atual",
    "atb_2_nome": "Vancomicina",
    "atb_2_foco": "Cobertura",
    "atb_2_tipo": "Empírico",
    "atb_2_data_ini": "18/01/2026",
    "atb_2_data_fim": "25/01/2026",
    "atb_2_num_dias": "",
    "atb_2_status": "Atual",
    "atb_3_nome": "Ceftriaxone",
    "atb_3_foco": "ITU",
    "atb_3_tipo": "Empírico",
    "atb_3_data_ini": "15/01/2026",
    "atb_3_data_fim": "20/01/2026",
    "atb_3_status": "Prévio",
    "atb_4_nome": "Piperacilina-Tazobactam",
    "atb_4_foco": "Sepse",
    "atb_4_tipo": "Empírico",
    "atb_4_data_ini": "18/01/2026",
    "atb_4_data_fim": "20/01/2026",
    "atb_4_status": "Prévio",
    # Complementares
    "comp_1_exame": "TC de Tórax",
    "comp_1_data": "19/01/2026",
    "comp_1_laudo": "Consolidação em base D. Derrame pleural discreto.",
    "comp_2_exame": "Ecocardiograma",
    "comp_2_data": "20/01/2026",
    "comp_2_laudo": "FE 55%. Valvas sem alterações.",
    # Laboratoriais (3 slots)
    "lab_1_data": "22/01/2026",
    "lab_1_hb": "9.2", "lab_1_ht": "28", "lab_1_leuco": "12.500", "lab_1_plaq": "180",
    "lab_1_cr": "2.1", "lab_1_ur": "85", "lab_1_na": "138", "lab_1_k": "4.2",
    "lab_1_mg": "1.8", "lab_1_pi": "3.2", "lab_1_cai": "1.15",
    "lab_1_pcr": "45", "lab_1_tp": "14s (1.1)",
    "lab_2_data": "21/01/2026",
    "lab_2_hb": "8.8", "lab_2_cr": "2.5", "lab_2_ur": "95", "lab_2_pcr": "78",
    "lab_3_data": "20/01/2026",
    "lab_3_hb": "8.5", "lab_3_cr": "2.8", "lab_3_ur": "110", "lab_3_pcr": "120",
    # Controles
    "ctrl_hoje_data": "22/01/2026",
    "ctrl_hoje_pas_min": "110", "ctrl_hoje_pas_max": "130",
    "ctrl_hoje_pad_min": "65", "ctrl_hoje_pad_max": "80",
    "ctrl_hoje_fc_min": "78", "ctrl_hoje_fc_max": "92",
    "ctrl_hoje_temp_min": "36.5", "ctrl_hoje_temp_max": "37.2",
    "ctrl_hoje_diurese": "1800",
    "ctrl_hoje_balanco": "+350",
    "ctrl_ontem_data": "21/01/2026",
    "ctrl_ontem_pas_min": "100", "ctrl_ontem_pas_max": "125",
    "ctrl_ontem_diurese": "1650",
    "ctrl_ontem_balanco": "+200",
    "ctrl_anteontem_data": "20/01/2026",
    "ctrl_anteontem_diurese": "1400",
    "ctrl_anteontem_balanco": "-100",
    # Evolução Clínica
    "evolucao_notas": "Paciente em melhora clínica. Desmame da VM em curso. Mantém cateter e SVD. Diurese adequada. Sem febre nas últimas 48h.",
    # Sistemas (amostra)
    "sis_neuro_ecg": "15", "sis_neuro_ecg_ao": "4", "sis_neuro_ecg_rv": "5", "sis_neuro_ecg_rm": "6",
    "sis_neuro_rass": "-2", "sis_neuro_delirium": "Não", "sis_neuro_cam_icu": "Negativo",
    "sis_neuro_pupilas_tam": "Normal", "sis_neuro_pupilas_simetria": "Simétricas",
    "sis_neuro_pupilas_foto": "Fotoreagente", "sis_neuro_analgesico_adequado": "Sim",
    "sis_neuro_deficits_ausente": "Ausente",
    "sis_neuro_sedacao_meta": "RASS -2",
    "sis_neuro_sedacao_1_drogas": "Dexmedetomidina", "sis_neuro_sedacao_1_dose": "0.5 mcg/kg/h",
    "sis_resp_ausculta": "MV+ bilateral, sem sibilos",
    "sis_resp_modo": "Ventilação Mecânica", "sis_resp_modo_vent": "PSV",
    "sis_resp_pressao": "8", "sis_resp_volume": "450", "sis_resp_fio2": "35",
    "sis_resp_peep": "5", "sis_resp_freq": "18",
    "sis_resp_vent_protetora": "Sim", "sis_resp_sincronico": "Sim",
    "sis_cardio_fc": "85", "sis_cardio_cardioscopia": "Ritmo sinusal",
    "sis_cardio_pam": "75", "sis_cardio_perfusao": "Normal", "sis_cardio_tec": "2",
    "sis_cardio_fluido_responsivo": "Não", "sis_cardio_fluido_tolerante": "Sim",
    "sis_renal_diurese": "1800", "sis_renal_balanco": "+350", "sis_renal_balanco_acum": "+800",
    "sis_renal_volemia": "Euvolêmico",
    "sis_renal_cr_hoje": "2.1", "sis_renal_cr_ult": "2.5", "sis_renal_cr_antepen": "2.8",
    "sis_renal_ur_hoje": "85", "sis_renal_ur_ult": "95", "sis_renal_ur_antepen": "110",
    "sis_renal_sodio": None, "sis_renal_potassio": None, "sis_renal_magnesio": None,
    "sis_renal_fosforo": None, "sis_renal_calcio": None,
    "sis_renal_trs": "Sim", "sis_renal_trs_via": "Cateter femoral D",
    "sis_renal_trs_ultima": "22/01/2026", "sis_renal_trs_proxima": "24/01/2026",
    "sis_gastro_exame_fisico": "Abdome flácido, timpânico, DB negativo",
    "sis_gastro_ictericia_presente": "Ausente",
    "sis_gastro_dieta_enteral": "Sonda", "sis_gastro_dieta_enteral_vol": "1200",
    "sis_gastro_meta_calorica": "1500", "sis_gastro_na_meta": "Sim",
    "sis_gastro_escape_glicemico": "Não", "sis_gastro_evacuacao": "Sim",
    "sis_gastro_evacuacao_data": "21/01/2026",
    "sis_infec_febre": "Não", "sis_infec_atb": "Sim", "sis_infec_atb_guiado": "Sim",
    "sis_infec_atb_1": "Meropenem", "sis_infec_atb_2": "Vancomicina",
    "sis_infec_culturas_and": "Sim", "sis_infec_cult_1_sitio": "Hem cultura",
    "sis_infec_cult_1_data": "18/01", "sis_infec_pcr_hoje": "45", "sis_infec_pcr_ult": "78",
    "sis_infec_pcr_antepen": "120", "sis_infec_leuc_hoje": "12.500",
    "sis_infec_leuc_ult": "14.200", "sis_infec_leuc_antepen": "18.000",
    "sis_infec_isolamento": "Sim", "sis_infec_isolamento_tipo": "Contato",
    "sis_infec_patogenos": "K. pneumoniae KPC-",
    "sis_hemato_hb_hoje": "9.2", "sis_hemato_hb_ult": "8.8", "sis_hemato_hb_antepen": "8.5",
    "sis_hemato_plaq_hoje": "180", "sis_hemato_plaq_ult": "165",
    "sis_hemato_inr_hoje": "1.1", "sis_hemato_inr_ult": "1.2",
    "sis_hemato_anticoag": "Sim", "sis_hemato_anticoag_tipo": "Profilática",
    "sis_hemato_sangramento": "Não",
    "sis_pele_edema": "Presente", "sis_pele_edema_cruzes": "1",
    "sis_pele_lpp": "Não",
    # Condutas
    "hd_1_conduta": "Manter TRS. Avaliar retirada de cateter.",
    "hd_2_conduta": "Continuar desmame. Manter Meropenem D5/10.",
    "sis_renal_conduta": "Manter TRS. Reposição de K conforme gasometria.",
    "sis_infec_conduta": "Manter ATB até D10. Reavaliar culturas.",
    "conduta_final_lista": "- Manter Meropenem (D5/10)\n- Desmame da VM\n- TRS em 24/01\n- Solicitar parecer nefrologia",
    # Prescrição
    "prescricao_formatada": "Meropenem 1g EV 8/8h\nVancomicina 1g EV 12/12h (ajustar por nível)\nInsulina NPH 10 UI SC 6/6h\nOmeprazol 40mg EV 24/24h",
}

for k, v in EXEMPLO.items():
    st.session_state[k] = v

# Gerar texto
from modules import gerador
texto = gerador.gerar_texto_final()

# Salvar em arquivo (raiz do projeto)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_path = os.path.join(_root, "PRONTUARIO_EXEMPLO_COMPLETO.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(texto)

st.success(f"✅ Prontuário gerado e salvo em **{out_path}**")

st.text_area(
    "Prontuário Completo (Bloco 3 - Saída Determinística)",
    texto,
    height=600,
    label_visibility="collapsed"
)

st.download_button(
    "📥 Download TXT",
    texto,
    file_name="prontuario_exemplo_completo.txt",
    mime="text/plain"
)
