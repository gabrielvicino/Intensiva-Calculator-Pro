"""
Parser determinístico para Evolução por Sistemas no formato padronizado:

  # Evolução por sistemas
  - Neurológico
  ECG 15 | RASS -2
  CAM-ICU: Negativo
  Pupilas: Normais, simétricas, fotoreagentes
  Sedação: Dexmedetomidina 0.5 mcg/kg/h; Meta Rass -2
  Sem déficit focal

  - Respiratório
  EF: MV+ bilateral (ou Exame Respiratório: ...)
  Ventilação Mecânica; PSV, Pressão 8 cmH₂O, Volume 450 mL...
  Em ventilação protetora, sincrônico

  - Cardiovascular
  FC 85 bpm, Ritmo sinusal, PAM 75 mmHg
  Exame Cardiológico: 2BNRF, não ausculto sopros
  Perfusão: Normal, TEC: 2 seg
  fluidoresponsivo; fluidotolerante

  - Gastrointestinal (ou Exame Abdominal)
  EF: Abdome flácido, timpânico
  Dieta: Enteral 1200 kcal; Meta calórica 1500 kcal
  Na meta calórica | Sem escape glicêmico | Evacuação: Presente

  - Renal
  Diurese 1800 mL | BH +350 mL | BH Acumulado +800 mL
  Cr: 2.8 → 2.5 → 2.1 | Ur: 110 → 95 → 85
  Em TRS, Cateter femoral D

  - Infeccioso
  Febre: Ausente
  Antibioticoterapia guiada | Meropenem e Vancomicina
  PCR: 120 → 78 → 45 | Leucócitos: 12.500
  Isolamento: Contato | Patógenos: K. pneumoniae

  - Hematológico
  Anticoagulaçao: Profilática | Hb: 8.5 → 8.8 → 9.2 | Plaq: 180 | INR: 1.1

  - Pele
  Edema presente, 1+ | Sem LPP
"""
import re
from typing import Optional


def _extrair_secao(texto: str, titulo: str) -> str:
    """Extrai o bloco de texto de uma seção (ex: '- Neurológico' até a próxima '- ')."""
    # Busca "- Titulo" e captura até a próxima linha que comece com "- "
    m = re.search(
        r"(?:^|\n)\s*-\s*" + re.escape(titulo) + r"\s*\n(.*?)(?=\n\s*-\s+\w|\Z)",
        texto,
        re.DOTALL | re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _re_busca(pat: str, texto: str, group: int = 1) -> Optional[str]:
    m = re.search(pat, texto, re.IGNORECASE | re.DOTALL)
    return m.group(group).strip() if m and m.lastindex >= group else None


def _parse_neuro(bloco: str) -> dict:
    r = {}
    # ECG 15 | RASS -2
    m_ecg = re.search(r"ECG\s*[:\s]+(\d{1,2})", bloco, re.IGNORECASE)
    if m_ecg:
        r["sis_neuro_ecg"] = m_ecg.group(1)
    m_rass = re.search(r"RASS\s*[:\s]*([+-]?\d)", bloco, re.IGNORECASE)
    if m_rass:
        r["sis_neuro_rass"] = m_rass.group(1)
    # CAM-ICU: Negativo
    m_cam = re.search(r"CAM-ICU\s*[:\s]+([^;\n]+)", bloco, re.IGNORECASE)
    if m_cam:
        val = m_cam.group(1).strip()
        r["sis_neuro_cam_icu"] = "Positivo" if "positivo" in val.lower() else ("Negativo" if "negativo" in val.lower() else val)
    # Pupilas: Normais, simétricas, fotoreagentes
    m_pup = re.search(r"Pupilas?\s*[:\s]+([^\n]+)", bloco, re.IGNORECASE)
    if m_pup:
        val = m_pup.group(1).strip()
        if "simétric" in val.lower() or "simetric" in val.lower():
            r["sis_neuro_pupilas_simetria"] = "Simétricas"
        if "fotoreagente" in val.lower() or "foto-reagente" in val.lower():
            r["sis_neuro_pupilas_foto"] = "Fotoreagente"
        if "miótic" in val.lower() or "miotic" in val.lower():
            r["sis_neuro_pupilas_tam"] = "Miótica"
        elif "midríase" in val.lower() or "midriase" in val.lower():
            r["sis_neuro_pupilas_tam"] = "Midríase"
        elif "normal" in val.lower():
            r["sis_neuro_pupilas_tam"] = "Normal"
    # Sedação: Dexmedetomidina 0.5 mcg/kg/h; Meta Rass -2
    m_sed = re.search(r"Seda[çc][ãa]o\s*[:\s]+([^\n]+)", bloco, re.IGNORECASE)
    if m_sed:
        val = m_sed.group(1).strip()
        if "Meta" in val or "Rass" in val.lower():
            m_meta = re.search(r"Meta\s*Rass?\s*([+-]?\d)", val, re.IGNORECASE)
            if m_meta:
                r["sis_neuro_sedacao_meta"] = f"RASS {m_meta.group(1)}"
        parts = re.split(r"[;,]+\s*", val)
        for i, p in enumerate(parts[:3]):
            p = p.strip()
            if "mcg" in p.lower() or "mg" in p.lower():
                med = re.sub(r"\s*\d+[\d.,]*\s*(mcg|mg).*", "", p, flags=re.I).strip()
                dose = re.search(r"[\d.,]+\s*(?:mcg|mg)[^;]*", p, re.I)
                if med:
                    r[f"sis_neuro_sedacao_{i+1}_drogas"] = med
                if dose:
                    r[f"sis_neuro_sedacao_{i+1}_dose"] = dose.group(0).strip()
    # Sem déficit focal
    if re.search(r"sem\s+d[eé]ficit\s+focal", bloco, re.IGNORECASE):
        r["sis_neuro_deficits_ausente"] = "Ausente"
    return r


def _parse_resp(bloco: str) -> dict:
    r = {}
    # EF: ou Exame Respiratório:
    m_ef = re.search(r"(?:EF|Exame\s+Respirat[oó]rio)\s*[:\s]+([^\n]+)", bloco, re.IGNORECASE)
    if m_ef:
        r["sis_resp_ausculta"] = m_ef.group(1).strip()
    # Ventilação Mecânica; PSV, Pressão 8, Volume 450, FiO2 35%, PEEP 5, FR 18
    if "Ventilação Mecânica" in bloco or "Ventilacao Mecanica" in bloco:
        r["sis_resp_modo"] = "Ventilação Mecânica"
        m_press = re.search(r"Press[ãa]o\s+([\d.,]+)", bloco, re.IGNORECASE)
        if m_press:
            r["sis_resp_pressao"] = m_press.group(1)
        m_vol = re.search(r"Volume\s+([\d.,]+)", bloco, re.IGNORECASE)
        if m_vol:
            r["sis_resp_volume"] = m_vol.group(1)
        m_fio2 = re.search(r"FiO2\s+([\d.,]+)", bloco, re.IGNORECASE)
        if m_fio2:
            r["sis_resp_fio2"] = m_fio2.group(1)
        m_peep = re.search(r"PEEP\s+([\d.,]+)", bloco, re.IGNORECASE)
        if m_peep:
            r["sis_resp_peep"] = m_peep.group(1)
        m_fr = re.search(r"FR\s+([\d.,]+)", bloco, re.IGNORECASE)
        if m_fr:
            r["sis_resp_freq"] = m_fr.group(1)
        if "PSV" in bloco:
            r["sis_resp_modo_vent"] = "PSV"
        elif "PCV" in bloco:
            r["sis_resp_modo_vent"] = "PCV"
        elif "VCV" in bloco:
            r["sis_resp_modo_vent"] = "VCV"
    # Em ventilação protetora, sincrônico
    if re.search(r"em\s+ventila[çc][ãa]o\s+protetora", bloco, re.IGNORECASE):
        r["sis_resp_vent_protetora"] = "Sim"
    if re.search(r"sincr[oó]nico", bloco, re.IGNORECASE):
        r["sis_resp_sincronico"] = "Sim"
    elif re.search(r"assincr[oó]nico", bloco, re.IGNORECASE):
        r["sis_resp_sincronico"] = "Não"
        m_ass = re.search(r"assincr[oó]nico[,\s]+(?:apresenta\s+)?([^\n.]+)", bloco, re.IGNORECASE)
        if m_ass:
            r["sis_resp_assincronia"] = m_ass.group(1).strip()
    return r


def _parse_cardio(bloco: str) -> dict:
    r = {}
    # FC 85 bpm, Ritmo sinusal, PAM 75 mmHg
    m_fc = re.search(r"FC\s+([\d.,]+)\s*(?:bpm)?", bloco, re.IGNORECASE)
    if m_fc:
        r["sis_cardio_fc"] = m_fc.group(1)
    m_rit = re.search(r"Ritmo\s+([^,;\n]+)", bloco, re.IGNORECASE)
    if m_rit:
        r["sis_cardio_cardioscopia"] = m_rit.group(1).strip()
    m_pam = re.search(r"PAM\s+([\d.,]+)\s*(?:mmHg)?", bloco, re.IGNORECASE)
    if m_pam:
        r["sis_cardio_pam"] = m_pam.group(1)
    # Exame Cardiológico: 2BNRF
    m_ex = re.search(r"Exame\s+Cardiol[oó]gico\s*[:\s]+([^\n]+)", bloco, re.IGNORECASE)
    if m_ex:
        r["sis_cardio_exame_cardio"] = m_ex.group(1).strip()
    # Perfusão: Normal, TEC: 2 seg
    m_perf = re.search(r"Perfus[ãa]o\s*[:\s]+(Normal|Lentificada|Flush)", bloco, re.IGNORECASE)
    if m_perf:
        r["sis_cardio_perfusao"] = m_perf.group(1).strip()
    m_tec = re.search(r"TEC\s*[:\s]*([\d.,]+)\s*(?:seg)?", bloco, re.IGNORECASE)
    if m_tec:
        r["sis_cardio_tec"] = m_tec.group(1) + " seg"
    # fluidoresponsivo; fluidotolerante
    if re.search(r"(?:n[aã]o\s+)?fluidoresponsivo", bloco, re.IGNORECASE):
        r["sis_cardio_fluido_responsivo"] = "Não" if re.search(r"n[aã]o\s+fluidoresponsivo", bloco, re.IGNORECASE) else "Sim"
    if re.search(r"(?:n[aã]o\s+)?fluidotolerante", bloco, re.IGNORECASE):
        r["sis_cardio_fluido_tolerante"] = "Não" if re.search(r"n[aã]o\s+fluidotolerante", bloco, re.IGNORECASE) else "Sim"
    return r


def _parse_gastro(bloco: str) -> dict:
    r = {}
    # EF: Abdome flácido
    m_ef = re.search(r"(?:EF|Exame\s+Abdominal)\s*[:\s]+([^\n]+)", bloco, re.IGNORECASE)
    if m_ef:
        r["sis_gastro_exame_fisico"] = m_ef.group(1).strip()
    # Icterícia
    if re.search(r"icter[íi]cio|icter[íi]co", bloco, re.IGNORECASE) and not re.search(r"sem\s+icter[íi]cia", bloco, re.IGNORECASE):
        r["sis_gastro_ictericia_presente"] = "Presente"
    # Dieta: Enteral Sonda 1200 kcal; Meta calórica 1500 kcal
    m_ent = re.search(r"Enteral\s+([^;]+)", bloco, re.IGNORECASE)
    if m_ent:
        ent = m_ent.group(1).strip()
        m_kcal = re.search(r"(\d[\d.,]*)\s*kcal\s*$", ent, re.IGNORECASE)
        if m_kcal:
            r["sis_gastro_dieta_enteral"] = ent[: m_kcal.start()].strip()
            r["sis_gastro_dieta_enteral_vol"] = m_kcal.group(1) + " kcal"
        else:
            r["sis_gastro_dieta_enteral"] = ent
    m_meta = re.search(r"Meta\s+cal[oó]rica\s+(?:de\s+)?([\d.,]+)", bloco, re.IGNORECASE)
    if m_meta:
        r["sis_gastro_meta_calorica"] = m_meta.group(1)
    # Na meta calórica
    if re.search(r"na\s+meta\s+cal[oó]rica", bloco, re.IGNORECASE):
        r["sis_gastro_na_meta"] = "Sim"
    # Sem escape glicêmico
    if re.search(r"sem\s+escape\s+glic[eê]mico", bloco, re.IGNORECASE):
        r["sis_gastro_escape_glicemico"] = "Não"
    # Evacuação: Presente
    if re.search(r"Evacua[çc][ãa]o\s*[:\s]+Presente", bloco, re.IGNORECASE):
        r["sis_gastro_evacuacao"] = "Sim"
    return r


def _parse_renal(bloco: str) -> dict:
    r = {}
    # Diurese 1800 mL | BH +350 mL | BH Acumulado +800 mL
    m_diur = re.search(r"Diurese\s+([^\n|]+)", bloco, re.IGNORECASE)
    if m_diur:
        r["sis_renal_diurese"] = m_diur.group(1).strip()
    m_bh = re.search(r"BH\s+([+-]?\d+[^|]*?)(?:\s*\|\s*|BH Acumulado|$)", bloco, re.IGNORECASE)
    if m_bh:
        r["sis_renal_balanco"] = m_bh.group(1).strip()
    m_acum = re.search(r"BH\s+Acumulado\s+([^\n|]+)", bloco, re.IGNORECASE)
    if m_acum:
        r["sis_renal_balanco_acum"] = m_acum.group(1).strip()
    # Euvolêmico
    if re.search(r"euvol[eê]mico", bloco, re.IGNORECASE):
        r["sis_renal_volemia"] = "Euvolêmico"
    elif re.search(r"hipovol[eê]mico", bloco, re.IGNORECASE):
        r["sis_renal_volemia"] = "Hipovolêmico"
    elif re.search(r"hipervol[eê]mico", bloco, re.IGNORECASE):
        r["sis_renal_volemia"] = "Hipervolêmico"
    # Cr: 2.8 → 2.5 → 2.1
    m_cr = re.search(r"Cr\s*[:\s]*([\d.,]+)\s*[→\-]\s*([\d.,]+)\s*[→\-]\s*([\d.,]+)", bloco, re.IGNORECASE)
    if m_cr:
        r["sis_renal_cr_antepen"] = m_cr.group(1)
        r["sis_renal_cr_ult"] = m_cr.group(2)
        r["sis_renal_cr_hoje"] = m_cr.group(3)
    # Ur: 110 → 95 → 85
    m_ur = re.search(r"Ur\s*[:\s]*([\d.,]+)\s*[→\-]\s*([\d.,]+)\s*[→\-]\s*([\d.,]+)", bloco, re.IGNORECASE)
    if m_ur:
        r["sis_renal_ur_antepen"] = m_ur.group(1)
        r["sis_renal_ur_ult"] = m_ur.group(2)
        r["sis_renal_ur_hoje"] = m_ur.group(3)
    # Em TRS, Cateter femoral D
    if re.search(r"em\s+TRS|em\s+TSR", bloco, re.IGNORECASE):
        r["sis_renal_trs"] = "Sim"
        m_via = re.search(r"(Cateter\s+[^\n,]+)", bloco, re.IGNORECASE)
        if not m_via:
            m_via = re.search(r"(?:via|acesso)\s+([^\n,]+)", bloco, re.IGNORECASE)
        if m_via:
            r["sis_renal_trs_via"] = m_via.group(1).strip()
        m_ult = re.search(r"[Uú]ltima\s+(?:TSR|sess[ãa]o)\s+em\s+([\d/]+)", bloco, re.IGNORECASE)
        if m_ult:
            r["sis_renal_trs_ultima"] = m_ult.group(1)
        m_prox = re.search(r"pr[oó]xima\s+(?:programada\s+)?(?:para\s+)?([\d/]+)", bloco, re.IGNORECASE)
        if m_prox:
            r["sis_renal_trs_proxima"] = m_prox.group(1)
    return r


def _parse_infec(bloco: str) -> dict:
    r = {}
    # Febre: Ausente/Presente → Não/Sim (compatível com pills)
    m_febre = re.search(r"Febre\s*[:\s]+(Ausente|Presente)", bloco, re.IGNORECASE)
    if m_febre:
        val = m_febre.group(1).strip().lower()
        r["sis_infec_febre"] = "Não" if val == "ausente" else "Sim"
    # Antibioticoterapia guiada | Meropenem e Vancomicina
    if re.search(r"guiada\s+por\s+cultura|guiado\s+por\s+cultura", bloco, re.IGNORECASE):
        r["sis_infec_atb_guiado"] = "Sim"
    m_atb = re.search(r"(?:Meropenem|Vancomicina|Piperacilina|Ceftriaxone)[^;]*", bloco, re.IGNORECASE)
    if m_atb:
        atbs = re.findall(r"\b(Meropenem|Vancomicina|Piperacilina|Ceftriaxone|Cefepime)\b", bloco, re.IGNORECASE)
        for i, a in enumerate(atbs[:3]):
            r[f"sis_infec_atb_{i+1}"] = a
    # PCR: 120 → 78 → 45
    m_pcr = re.search(r"PCR\s*[:\s]*([\d.,]+)\s*[→\-]\s*([\d.,]+)\s*[→\-]\s*([\d.,]+)", bloco, re.IGNORECASE)
    if m_pcr:
        r["sis_infec_pcr_antepen"] = m_pcr.group(1)
        r["sis_infec_pcr_ult"] = m_pcr.group(2)
        r["sis_infec_pcr_hoje"] = m_pcr.group(3)
    # Leucócitos: 12.500
    m_leuc = re.search(r"Leuc[oó]citos?\s*[:\s]*([\d.,]+)", bloco, re.IGNORECASE)
    if m_leuc:
        r["sis_infec_leuc_hoje"] = m_leuc.group(1)
    # Isolamento: Contato
    m_isol = re.search(r"Isolamento\s*[:\s]+([^\n]+)", bloco, re.IGNORECASE)
    if m_isol:
        r["sis_infec_isolamento"] = "Sim"
        r["sis_infec_isolamento_tipo"] = m_isol.group(1).strip()
    # Patógenos: K. pneumoniae ou Patógenos isolados: K. pneumoniae
    m_pat = re.search(r"Pat[oó]genos?(?:\s+isolados?)?\s*[:\s]+([^\n]+)", bloco, re.IGNORECASE)
    if m_pat:
        r["sis_infec_patogenos"] = m_pat.group(1).strip()
    return r


def _parse_hemato(bloco: str) -> dict:
    r = {}
    # Anticoagulação: Profilática
    m_ant = re.search(r"Anticoagula[çc][ãa]o\s*[:\s]+([^\n|]+)", bloco, re.IGNORECASE)
    if m_ant:
        r["sis_hemato_anticoag"] = "Sim"
        _tipo_raw = m_ant.group(1).strip()
        _tipo_map = {"profilática": "Profilática", "profilatica": "Profilática", "plena": "Plena"}
        r["sis_hemato_anticoag_tipo"] = _tipo_map.get(_tipo_raw.lower(), _tipo_raw)
    # Sem sangramentos
    if re.search(r"sem\s+sangramento", bloco, re.IGNORECASE):
        r["sis_hemato_sangramento"] = "Não"
    # Hb: 8.5 → 8.8 → 9.2
    m_hb = re.search(r"Hb\s*[:\s]*([\d.,]+)\s*[→\-]\s*([\d.,]+)\s*[→\-]\s*([\d.,]+)", bloco, re.IGNORECASE)
    if m_hb:
        r["sis_hemato_hb_antepen"] = m_hb.group(1)
        r["sis_hemato_hb_ult"] = m_hb.group(2)
        r["sis_hemato_hb_hoje"] = m_hb.group(3)
    m_plaq = re.search(r"Plaq(?:ueta)?\s*[:\s]*([\d.,]+)", bloco, re.IGNORECASE)
    if m_plaq:
        r["sis_hemato_plaq_hoje"] = m_plaq.group(1)
    m_inr = re.search(r"INR\s*[:\s]*([\d.,]+)", bloco, re.IGNORECASE)
    if m_inr:
        r["sis_hemato_inr_hoje"] = m_inr.group(1)
    return r


def _parse_pele(bloco: str) -> dict:
    r = {}
    # Edema presente, 1+
    if re.search(r"edema\s+presente", bloco, re.IGNORECASE):
        r["sis_pele_edema"] = "Presente"
        m_cruz = re.search(r"(\d)\s*\+", bloco)
        if m_cruz:
            r["sis_pele_edema_cruzes"] = m_cruz.group(1)
    # Sem LPP
    if re.search(r"sem\s+LPP", bloco, re.IGNORECASE):
        r["sis_pele_lpp"] = "Não"
    return r


def parse_sistemas_deterministico(texto: str) -> dict[str, str | None]:
    """
    Parseia texto de evolução por sistemas no formato padronizado.
    Retorna dict para session_state: sis_* = valor.
    """
    if not texto or not texto.strip():
        return {}

    # Normaliza: pode vir com # Evolução por sistemas ou direto as seções
    texto = texto.strip()
    if "# Evolução" in texto or "# evolucao" in texto.lower():
        idx = re.search(r"#\s*Evolu[çc][ãa]o\s+por\s+sistemas?", texto, re.IGNORECASE)
        if idx:
            texto = texto[idx.end():].strip()

    resultado = {}

    # Extrai cada seção e aplica o parser correspondente
    secao_parser = [
        ("Neurológico", _parse_neuro),
        ("Respiratório", _parse_resp),
        ("Cardiovascular", _parse_cardio),
        ("Gastrointestinal", _parse_gastro),
        ("Exame Abdominal", _parse_gastro),
        ("Renal", _parse_renal),
        ("Infeccioso", _parse_infec),
        ("Hematológico", _parse_hemato),
        ("Pele", _parse_pele),
    ]

    for titulo, parser_fn in secao_parser:
        bloco = _extrair_secao(texto, titulo)
        if not bloco:
            # Tenta com "- Titulo" no início
            m = re.search(r"-\s*" + re.escape(titulo) + r"\s*\n(.*?)(?=\n\s*-\s+\w|\Z)", texto, re.DOTALL | re.IGNORECASE)
            if m:
                bloco = m.group(1).strip()
        if bloco:
            parsed = parser_fn(bloco)
            resultado.update(parsed)

    return resultado
