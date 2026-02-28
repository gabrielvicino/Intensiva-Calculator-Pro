# Exemplo — Seção 13: Evolução Detalhada por Sistemas

Todos os campos preenchidos com valores de exemplo e a **saída determinística** correspondente.

---

## 1. Campos preenchidos (valores de exemplo)

### Neurológico
| Campo | Valor |
|-------|-------|
| sis_neuro_ecg | 10 |
| sis_neuro_ecg_ao | 3 |
| sis_neuro_ecg_rv | 4 |
| sis_neuro_ecg_rm | 3 |
| sis_neuro_ecg_p | 12 |
| sis_neuro_rass | -2 |
| sis_neuro_delirium | Sim |
| sis_neuro_delirium_tipo | Hipoativo |
| sis_neuro_cam_icu | Positivo |
| sis_neuro_pupilas_tam | Normal |
| sis_neuro_pupilas_simetria | Simétricas |
| sis_neuro_pupilas_foto | Fotoreagente |
| sis_neuro_analgesico_adequado | Sim |
| sis_neuro_deficits_focais | Hemiparesia D grau 2 |
| sis_neuro_analgesia_1_tipo | Fixa |
| sis_neuro_analgesia_1_drogas | Fentanil |
| sis_neuro_analgesia_1_dose | 50 mcg/h |
| sis_neuro_analgesia_1_freq | Contínua |
| sis_neuro_sedacao_meta | RASS -2 |
| sis_neuro_sedacao_1_drogas | Propofol |
| sis_neuro_sedacao_1_dose | 20 mg/h |
| sis_neuro_bloqueador_med | Rocurônio |
| sis_neuro_bloqueador_dose | 15 mL/h |
| sis_neuro_obs | Avaliar desmame de sedação amanhã |

### Respiratório
| Campo | Valor |
|-------|-------|
| sis_resp_ausculta | MV+ bilateral, roncos em bases |
| sis_resp_modo | Ventilação Mecânica |
| sis_resp_modo_vent | VCV |
| sis_resp_pressao | 18 |
| sis_resp_volume | 450 |
| sis_resp_fio2 | 45 |
| sis_resp_peep | 8 |
| sis_resp_freq | 16 |
| sis_resp_vent_protetora | Sim |
| sis_resp_sincronico | Sim |
| sis_resp_complacencia | 35 |
| sis_resp_resistencia | 12 |
| sis_resp_dp | 12 |
| sis_resp_plato | 22 |
| sis_resp_pico | 28 |
| sis_resp_dreno_1 | Pleural E |
| sis_resp_dreno_1_debito | 80 mL/dia |
| sis_resp_obs | Mantém ventilação protetora |

### Cardiovascular
| Campo | Valor |
|-------|-------|
| sis_cardio_fc | 95 |
| sis_cardio_cardioscopia | Fibrilação Atrial |
| sis_cardio_pam | 72 |
| sis_cardio_perfusao | Normal |
| sis_cardio_tec | 3 seg. |
| sis_cardio_fluido_responsivo | Sim |
| sis_cardio_fluido_tolerante | Sim |
| sis_cardio_dva_1_med | Noradrenalina |
| sis_cardio_dva_1_dose | 0,15 mcg/kg/min |
| sis_cardio_dva_2_med | Vasopressina |
| sis_cardio_dva_2_dose | 0,03 UI/min |
| sis_cardio_obs | Meta PAM 65-70 |

### Renal
| Campo | Valor |
|-------|-------|
| sis_renal_diurese | 1500 mL |
| sis_renal_balanco | +300 mL |
| sis_renal_balanco_acum | +300 mL |
| sis_renal_volemia | Euvolêmico |
| sis_renal_cr_antepen | 3,2 |
| sis_renal_cr_ult | 3,8 |
| sis_renal_cr_hoje | 4,2 |
| sis_renal_ur_antepen | 95 |
| sis_renal_ur_ult | 110 |
| sis_renal_ur_hoje | 120 |
| sis_renal_trs | Sim |
| sis_renal_trs_via | Cateter venovenoso |
| sis_renal_trs_ultima | 14h |
| sis_renal_trs_proxima | 06h |
| sis_renal_obs | Avaliar desmame de TRS amanhã |
| sis_metab_obs | Hipocalemia corrigida |

### Infeccioso
| Campo | Valor |
|-------|-------|
| sis_infec_febre | Sim |
| sis_infec_febre_vezes | 2 |
| sis_infec_febre_ultima | 11/02 18h |
| sis_infec_atb | Sim |
| sis_infec_atb_guiado | Sim |
| sis_infec_atb_1 | Meropenem |
| sis_infec_atb_2 | Vancomicina |
| sis_infec_culturas_and | Sim |
| sis_infec_cult_1_sitio | Hemocultura periférica |
| sis_infec_cult_1_data | 12/02 |
| sis_infec_pcr_hoje | 180 |
| sis_infec_pcr_ult | 220 |
| sis_infec_pcr_antepen | 250 |
| sis_infec_leuc_hoje | 15.200 |
| sis_infec_leuc_ult | 16.200 |
| sis_infec_leuc_antepen | 18.500 |
| sis_infec_isolamento | Sim |
| sis_infec_isolamento_tipo | Contato |
| sis_infec_isolamento_motivo | K. pneumoniae KPC+ |
| sis_infec_patogenos | K. pneumoniae KPC+, Pseudomonas aeruginosa |
| sis_infec_obs | Reavaliar ATB em 72h |

### Gastrointestinal
| Campo | Valor |
|-------|-------|
| sis_gastro_exame_fisico | Abdome flácido, RHA presentes |
| sis_gastro_dieta_enteral | Fresubin |
| sis_gastro_dieta_enteral_vol | 1200 mL |
| sis_gastro_meta_calorica | 1800 |
| sis_gastro_na_meta | Sim |
| sis_gastro_escape_glicemico | Sim |
| sis_gastro_escape_vezes | 2 |
| sis_gastro_escape_manha | true |
| sis_gastro_escape_tarde | true |
| sis_gastro_insulino | Sim |
| sis_gastro_insulino_dose | 4 Un SC 8/8h |
| sis_gastro_evacuacao | Não |
| sis_gastro_evacuacao_data | 10/02 |
| sis_gastro_laxativo | Lactulose 10 mL 8/8h |
| sis_gastro_obs | Manter dieta enteral |
| sis_nutri_obs | Avaliar via oral em 48h |

### Hematológico
| Campo | Valor |
|-------|-------|
| sis_hemato_anticoag | Sim |
| sis_hemato_anticoag_tipo | Profilática |
| sis_hemato_anticoag_motivo | Imobilização |
| sis_hemato_sangramento | Não |
| sis_hemato_transf_data | 11/02 |
| sis_hemato_transf_1_comp | Concentrado de hemácias |
| sis_hemato_transf_1_bolsas | 2 bolsas |
| sis_hemato_transf_2_comp | PFC |
| sis_hemato_transf_2_bolsas | 2 bolsas |
| sis_hemato_hb_antepen | 7,8 |
| sis_hemato_hb_ult | 8,2 |
| sis_hemato_hb_hoje | 8,5 |
| sis_hemato_plaq_antepen | 85.000 |
| sis_hemato_plaq_ult | 95.000 |
| sis_hemato_plaq_hoje | 102.000 |
| sis_hemato_inr_antepen | 1,8 |
| sis_hemato_inr_ult | 1,5 |
| sis_hemato_inr_hoje | 1,3 |
| sis_hemato_obs | Manter Hb > 8 |

### Pele e musculoesquelético
| Campo | Valor |
|-------|-------|
| sis_pele_lpp | Sim |
| sis_pele_lpp_local_1 | Sacro |
| sis_pele_lpp_grau_1 | Grau II |
| sis_pele_lpp_local_2 | Calcâneo D |
| sis_pele_lpp_grau_2 | Grau I |
| sis_pele_polineuropatia | Não |
| sis_pele_obs | Curativos com ácido hialurônico. Mobilização passiva |

---

## 2. Saída determinística gerada

```
# Evolução por sistemas

- Neurológico
ECG 10 (AO 3 RV 4 RM 3) | ECG-P 12 | RASS -2
CAM-ICU: Positivo, delirium hipoativo
Pupilas: Normais, simétricas, fotoreagentes
Paciente com bom controle álgico
Analgesia Fixa: Fentanil; 50 mcg/h; Contínua
Sedação: Propofol; 20 mg/h; Meta RASS -2
Bloqueador Neuromuscular: Rocurônio 15 mL/h
Déficits focais: Hemiparesia D grau 2
Obs: Avaliar desmame de sedação amanhã

- Respiratório
EF: MV+ bilateral, roncos em bases
Ventilação Mecânica; VCV, Pressão 18 cmH₂O, Volume 450 mL, FiO2 45%, PEEP 8 cmH₂O e FR 16 ipm
Em ventilação protetora, sincrônico
Mecânica Ventilatória: Complacência 35 mL/cmH₂O, Resistência 12 cmH₂O/L/s, Driving Pressure 15 cmH₂O, Pressão de platô 30 cmH₂O, Pressão de pico 40 cmH₂O
Dreno Pleural E: 80 mL/dia | Dreno Mediastino: 10 mL | Dreno torácico D: 50 mL
Obs: Mantém ventilação protetora

- Cardiovascular
FC 95 bpm, Ritmo fibrilação atrial, PAM 72 mmHg
Perfusão: Normal, TEC: 3 seg, fluidoresponsivo, fluidotolerante
DVA: Noradrenalina 0,15 mcg/kg/min | Vasopressina 0,03 UI/min
Obs: Meta PAM 65-70

- Gastrointestinal
EF: Abdome flácido, RHA presentes
Dieta: Enteral Fresubin 1200 mL; Meta calórica de 1800 kcal
Na meta calórica
Escape glicêmico: 2x, período Manhã e Tarde, em insulinoterapia 4 Un SC 8/8h
Evacuação: Ausente, última em 10/02, em uso de Lactulose 10 mL 8/8h
Obs: Manter dieta enteral
Nutri: Avaliar via oral em 48h

- Renal
Diurese 1500 mL | BH +300 mL | BH Acumulado +300 mL
Euvolêmico
Cr: 3,2 → 3,8 → 4,2 | Ur: 95 → 110 → 120
Em TRS, Cateter venovenoso, Última TSR 14h, próxima programada 06h
Obs: Avaliar desmame de TRS amanhã
Metab: Hipocalemia corrigida

- Infeccioso
Febre: Sim, 2x | Último pico febril: 11/02 18h
Antibioticoterapia guiada por culturas em uso de Meropenem e Vancomicina
Culturas em andamento: Hemocultura periférica (12/02)
PCR: 250 → 220 → 180 | Leucócitos: 18.500 → 16.200 → 15.200 | PCT: 2,5
Isolamento: Contato por K. pneumoniae KPC+
Patógenos isolados: K. pneumoniae KPC+, Pseudomonas aeruginosa
Obs: Reavaliar ATB em 72h

- Hematológico
Anticoagulação: Profilática devido Imobilização
Sem sangramentos
Transfusão em 11/02; Concentrado de hemácias 2 bolsas, PFC 2 bolsas
Hb: 7,8 → 8,2 → 8,5 | Plaq: 85.000 → 95.000 → 102.000
INR: 1,8 → 1,5 → 1,3
Obs: Manter Hb > 8

- Pele e musculoesquelético
LPP: Sacro Grau II, Calcâneo D Grau I
Sem polineuropatia
Obs: Curativos com ácido hialurônico. Mobilização passiva
```

---

## Nota

Os campos `*_conduta` (ex.: sis_neuro_conduta, sis_resp_conduta) não aparecem na seção "Evolução por sistemas" — são agregados na seção **# Condutas** do prontuário final.
