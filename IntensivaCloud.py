import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E ESTILO
# ==============================================================================
st.set_page_config(page_title="Intensiva Calculator Pro", page_icon="⚕️", layout="wide")

COLOR_PRIMARY = "#0F9D58"  # Verde Técnico
COLOR_ACCENT = "#1a73e8"   # Azul Google
COLOR_BG = "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
    
    /* ESTILO DOS CARTÕES */
    .result-box {{
        background-color: white; 
        padding: 15px; 
        border-radius: 8px;
        border: 1px solid #ddd; 
        border-left: 5px solid {COLOR_ACCENT}; 
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .result-title {{ font-size: 0.9em; color: #666; font-weight: bold; text-transform: uppercase; }}
    .result-value {{ font-size: 1.4em; color: #333; font-weight: bold; margin-top: 5px; }}
    
    .stForm {{ background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #eee; }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO GOOGLE SHEETS (SOMENTE LEITURA)
# ==============================================================================
SHEET_NAME_INF = "DB_INFUSAO"
SHEET_NAME_IOT = "DB_IOT"

def get_google_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
    }
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_tab_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open("IntensivaDB").worksheet(sheet_tab_name)
        data = sheet.get_all_records()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        cols_numericas = ['mg_amp', 'vol_amp', 'dose_min', 'dose_max_hab', 'dose_max_tol', 'conc', 'dose_hab', 'dose_max']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

# Carregamento Inicial
df_inf = load_data_from_sheet(SHEET_NAME_INF)
df_iot = load_data_from_sheet(SHEET_NAME_IOT)

def df_to_dict_inf(df):
    if df.empty: return {}
    df = df.drop_duplicates(subset=['nome_formatado'], keep='last')
    return df.set_index('nome_formatado').to_dict(orient='index')

def df_to_dict_iot(df):
    if df.empty: return {}
    df = df.drop_duplicates(subset=['nome_formatado'], keep='last')
    return df.set_index('nome_formatado').to_dict(orient='index')

MED_DB_INF = df_to_dict_inf(df_inf)
MED_DB_IOT = df_to_dict_iot(df_iot)

def format_br(valor):
    if valor is None: return ""
    if isinstance(valor, (int, float)):
        # Formata com vírgula no decimal e ponto no milhar
        texto = f"{valor:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if "," in texto:
            texto = texto.rstrip("0")
            if texto.endswith(","): texto = texto[:-1]
        return texto
    return str(valor)

# ==============================================================================
# PÁGINA: INFUSÃO
# ==============================================================================
def calcular_infusao():
    st.header("💉 Calculadora de Infusão")
    
    col_input_1, col_input_2 = st.columns([1, 2.5])
    with col_input_1:
        # PESO: Inteiro (step=1)
        peso = st.number_input("Peso do Paciente (kg)", value=70, step=1, format="%d")
    with col_input_2:
        lista_drogas = sorted(list(MED_DB_INF.keys()))
        if not lista_drogas:
            st.warning("Banco de dados vazio. Preencha a Planilha Google.")
            droga_nome = None
        else:
            droga_nome = st.selectbox("Selecione a Medicação", lista_drogas)
    
    if droga_nome:
        info = MED_DB_INF[droga_nome]
        st.markdown("### Preparo")
        c1, c2, c3 = st.columns(3)
        
        padrao_amp = float(info.get('qtd_amp_padrao', 1.0)) if 'qtd_amp_padrao' in info else 1.0
        padrao_dil = int(info.get('diluente_padrao', 246)) if 'diluente_padrao' in info else 246

        with c1: 
            # Ampolas: Permite decimal
            n_ampolas = st.number_input("Número de Ampolas", value=padrao_amp, step=0.1, format="%.1f")
        with c2: 
            # Diluente: Inteiro
            vol_diluente = st.number_input("Volume de Diluente (ml)", value=padrao_dil, step=1, format="%d")
            
        qtd_total = n_ampolas * float(info['mg_amp'])
        vol_total = (n_ampolas * float(info['vol_amp'])) + vol_diluente
        if vol_total <= 0: vol_total = 1
        conc_principal = qtd_total / vol_total
        conc_secundaria = conc_principal * 1000
        unidade_str = str(info['unidade'])
        
        if "UI" in unidade_str:
            label_conc_1, label_conc_2 = "UI/ml", "mUI/ml"
        else:
            label_conc_1, label_conc_2 = "mg/ml", "mcg/ml"

        def converte_dose_para_mlh(dose, unidade_droga):
            dose = float(dose)
            if dose == 0: return 0
            if unidade_droga == "mcg/kg/min": return (dose * peso * 60) / conc_secundaria
            elif unidade_droga == "mcg/kg/h": return (dose * peso) / conc_secundaria
            elif unidade_droga == "mg/kg/h": return (dose * peso) / conc_principal
            elif unidade_droga == "mg/h": return dose / conc_principal
            elif unidade_droga == "mcg/min": return (dose * 60) / conc_secundaria
            elif unidade_droga == "mg/min": return (dose * 60) / conc_principal
            elif unidade_droga == "UI/min": return (dose * 60) / conc_principal
            elif unidade_droga == "UI/kg/h": return (dose * peso) / conc_principal
            elif unidade_droga == "mg/kg/min": return (dose * peso * 60) / conc_principal
            return 0

        bomba_min = converte_dose_para_mlh(info['dose_min'], unidade_str)
        bomba_max_hab = converte_dose_para_mlh(info['dose_max_hab'], unidade_str)
        bomba_max_tol = converte_dose_para_mlh(info['dose_max_tol'], unidade_str)

        st.markdown("### 1. Dados da Solução")
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.markdown(f"""<div class="result-box"><div class="result-title">VOLUME FINAL</div><div class="result-value">{format_br(vol_total)} ml</div></div>""", unsafe_allow_html=True)
        with col_res2:
            st.markdown(f"""<div class="result-box"><div class="result-title">CONCENTRAÇÃO ({label_conc_1})</div><div class="result-value">{format_br(conc_principal)} {label_conc_1}</div></div>""", unsafe_allow_html=True)
        with col_res3:
            st.markdown(f"""<div class="result-box"><div class="result-title">CONCENTRAÇÃO ({label_conc_2})</div><div class="result-value">{format_br(conc_secundaria)} {label_conc_2}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"### 2. Limites de Velocidade da Bomba ({unidade_str})")
        c_lim1, c_lim2, c_lim3 = st.columns(3)
        with c_lim1:
            st.markdown(f"""<div class="result-box" style="border-left-color: #f1c40f;"><div class="result-title">VELOCIDADE MÍNIMA<br>({format_br(info['dose_min'])} {unidade_str})</div><div class="result-value">{format_br(bomba_min)} ml/h</div></div>""", unsafe_allow_html=True)
        with c_lim2:
            st.markdown(f"""<div class="result-box" style="border-left-color: #2ecc71;"><div class="result-title">MÁXIMA HABITUAL<br>({format_br(info['dose_max_hab'])} {unidade_str})</div><div class="result-value">{format_br(bomba_max_hab)} ml/h</div></div>""", unsafe_allow_html=True)
        with c_lim3:
            st.markdown(f"""<div class="result-box" style="border-left-color: #e74c3c;"><div class="result-title">MÁXIMA TOLERADA<br>({format_br(info['dose_max_tol'])} {unidade_str})</div><div class="result-value">{format_br(bomba_max_tol)} ml/h</div></div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("3. Simulador em Tempo Real")
        col_sim1, col_sim2 = st.columns(2)
        with col_sim1:
            ml_h_atual = st.number_input("Velocidade Atual da Bomba (ml/h)", value=float(bomba_min) if bomba_min > 0 else 0.0, step=0.1, format="%.1f")
            if ml_h_atual > 0:
                if unidade_str == "mcg/kg/min": dose_real = (ml_h_atual * conc_secundaria) / peso / 60
                elif unidade_str == "mcg/kg/h": dose_real = (ml_h_atual * conc_secundaria) / peso
                elif unidade_str == "mg/kg/h": dose_real = (ml_h_atual * conc_principal) / peso
                elif unidade_str == "mg/h": dose_real = ml_h_atual * conc_principal
                elif unidade_str == "mcg/min": dose_real = (ml_h_atual * conc_secundaria) / 60
                elif unidade_str == "mg/min": dose_real = (ml_h_atual * conc_principal) / 60
                elif unidade_str == "UI/min": dose_real = (ml_h_atual * conc_principal) / 60
                elif unidade_str == "UI/kg/h": dose_real = (ml_h_atual * conc_principal) / peso
                elif unidade_str == "mg/kg/min": dose_real = (ml_h_atual * conc_principal) / peso / 60
                else: dose_real = 0
                
                st.metric(f"Dose Entregue ({unidade_str})", f"{format_br(dose_real)}")
                
                if dose_real > float(info['dose_max_tol']): st.error("🚨 PERIGO: Dose acima do máximo tolerado!")
                elif dose_real > float(info['dose_max_hab']): st.warning("⚠️ Atenção: Dose acima do habitual.")
                else: st.success("✅ Dentro da faixa segura.")

# ==============================================================================
# PÁGINA: IOT
# ==============================================================================
def page_iot():
    st.header("⚡ Intubação Orotraqueal")
    col_p, col_void = st.columns([1, 3])
    with col_p:
        # PESO: Inteiro
        peso = st.number_input("Peso do Paciente (kg)", value=70, step=1, format="%d")
    
    dados_tabela = []
    for nome_droga in sorted(MED_DB_IOT.keys()):
        dado = MED_DB_IOT[nome_droga]
        conc = float(dado['conc'])
        if conc > 0:
            vol_min = (float(dado['dose_min']) * peso) / conc
            vol_hab = (float(dado['dose_hab']) * peso) / conc
            vol_max = (float(dado['dose_max']) * peso) / conc
            
            # Formatação limpa (sem asteriscos)
            dados_tabela.append({
                "Medicação": nome_droga,
                "Vol. Mínimo": f"{format_br(vol_min)} ml",
                "Vol. Médio": f"{format_br(vol_hab)} ml",  
                "Vol. Máximo": f"{format_br(vol_max)} ml"
            })
    
    if dados_tabela:
        # Destaca ligeiramente o volume médio usando estilo do pandas (se suportado) ou apenas texto limpo
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado encontrado na aba DB_IOT da planilha.")

# ==============================================================================
# PÁGINA: CONVERSÃO
# ==============================================================================
def page_conversao():
    st.header("🔄 Conversão Universal")
    col_setup1, col_setup2 = st.columns([1, 3])
    with col_setup1:
        # PESO: Inteiro
        peso = st.number_input("Peso do Paciente (kg)", value=70, step=1, key="conv_peso", format="%d")
    with col_setup2:
        c_qtd, c_unid, c_vol = st.columns(3)
        with c_qtd: 
            # Peso Total: 1 casa decimal e Label Correto
            qtd = st.number_input("Peso Total (mg/g/mcg)", value=250.0, step=0.1, key="conv_qtd", format="%.1f")
        with c_unid: unid = st.selectbox("Unidade", ["mg", "mcg", "g", "UI"], key="conv_unid")
        with c_vol: 
            # Volume: Inteiro
            vol = st.number_input("Volume Total (ml)", value=250, step=1, key="conv_vol", format="%d")

    if vol <= 0: vol = 1
    conc_base = qtd / vol
    
    if unid == "g":
        val_base = conc_base * 1000
        val_sec = val_base * 1000
        lbl_base, lbl_sec = "mg/ml", "mcg/ml"
    elif unid == "mg":
        val_base = conc_base
        val_sec = conc_base * 1000
        lbl_base, lbl_sec = "mg/ml", "mcg/ml"
    elif unid == "mcg":
        val_base = conc_base
        val_sec = conc_base 
        lbl_base, lbl_sec = "mcg/ml", "-"
    elif unid == "UI":
        val_base = conc_base
        val_sec = conc_base * 1000
        lbl_base, lbl_sec = "UI/ml", "mUI/ml"
    
    st.info(f"Concentração: **{format_br(val_base)} {lbl_base}**" + (f" | **{format_br(val_sec)} {lbl_sec}**" if lbl_sec != "-" else ""))
    st.markdown("---")
    
    t1, t2 = st.tabs(["ml/h -> Dose", "Dose -> ml/h"])
    with t1:
        ml_h = st.number_input("ml/h", value=10.0, key="c_mlh")
        qtd_h = ml_h * val_base
        st.metric(f"Dose ({lbl_base.split('/')[0]}/kg/h)", format_br(qtd_h/peso))

# ==============================================================================
# NAVEGAÇÃO
# ==============================================================================
st.sidebar.title("Menu")
nav = st.sidebar.radio("Ir para:", ["Infusão Contínua", "Intubação Orotraqueal", "Conversão Universal"])

if nav == "Infusão Contínua": calcular_infusao()
elif nav == "Intubação Orotraqueal": page_iot()
elif nav == "Conversão Universal": page_conversao()