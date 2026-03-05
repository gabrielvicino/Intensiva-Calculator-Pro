import streamlit as st
import pandas as pd
from utils import load_data, mostrar_rodape

# ==============================================================================
# CSS
# ==============================================================================
COLOR_PRIMARY = "#0F9D58"

st.markdown(f"""
    <style>
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
    .stDataFrame {{ font-size: 1.1rem; }}
    .block-container {{ padding-top: 2rem; }}
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


def calcular_tubo_sugerido(sexo: str, idade: int, peso: float) -> tuple[str, str]:
    if idade >= 14:
        if sexo == "Feminino":
            return ("6.5 mm", f"Mulher, {idade} anos") if peso < 45 else ("7.0 - 7.5 mm", f"Mulher, {idade} anos")
        return "7.5 - 8.0 mm", f"Homem, {idade} anos"
    if idade < 1 or peso < 10:
        anos = "ano" if idade == 1 else "anos"
        if peso < 1:   return "2.5 mm (sem cuff)", f"Criança, {idade} {anos}"
        if peso < 2:   return "3.0 mm (sem cuff)", f"Criança, {idade} {anos}"
        if idade < 0.5: return "3.0 - 3.5 mm",    f"Criança, {idade} {anos}"
        return "3.5 - 4.0 mm", f"Criança, {idade} {anos}"
    tubo_s = round((idade / 4) + 4, 1)
    tubo_c = round((idade / 4) + 3.5, 1)
    anos = "ano" if idade == 1 else "anos"
    return f"{tubo_c} mm (c/ cuff) ou {tubo_s} mm (s/ cuff)", f"Criança, {idade} {anos}"


@st.cache_data
def _calcular_tabela(df_iot: pd.DataFrame, peso: float) -> pd.DataFrame | None:
    """
    Calcula volumes por droga para um dado peso.
    Resultado cacheado — só recalcula quando df ou peso mudam.
    """
    col_nome = next((c for c in ("nome_formatado", "medicacao", "apresentacao", "droga") if c in df_iot.columns), None)
    if col_nome is None:
        return None

    rows = []
    for _, row in df_iot.iterrows():
        try:
            nome     = row[col_nome]
            conc     = float(row.get("conc", 0))
            dose_min = float(row.get("dose_min", 0))
            dose_hab = float(row.get("dose_hab", row.get("dose_media", 0)))
            dose_max = float(row.get("dose_max", 0))
            if conc <= 0:
                continue
            rows.append({
                "Medicação":   nome,
                "Vol. Mínimo": f"{format_br((dose_min * peso) / conc)} ml",
                "Vol. Habitual": f"{format_br((dose_hab * peso) / conc)} ml",
                "Vol. Máximo": f"{format_br((dose_max * peso) / conc)} ml",
            })
        except Exception:
            continue

    if not rows:
        return None
    return pd.DataFrame(rows)


def _estilizar_tabela(df: pd.DataFrame):
    """Cria o Styler — não cacheado (Styler com lambdas não é serializável)."""
    return (
        df.style
        .map(lambda _: "color: #1565C0; font-weight: bold;", subset=["Vol. Mínimo"])
        .map(lambda _: "color: #2E7D32; font-weight: bold;", subset=["Vol. Habitual"])
        .map(lambda _: "color: #C62828; font-weight: bold;", subset=["Vol. Máximo"])
        .map(lambda _: "font-weight: 600; color: #333;",     subset=["Medicação"])
    )


# ==============================================================================
# PÁGINA PRINCIPAL
# ==============================================================================
st.header("⚡ Intubação Orotraqueal")

df_iot = load_data("DB_IOT")
if df_iot.empty:
    st.error("Banco de dados não encontrado. Verifique a conexão com o Google Sheets (aba DB_IOT).")
    st.stop()

# Inputs
col_p, col_idade, col_sexo = st.columns(3)
with col_p:
    peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.5, format="%.1f")
with col_idade:
    idade = st.number_input("Idade (anos)", min_value=0, max_value=120, value=50, step=1)
with col_sexo:
    sexo = st.radio("Sexo", ["Masculino", "Feminino"], horizontal=True)

# Tubo sugerido
tubo_sugerido, categoria = calcular_tubo_sugerido(sexo, idade, peso)

st.markdown(
    f"<p style='margin-top:1rem;margin-bottom:0.2rem;font-size:0.95rem;'>"
    f"<strong>Tubo sugerido: {tubo_sugerido} ({categoria})</strong>"
    f" — Variação padrão: ±0.5 mm</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-size:0.8rem;color:#808495;margin-bottom:0.5rem;'>"
    "A avaliação individual é imprescindível e deve contemplar a estratificação dos preditores de via aérea difícil "
    "e a análise das variáveis clínicas e anatômicas específicas de cada paciente.</p>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='margin-top:0.5rem;margin-bottom:0.5rem;'>", unsafe_allow_html=True)

# Tabela — cacheada por (df_iot, peso), Styler também cacheado
df_display = _calcular_tabela(df_iot, peso)
if df_display is not None:
    styler = _estilizar_tabela(df_display)
    st.dataframe(
        styler,
        use_container_width=True,
        hide_index=True,
        height=(len(df_display) + 1) * 35 + 3,
    )
else:
    st.warning("Não foi possível calcular as doses. Verifique a estrutura da aba DB_IOT.")

mostrar_rodape()
