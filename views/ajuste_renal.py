"""💧 Função Renal — Ajuste Medicação."""

import streamlit as st
import pandas as pd
from utils import load_db_atb, mostrar_rodape

# ── CSS (mesmo padrão do projeto) ────────────────────────────────────────────
COLOR_PRIMARY = "#0F9D58"
COLOR_ACCENT = "#1a73e8"

st.markdown(f"""<style>
h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
[data-testid="stStatusWidget"] {{ display: none !important; }}
.card-atb {{
    background: #fff; border-radius: 10px; padding: 20px 24px;
    border: 1px solid #e0e0e0; border-left: 5px solid {COLOR_ACCENT};
    margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}}
.card-atb-title {{
    font-size: 1.15em; font-weight: 700; color: #222;
    margin-bottom: 14px; letter-spacing: 0.3px;
}}
.card-atb-subtitle {{
    font-size: .95em; color: #555; margin-bottom: 4px; padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
}}
.card-atb-subtitle:last-child {{ border-bottom: none; }}
.card-atb-label {{
    font-size: .82em; color: #888; font-weight: 600;
    text-transform: uppercase; margin-bottom: 2px;
}}
.card-atb-dose {{
    font-size: 1.0em; color: #333; margin: 3px 0 0 12px; line-height: 1.5;
}}
.tfg-result {{
    background: #E8F5E9; border-radius: 8px; padding: 12px 18px;
    border-left: 4px solid {COLOR_PRIMARY}; margin: 10px 0 16px 0;
    font-size: 1.1em; color: #2E7D32; font-weight: 600;
}}
</style>""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _cockcroft_gault(idade: float, peso: float, creatinina: float, feminino: bool) -> float:
    if creatinina <= 0:
        return 0.0
    crcl = ((140 - idade) * peso) / (72 * creatinina)
    if feminino:
        crcl *= 0.85
    return round(crcl, 1)


def _normalizar_farmaco(nome: str) -> str:
    return nome.strip().title()


def _doses_validas(row: pd.Series) -> list[str]:
    """Retorna lista de doses não vazias (ignora '-' e vazios)."""
    doses = []
    for col in ["dose_1", "dose_2", "dose_3", "dose_4", "dose_5"]:
        val = str(row.get(col, "")).strip()
        if val and val != "-":
            doses.append(val)
    return doses


# ── Página ───────────────────────────────────────────────────────────────────

st.header("💧 Função Renal — Ajuste Medicação")

df_atb = load_db_atb()
if df_atb.empty:
    st.error("Banco de dados não encontrado. Verifique a tabela db_atb no Supabase.")
    st.stop()

# Normalizar nomes de fármacos para o selectbox
df_atb = df_atb.copy()
df_atb["_farmaco_norm"] = df_atb["farmaco"].apply(_normalizar_farmaco)
lista_farmacos = sorted(df_atb["_farmaco_norm"].unique().tolist())

# ── Seção 1: Perfil do Paciente ──────────────────────────────────────────────

st.subheader("1. Perfil do Paciente")

perfil = st.radio(
    "Selecione o perfil:",
    ["Função Renal (estimar TFG)", "Paciente em Diálise"],
    horizontal=True,
)

tfg_valor = None
modalidade_sel = None

if perfil == "Função Renal (estimar TFG)":
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        idade = st.number_input("Idade (anos)", min_value=1, max_value=120, value=65, step=1)
    with c2:
        peso = st.number_input("Peso (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.5, format="%.1f")
    with c3:
        creatinina = st.number_input("Creatinina (mg/dL)", min_value=0.1, max_value=30.0, value=1.0, step=0.1, format="%.1f")
    with c4:
        sexo = st.selectbox("Sexo", ["Masculino", "Feminino"])

    feminino = sexo == "Feminino"
    tfg_valor = _cockcroft_gault(idade, peso, creatinina, feminino)

    st.markdown(
        f'<div class="tfg-result">TFG estimada (Cockcroft-Gault): <b>{tfg_valor} mL/min</b></div>',
        unsafe_allow_html=True,
    )

else:
    modalidades = {
        "Hemodiálise Clássica (IHD)": "IHD",
        "Terapias Contínuas de UTI (CRRT)": "CRRT",
        "Terapias Prolongadas / SLED (PIRRT)": "PIRRT",
        "Diálise Peritoneal (PD)": "PD",
    }
    mod_label = st.selectbox("Modalidade de Diálise", list(modalidades.keys()))
    modalidade_sel = modalidades[mod_label]

# ── Seção 2: Medicação ──────────────────────────────────────────────────────

st.subheader("2. Medicação")
farmaco_sel = st.selectbox("Selecione o fármaco", lista_farmacos)

# ── Seção 3: Resultado ──────────────────────────────────────────────────────

st.subheader("3. Prescrição Ajustada")

df_farmaco = df_atb[df_atb["_farmaco_norm"] == farmaco_sel].copy()

if df_farmaco.empty:
    st.info("Nenhum dado encontrado para este fármaco.")
    mostrar_rodape()
    st.stop()

if tfg_valor is not None:
    df_filtrado = df_farmaco[
        (df_farmaco["modalidade_dialise"].str.strip() == "-") &
        (df_farmaco["tfg_min"] <= tfg_valor) &
        (df_farmaco["tfg_max"] >= tfg_valor)
    ].copy()
    titulo_contexto = f"Ajuste para TFG: {tfg_valor} mL/min"
else:
    df_filtrado = df_farmaco[
        df_farmaco["modalidade_dialise"].str.strip().str.upper() == modalidade_sel.upper()
    ].copy()
    titulo_contexto = f"Ajuste para {mod_label}"

if df_filtrado.empty:
    st.warning("Nenhuma recomendação encontrada para os parâmetros informados.")
    mostrar_rodape()
    st.stop()

# Faixa de TFG para o cabeçalho
if tfg_valor is not None:
    tfg_mins = df_filtrado["tfg_min"].unique()
    tfg_maxs = df_filtrado["tfg_max"].unique()
    if len(tfg_mins) == 1 and len(tfg_maxs) == 1:
        faixa_str = f"TFG: {int(tfg_mins[0])} a {int(tfg_maxs[0])} mL/min"
    else:
        faixa_str = f"TFG: {tfg_valor} mL/min"
else:
    faixa_str = modalidade_sel

st.markdown(
    f'<div class="card-atb" style="border-left-color:{COLOR_PRIMARY}">'
    f'<div class="card-atb-title">{farmaco_sel.upper()} — {titulo_contexto}</div>',
    unsafe_allow_html=True,
)

for _, row in df_filtrado.iterrows():
    condicao = str(row.get("condicao_clinica", "")).strip()
    doses = _doses_validas(row)

    if not doses:
        continue

    html_doses = ""
    for j, d in enumerate(doses):
        label = f"Dose {j+1}" if len(doses) > 1 else "Prescrição"
        html_doses += (
            f'<div class="card-atb-dose">'
            f'<span style="color:{COLOR_ACCENT};font-weight:600">▸</span> {d}'
            f'</div>'
        )

    st.markdown(
        f'<div class="card-atb-subtitle">'
        f'<div class="card-atb-label">{condicao}</div>'
        f'{html_doses}'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

mostrar_rodape()
