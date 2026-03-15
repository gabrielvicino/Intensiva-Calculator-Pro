"""Dose Infusão Contínua — tabela AG Grid (tipo Excel)."""

import math
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from utils import load_db_infusao, mostrar_rodape

st.markdown("""<style>
h1,h2,h3{color:#0F9D58;font-family:'Roboto',sans-serif}
[data-testid="stStatusWidget"]{display:none!important}
/* label do peso */
div[data-testid="stNumberInput"] label p{font-size:1.1em!important;font-weight:700!important}
</style>""", unsafe_allow_html=True)

_AGGRID_CSS = {
    ".ag-cell": {
        "display": "flex !important",
        "align-items": "center !important",
        "justify-content": "center !important",
        "border-right": "1px solid #e0e0e0 !important",
    },
    '.ag-cell[col-id="Medicação"]': {
        "justify-content": "flex-start !important",
    },
    ".ag-header-cell-label": {
        "justify-content": "center !important",
        "font-weight": "700 !important",
        "font-size": "1.0em !important",
        "color": "#222 !important",
    },
    ".ag-header-cell": {
        "border-right": "1px solid #d0d0d0 !important",
    },
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def _fmt(v, casas=1):
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        if v == 0:
            return "—"
        return (
            f"{{:,.{casas}f}}"
            .format(v)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    return str(v)


def _fmt_dose(v):
    if v is None or v == 0:
        return "0"
    if v >= 1 and v == int(v):
        return str(int(v))
    if v >= 1:
        return _fmt(v, 1)
    return _fmt(v, 2)


def _fl(row, col, fb=0.0):
    try:
        val = row.get(col, fb)
        return float(val) if val is not None and pd.notna(val) else fb
    except (TypeError, ValueError):
        return fb


def _dose_to_mlh(dose, u, cp, cs, w):
    try:
        dose = float(dose)
    except Exception:
        return 0.0
    if dose == 0 or cp == 0 or w == 0:
        return 0.0
    if   u == "ng/kg/min":  return (dose * w * 60) / (cs * 1000) if cs else 0
    elif u == "ng/kg/h":    return (dose * w) / (cs * 1000) if cs else 0
    elif u == "mcg/kg/min": return (dose * w * 60) / cs if cs else 0
    elif u == "mcg/kg/h":   return (dose * w) / cs if cs else 0
    elif u == "mcg/min":    return (dose * 60) / cs if cs else 0
    elif u == "mcg/h":      return dose / cs if cs else 0
    elif u == "mg/kg/h":    return (dose * w) / cp
    elif u == "mg/kg/min":  return (dose * w * 60) / cp
    elif u == "mg/h":       return dose / cp
    elif u == "mg/min":     return (dose * 60) / cp
    elif u == "g/h":        return dose / cp
    elif u == "UI/kg/h":    return (dose * w) / cp
    elif u == "UI/kg/min":  return (dose * w * 60) / cp
    elif u == "UI/h":       return dose / cp
    elif u == "UI/min":     return (dose * 60) / cp
    elif u == "mEq/h":      return dose / cp
    elif u == "mEq/kg/h":   return (dose * w) / cp
    elif u == "mmol/h":     return dose / cp
    elif u == "mmol/kg/h":  return (dose * w) / cp
    return 0.0


def _mlh_to_dose(mlh, u, cp, cs, w):
    if mlh <= 0 or w <= 0:
        return 0.0
    if   u == "mcg/kg/min": return (mlh * cs) / w / 60 if cs else 0
    elif u == "mcg/kg/h":   return (mlh * cs) / w if cs else 0
    elif u == "mg/kg/h":    return (mlh * cp) / w
    elif u == "mg/kg/min":  return (mlh * cp) / w / 60
    elif u == "UI/kg/h":    return (mlh * cp) / w
    elif u == "UI/kg/min":  return (mlh * cp) / w / 60
    elif u == "mcg/h":      return mlh * cs if cs else 0
    elif u == "mcg/min":    return (mlh * cs) / 60 if cs else 0
    elif u == "mg/h":       return mlh * cp
    elif u == "mg/min":     return (mlh * cp) / 60
    elif u == "UI/h":       return mlh * cp
    elif u == "UI/min":     return (mlh * cp) / 60
    elif u == "g/h":        return mlh * cp
    elif u == "ng/kg/min":  return (mlh * cs * 1000) / w / 60 if cs else 0
    elif u == "ng/kg/h":    return (mlh * cs * 1000) / w if cs else 0
    elif u == "mEq/h":      return mlh * cp
    elif u == "mEq/kg/h":   return (mlh * cp) / w
    elif u == "mmol/h":     return mlh * cp
    elif u == "mmol/kg/h":  return (mlh * cp) / w
    return 0.0


def _conc_label(unit):
    if "UI" in unit:
        return "UI/ml"
    if unit.startswith("g"):
        return "g/ml"
    return "mg/ml"


def _vel_str(mlh):
    if mlh <= 0:
        return "—"
    return f"{mlh} ml/h"


# ── Página ───────────────────────────────────────────────────────────────────

st.header("💉 Dose Infusão Contínua")

df_inf = load_db_infusao()
if df_inf.empty:
    st.error("Banco de dados não encontrado.")
    st.stop()

df_inf = df_inf.sort_values("nome_formatado").reset_index(drop=True)

peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.5, format="%.1f")
if st.button("🔄 Restaurar padrões"):
    for k in list(st.session_state.keys()):
        if k.startswith("_inf_"):
            del st.session_state[k]
    st.rerun()

st.markdown(
    '<div style="font-size:.85em;color:#333;margin:6px 0 10px 0">'
    '*Modifique os valores em <b>negrito</b> dentro das colunas cinzas.'
    '</div>',
    unsafe_allow_html=True,
)

# ── Construir DataFrame para o grid ──────────────────────────────────────────
rows = []
for i, row in df_inf.iterrows():
    nome = str(row.get("nome_formatado", "")).strip()
    if not nome:
        continue

    mg_a = _fl(row, "mg_amp")
    v_a  = _fl(row, "vol_amp")
    dmin = _fl(row, "dose_min")
    dhab = _fl(row, "dose_max_hab")
    dmax = _fl(row, "dose_max_tol")
    unit = str(row.get("unidade", "")).strip()
    d_amp = int(max(_fl(row, "qtd_amp_padrao", 1), 1))
    d_dil = int(max(_fl(row, "diluente_padrao", 50), 0))

    amp = int(st.session_state.get(f"_inf_a_{i}", d_amp))
    dil = int(st.session_state.get(f"_inf_d_{i}", d_dil))

    qt = amp * mg_a
    vt = max((amp * v_a) + dil, 1)
    cp = qt / vt
    cs = cp * 1000

    b_min = math.ceil(_dose_to_mlh(dmin, unit, cp, cs, peso))
    b_hab = round(_dose_to_mlh(dhab, unit, cp, cs, peso))
    b_max = round(_dose_to_mlh(dmax, unit, cp, cs, peso))

    vel_preset = max(b_min, 0)
    vel = int(st.session_state.get(f"_inf_v_{i}", vel_preset))

    dose_str = ""
    alerta = ""
    if vel > 0:
        dr = _mlh_to_dose(vel, unit, cp, cs, peso)
        dose_str = f"{_fmt(dr, 2)} {unit}"
        if dmax > 0 and dr > dmax:
            alerta = "🚨 Acima máx."
        elif dhab > 0 and dr > dhab:
            alerta = "⚠️ Acima hab."
        elif dmin > 0 and dr < dmin:
            alerta = "↘️ Abaixo mín."
        else:
            alerta = "✅ Adequada"

    rows.append({
        "_idx": i,
        "_amp": amp, "_dil": dil, "_vel": vel,
        "Medicação": nome,
        "*Nº Ampolas": f"{amp} amp",
        "*Vol. Diluente": "Puro" if dil == 0 else f"{dil} ml",
        "Vol. Total": f"{int(vt)} ml",
        "Concentração": f"{_fmt(cp, 2)} {_conc_label(unit)}",
        "Vel. Mínima": _vel_str(b_min),
        "Vel. Máx. Habitual": _vel_str(b_hab),
        "Vel. Máx. Estudada": _vel_str(b_max),
        "*Vel. Bomba": f"{vel} ml/h",
        "Dose Atual": dose_str,
        "Interpretação": alerta,
    })

df_grid = pd.DataFrame(rows)

# ── Configurar AG Grid ───────────────────────────────────────────────────────

gb = GridOptionsBuilder.from_dataframe(df_grid)

gb.configure_default_column(
    sortable=False, filterable=False, resizable=True,
    cellStyle={"textAlign": "center"},
)

gb.configure_grid_options(
    rowHeight=40,
    headerHeight=42,
    suppressMovableColumns=True,
    domLayout="autoHeight",
)

gb.configure_column("_idx", hide=True)
gb.configure_column("_amp", hide=True)
gb.configure_column("_dil", hide=True)
gb.configure_column("_vel", hide=True)

gb.configure_column("Medicação",
    cellStyle={"textAlign": "left", "fontWeight": "700", "color": "#222"},
    width=190, minWidth=170, pinned="left")

_C = {"textAlign": "center"}
_EDIT = {**_C, "backgroundColor": "#F5F5F5", "fontWeight": "600"}

gb.configure_column("*Nº Ampolas",
    editable=True, cellStyle=_EDIT, width=105, minWidth=95)

gb.configure_column("*Vol. Diluente",
    editable=True, cellStyle=_EDIT, width=115, minWidth=105)

gb.configure_column("Vol. Total", cellStyle=_C, width=90, minWidth=85)
gb.configure_column("Concentração", cellStyle=_C, width=115, minWidth=105)

gb.configure_column("Vel. Mínima",
    cellStyle={**_C, "color": "#1565C0", "fontWeight": "bold"},
    width=120, minWidth=100)

gb.configure_column("Vel. Máx. Habitual",
    cellStyle={**_C, "color": "#E65100", "fontWeight": "bold"},
    width=145, minWidth=130)

gb.configure_column("Vel. Máx. Estudada",
    cellStyle={**_C, "color": "#C62828", "fontWeight": "bold"},
    width=145, minWidth=130)

gb.configure_column("*Vel. Bomba",
    editable=True, cellStyle=_EDIT, width=105, minWidth=95)

_DOSE_JS = JsCode("""
function(params) {
    var base = {textAlign:'center'};
    var interp = params.data['Interpretação'] || '';
    if (interp.indexOf('Adequada') >= 0)
        return Object.assign(base, {color:'#2E7D32', fontWeight:'bold'});
    if (interp.indexOf('Abaixo') >= 0)
        return Object.assign(base, {color:'#1565C0', fontWeight:'bold'});
    if (interp.indexOf('Acima hab') >= 0)
        return Object.assign(base, {color:'#E65100', fontWeight:'bold'});
    if (interp.indexOf('Acima') >= 0)
        return Object.assign(base, {color:'#C62828', fontWeight:'bold'});
    return base;
}
""")

gb.configure_column("Dose Atual",
    cellStyle=_DOSE_JS, width=140, minWidth=120)

_INTERP_JS = JsCode("""
function(params) {
    var base = {textAlign:'center'};
    var v = params.value || '';
    if (v.indexOf('Adequada') >= 0)
        return Object.assign(base, {backgroundColor:'#E8F5E9', color:'#2E7D32', fontWeight:'bold'});
    if (v.indexOf('Abaixo') >= 0)
        return Object.assign(base, {backgroundColor:'#E3F2FD', color:'#1565C0', fontWeight:'bold'});
    if (v.indexOf('Acima hab') >= 0)
        return Object.assign(base, {backgroundColor:'#FFF8E1', color:'#F57F17', fontWeight:'bold'});
    if (v.indexOf('Acima') >= 0)
        return Object.assign(base, {backgroundColor:'#FFEBEE', color:'#C62828', fontWeight:'bold'});
    return base;
}
""")

gb.configure_column("Interpretação", cellStyle=_INTERP_JS, width=140, minWidth=120)

# ── Renderizar grid ──────────────────────────────────────────────────────────

_grid_height = 42 + len(rows) * 40 + 10

response = AgGrid(
    df_grid,
    gridOptions=gb.build(),
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    theme="streamlit",
    custom_css=_AGGRID_CSS,
    height=_grid_height,
)

# ── Detectar edições e salvar no session_state ───────────────────────────────

def _parse_int(val, fallback=0):
    """Extrai inteiro de strings como '5 amp', '246 ml', '3 ml/h'."""
    try:
        return int(val)
    except (ValueError, TypeError):
        pass
    import re
    m = re.match(r"(\d+)", str(val).strip())
    return int(m.group(1)) if m else fallback

edited = pd.DataFrame(response["data"])
changed = False

for _, erow in edited.iterrows():
    try:
        idx = int(erow["_idx"])
    except (ValueError, TypeError):
        continue

    orig_row = df_grid.loc[df_grid["_idx"] == idx]
    if orig_row.empty:
        continue
    orig = orig_row.iloc[0]

    new_amp = _parse_int(erow["*Nº Ampolas"], int(orig["_amp"]))
    if new_amp != int(orig["_amp"]):
        st.session_state[f"_inf_a_{idx}"] = max(new_amp, 1)
        changed = True

    new_dil = _parse_int(erow["*Vol. Diluente"], int(orig["_dil"]))
    if new_dil != int(orig["_dil"]):
        st.session_state[f"_inf_d_{idx}"] = max(new_dil, 0)
        changed = True

    new_vel = _parse_int(erow["*Vel. Bomba"], int(orig["_vel"]))
    if new_vel != int(orig["_vel"]):
        st.session_state[f"_inf_v_{idx}"] = max(new_vel, 0)
        changed = True

if changed:
    st.rerun()

# ── Legenda ──────────────────────────────────────────────────────────────────

st.markdown(
    '<div style="font-size:.82em;color:#5f6368;margin-top:8px;line-height:1.9">'
    '<span style="margin-right:16px">✅ Adequada</span>'
    '<span style="margin-right:16px">↘️ Abaixo da mínima</span>'
    '<span style="margin-right:16px">⚠️ Acima da habitual</span>'
    '<span style="margin-right:16px">🚨 Acima da máxima estudada</span>'
    '<span style="margin-left:16px;background:#F5F5F5;padding:2px 6px;border-radius:3px">Colunas editáveis (cinza claro)</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Calculadora de dose → velocidade ─────────────────────────────────────────

st.markdown("---")
st.subheader("Calculadora: Medicação e dose → Velocidade na bomba")

nomes = df_inf["nome_formatado"].tolist()
col_med, col_dose = st.columns([3, 2])

with col_med:
    med_sel = st.selectbox("Medicação", nomes, key="_calc_med")

with col_dose:
    row_sel = df_inf[df_inf["nome_formatado"] == med_sel].iloc[0]
    unit_sel = str(row_sel.get("unidade", "")).strip()
    dose_input = st.number_input(
        f"Dose desejada ({unit_sel})",
        min_value=0.0, value=0.0, step=0.001, format="%.3f",
        key="_calc_dose",
    )

if dose_input > 0:
    idx_sel = int(row_sel.name)
    mg_a = _fl(row_sel, "mg_amp")
    v_a  = _fl(row_sel, "vol_amp")
    d_amp_def = int(max(_fl(row_sel, "qtd_amp_padrao", 1), 1))
    d_dil_def = int(max(_fl(row_sel, "diluente_padrao", 0), 0))
    d_amp = int(st.session_state.get(f"_inf_a_{idx_sel}", d_amp_def))
    d_dil = int(st.session_state.get(f"_inf_d_{idx_sel}", d_dil_def))

    qt = d_amp * mg_a
    vt = max((d_amp * v_a) + d_dil, 1)
    cp = qt / vt
    cs = cp * 1000

    vel_calc = _dose_to_mlh(dose_input, unit_sel, cp, cs, peso)
    conc_str = f"{_fmt(cp, 2)} {_conc_label(unit_sel)}"

    dmin = _fl(row_sel, "dose_min")
    dhab = _fl(row_sel, "dose_max_hab")
    dmax = _fl(row_sel, "dose_max_tol")

    if dmax > 0 and dose_input > dmax:
        badge = "🚨 Acima da máxima estudada"
        badge_color = "#C62828"
    elif dhab > 0 and dose_input > dhab:
        badge = "⚠️ Acima da habitual"
        badge_color = "#F57F17"
    elif dmin > 0 and dose_input < dmin:
        badge = "↘️ Abaixo da mínima"
        badge_color = "#1565C0"
    else:
        badge = "✅ Adequada"
        badge_color = "#2E7D32"

    dil_str = "Puro" if d_dil == 0 else f"{d_dil} ml"

    st.markdown(
        f'<div style="background:#F8F9FA;border-radius:8px;padding:16px 20px;margin-top:10px;'
        f'border-left:4px solid {badge_color}">'
        f'<div style="font-size:1.05em;color:#333;margin-bottom:10px;line-height:1.6">'
        f'Diluição: <b>{d_amp} amp</b> + <b>{dil_str}</b> de diluente '
        f'→ Vol. total: <b>{int(vt)} ml</b> | Concentração: <b>{conc_str}</b></div>'
        f'<div style="font-size:1.15em;color:#222">'
        f'<b>Velocidade da bomba: {_fmt(vel_calc, 1)} ml/h</b> '
        f'<span style="font-size:.85em;color:#555">para {f"{dose_input:.3f}".rstrip("0").rstrip(".").replace(".", ",")} {unit_sel} de {med_sel.split(" ")[0]}</span></div>'
        f'<div style="font-size:.95em;margin-top:6px;color:{badge_color};font-weight:600">'
        f'{badge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

mostrar_rodape()
