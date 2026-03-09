"""
Pacote gerador — cada seção em seu próprio módulo.
Interface pública idêntica ao arquivo original.
"""
import streamlit as st
from ._base import (
    _get,
    _caps_para_certo,
    _caps_obs_linha,
    _sigla_upper,
    _obs_para_linhas,
    _calcular_dias,
)
from .html import gerar_html_labs, gerar_html_controles

from .identificacao import _secao_identificacao
from .scores import _secao_scores
from .diagnosticos import _secao_diagnosticos
from .culturas import _secao_culturas
from .dispositivos import _secao_dispositivos
from .hmpa import _secao_hmpa
from .intraoperatorio import _secao_intraoperatorio
from .muc import _secao_muc
from .comorbidades import _secao_comorbidades
from .antibioticos import _secao_antibioticos
from .complementares import _secao_complementares
from .laboratoriais import _secao_laboratoriais
from .controles import _secao_controles
from .evolucao_clinica import _secao_evolucao_clinica
from .condutas import _secao_condutas
from .prescricao import _secao_prescricao
from .sistemas import _secao_sistemas

_SECAO_MAP: dict = {}   # populado após definição das funções


def _init_secao_map():
    global _SECAO_MAP
    _SECAO_MAP = {
        "identificacao":  _secao_identificacao,
        "scores":         _secao_scores,
        "hd":             _secao_diagnosticos,
        "comorbidades":   _secao_comorbidades,
        "muc":            _secao_muc,
        "hmpa":             _secao_hmpa,
        "intraoperatorio":  _secao_intraoperatorio,
        "dispositivos":     _secao_dispositivos,
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


def gerar_secao(key: str) -> str:
    """Gera o texto de uma seção específica pelo seu identificador.
    Retorna string vazia se a flag inc_{key} estiver desativada."""
    if not st.session_state.get(f"inc_{key}", True):
        return ""
    if not _SECAO_MAP:
        _init_secao_map()
    fn = _SECAO_MAP.get(key)
    if fn is None:
        return ""
    linhas = fn()
    if not linhas:
        return ""
    return "\n".join(linhas)


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

    SLOTS = [i for i in range(1, 31)
             if any(_v(i, k) for k in ("data", "hb", "cr", "na", "tp", "plaq", "gas_ph"))]
    if not SLOTS:
        return ""

    _T = {1: "Hoje", 2: "Ontem", 3: "Anteontem"}
    headers = []
    for i in SLOTS:
        d = _v(i, "data")
        if d:
            p = d.split("/")
            headers.append(f"{p[0]}/{p[1]}" if len(p) >= 2 else d[:5])
        else:
            headers.append(_T.get(i, f"S{i}"))

    # rows: list of (label, values | None, is_sep)
    rows: list = []

    def _vals(key):
        return [_v(i, key) or "-" for i in SLOTS]

    def _add(lbl, key):
        v = _vals(key)
        if any(x not in ("-", "") for x in v):
            rows.append((lbl, v, False))

    def _sep(nome):
        rows.append((nome, None, True))

    # HEMATO
    _add("Hb", "hb")
    ht = [_v(i, "ht").rstrip("%") or "-" for i in SLOTS]
    if any(x not in ("-", "") for x in ht):
        rows.append(("Ht (%)", ht, False))
    for lbl, k in [("VCM", "vcm"), ("HCM", "hcm"), ("RDW", "rdw")]:
        _add(lbl, k)

    leuco_raw = [_v(i, "leuco") for i in SLOTS]
    leuco_tot = [(_P_NUM.match(r) or type("", (), {"group": lambda s, x: r})()).group(1) or r
                 for r in leuco_raw]
    if any(x not in ("-", "") for x in leuco_tot):
        rows.append(("Leuco", leuco_tot, False))
    for dlbl, dpat in _DIFFS:
        dv = [(dpat.search(r) and dpat.search(r).group(1) + "%") or "-" for r in leuco_raw]
        if any(x != "-" for x in dv):
            rows.append((dlbl, dv, False))
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
        if any(x not in ("-","") for x in v):
            rows.append((lbl, v, False))

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

    _DIAS   = ["ant5", "ant4", "anteontem", "ontem", "hoje"]
    _LABELS = {"ant5": "5º dia", "ant4": "4º dia", "anteontem": "Anteontem", "ontem": "Ontem", "hoje": "Hoje"}
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
        if data:
            p = data.split("/")
            headers.append(f"{p[0]}/{p[1]}" if len(p) >= 2 else data[:5])
        else:
            headers.append(_LABELS[d])

    rows: list = []

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
            rows.append((lbl, vals, False))

    def _add_single(lbl, chave):
        vals = [_v(d, chave) or "-" for d in dias_ativos]
        if any(v != "-" for v in vals):
            rows.append((lbl, vals, False))

    for lbl, chave in _VITAIS:
        _add_mm(lbl, chave)

    rows.append(("─", None, True))  # separador visual
    _add_single("Diurese", "diurese")
    _add_single("BH", "balanco")

    if not any(not is_sep for _, _, is_sep in rows):
        return ""

    return _build_html_table(headers, rows)


def _build_html_table(headers: list, rows: list) -> str:
    """Monta string HTML de tabela comparativa a partir de headers e rows."""
    n = len(headers)
    th = "".join(f"<th>{h}</th>" for h in headers)
    css = (
        "<style>"
        ".ct{border-collapse:collapse;width:100%;font-size:0.83rem;font-family:sans-serif}"
        ".ct th,.ct td{border:1px solid #e0e0e0;padding:4px 10px;text-align:center;white-space:nowrap}"
        ".ct th{background:#1a73e8;color:#fff;font-weight:600;position:sticky;top:0;z-index:1}"
        ".ct td:first-child{text-align:left;font-weight:500;color:#202124;background:#f8f9fa;min-width:90px}"
        ".ct tr:hover td{background:#e8f0fe!important}"
        ".ct tr.sp td{background:#1a73e8;color:#fff;font-size:0.7rem;font-weight:700;"
        "letter-spacing:.08em;text-transform:uppercase;padding:3px 10px}"
        ".ct tr:nth-child(even):not(.sp) td:first-child{background:#f1f3f4}"
        "</style>"
    )
    parts = [css, f'<div style="overflow:auto;max-height:74vh">',
             f'<table class="ct"><thead><tr><th>Parâmetro</th>{th}</tr></thead><tbody>']
    for lbl, vals, is_sep in rows:
        if is_sep:
            label = lbl if lbl and lbl != "─" else "&nbsp;"
            parts.append(f'<tr class="sp"><td colspan="{n+1}">{label}</td></tr>')
        else:
            tds = "".join(f"<td>{'—' if v == '-' else v}</td>" for v in vals)
            parts.append(f"<tr><td>{lbl}</td>{tds}</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def gerar_texto_final() -> str:
    """
    Monta o texto final do prontuário concatenando todas as seções.
    Seções com inc_{key}=False são excluídas da saída (dados preservados).
    """
    def _inc(key: str) -> bool:
        return st.session_state.get(f"inc_{key}", True)

    secoes = []

    if _inc("identificacao"):   secoes.append(_secao_identificacao())
    if _inc("scores"):          secoes.append(_secao_scores())
    if _inc("hd"):              secoes.append(_secao_diagnosticos())
    if _inc("comorbidades"):    secoes.append(_secao_comorbidades())
    if _inc("muc"):             secoes.append(_secao_muc())
    if _inc("dispositivos"):    secoes.append(_secao_dispositivos())
    if _inc("culturas"):        secoes.append(_secao_culturas())
    if _inc("hmpa"):            secoes.append(_secao_hmpa())
    if _inc("intraoperatorio"): secoes.append(_secao_intraoperatorio())
    if _inc("antibioticos"):    secoes.append(_secao_antibioticos())
    if _inc("complementares"):  secoes.append(_secao_complementares())
    if _inc("laboratoriais"):   secoes.append(_secao_laboratoriais())
    if _inc("controles"):       secoes.append(_secao_controles())
    if _inc("evolucao"):        secoes.append(_secao_evolucao_clinica())
    if _inc("sistemas"):        secoes.append(_secao_sistemas())
    if _inc("condutas"):        secoes.append(_secao_condutas())
    if _inc("prescricao"):      secoes.append(_secao_prescricao())

    blocos = []
    for s in secoes:
        if not s:
            continue
        # Garante que nenhuma seção termine com linhas em branco
        while s and s[-1] == "":
            s.pop()
        if s:
            blocos.append("\n".join(s))
    texto = "\n\n".join(blocos)
    # Normaliza ml → mL em toda a saída
    texto = texto.replace(" ml", " mL")
    return texto
