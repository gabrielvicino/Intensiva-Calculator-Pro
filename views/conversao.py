import streamlit as st
from utils import mostrar_rodape

# ==============================================================================
# 0. FUNÇÕES UTILITÁRIAS
# ==============================================================================
def safe_float(val_str):
    if not val_str or val_str.strip() == "":
        return 0.0
    try:
        return float(str(val_str).replace(',', '.'))
    except ValueError:
        return 0.0

def format_br(valor, casas=2):
    if valor is None: return ""
    if isinstance(valor, (int, float)):
        fmt = f"{{:,.{casas}f}}"
        return fmt.format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)

def get_label(texto_base, valor_atual):
    """
    Adiciona um marcador vermelho (*) se o campo estiver vazio.
    Usa sintaxe Markdown do Streamlit para cor.
    """
    if not valor_atual or str(valor_atual).strip() == "":
        return f"{texto_base} :red[(*)]"
    return texto_base

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E ESTILO
# ==============================================================================
# st.set_page_config(page_title="Conversão Universal", page_icon="🔄", layout="wide")

COLOR_PRIMARY = "#0F9D58"
COLOR_ACCENT = "#1a73e8"
COLOR_BG = "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
    
    /* Result Boxes */
    .result-box {{
        background-color: white; 
        padding: 15px; 
        border-radius: 8px;
        border: 1px solid #ddd; 
        border-left: 5px solid {COLOR_ACCENT}; 
        margin-bottom: 10px;
        box_shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .result-title {{ font-size: 0.85em; color: #666; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; }}
    .result-value {{ font-size: 1.3em; color: #333; font-weight: bold; }}
    
    .stForm {{ background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #eee; }}
    
    /* Highlight Bolus */
    .highlight-bolus {{
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #c8e6c9;
        color: #2e7d32;
        font-weight: bold;
        text-align: center;
        font-size: 1.2rem;
    }}

    /* Alerta Rodapé - Design Ajustado */
    .fill-alert {{
        background-color: #fff9db; /* Amarelo muito suave */
        color: #d9480f; /* Laranja escuro para texto */
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #ffe066; /* Borda amarela mais forte */
        text-align: center;
        font-weight: bold;
        margin-top: 20px;
        font-size: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    
    /* Texto Discreto */
    .discreet-note {{
        font-size: 0.85em;
        color: #666;
        margin-top: 5px;
        margin-bottom: 15px;
        line-height: 1.4;
    }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. LÓGICA DA PÁGINA
# ==============================================================================
st.header("🔄 Conversão Universal")

# Captura prévia dos valores (Session State hack para Labels dinâmicos)
val_peso = st.session_state.get("conv_peso", "70")
val_qtd = st.session_state.get("conv_qtd", "")
val_vol = st.session_state.get("conv_vol", "")
val_dose = st.session_state.get("bolus_dose", "") # Captura para o Bolus
val_mlh = st.session_state.get("bomba_mlh", "")

# ------------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA SOLUÇÃO
# ------------------------------------------------------------------------------
st.markdown("##### 1. Configurar Solução")
c1, c2, c3, c4 = st.columns(4)

with c1: 
    lbl_peso = get_label("Peso (kg)", val_peso)
    peso_str = st.text_input(lbl_peso, value="70", key="conv_peso")
    peso = safe_float(peso_str)

with c2: 
    lbl_qtd = get_label("Peso Total na Ampola / Solução", val_qtd)
    qtd_str = st.text_input(lbl_qtd, value="", key="conv_qtd")
    qtd = safe_float(qtd_str)

with c3: 
    unid_solucao = st.selectbox("Unidade da Solução", ["mg", "mcg", "g", "UI"], key="conv_unid")

with c4: 
    lbl_vol = get_label("Volume Total na Ampola / Solução (ml)", val_vol)
    vol_str = st.text_input(lbl_vol, value="", key="conv_vol")
    vol_amp = safe_float(vol_str)

# Texto Informativo Discreto
st.markdown("""
<div class="discreet-note">
    <b>Exemplo 1:</b> Propofol a 10% corresponde a 10 g de propofol diluídos para cada 100 mL de solução.<br>
    <b>Exemplo 1.1:</b> Em uma ampola de propofol a 10% contendo 20 mL, há 2 g de propofol. Portanto, para o cálculo do bolus (dose única), deve-se inserir o valor de 2 g em 20 mL.
</div>
""", unsafe_allow_html=True)

# Lógica da Barra de Concentração
msg_concentracao = "**Preencha os dados**"
tipo_alerta = "warning"

if qtd > 0 and vol_amp > 0:
    conc_base = qtd / vol_amp
    msg_concentracao = f"**{format_br(conc_base)} {unid_solucao}/ml**"
    st.info(f"🧪 Concentração Calculada: {msg_concentracao}")
else:
    st.info(f"🧪 Concentração Calculada: {msg_concentracao}")
    conc_base = 0.0

st.markdown("---")

# ------------------------------------------------------------------------------
# 2. USO EM BOLUS (DOSE ÚNICA)
# ------------------------------------------------------------------------------
st.markdown("##### 2. Uso em Bolus (Dose Única)")

col_b1, col_b2 = st.columns(2)

with col_b1:
    # APLICADO: Marcador no campo Dose Desejada
    lbl_dose = get_label("Dose Desejada (Bolus)", val_dose)
    dose_str = st.text_input(lbl_dose, value="", key="bolus_dose")
    dose_desejada = safe_float(dose_str)

with col_b2:
    if unid_solucao in ["UI"]:
        opcoes_unid = ["UI", "UI/kg"]
    else:
        opcoes_unid = ["mg", "mg/kg", "mcg", "mcg/kg", "g", "g/kg"]
    unid_bolus = st.selectbox("Unidade do Bolus", opcoes_unid)

# Lógica Bolus
vol_aspirar = 0.0
fracao_amp = 0.0
erro_msg = None

if dose_desejada > 0 and qtd > 0 and conc_base > 0:
    dose_total_calc = dose_desejada
    if "/kg" in unid_bolus:
        dose_total_calc = dose_desejada * peso

    fatores_para_mg = {"g": 1000, "mg": 1, "mcg": 0.001, "UI": 1}
    prefixo_bolus = unid_bolus.split("/")[0]
    
    if (unid_solucao == "UI" and prefixo_bolus != "UI") or (unid_solucao != "UI" and prefixo_bolus == "UI"):
        erro_msg = "Incompatibilidade: Solução e Bolus devem ser do mesmo tipo."
    else:
        try:
            fator_solucao = fatores_para_mg.get(unid_solucao, 1)
            fator_bolus = fatores_para_mg.get(prefixo_bolus, 1)
            
            qtd_solucao_mg = qtd * fator_solucao
            dose_bolus_mg = dose_total_calc * fator_bolus
            conc_mg_ml = qtd_solucao_mg / vol_amp
            
            if conc_mg_ml > 0:
                vol_aspirar = dose_bolus_mg / conc_mg_ml
                fracao_amp = vol_aspirar / vol_amp
        except:
            erro_msg = "Erro no cálculo."

if erro_msg:
    st.error(erro_msg)
elif vol_aspirar > 0:
    st.markdown(f"""<div class="highlight-bolus">💉 Administrar: {format_br(vol_aspirar, 2)} ml <br><span style="font-size:0.8em;font-weight:normal;color:#555;">(Equivalente a {format_br(fracao_amp, 2)} Ampola / Frasco da Solução)</span></div>""", unsafe_allow_html=True)

st.markdown("---")

# ------------------------------------------------------------------------------
# 3. USO EM BOMBA DE INFUSÃO (CONTÍNUO)
# ------------------------------------------------------------------------------
st.markdown("##### 3. Uso em Bomba de Infusão (Contínuo)")

# Check visual de preenchimento
lbl_mlh = get_label("Vazão da Bomba (ml/h)", val_mlh)
ml_h_str = st.text_input(lbl_mlh, value="", key="bomba_mlh")
ml_h = safe_float(ml_h_str)

st.markdown("**Resultados Detalhados**")

# LÓGICA DE EXIBIÇÃO
dados_completos = (ml_h > 0) and (qtd > 0) and (vol_amp > 0)

if dados_completos:
    # --- CÁLCULOS FINAIS ---
    fator_c1 = 1
    lbl_c1 = ""
    fator_c2 = None
    lbl_c2 = "-"

    if unid_solucao == "g":
        fator_c1, lbl_c1 = 1000, "mg"
        fator_c2, lbl_c2 = 1000000, "mcg"
    elif unid_solucao == "mg":
        fator_c1, lbl_c1 = 1, "mg"
        fator_c2, lbl_c2 = 1000, "mcg"
    elif unid_solucao == "mcg":
        fator_c1, lbl_c1 = 1, "mcg"
    elif unid_solucao == "UI":
        fator_c1, lbl_c1 = 1, "UI"
        fator_c2, lbl_c2 = 1000, "mUI"

    conc_c1 = conc_base * fator_c1
    conc_c2 = conc_base * fator_c2 if fator_c2 else 0

    dose_h_c1 = ml_h * conc_c1
    dose_min_c1 = dose_h_c1 / 60
    dose_kg_h_c1 = dose_h_c1 / peso if peso > 0 else 0
    dose_kg_min_c1 = dose_kg_h_c1 / 60

    col_res_a, col_res_b = st.columns(2)

    with col_res_a:
        st.markdown(f"**Unidade Principal ({lbl_c1})**")
        st.markdown(f"""
        <div class="result-box" style="border-left-color: #2ecc71;">
            <div class="result-title">DOSE / HORA</div>
            <div class="result-value">{format_br(dose_h_c1)} {lbl_c1}/h</div>
            <div class="result-title" style="margin-top:10px;">DOSE / MINUTO</div>
            <div class="result-value">{format_br(dose_min_c1)} {lbl_c1}/min</div>
        </div>
        <div class="result-box" style="border-left-color: #2ecc71;">
            <div class="result-title">DOSE / KG / HORA</div>
            <div class="result-value">{format_br(dose_kg_h_c1)} {lbl_c1}/kg/h</div>
            <div class="result-title" style="margin-top:10px;">DOSE / KG / MINUTO</div>
            <div class="result-value">{format_br(dose_kg_min_c1)} {lbl_c1}/kg/min</div>
        </div>
        """, unsafe_allow_html=True)

    if fator_c2:
        dose_h_c2 = ml_h * conc_c2
        dose_min_c2 = dose_h_c2 / 60
        dose_kg_h_c2 = dose_h_c2 / peso if peso > 0 else 0
        dose_kg_min_c2 = dose_kg_h_c2 / 60
        
        with col_res_b:
            st.markdown(f"**Unidade Secundária ({lbl_c2})**")
            st.markdown(f"""
            <div class="result-box" style="border-left-color: #3498db;">
                <div class="result-title">DOSE / HORA</div>
                <div class="result-value">{format_br(dose_h_c2)} {lbl_c2}/h</div>
                <div class="result-title" style="margin-top:10px;">DOSE / MINUTO</div>
                <div class="result-value">{format_br(dose_min_c2)} {lbl_c2}/min</div>
            </div>
            <div class="result-box" style="border-left-color: #3498db;">
                <div class="result-title">DOSE / KG / HORA</div>
                <div class="result-value">{format_br(dose_kg_h_c2)} {lbl_c2}/kg/h</div>
                <div class="result-title" style="margin-top:10px;">DOSE / KG / MINUTO</div>
                <div class="result-value">{format_br(dose_kg_min_c2)} {lbl_c2}/kg/min</div>
            </div>
            """, unsafe_allow_html=True)

else:
    # AVISO FINAL (Atualizado)
    st.markdown("""
    <div class="fill-alert">
        ⚠️ Preencha os campos marcados com <span style="color:#d9480f">(*)</span> acima para ver os resultados
    </div>
    """, unsafe_allow_html=True)

# Rodapé com nota legal
mostrar_rodape()