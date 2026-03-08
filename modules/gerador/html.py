from ._base import *
import streamlit as st


def _fmt_data_hdr(d: str) -> str:
    """Formata data para cabeçalho de tabela HTML.

    - DD/MM/AAAA → DD/MM/AAAA
    - DD/MM      → DD/MM/2026  (ano padrão)
    - Vazio/None → '—'
    """
    if not d or not d.strip():
        return "—"
    p = d.strip().split("/")
    if len(p) >= 3:
        return f"{p[0]}/{p[1]}/{p[2]}"
    if len(p) == 2:
        return f"{p[0]}/{p[1]}/2026"
    return d.strip()[:10]


def gerar_html_labs() -> str:
    """
    Gera tabela comparativa de laboratoriais como HTML puro (sem pandas).
    Mais rápido que DataFrame para renderização em st.markdown.
    Inclui todos os campos: hemato, bioquímica, gasometria, urina.
    """
    import re as _re2

    _P_NUM  = _re2.compile(r"^([0-9.,]+)")
    _P_COAG = _re2.compile(r"^([0-9.,]+[s%]?)")
    _DIFFS  = [
        ("Seg(%)",  _re2.compile(r"Seg\s*([0-9]+)",  _re2.I)),
        ("Bast(%)", _re2.compile(r"Bast\s*([0-9]+)", _re2.I)),
        ("Linf(%)", _re2.compile(r"Linf\s*([0-9]+)", _re2.I)),
        ("Mon(%)",  _re2.compile(r"Mon\s*([0-9]+)",  _re2.I)),
        ("Eos(%)",  _re2.compile(r"Eos\s*([0-9]+)",  _re2.I)),
        ("Bas(%)",  _re2.compile(r"Bas\s*([0-9]+)",  _re2.I)),
    ]

    def _v(i, campo):
        v = _get(f"lab_{i}_{campo}")
        return str(v).strip() if v else ""

    SLOTS = [i for i in range(1, 11)
             if any(_v(i, k) for k in ("data", "hb", "cr", "na", "tp", "plaq", "gas_ph"))]
    if not SLOTS:
        return ""

    _T = {1: "Hoje", 2: "Ontem", 3: "Anteontem"}
    headers = []
    for i in SLOTS:
        d = _v(i, "data")
        headers.append(_fmt_data_hdr(d) if d else _T.get(i, f"S{i}"))

    # rows: list of (label, values | None, is_sep)
    rows: list = []
    _sep_pendente: list = [None]  # separador aguardando dado para ser inserido

    def _vals(key):
        return [_v(i, key) or "-" for i in SLOTS]

    def _add(lbl, key):
        v = _vals(key)
        if any(x not in ("-", "") for x in v):
            if _sep_pendente[0] is not None:
                rows.append((_sep_pendente[0], None, True))
                _sep_pendente[0] = None
            rows.append((lbl, v, False))

    def _add_row(lbl, v):
        """Insere linha pré-calculada (para casos customizados como Ht/Leuco)."""
        if any(x not in ("-", "") for x in v):
            if _sep_pendente[0] is not None:
                rows.append((_sep_pendente[0], None, True))
                _sep_pendente[0] = None
            rows.append((lbl, v, False))

    def _sep(nome):
        _sep_pendente[0] = nome

    # HEMATO (sem separador de seção — é a primeira, aparece direto)
    _add("Hb", "hb")
    ht = [_v(i, "ht").rstrip("%") or "-" for i in SLOTS]
    _add_row("Ht (%)", ht)
    for lbl, k in [("VCM", "vcm"), ("HCM", "hcm"), ("RDW", "rdw")]:
        _add(lbl, k)

    leuco_raw = [_v(i, "leuco") for i in SLOTS]
    leuco_tot = [(_P_NUM.match(r) or type("", (), {"group": lambda s, x: r})()).group(1) or r
                 for r in leuco_raw]
    _add_row("Leuco", leuco_tot)
    for dlbl, dpat in _DIFFS:
        dv = [(dpat.search(r) and dpat.search(r).group(1) + "%") or "-" for r in leuco_raw]
        _add_row(dlbl, dv)
    _add("Plaq", "plaq")

    _sep("Renal")
    _add("Cr", "cr"); _add("Ur", "ur")

    _sep("Eletrólitos")
    for lbl, k in [("Na","na"),("K","k"),("Mg","mg"),("Pi","pi"),
                   ("CaT","cat"),("CaI","cai"),("Cl","cl")]:
        _add(lbl, k)

    _sep("Hepático")
    for lbl, k in [("TGO","tgo"),("TGP","tgp"),("FAL","fal"),("GGT","ggt")]:
        _add(lbl, k)
    _add("BT","bt"); _add("BD","bd")
    for lbl, k in [("ProtTot","prot_tot"),("Alb","alb"),
                   ("Amil","amil"),("Lipas","lipas")]:
        _add(lbl, k)

    _sep("Cardio / Inflamação")
    for lbl, k in [("CPK","cpk"),("CPK-MB","cpk_mb"),("BNP","bnp"),
                   ("Trop","trop"),("PCR","pcr"),("VHS","vhs")]:
        _add(lbl, k)

    _sep("Coagulação")
    for lbl, key in [("TP","tp"), ("TTPa","ttpa")]:
        v = [(_P_COAG.match(r) and _P_COAG.match(r).group(1)) or r for r in _vals(key)]
        _add_row(lbl, v)

    _sep("Gasometria")
    for lbl, k in [("Hora","gas_hora"),("Tipo","gas_tipo"),
                   ("pH","gas_ph"),("pCO2","gas_pco2"),("Bic","gas_hco3"),
                   ("BE","gas_be"),("Cl(g)","gas_cl"),("AG","gas_ag"),
                   ("pO2","gas_po2"),("SatO2","gas_sat"),
                   ("Na(g)","gas_na"),("K(g)","gas_k"),("CaI(g)","gas_cai"),
                   ("Lac","gas_lac"),("pCO2(v)","gasv_pco2"),("SvO2","svo2")]:
        _add(lbl, k)

    _sep("Urina")
    for lbl, k in [("Dens","ur_dens"),("L.Est","ur_le"),("Nit","ur_nit"),
                   ("Leuco(U)","ur_leu"),("Hem","ur_hm"),("Prot(U)","ur_prot"),
                   ("Cet","ur_cet"),("Glic(U)","ur_glic")]:
        _add(lbl, k)

    if not any(not is_sep for _, _, is_sep in rows):
        return ""

    return _build_html_table(headers, rows)


def gerar_html_controles() -> str:
    """
    Tabela comparativa dos Controles & BH como HTML puro.
    Colunas = dias (anteontem → ontem → hoje), linhas = parâmetros.
    """
    def _v(dia, campo):
        v = _get(f"ctrl_{dia}_{campo}")
        return str(v).strip() if v else ""

    _DIAS   = ["ant10", "ant9", "ant8", "ant7", "ant6",
               "ant5", "ant4", "anteontem", "ontem", "hoje"]
    _LABELS = {
        "ant10": "10º dia", "ant9": "9º dia", "ant8": "8º dia",
        "ant7":  "7º dia",  "ant6": "6º dia", "ant5": "5º dia",
        "ant4":  "4º dia",  "anteontem": "Anteontem",
        "ontem": "Ontem",   "hoje": "Hoje",
    }
    _VITAIS = [
        ("PAS",    "pas"),   ("PAD",   "pad"),  ("PAM",   "pam"),
        ("FC",     "fc"),    ("FR",    "fr"),    ("SatO2", "sato2"),
        ("Temp",   "temp"),  ("Glic",  "glic"),
    ]

    # Descobre quais dias têm dados
    dias_ativos = [d for d in _DIAS
                   if any(_v(d, k) for k in ("data", "pas_min", "diurese", "balanco"))]
    if not dias_ativos:
        return ""

    headers = []
    for d in dias_ativos:
        data = _v(d, "data")
        headers.append(_fmt_data_hdr(data) if data else _LABELS[d])

    rows: list = []
    _sep_pendente: list = [None]

    def _flush_sep():
        if _sep_pendente[0] is not None:
            rows.append((_sep_pendente[0], None, True))
            _sep_pendente[0] = None

    def _add_mm(lbl, chave):
        vals = []
        for d in dias_ativos:
            mn = _v(d, f"{chave}_min")
            mx = _v(d, f"{chave}_max")
            if mn and mx:
                vals.append(f"{mn}-{mx}")
            elif mn or mx:
                vals.append(mn or mx)
            else:
                vals.append("-")
        if any(v != "-" for v in vals):
            _flush_sep()
            rows.append((lbl, vals, False))

    def _add_single(lbl, chave):
        vals = [_v(d, chave) or "-" for d in dias_ativos]
        if any(v != "-" for v in vals):
            _flush_sep()
            rows.append((lbl, vals, False))

    for lbl, chave in _VITAIS:
        _add_mm(lbl, chave)

    _sep_pendente[0] = "─"  # separador só aparece se houver dado abaixo
    _add_single("Diurese", "diurese")
    _add_single("Evacuação", "evacuacao")
    _add_single("BH", "balanco")

    if not any(not is_sep for _, _, is_sep in rows):
        return ""

    return _build_html_table(headers, rows)


def _build_html_table(headers: list, rows: list, max_height: str = "74vh") -> str:
    """Monta string HTML de tabela comparativa a partir de headers e rows."""
    n = len(headers)
    colgroup = f'<colgroup><col style="width:130px">{"<col>" * n}</colgroup>'
    th = "".join(f"<th>{h}</th>" for h in headers)
    css = (
        "<style>"
        ".ct{border-collapse:collapse;width:100%;font-size:0.83rem;font-family:sans-serif;table-layout:fixed}"
        ".ct th,.ct td{border:1px solid #e0e0e0;padding:4px 8px;text-align:center;"
        "overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
        ".ct th{background:#1a73e8;color:#fff;font-weight:600;position:sticky;top:0;z-index:1}"
        ".ct td:first-child{text-align:left;font-weight:500;color:#202124;background:#f8f9fa}"
        ".ct tr:hover td{background:#e8f0fe!important}"
        ".ct tr.sp td{background:#1a73e8;color:#fff;font-size:0.7rem;font-weight:700;"
        "letter-spacing:.08em;text-transform:uppercase;padding:3px 8px}"
        ".ct tr:nth-child(even):not(.sp) td:first-child{background:#f1f3f4}"
        "</style>"
    )
    parts = [css, f'<div style="overflow:auto;max-height:{max_height}">',
             f'<table class="ct">{colgroup}<thead><tr><th>Parâmetro</th>{th}</tr></thead><tbody>']
    for lbl, vals, is_sep in rows:
        if is_sep:
            label = lbl if lbl and lbl != "─" else "&nbsp;"
            parts.append(f'<tr class="sp"><td colspan="{n+1}">{label}</td></tr>')
        else:
            tds = "".join(f"<td>{'—' if v == '-' else v}</td>" for v in vals)
            parts.append(f"<tr><td>{lbl}</td>{tds}</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def gerar_html_comparativo() -> tuple[str, str]:
    """
    Retorna (html_labs, html_ctrl) — cada tabela com suas próprias colunas/datas.

    Regras:
      - Título de cada coluna = data preenchida pelo usuário.
      - Ordem das colunas = ordem de preenchimento (slot 1 → slot 3, slot 5 → slot 10).
      - Slot 4 (Admissão/Externo) SEMPRE última coluna de labs — nunca é deslocado.
      - Controles: hoje → ant5 em ordem.
      - As duas tabelas são independentes; datas podem ser diferentes entre elas.
    """
    import re as _re2

    def _slot_tem_dado(slot: int) -> bool:
        for suf in ("data", "hb", "cr", "na", "gas_ph", "ur_dens"):
            if (_get(f"lab_{slot}_{suf}") or "").strip():
                return True
        return False

    def _dia_tem_dado(dia: str) -> bool:
        for suf in ("data", "pas_min", "fc_min", "diurese", "balanco"):
            if (_get(f"ctrl_{dia}_{suf}") or "").strip():
                return True
        return False

    # ── 1. Slots de labs (regulares em ordem + admissão ao final) ────────────
    lab_slots = [s for s in [1, 2, 3, 5, 6, 7, 8, 9, 10] if _slot_tem_dado(s)]
    if _slot_tem_dado(4):
        lab_slots.append(4)   # admissão sempre por último

    # ── 2. Dias de controles em ordem ────────────────────────────────────────
    _DIAS_CTRL = ["hoje", "ontem", "anteontem", "ant4", "ant5"]
    ctrl_dias = [d for d in _DIAS_CTRL if _dia_tem_dado(d)]

    # ── 3. Cabeçalhos independentes ───────────────────────────────────────────
    lab_headers  = [_fmt_data_hdr((_get(f"lab_{s}_data") or "").strip()) for s in lab_slots]
    ctrl_headers = [_fmt_data_hdr((_get(f"ctrl_{d}_data") or "").strip()) for d in ctrl_dias]

    # ── 4. Linhas de labs ─────────────────────────────────────────────────────
    _P_NUM  = _re2.compile(r"^([0-9.,]+)")
    _P_COAG = _re2.compile(r"^([0-9.,]+[s%]?)")
    _DIFFS  = [
        ("Seg(%)",  _re2.compile(r"Seg\s*([0-9]+)",  _re2.I)),
        ("Bast(%)", _re2.compile(r"Bast\s*([0-9]+)", _re2.I)),
        ("Linf(%)", _re2.compile(r"Linf\s*([0-9]+)", _re2.I)),
        ("Mon(%)",  _re2.compile(r"Mon\s*([0-9]+)",  _re2.I)),
        ("Eos(%)",  _re2.compile(r"Eos\s*([0-9]+)",  _re2.I)),
        ("Bas(%)",  _re2.compile(r"Bas\s*([0-9]+)",  _re2.I)),
    ]

    def _vl(slot, campo):
        v = _get(f"lab_{slot}_{campo}")
        return str(v).strip() if v else ""

    lab_rows: list = []
    _sep_l: list = [None]

    def _add_l(lbl, key):
        v = [_vl(s, key) or "-" for s in lab_slots]
        if any(x not in ("-", "") for x in v):
            if _sep_l[0]: lab_rows.append((_sep_l[0], None, True)); _sep_l[0] = None
            lab_rows.append((lbl, v, False))

    def _add_l_row(lbl, v):
        if any(x not in ("-", "") for x in v):
            if _sep_l[0]: lab_rows.append((_sep_l[0], None, True)); _sep_l[0] = None
            lab_rows.append((lbl, v, False))

    def _sep_l_set(nome): _sep_l[0] = nome

    _add_l("Hb", "hb")
    ht = [_vl(s, "ht").rstrip("%") or "-" for s in lab_slots]
    _add_l_row("Ht (%)", ht)
    for lbl, k in [("VCM","vcm"),("HCM","hcm"),("RDW","rdw")]: _add_l(lbl, k)
    leuco_raw = [_vl(s, "leuco") for s in lab_slots]
    leuco_tot = [(_P_NUM.match(r) and _P_NUM.match(r).group(1)) or r for r in leuco_raw]
    _add_l_row("Leuco", leuco_tot)
    for dlbl, dpat in _DIFFS:
        dv = [(dpat.search(r) and dpat.search(r).group(1)+"%") or "-" for r in leuco_raw]
        _add_l_row(dlbl, dv)
    _add_l("Plaq", "plaq")
    _sep_l_set("Renal"); _add_l("Cr","cr"); _add_l("Ur","ur")
    _sep_l_set("Eletrólitos")
    for lbl, k in [("Na","na"),("K","k"),("Mg","mg"),("Pi","pi"),
                   ("CaT","cat"),("CaI","cai"),("Cl","cl")]: _add_l(lbl, k)
    _sep_l_set("Hepático")
    for lbl, k in [("TGO","tgo"),("TGP","tgp"),("FAL","fal"),("GGT","ggt")]: _add_l(lbl, k)
    _add_l("BT","bt"); _add_l("BD","bd")
    for lbl, k in [("ProtTot","prot_tot"),("Alb","alb"),
                   ("Amil","amil"),("Lipas","lipas")]: _add_l(lbl, k)
    _sep_l_set("Cardio / Inflamação")
    for lbl, k in [("CPK","cpk"),("CPK-MB","cpk_mb"),("BNP","bnp"),
                   ("Trop","trop"),("PCR","pcr"),("VHS","vhs")]: _add_l(lbl, k)
    _sep_l_set("Coagulação")
    for lbl, key in [("TP","tp"),("TTPa","ttpa")]:
        v = [(_P_COAG.match(_vl(s,key)) and _P_COAG.match(_vl(s,key)).group(1))
             or _vl(s,key) or "-" for s in lab_slots]
        _add_l_row(lbl, v)
    _sep_l_set("Gasometria")
    for lbl, k in [("Hora","gas_hora"),("Tipo","gas_tipo"),
                   ("pH","gas_ph"),("pCO2","gas_pco2"),("Bic","gas_hco3"),
                   ("BE","gas_be"),("Cl(g)","gas_cl"),("AG","gas_ag"),
                   ("pO2","gas_po2"),("SatO2","gas_sat"),
                   ("Na(g)","gas_na"),("K(g)","gas_k"),("CaI(g)","gas_cai"),
                   ("Lac","gas_lac"),("pCO2(v)","gasv_pco2"),("SvO2","svo2")]:
        _add_l(lbl, k)
    _sep_l_set("Urina")
    for lbl, k in [("Dens","ur_dens"),("L.Est","ur_le"),("Nit","ur_nit"),
                   ("Leuco(U)","ur_leu"),("Hem","ur_hm"),("Prot(U)","ur_prot"),
                   ("Cet","ur_cet"),("Glic(U)","ur_glic")]: _add_l(lbl, k)

    html_labs = _build_html_table(lab_headers, lab_rows, "60vh") if any(
        not s for _, _, s in lab_rows) else ""

    # ── 5. Linhas de controles ────────────────────────────────────────────────
    _VITAIS_C = [("PAS","pas"),("PAD","pad"),("PAM","pam"),("FC","fc"),
                 ("FR","fr"),("SatO2","sato2"),("Temp","temp"),("Glic","glic")]

    def _vc(dia, campo):
        v = _get(f"ctrl_{dia}_{campo}")
        return str(v).strip() if v else ""

    def _parse_num(val: str) -> float:
        if not val or val.strip() in ("-", ""):
            return 0.0
        try:
            return float(val.strip().replace(",", ".").replace(" ", ""))
        except ValueError:
            return 0.0

    # BH Acumulado: soma corrente da mais antiga → mais recente.
    # ctrl_dias está ordenado do mais recente (hoje) ao mais antigo (ant5).
    # Para cada posição i, o acumulado = soma de ctrl_dias[i..fim] (mais antigos incluídos).
    bh_raw = [_parse_num(_vc(d, "balanco")) for d in ctrl_dias]
    # sufixo reverso: soma de i até o final
    n_c = len(bh_raw)
    bh_acum: list[str] = []
    for i in range(n_c):
        total = sum(bh_raw[i:])           # soma deste dia até o mais antigo
        if total == 0 and all(v == 0 for v in bh_raw[i:]):
            bh_acum.append("-")
        else:
            bh_acum.append(f"{total:+.0f}" if total != 0 else "0")

    ctrl_rows: list = []
    _sep_c: list = [None]

    def _flush_c():
        if _sep_c[0]: ctrl_rows.append((_sep_c[0], None, True)); _sep_c[0] = None

    def _add_c_mm(lbl, chave):
        vals = []
        for dia in ctrl_dias:
            mn = _vc(dia, f"{chave}_min"); mx = _vc(dia, f"{chave}_max")
            vals.append(f"{mn}-{mx}" if mn and mx else (mn or mx or "-"))
        if any(v != "-" for v in vals):
            _flush_c(); ctrl_rows.append((lbl, vals, False))

    def _add_c_single(lbl, chave):
        vals = [_vc(dia, chave) or "-" for dia in ctrl_dias]
        if any(v != "-" for v in vals):
            _flush_c(); ctrl_rows.append((lbl, vals, False))

    for lbl, chave in _VITAIS_C: _add_c_mm(lbl, chave)
    _sep_c[0] = "─"
    _add_c_single("Diurese", "diurese")
    _add_c_single("Evacuação", "evacuacao")

    # BH: linha normal
    bh_vals = [_vc(d, "balanco") or "-" for d in ctrl_dias]
    if any(v != "-" for v in bh_vals):
        _flush_c(); ctrl_rows.append(("BH", bh_vals, False))

    # BH Acumulado: só aparece se houver pelo menos um BH preenchido
    if any(v != "-" for v in bh_acum):
        ctrl_rows.append(("BH Acumulado", bh_acum, False))

    html_ctrl = _build_html_table(ctrl_headers, ctrl_rows, "40vh") if any(
        not s for _, _, s in ctrl_rows) else ""

    return html_labs, html_ctrl
