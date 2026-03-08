from ._base import *
import streamlit as st

def _secao_sistemas() -> list[str]:
    """
    Gera a saída determinística da Evolução por Sistemas.
    Regra: campo preenchido → aparece; campo vazio/None → não aparece.
    Campos Sim/Não → positivo ou negativo conforme valor.
    """
    corpo = []

    def _s(key):
        v = _get(key)
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() or None
        return v

    def _jun(items, sep=", "):
        """Junta lista não-vazia com separador."""
        return sep.join(i for i in items if i)

    def _lista_e(items):
        """Junta com vírgulas e 'e' antes do último."""
        items = [i for i in items if i]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + " e " + items[-1]

    def _evo(label, prefix, show_key=None):
        """Retorna 'label: v5 → v4 → ... → hoje' se show_key=True (ou None para sempre emitir)."""
        if show_key is not None and not _get(show_key):
            return None
        vals = [_s(f"{prefix}_ant5"), _s(f"{prefix}_ant4"), _s(f"{prefix}_antepen"),
                _s(f"{prefix}_ult"), _s(f"{prefix}_hoje")]
        partes = [str(_limpar_barra(v) or v) for v in vals if v]
        if not partes:
            return None
        return f"{label}: " + " → ".join(partes)

    def _turnos():
        t = []
        if st.session_state.get("sis_gastro_escape_manha", False): t.append("manhã")
        if st.session_state.get("sis_gastro_escape_tarde",  False): t.append("tarde")
        if st.session_state.get("sis_gastro_escape_noite",  False): t.append("noite")
        lista = _lista_e(t)
        return f"nos períodos da {lista}" if lista else ""

    def _limpar_barra(val):
        """Remove barras dos valores (ex: 3/ → 3, 22/00/0 → 22000)."""
        if val is None or not isinstance(val, str):
            return val
        return str(val).replace("/", "").strip() or None

    # ── NEUROLÓGICO ──────────────────────────────────────────────────────────
    neuro = []

    ecg  = st.session_state.get("sis_neuro_ecg", "") or ""
    ecgp = st.session_state.get("sis_neuro_ecg_p", "") or ""
    rass = st.session_state.get("sis_neuro_rass", "") or ""
    ao   = st.session_state.get("sis_neuro_ecg_ao", "") or ""
    rv   = st.session_state.get("sis_neuro_ecg_rv", "") or ""
    rm   = st.session_state.get("sis_neuro_ecg_rm", "") or ""

    ecg_parts = []
    if str(ecg).strip():
        ecg_str = f"ECG {ecg}"
        sub = [p for p in [
            f"AO {ao}" if str(ao).strip() else None,
            f"RV {rv}" if str(rv).strip() else None,
            f"RM {rm}" if str(rm).strip() else None,
        ] if p]
        if sub:
            ecg_str += f" ({' '.join(sub)})"
        ecg_parts.append(ecg_str)
    if str(ecgp).strip():
        ecg_parts.append(f"ECG-P {ecgp}")
    if str(rass).strip():
        ecg_parts.append(f"RASS {rass}")
    if ecg_parts:
        neuro.append(" | ".join(ecg_parts))

    cam      = _s("sis_neuro_cam_icu")
    delirium = _s("sis_neuro_delirium")
    del_tipo = _s("sis_neuro_delirium_tipo")
    if cam or delirium:
        cam_parts = []
        if cam:
            cam_parts.append(f"CAM-ICU: {cam}")
        if delirium == "Sim":
            cam_parts.append(f"delirium {del_tipo.lower()}" if del_tipo else "com delirium")
        elif delirium == "Não":
            cam_parts.append("sem delirium")
        neuro.append(", ".join(cam_parts))

    tam  = _s("sis_neuro_pupilas_tam")
    sime = _s("sis_neuro_pupilas_simetria")
    foto = _s("sis_neuro_pupilas_foto")
    if tam or sime or foto:
        pup = []
        if tam:  pup.append({"Normal": "Normais", "Miótica": "Mióticas", "Midríase": "Midríase"}.get(tam, tam))
        if sime: pup.append({"Simétricas": "simétricas", "Anisocoria": "anisocóricas"}.get(sime, sime))
        if foto: pup.append({"Fotoreagente": "fotoreagentes", "Não fotoreagente": "não fotoreagentes"}.get(foto, foto))
        neuro.append("Pupilas: " + ", ".join(pup))

    algico = _s("sis_neuro_analgesico_adequado")
    if algico == "Sim":   neuro.append("Paciente com bom controle álgico")
    elif algico == "Não": neuro.append("Sem controle álgico adequado")

    fixas, resgates = [], []
    for i in range(1, 4):
        tipo   = _s(f"sis_neuro_analgesia_{i}_tipo")
        drogas = _s(f"sis_neuro_analgesia_{i}_drogas")
        dose   = _s(f"sis_neuro_analgesia_{i}_dose")
        freq   = _s(f"sis_neuro_analgesia_{i}_freq")
        if not drogas:
            continue
        if dose and freq:
            entry = f"{drogas} {dose}, {freq}"
        elif dose:
            entry = f"{drogas} {dose}"
        elif freq:
            entry = f"{drogas}, {freq}"
        else:
            entry = drogas
        (fixas if tipo == "Fixa" else resgates).append(entry)
    if fixas:    neuro.append("Analgesia Fixa: "    + " | ".join(fixas))
    if resgates: neuro.append("Analgesia Resgate: " + " | ".join(resgates))

    sed_entries = []
    for i in range(1, 4):
        dr   = _s(f"sis_neuro_sedacao_{i}_drogas")
        dose = _s(f"sis_neuro_sedacao_{i}_dose")
        if not dr:
            continue
        sed_entries.append(f"{dr} {dose}" if dose else dr)
    if sed_entries:
        meta = _s("sis_neuro_sedacao_meta")
        linha_sed = "Sedação: " + " | ".join(sed_entries)
        if meta:
            m = str(meta).strip()
            m = m.replace("RASS", "").replace("Rass", "").strip() or m
            linha_sed += f"; Meta Rass {m}"
        neuro.append(linha_sed)

    _VALORES_VAZIOS = {"", "none", "nenhum", "não", "nao", "-"}
    bnm_med = _s("sis_neuro_bloqueador_med")
    bnm_dose = _s("sis_neuro_bloqueador_dose")
    bnm_med_ok = bnm_med and str(bnm_med).lower().strip() not in _VALORES_VAZIOS
    bnm_dose_ok = bnm_dose and str(bnm_dose).lower().strip() not in _VALORES_VAZIOS
    if bnm_med_ok or bnm_dose_ok:
        partes_bnm = [p for p in [bnm_med if bnm_med_ok else "", bnm_dose if bnm_dose_ok else ""] if p]
        neuro.append(f"Bloqueador Neuromuscular: {' '.join(partes_bnm)}")

    df = _s("sis_neuro_deficits_focais")
    df_ausente = st.session_state.get("sis_neuro_deficits_ausente") in ("Ausente", True)
    if df:
        neuro.append(f"Déficit Focal: {df}")
    elif df_ausente:
        neuro.append("Sem déficit focal")

    pocus = _s("sis_neuro_pocus")
    if pocus: neuro.append(f"Pocus Neurológico: {pocus}")
    obs = _s("sis_neuro_obs")
    if obs: neuro.append(f"Obs: {obs}")

    if neuro:
        corpo.append("- Neurológico")
        corpo.extend(neuro)

    # ── RESPIRATÓRIO ─────────────────────────────────────────────────────────
    resp = []

    exame_resp = _s("sis_resp_ausculta")
    if exame_resp: resp.append(f"Respiratório: {exame_resp}")

    modo      = _s("sis_resp_modo")
    modo_vent = _s("sis_resp_modo_vent")
    if modo:
        if modo == "Ventilação Mecânica":
            vm_params = []
            if modo_vent:
                vm_params.append(modo_vent.upper())
            pressao = _s("sis_resp_pressao"); volume = _s("sis_resp_volume")
            fio2    = _s("sis_resp_fio2");    peep   = _s("sis_resp_peep")
            freq_r  = _s("sis_resp_freq")
            if pressao:
                p = pressao if any(u in pressao.lower() for u in ["mmhg", "mmh2o", "cmh2o"]) else f"{pressao} cmH₂O"
                vm_params.append(f"Pressão {p}")
            if volume:
                v = volume if "ml" in volume.lower() else f"{volume} mL"
                vm_params.append(f"Volume {v}")
            if fio2:
                vm_params.append(f"FiO2 {fio2}" if "%" in fio2 else f"FiO2 {fio2}%")
            if peep:
                pe = peep if any(u in peep.lower() for u in ["mmhg", "mmh2o", "cmh2o"]) else f"{peep} cmH₂O"
                vm_params.append(f"PEEP {pe}")
            if freq_r:
                fr = freq_r if "ipm" in freq_r.lower() else f"{freq_r} ipm"
                vm_params.append(f"FR {fr}")
            if vm_params:
                if len(vm_params) > 1:
                    sufixo = ", ".join(vm_params[:-1]) + " e " + vm_params[-1]
                else:
                    sufixo = vm_params[0]
                resp.append(f"Ventilação Mecânica; {sufixo}")
            else:
                resp.append("Ventilação Mecânica")
        elif modo == "Oxigenoterapia":
            ox_modo = _s("sis_resp_oxigenio_modo")
            ox_fluxo = _s("sis_resp_oxigenio_fluxo")
            partes = []
            if ox_modo:
                partes.append(ox_modo)
            if ox_fluxo:
                fluxo_str = ox_fluxo if "L/min" in ox_fluxo or "l/min" in ox_fluxo.lower() else f"{ox_fluxo} L/min"
                partes.append(fluxo_str)
            resp.append("Oxigenoterapia; " + ", ".join(partes) if partes else "Oxigenoterapia")
        elif modo == "Cateter de Alto Fluxo":
            volume = _s("sis_resp_volume"); fio2 = _s("sis_resp_fio2")
            partes = ["Cateter de Alto Fluxo"]
            if volume:
                v = volume if "ml" in volume.lower() else f"{volume} mL"
                partes.append(f"Volume {v}")
            if fio2:
                partes.append(f"FiO2 {fio2}" if "%" in fio2 else f"FiO2 {fio2}%")
            resp.append(", ".join(partes))
        else:
            resp.append(modo)

    vent_prot = _s("sis_resp_vent_protetora")
    sincro    = _s("sis_resp_sincronico")
    assincr   = _s("sis_resp_assincronia")
    if vent_prot or sincro:
        vs = []
        if vent_prot == "Sim":   vs.append("Em ventilação protetora")
        elif vent_prot == "Não": vs.append("Sem ventilação protetora")
        if sincro == "Sim":
            vs.append("sincrônico")
        elif sincro == "Não":
            vs.append(f"assincrônico, apresenta {assincr}" if assincr else "assincrônico")
        resp.append(", ".join(vs))

    mec = []
    comp   = _s("sis_resp_complacencia"); resist = _s("sis_resp_resistencia")
    dp     = _s("sis_resp_dp");           plato  = _s("sis_resp_plato")
    pico   = _s("sis_resp_pico")
    if comp:   mec.append(f"Complacência {comp} mL/cmH₂O")
    if resist: mec.append(f"Resistência {resist} cmH₂O/L/s")
    if dp:     mec.append(f"Driving Pressure {dp} cmH₂O")
    if plato:  mec.append(f"Pressão de platô {plato} cmH₂O")
    if pico:   mec.append(f"Pressão de pico {pico} cmH₂O")
    if mec: resp.append("Mecânica Ventilatória: " + ", ".join(mec))

    drenos = []
    for i in range(1, 4):
        nome = _s(f"sis_resp_dreno_{i}")
        deb  = _s(f"sis_resp_dreno_{i}_debito")
        if nome:
            prefixo = "" if "dreno" in nome.lower() else "Dreno "
            if deb:
                suf = "" if any(u in deb for u in ("ml", "mL", "L", "/")) else " mL"
                drenos.append(f"{prefixo}{nome}: {deb}{suf}")
            else:
                drenos.append(f"{prefixo}{nome}")
    if drenos: resp.append(" | ".join(drenos))

    pocus = _s("sis_resp_pocus")
    if pocus: resp.append(f"Pocus Respiratório: {pocus}")
    obs = _s("sis_resp_obs")
    if obs: resp.append(f"Obs: {obs}")

    if resp:
        corpo.append("")
        corpo.append("- Respiratório")
        corpo.extend(resp)

    # ── CARDIOVASCULAR ───────────────────────────────────────────────────────
    cardio = []

    fc    = _s("sis_cardio_fc");           crd = _s("sis_cardio_cardioscopia")
    pam_c = _s("sis_cardio_pam")
    exame_cardio = _s("sis_cardio_exame_cardio")
    _fc   = f"FC {fc} bpm" if fc and "bpm" not in fc.lower() else (f"FC {fc}" if fc else None)
    _rit  = None
    if crd:
        r = crd.strip()
        if r.lower().startswith("ritmo"):
            _rit = "Ritmo " + r[5:].strip()
        else:
            _rit = f"Ritmo {r}"
    _pam  = f"PAM {pam_c} mmHg" if pam_c and "mmhg" not in pam_c.lower() else (f"PAM {pam_c}" if pam_c else None)
    hemo  = [p for p in [_fc, _rit, _pam] if p]
    if hemo: cardio.append(", ".join(hemo))
    if exame_cardio: cardio.append(f"Cardiológico: {exame_cardio}")

    perf = _s("sis_cardio_perfusao")
    tec = _s("sis_cardio_tec")
    if perf or tec:
        perf_p = []
        if perf:
            perf_p.append(f"Perfusão: {perf}")
        if tec:
            tec_s = f"{tec} seg" if tec.strip() and "seg" not in tec.lower() else tec
            perf_p.append(f"TEC: {tec_s}")
        cardio.append(", ".join(perf_p))
    fr_ = _s("sis_cardio_fluido_responsivo")
    ft_ = _s("sis_cardio_fluido_tolerante")
    if fr_ or ft_:
        l1 = "Fluidoresponsivo" if fr_ == "Sim" else ("Não fluidoresponsivo" if fr_ == "Não" else None)
        l2 = "fluidotolerante" if ft_ == "Sim" else ("não fluidotolerante" if ft_ == "Não" else None)
        partes_f = [p for p in [l1, l2] if p]
        if partes_f:
            cardio.append("; ".join(partes_f))

    dvas = []
    for i in range(1, 5):
        med  = _s(f"sis_cardio_dva_{i}_med")
        dose = _s(f"sis_cardio_dva_{i}_dose")
        if med: dvas.append(f"{med} {dose}" if dose else med)
    if dvas: cardio.append("DVA: " + " | ".join(dvas))

    _cardio_evo = [
        _evo("Lactato",   "sis_cardio_lac",  "sis_cardio_lac_show"),
        _evo("Troponina", "sis_cardio_trop", "sis_cardio_trop_show"),
    ]
    for linha in _cardio_evo:
        if linha: cardio.append(linha)

    pocus = _s("sis_cardio_pocus")
    if pocus: cardio.append(f"Pocus Cardiovascular: {pocus}")
    obs = _s("sis_cardio_obs")
    if obs: cardio.append(f"Obs: {obs}")

    if cardio:
        corpo.append("")
        corpo.append("- Cardiovascular")
        corpo.extend(cardio)

    # ── EXAME ABDOMINAL / NUTRICIONAL ─────────────────────────────────────────
    gastro = []

    ef = _s("sis_gastro_exame_fisico")
    icter_presente = _s("sis_gastro_ictericia_presente") == "Presente"
    icter_cruzes = _s("sis_gastro_ictericia_cruzes")
    if ef:
        if icter_presente:
            cruzes_str = str(icter_cruzes).strip() if icter_cruzes else ""
            cruzes_valido = cruzes_str in ("1", "2", "3", "4")
            suf = f", icteríco {cruzes_str}+" if cruzes_valido else ", icteríco"
        else:
            suf = ", sem icterícia"
        gastro.append(f"Abdomen: {ef}{suf}")

    oral     = _s("sis_gastro_dieta_oral")
    enteral  = _s("sis_gastro_dieta_enteral"); e_vol = _s("sis_gastro_dieta_enteral_vol")
    parent   = _s("sis_gastro_dieta_parenteral"); p_vol = _s("sis_gastro_dieta_parenteral_vol")
    meta_cal = _s("sis_gastro_meta_calorica")
    dieta_p  = []
    if oral:    dieta_p.append(f"Oral {oral}")
    if enteral:
        ev = (e_vol or "").strip()
        if ev and "kcal" not in ev.lower() and "ml" not in ev.lower():
            ev = f"{ev} kcal"
        dieta_p.append(f"Enteral {enteral} {ev}" if ev else f"Enteral {enteral}")
    if parent:
        pv = (p_vol or "").strip()
        if pv and "kcal" not in pv.lower() and "ml" not in pv.lower():
            pv = f"{pv} kcal"
        dieta_p.append(f"Parenteral {parent} {pv}" if pv else f"Parenteral {parent}")
    if dieta_p or meta_cal:
        linha_d = "Dieta: " + (", ".join(dieta_p) if dieta_p else "")
        if meta_cal:
            sep = "; " if dieta_p else ""
            mc = f"{meta_cal} kcal" if "kcal" not in meta_cal.lower() else meta_cal
            linha_d += sep + f"Meta calórica de {mc}"
        gastro.append(linha_d)

    na_meta  = _s("sis_gastro_na_meta")
    ingestao = _s("sis_gastro_ingestao_quanto")
    if na_meta == "Sim":
        ing = f"{ingestao} kcal" if ingestao and "kcal" not in ingestao.lower() else ingestao
        gastro.append("Na meta calórica" + (f" - {ing} nas últimas 24 horas" if ing else ""))
    elif na_meta == "Não":
        ing = f"{ingestao} kcal" if ingestao and "kcal" not in ingestao.lower() else ingestao
        gastro.append("Fora da meta calórica" + (f", {ing} nas últimas 24 horas" if ing else ""))

    escape = _s("sis_gastro_escape_glicemico")
    if escape == "Sim":
        vezes   = _s("sis_gastro_escape_vezes")
        turnos  = _turnos()
        i_m = _s("sis_gastro_insulino_dose_manha")
        i_t = _s("sis_gastro_insulino_dose_tarde")
        i_n = _s("sis_gastro_insulino_dose_noite")
        insulino = _s("sis_gastro_insulino")
        doses = [f"{d} UI" for d in [i_m, i_t, i_n] if d]
        insulino_str = " - ".join(doses) if doses else ""
        esc = "Escape glicêmico:"
        if vezes:
            try:
                n = int(str(vezes).strip())
                esc += f" {n} vez" if n == 1 else f" {n} vezes"
            except (ValueError, TypeError):
                esc += f" {vezes}"
        if turnos:  esc += f", {turnos}"
        if insulino == "Sim" and insulino_str: esc += f", em insulinoterapia {insulino_str}"
        gastro.append(esc)
    elif escape == "Não":
        gastro.append("Sem escape glicêmico, sem insulinoterapia")

    evac      = _s("sis_gastro_evacuacao")
    evac_data = _s("sis_gastro_evacuacao_data")
    laxativo  = _s("sis_gastro_laxativo")
    if evac == "Sim":
        gastro.append("Evacuação: Presente" + (f", última em {evac_data}" if evac_data else ""))
    elif evac == "Não":
        linha_ev = "Evacuação: Ausente"
        if evac_data: linha_ev += f", última em {evac_data}"
        if laxativo:  linha_ev += f", em uso de {laxativo}"
        gastro.append(linha_ev)

    _tgi_evo = [
        _evo("TGO", "sis_gastro_tgo", "sis_gastro_tgo_show"),
        _evo("TGP", "sis_gastro_tgp", "sis_gastro_tgp_show"),
        _evo("FAL", "sis_gastro_fal", "sis_gastro_fal_show"),
        _evo("GGT", "sis_gastro_ggt", "sis_gastro_ggt_show"),
        _evo("BT",  "sis_gastro_bt",  "sis_gastro_bt_show"),
    ]
    for linha in _tgi_evo:
        if linha: gastro.append(linha)

    pocus = _s("sis_gastro_pocus")
    if pocus: gastro.append(f"Pocus Exame Abdominal: {pocus}")
    obs = _s("sis_gastro_obs")
    if obs: gastro.append(f"Obs: {obs}")
    nutri_obs = _s("sis_nutri_obs")
    if nutri_obs: gastro.append(f"Nutri: {nutri_obs}")

    if gastro:
        corpo.append("")
        corpo.append("- Exame Abdominal")
        corpo.extend(gastro)

    # ── RENAL ────────────────────────────────────────────────────────────────
    renal = []

    diurese  = _s("sis_renal_diurese"); balanco = _s("sis_renal_balanco"); bal_ac = _s("sis_renal_balanco_acum")
    _ml = lambda v: f"{v} mL" if v and "ml" not in str(v).lower() else v
    bh = [p for p in [
        f"Diurese {_ml(diurese)}" if diurese else None,
        f"BH {_ml(balanco)}" if balanco else None,
        f"BH Acumulado {_ml(bal_ac)}" if bal_ac else None,
    ] if p]
    if bh: renal.append(" | ".join(bh))

    volemia = _s("sis_renal_volemia")
    if volemia: renal.append(volemia)

    _renal_evo = [
        _evo("Bal. Hídrico", "sis_renal_bh",  "sis_renal_bh_show"),
        _evo("Diurese",    "sis_renal_diu", "sis_renal_diu_show"),
        _evo("Cr",         "sis_renal_cr",  "sis_renal_cr_show"),
        _evo("Ur",         "sis_renal_ur",  "sis_renal_ur_show"),
        _evo("Na",         "sis_renal_na",  "sis_renal_na_show"),
        _evo("K",          "sis_renal_k",   "sis_renal_k_show"),
        _evo("Mg",         "sis_renal_mg",  "sis_renal_mg_show"),
        _evo("Fos",        "sis_renal_fos", "sis_renal_fos_show"),
        _evo("CaI",        "sis_renal_cai", "sis_renal_cai_show"),
    ]
    for linha in _renal_evo:
        if linha: renal.append(linha)

    trs = _s("sis_renal_trs")
    if trs == "Sim":
        trs_p = ["Em TRS"]
        via = _s("sis_renal_trs_via"); ult = _s("sis_renal_trs_ultima"); prox = _s("sis_renal_trs_proxima")
        if via:  trs_p.append(via)
        if ult:  trs_p.append(f"Última TSR em {ult}")
        if prox: trs_p.append(f"próxima programada para {prox}")
        renal.append(", ".join(trs_p))
    elif trs == "Não":
        renal.append("Sem TRS")

    pocus = _s("sis_renal_pocus")
    if pocus: renal.append(f"Pocus Renal: {pocus}")
    obs = _s("sis_renal_obs")
    if obs: renal.append(f"Obs: {obs}")
    metab_obs = _s("sis_metab_obs")
    if metab_obs: renal.append(f"Metab: {metab_obs}")

    if renal:
        corpo.append("")
        corpo.append("- Renal")
        corpo.extend(renal)

    # ── INFECCIOSO ───────────────────────────────────────────────────────────
    infec = []

    febre = _s("sis_infec_febre"); f_v = _s("sis_infec_febre_vezes"); f_u = _s("sis_infec_febre_ultima")
    if febre == "Sim":
        feb = "Febre: Presente"
        if f_v:
            try:
                n = int(str(f_v).strip())
                feb += f", {n} vez" if n == 1 else f", {n} vezes"
            except (ValueError, TypeError):
                feb += f", {f_v}"
        if f_u: feb += f"; Último pico febril: {f_u}"
        infec.append(feb)
    elif febre == "Não":
        infec.append("Febre: Ausente")

    atb       = _s("sis_infec_atb");       atb_g = _s("sis_infec_atb_guiado")
    atb_lista = _lista_e([_s("sis_infec_atb_1"), _s("sis_infec_atb_2"), _s("sis_infec_atb_3")])
    if atb == "Sim":
        guiado = {"Sim": "guiada por culturas", "Não": "empírica"}.get(atb_g or "", "")
        base = f"Antibioticoterapia{f' {guiado}' if guiado else ''}"
        infec.append(f"{base} em uso de {atb_lista}" if atb_lista else base)
    elif atb == "Não":
        infec.append("Sem antibioticoterapia")

    cult_and = _s("sis_infec_culturas_and")
    if cult_and == "Sim":
        cults = []
        for i in range(1, 5):
            s = _s(f"sis_infec_cult_{i}_sitio"); d = _s(f"sis_infec_cult_{i}_data")
            if s: cults.append(f"{s} ({d})" if d else s)
        if cults: infec.append("Culturas em andamento: " + ", ".join(cults))
    elif cult_and == "Não":
        infec.append("Sem culturas em andamento")

    _infec_evo = [
        _evo("Leucócitos","sis_infec_leuc", "sis_infec_leuc_show"),
        _evo("PCR",       "sis_infec_pcr",  "sis_infec_pcr_show"),
        _evo("VHS",       "sis_infec_vhs",  "sis_infec_vhs_show"),
    ]
    for linha in _infec_evo:
        if linha: infec.append(linha)

    iso = _s("sis_infec_isolamento")
    if iso == "Sim":
        i_tipo = _s("sis_infec_isolamento_tipo")
        infec.append(f"Isolamento: {i_tipo}" if i_tipo else "Isolamento: presente")

    pat = _s("sis_infec_patogenos")
    if pat: infec.append(f"Patógenos isolados: {pat}")

    pocus = _s("sis_infec_pocus")
    if pocus: infec.append(f"Pocus Infeccioso: {pocus}")
    obs = _s("sis_infec_obs")
    if obs: infec.append(f"Obs: {obs}")

    if infec:
        corpo.append("")
        corpo.append("- Infeccioso")
        corpo.extend(infec)

    # ── HEMATOLÓGICO ─────────────────────────────────────────────────────────
    hemato = []

    anticoag = _s("sis_hemato_anticoag")
    if anticoag == "Sim":
        ac_t = _s("sis_hemato_anticoag_tipo")
        ac_m = _s("sis_hemato_anticoag_motivo")
        if ac_t == "Plena" and ac_m:
            ac_m_display = _sigla_upper(ac_m) if ac_m else ac_m  # TEP, TVP, FA em maiúsculas
            hemato.append(f"Anticoagulação: Plena, por {ac_m_display}")
        elif ac_t:
            hemato.append(f"Anticoagulação: {ac_t}")
        else:
            hemato.append("Anticoagulação: em uso")
    elif anticoag == "Não":
        hemato.append("Sem anticoagulação")

    sangr = _s("sis_hemato_sangramento")
    if sangr == "Sim":
        s_v = _s("sis_hemato_sangramento_via"); s_d = _s("sis_hemato_sangramento_data")
        linha_s = "Sangramento presente"
        if s_v: linha_s += f"; {s_v}"
        if s_d: linha_s += f", último apresentado em {s_d}"
        hemato.append(linha_s)
    elif sangr == "Não":
        hemato.append("Sem sangramentos")

    t_data = _s("sis_hemato_transf_data")
    if t_data:
        comps = []
        for i in range(1, 4):
            cn = _s(f"sis_hemato_transf_{i}_comp"); cb = _s(f"sis_hemato_transf_{i}_bolsas")
            if cn: comps.append(f"{cn} {cb}" if cb else cn)
        hemato.append(f"Transfusão em {t_data}" + ("; " + ", ".join(comps) if comps else ""))

    _hemato_evo = [
        _evo("Hb",   "sis_hemato_hb",   "sis_hemato_hb_show"),
        _evo("Plaq", "sis_hemato_plaq", "sis_hemato_plaq_show"),
        _evo("INR",  "sis_hemato_inr",  "sis_hemato_inr_show"),
        _evo("TTPa", "sis_hemato_ttpa", "sis_hemato_ttpa_show"),
    ]
    for linha in _hemato_evo:
        if linha: hemato.append(linha)

    pocus = _s("sis_hemato_pocus")
    if pocus: hemato.append(f"Pocus Hematológico: {pocus}")
    obs = _s("sis_hemato_obs")
    if obs: hemato.append(f"Obs: {obs}")

    if hemato:
        corpo.append("")
        corpo.append("- Hematológico")
        corpo.extend(hemato)

    # ── PELE E MUSCULOESQUELÉTICO ─────────────────────────────────────────────
    pele = []

    edema = _s("sis_pele_edema")
    cruzes = _s("sis_pele_edema_cruzes")
    if edema == "Presente":
        cruzes_str = str(cruzes).strip() if cruzes else ""
        if cruzes_str in ("1", "2", "3", "4"):
            pele.append(f"Edema presente, {cruzes_str}+")
        else:
            pele.append("Edema presente")
    elif edema == "Ausente":
        pele.append("Sem edema")

    lpp = _s("sis_pele_lpp")
    if lpp == "Sim":
        lpp_items = []
        for i in range(1, 4):
            loc = _s(f"sis_pele_lpp_local_{i}"); grau = _s(f"sis_pele_lpp_grau_{i}")
            if loc: lpp_items.append(f"{loc} {grau}" if grau else loc)
        pele.append("LPP: " + ", ".join(lpp_items) if lpp_items else "LPP: presente")
    elif lpp == "Não":
        pele.append("Sem LPP")

    polineu = _s("sis_pele_polineuropatia")
    if polineu == "Sim":   pele.append("Polineuropatia do doente crítico")
    elif polineu == "Não": pele.append("Sem polineuropatia")

    cpk = _evo("CPK", "sis_pele_cpk", "sis_pele_cpk_show")
    if cpk: pele.append(cpk)

    pocus = _s("sis_pele_pocus")
    if pocus: pele.append(f"Pocus Pele e musculoesquelético: {pocus}")
    obs = _s("sis_pele_obs")
    if obs: pele.append(f"Obs: {obs}")

    if pele:
        corpo.append("")
        corpo.append("- Pele e Musculoesquelético")
        corpo.extend(pele)

    if not corpo:
        return []
    return ["# Evolução por sistemas"] + corpo


_SECAO_MAP: dict = {}   # populado após definição das funções


def _init_secao_map():
    global _SECAO_MAP
    _SECAO_MAP = {
        "identificacao":  _secao_identificacao,
        "hd":             _secao_diagnosticos,
        "comorbidades":   _secao_comorbidades,
        "muc":            _secao_muc,
        "hmpa":           _secao_hmpa,
        "dispositivos":   _secao_dispositivos,
        "culturas":       _secao_culturas,
        "antibioticos":   _secao_antibioticos,
        "complementares": _secao_complementares,
        "laboratoriais":  _secao_laboratoriais,
        "controles":      _secao_controles,
        "evolucao":       _secao_evolucao_clinica,
        "sistemas":       _secao_sistemas,
        "condutas":       _secao_condutas,
        "prescricao":     _secao_prescricao,
    }
