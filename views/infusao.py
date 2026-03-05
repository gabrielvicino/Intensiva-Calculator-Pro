import streamlit as st
import pandas as pd
from utils import load_data, mostrar_rodape

# ==============================================================================
# CSS
# ==============================================================================
COLOR_PRIMARY = "#0F9D58"
COLOR_ACCENT  = "#1a73e8"

st.markdown(f"""
    <style>
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
    .result-box {{
        background-color: white; padding: 15px; border-radius: 8px;
        border: 1px solid #ddd; border-left: 5px solid {COLOR_ACCENT};
        margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .result-title {{ font-size: 0.85em; color: #666; font-weight: bold;
                     text-transform: uppercase; margin-bottom: 4px; }}
    .result-value {{ font-size: 1.3em; color: #333; font-weight: bold; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# HELPERS
# ==============================================================================
def format_br(valor, casas=1):
    if valor is None:
        return ""
    if isinstance(valor, (int, float)):
        return f"{{:,.{casas}f}}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)


@st.cache_data
def _get_lista_drogas(df_inf: pd.DataFrame, col_nome: str):
    """Retorna (lista_drogas, index_padrao) — calculado uma vez por df."""
    lista = sorted(df_inf[col_nome].unique().tolist())
    idx = next(
        (i for i, d in enumerate(lista)
         if "noradrenalina" in d.lower() or "norepinefrina" in d.lower()),
        0,
    )
    return lista, idx


@st.cache_data
def _get_drug_data(df_inf: pd.DataFrame, col_nome: str, droga_nome: str):
    """Extrai e normaliza os dados de uma droga — calculado uma vez por combinação."""
    row = df_inf[df_inf[col_nome] == droga_nome].iloc[0]
    info = row.to_dict()
    info_norm = {str(k).strip().lower().replace(" ", "_"): v for k, v in info.items()}
    return info, info_norm


def _converte_dose(dose, unidade: str, conc_p: float, conc_s: float, peso: float) -> float:
    """Dose → ml/h (direto)."""
    try:
        dose = float(dose)
    except Exception:
        return 0.0
    if dose == 0 or not conc_p:
        return 0.0
    u = unidade
    if   u == "ng/kg/min":  return (dose * peso * 60) / (conc_s * 1000) if conc_s else 0
    elif u == "ng/kg/h":    return (dose * peso) / (conc_s * 1000) if conc_s else 0
    elif u == "mEq/h":      return dose / conc_p
    elif u == "mEq/kg/h":   return (dose * peso) / conc_p
    elif u == "mmol/h":     return dose / conc_p
    elif u == "mmol/kg/h":  return (dose * peso) / conc_p
    elif u == "mcg/kg/min": return (dose * peso * 60) / conc_s if conc_s else 0
    elif u == "mcg/kg/h":   return (dose * peso) / conc_s if conc_s else 0
    elif u == "mg/kg/h":    return (dose * peso) / conc_p
    elif u == "mg/kg/min":  return (dose * peso * 60) / conc_p
    elif u == "UI/kg/h":    return (dose * peso) / conc_p
    elif u == "UI/kg/min":  return (dose * peso * 60) / conc_p
    elif u == "mcg/h":      return dose / conc_s if conc_s else 0
    elif u == "mcg/min":    return (dose * 60) / conc_s if conc_s else 0
    elif u == "mg/h":       return dose / conc_p
    elif u == "mg/min":     return (dose * 60) / conc_p
    elif u == "UI/h":       return dose / conc_p
    elif u == "UI/min":     return (dose * 60) / conc_p
    elif u == "g/h":        return dose / conc_p
    return 0.0


def _calc_dose_reversa(ml_h: float, unidade: str, conc_p: float, conc_s: float, peso: float) -> float:
    """ml/h → dose (reverso)."""
    if ml_h <= 0:
        return 0.0
    u = unidade
    if   u == "mcg/kg/min":  return (ml_h * conc_s) / peso / 60 if conc_s else 0
    elif u == "mcg/kg/h":    return (ml_h * conc_s) / peso if conc_s else 0
    elif u == "mg/kg/h":     return (ml_h * conc_p) / peso
    elif u == "mg/kg/min":   return (ml_h * conc_p) / peso / 60
    elif u == "UI/kg/h":     return (ml_h * conc_p) / peso
    elif u == "UI/kg/min":   return (ml_h * conc_p) / peso / 60
    elif u == "mcg/h":       return ml_h * conc_s if conc_s else 0
    elif u == "mcg/min":     return (ml_h * conc_s) / 60 if conc_s else 0
    elif u == "mg/h":        return ml_h * conc_p
    elif u == "mg/min":      return (ml_h * conc_p) / 60
    elif u == "UI/h":        return ml_h * conc_p
    elif u == "UI/min":      return (ml_h * conc_p) / 60
    elif u == "g/h":         return ml_h * conc_p
    elif u == "ng/kg/min":   return (ml_h * conc_s * 1000) / peso / 60 if conc_s else 0
    elif u == "ng/kg/h":     return (ml_h * conc_s * 1000) / peso if conc_s else 0
    elif u == "mEq/h":       return ml_h * conc_p
    elif u == "mEq/kg/h":    return (ml_h * conc_p) / peso
    elif u == "mmol/h":      return ml_h * conc_p
    elif u == "mmol/kg/h":   return (ml_h * conc_p) / peso
    return 0.0


# ==============================================================================
# SIMULADOR — @st.fragment: re-renderiza APENAS esta seção quando ml_h muda,
# sem acionar rerun no resto da página.
# ==============================================================================
@st.fragment
def _render_simulador(
    conc_p: float, conc_s: float, unidade_str: str, peso: float,
    bomba_min: float, dose_max_tol: float, dose_max_hab: float, key_safe: str,
):
    st.subheader("3. Simulador em Tempo Real")
    col_sim1, _ = st.columns(2)
    with col_sim1:
        val_ini = float(bomba_min) if bomba_min > 0 else 0.0
        ml_h = st.number_input(
            "Velocidade Atual da Bomba (ml/h)",
            value=val_ini, step=0.1, format="%.1f",
            key=f"inf_mlh_{key_safe}",
        )
        if ml_h > 0:
            dose_real = _calc_dose_reversa(ml_h, unidade_str, conc_p, conc_s, peso)
            st.metric(f"Dose Entregue ({unidade_str})", format_br(dose_real, 2))
            try:
                if float(dose_max_tol) > 0 and dose_real > float(dose_max_tol):
                    st.error("🚨 PERIGO: Dose acima da MÁXIMA ESTUDADA!")
                elif float(dose_max_hab) > 0 and dose_real > float(dose_max_hab):
                    st.warning("⚠️ Atenção: Dose acima da máxima habitual.")
                else:
                    st.success("✅ Dentro da faixa segura.")
            except Exception:
                pass


# ==============================================================================
# PÁGINA PRINCIPAL
# ==============================================================================
st.header("💉 Calculadora de Infusão")

df_inf = load_data("DB_INFUSAO")
if df_inf.empty:
    st.error("Banco de dados não encontrado. Verifique a conexão com o Google Sheets (aba DB_INFUSAO).")
    st.stop()

col_nome = "nome_formatado" if "nome_formatado" in df_inf.columns else "apresentacao"
if col_nome not in df_inf.columns:
    st.error("Erro de estrutura: coluna de nome não encontrada.")
    st.stop()

# Inputs principais (mudanças aqui causam rerun normal)
col_input_1, col_input_2 = st.columns([1, 2.5])
with col_input_1:
    peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.1, format="%.1f")

with col_input_2:
    lista_drogas, idx_padrao = _get_lista_drogas(df_inf, col_nome)
    droga_nome = st.selectbox("Selecione a Medicação", lista_drogas, index=idx_padrao)

if not droga_nome:
    st.stop()

# Dados da droga — cached: não recalcula ao mudar apenas ml_h_atual
info, info_norm = _get_drug_data(df_inf, col_nome, droga_nome)

try:
    v = info_norm.get("qtd_amp_padrao") or info.get("qtd_amp_padrao")
    def_amp = float(v) if v is not None and pd.notna(v) and float(v) > 0 else 1.0
except Exception:
    def_amp = 1.0
try:
    v = info_norm.get("diluente_padrao") or info.get("diluente_padrao")
    def_dil = int(float(v)) if v is not None and pd.notna(v) and float(v) >= 0 else 50
except Exception:
    def_dil = 50

try:
    mg_amp  = float(info.get("mg_amp", 0))
    vol_amp = float(info.get("vol_amp", 0))
except Exception:
    mg_amp = vol_amp = 0.0

_key_safe = droga_nome.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")[:40]

st.markdown("### Preparo")
c1, c2, _ = st.columns(3)
with c1:
    n_ampolas = st.number_input("Número de Ampolas", value=def_amp, step=1.0, format="%.1f", key=f"inf_amp_{_key_safe}")
with c2:
    vol_diluente = st.number_input("Volume de Diluente (ml)", value=def_dil, step=1, format="%d", key=f"inf_dil_{_key_safe}")

# Cálculos da solução
qtd_total   = n_ampolas * mg_amp
vol_total   = max((n_ampolas * vol_amp) + vol_diluente, 1)
conc_p      = qtd_total / vol_total
conc_s      = conc_p * 1000

unidade_str = str(info.get("unidade", "mg")).strip()
if "UI" in unidade_str:
    lbl1, lbl2 = "UI/ml", "mUI/ml"
elif unidade_str == "g":
    lbl1, lbl2 = "g/ml", "mg/ml"
else:
    lbl1, lbl2 = "mg/ml", "mcg/ml"

dose_min     = info.get("dose_min", 0)
dose_max_hab = info.get("dose_max_hab", 0)
dose_max_tol = info.get("dose_max_tol", 0)
bomba_min    = _converte_dose(dose_min, unidade_str, conc_p, conc_s, peso)
bomba_max_hab = _converte_dose(dose_max_hab, unidade_str, conc_p, conc_s, peso)
bomba_max_tol = _converte_dose(dose_max_tol, unidade_str, conc_p, conc_s, peso)

# Resultados da solução
st.markdown("### 1. Dados da Solução")
r1, r2, r3 = st.columns(3)
with r1:
    st.markdown(f'<div class="result-box" style="border-left-color:#28a745;"><div class="result-title">VOLUME FINAL</div><div class="result-value">{int(vol_total)} ml</div></div>', unsafe_allow_html=True)
with r2:
    st.markdown(f'<div class="result-box" style="border-left-color:#28a745;"><div class="result-title">CONCENTRAÇÃO ({lbl1})</div><div class="result-value">{format_br(conc_p, 2)} {lbl1}</div></div>', unsafe_allow_html=True)
with r3:
    st.markdown(f'<div class="result-box" style="border-left-color:#28a745;"><div class="result-title">CONCENTRAÇÃO ({lbl2})</div><div class="result-value">{format_br(conc_s, 2)} {lbl2}</div></div>', unsafe_allow_html=True)

# Limites
st.markdown("### 2. Limites de Velocidade da Bomba")
l1, l2, l3 = st.columns(3)
with l1:
    st.markdown(f'<div class="result-box" style="border-left-color:#1a73e8;"><div class="result-title">MÍNIMA<br>({format_br(dose_min, 2)} {unidade_str})</div><div class="result-value">{format_br(bomba_min)} ml/h</div></div>', unsafe_allow_html=True)
with l2:
    st.markdown(f'<div class="result-box" style="border-left-color:#ffc107;"><div class="result-title">MÁXIMA HABITUAL<br>({format_br(dose_max_hab, 2)} {unidade_str})</div><div class="result-value">{format_br(bomba_max_hab)} ml/h</div></div>', unsafe_allow_html=True)
with l3:
    st.markdown(f'<div class="result-box" style="border-left-color:#dc3545;"><div class="result-title">MÁXIMA ESTUDADA<br>({format_br(dose_max_tol, 2)} {unidade_str})</div><div class="result-value">{format_br(bomba_max_tol)} ml/h</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Simulador isolado via fragment — muda ml_h sem rerun na página
_render_simulador(conc_p, conc_s, unidade_str, peso, bomba_min, dose_max_tol, dose_max_hab, _key_safe)

mostrar_rodape()
