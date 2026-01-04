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
    
    /* ESTILO DOS CARTÕES DE RESULTADO */
    .result-box {{
        background-color: white; 
        padding: 15px; 
        border-radius: 8px;
        border: 1px solid #ddd; 
        border-left: 5px solid {COLOR_ACCENT}; 
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .result-title {{ font-size: 0.85em; color: #666; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; }}
    .result-value {{ font-size: 1.3em; color: #333; font-weight: bold; }}
    
    .stForm {{ background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #eee; }}
    
    .stDataFrame {{ font-size: 0.95rem; }}
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

# --- FUNÇÃO DE FORMATAÇÃO (Atualizada para aceitar casas decimais variáveis) ---
def format_br(valor, casas=1):
    """
    Formata número para padrão BR (vírgula decimal, ponto milhar).
    casas: número de casas decimais (padrão = 1).
    """
    if valor is None: return ""
    if isinstance(valor, (int, float)):
        # Cria a string de formatação dinamicamente, ex: "{:,.2f}"
        fmt = f"{{:,.{casas}f}}"
        texto = fmt.format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
        return texto
    return str(valor)

# ==============================================================================
# PÁGINA: INFUSÃO
# ==============================================================================
def calcular_infusao():
    st.header("💉 Calculadora de Infusão")
    
    col_input_1, col_input_2 = st.columns([1, 2.5])
    with col_input_1:
        # PESO: 1 casa decimal
        peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.1, format="%.1f")
    with col_input_2:
        lista_drogas = sorted(list(MED_DB_INF.keys()))
        if not lista_drogas:
            st.warning("Banco de dados vazio.")
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
            # Ampolas: 1 casa decimal
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
            st.markdown(f"""<div class="result-box"><div class="result-title">VOLUME FINAL</div><div class="result-value">{int(vol_total)} ml</div></div>""", unsafe_allow_html=True)
        with col_res2:
            st.markdown(f"""<div class="result-box"><div class="result-title">CONCENTRAÇÃO ({label_conc_1})</div><div class="result-value">{format_br(conc_principal)} {label_conc_1}</div></div>""", unsafe_allow_html=True)
        with col_res3:
            st.markdown(f"""<div class="result-box"><div class="result-title">CONCENTRAÇÃO ({label_conc_2})</div><div class="result-value">{format_br(conc_secundaria)} {label_conc_2}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"### 2. Limites de Velocidade da Bomba ({unidade_str})")
        c_lim1, c_lim2, c_lim3 = st.columns(3)
        with c_lim1:
            st.markdown(f"""<div class="result-box" style="border-left-color: #f1c40f;"><div class="result-title">MÍNIMA<br>({format_br(info['dose_min'])})</div><div class="result-value">{format_br(bomba_min)} ml/h</div></div>""", unsafe_allow_html=True)
        with c_lim2:
            st.markdown(f"""<div class="result-box" style="border-left-color: #2ecc71;"><div class="result-title">HABITUAL<br>({format_br(info['dose_max_hab'])})</div><div class="result-value">{format_br(bomba_max_hab)} ml/h</div></div>""", unsafe_allow_html=True)
        with c_lim3:
            st.markdown(f"""<div class="result-box" style="border-left-color: #e74c3c;"><div class="result-title">TOLERADA<br>({format_br(info['dose_max_tol'])})</div><div class="result-value">{format_br(bomba_max_tol)} ml/h</div></div>""", unsafe_allow_html=True)

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
                
                # AQUI ESTÁ A MUDANÇA: 'format_br(dose_real, 2)' força 2 casas decimais
                st.metric(f"Dose Entregue ({unidade_str})", f"{format_br(dose_real, 2)}")
                
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
        # PESO: 1 casa decimal
        peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.1, format="%.1f")
    
    dados_tabela = []
    for nome_droga in sorted(MED_DB_IOT.keys()):
        dado = MED_DB_IOT[nome_droga]
        conc = float(dado['conc'])
        if conc > 0:
            vol_min = (float(dado['dose_min']) * peso) / conc
            vol_hab = (float(dado['dose_hab']) * peso) / conc
            vol_max = (float(dado['dose_max']) * peso) / conc
            
            dados_tabela.append({
                "Medicação": nome_droga,
                "Vol. Mínimo": f"{format_br(vol_min)} ml",
                "Vol. Médio": f"{format_br(vol_hab)} ml",  
                "Vol. Máximo": f"{format_br(vol_max)} ml"
            })
    
    if dados_tabela:
        st.dataframe(pd.DataFrame(dados_tabela), use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado encontrado na aba DB_IOT da planilha.")

# ==============================================================================
# PÁGINA: CONVERSÃO (LAYOUT DETALHADO)
# ==============================================================================
def page_conversao():
    st.header("🔄 Conversão Universal")
    
    # --- 1. CONFIGURAÇÃO ---
    st.markdown("##### 1. Configurar Solução")
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        # PESO: 1 casa decimal
        peso = st.number_input("Peso (kg)", value=70.0, step=0.1, key="conv_peso", format="%.1f")
    with c2: 
        # DOSE TOTAL: 1 casa decimal
        qtd = st.number_input("Qtd. Total", value=250.0, step=0.1, key="conv_qtd", format="%.1f")
    with c3: 
        unid = st.selectbox("Unidade", ["mg", "mcg", "g", "UI"], key="conv_unid")
    with c4: 
        # VOLUME: Inteiro
        vol = st.number_input("Volume Total (ml)", value=250, step=1, key="conv_vol", format="%d")

    if vol <= 0: vol = 1
    conc_base = qtd / vol
    
    # Define fator de conversão e rótulos
    if unid == "g":
        fator_c1 = 1000        # g -> mg
        lbl_c1 = "mg"
        fator_c2 = 1000000     # g -> mcg
        lbl_c2 = "mcg"
    elif unid == "mg":
        fator_c1 = 1           # mg -> mg
        lbl_c1 = "mg"
        fator_c2 = 1000        # mg -> mcg
        lbl_c2 = "mcg"
    elif unid == "mcg":
        fator_c1 = 1
        lbl_c1 = "mcg"
        fator_c2 = None
        lbl_c2 = "-"
    elif unid == "UI":
        fator_c1 = 1
        lbl_c1 = "UI"
        fator_c2 = 1000
        lbl_c2 = "mUI"

    conc_c1 = conc_base * fator_c1
    conc_c2 = conc_base * fator_c2 if fator_c2 else 0

    st.info(f"Concentração: **{format_br(conc_c1)} {lbl_c1}/ml**" + (f" | **{format_br(conc_c2)} {lbl_c2}/ml**" if fator_c2 else ""))

    # --- 2. INPUT DE VELOCIDADE ---
    st.markdown("##### 2. Velocidade de Infusão")
    ml_h = st.number_input("Vazão da Bomba (ml/h)", value=10.0, step=0.1, key="c_mlh", format="%.1f")

    # --- 3. CÁLCULOS DETALHADOS (TABELA COMPLETA) ---
    st.markdown("##### 3. Resultados Detalhados")
    
    # Cálculos Coluna 1
    dose_h_c1 = ml_h * conc_c1
    dose_min_c1 = dose_h_c1 / 60
    dose_kg_h_c1 = dose_h_c1 / peso
    dose_kg_min_c1 = dose_kg_h_c1 / 60
    
    # Cálculos Coluna 2
    if fator_c2:
        dose_h_c2 = ml_h * conc_c2
        dose_min_c2 = dose_h_c2 / 60
        dose_kg_h_c2 = dose_h_c2 / peso
        dose_kg_min_c2 = dose_kg_h_c2 / 60
    
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

# ==============================================================================
# NAVEGAÇÃO
# ==============================================================================
st.sidebar.title("Menu")
nav = st.sidebar.radio("Ir para:", ["Infusão Contínua", "Intubação Orotraqueal", "Conversão Universal"])

if nav == "Infusão Contínua": calcular_infusao()
elif nav == "Intubação Orotraqueal": page_iot()
elif nav == "Conversão Universal": page_conversao()