import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E IDENTIDADE
# ==============================================================================
st.set_page_config(page_title="Intensiva Calculator Pro", page_icon="⚕️", layout="wide")

COLOR_PRIMARY = "#0F9D58"  # Verde Técnico
COLOR_ACCENT = "#1a73e8"   # Azul Google
COLOR_BG = "#F8F9FA"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
    .result-box {{
        background-color: white; padding: 15px; border-radius: 8px;
        border: 1px solid #ddd; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 10px;
    }}
    .result-title {{ font-size: 0.9em; color: #666; font-weight: bold; }}
    .result-value {{ font-size: 1.4em; color: #333; font-weight: bold; }}
    .stForm {{ background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #eee; }}
    .dataframe {{ font-size: 0.9rem !important; }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO COM GOOGLE SHEETS (O CORAÇÃO DA NUVEM)
# ==============================================================================
# Nomes das abas na sua planilha do Google
SHEET_NAME_INF = "DB_INFUSAO"
SHEET_NAME_IOT = "DB_IOT"

def get_google_sheet_client():
    # Esta função busca as credenciais que estarão salvas nos "Secrets" do Streamlit Cloud
    # Isso evita expor senhas no código.
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Monta as credenciais a partir do dicionário de segredos
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
    client = gspread.authorize(creds)
    return client

def load_data_from_sheet(sheet_tab_name):
    """Lê os dados da aba específica da planilha e retorna um DataFrame"""
    try:
        client = get_google_sheet_client()
        # Abre a planilha pelo nome do arquivo principal (você deve criar uma planilha chamada 'IntensivaDB')
        sheet = client.open("IntensivaDB").worksheet(sheet_tab_name)
        data = sheet.get_all_records()
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Garante que números venham como números (Google Sheets as vezes manda texto)
        cols_numericas = ['mg_amp', 'vol_amp', 'dose_min', 'dose_max_hab', 'dose_max_tol', 'conc', 'dose_hab', 'dose_max']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets ({sheet_tab_name}): {e}")
        return pd.DataFrame()

def save_row_to_sheet(sheet_tab_name, row_data_dict):
    """Adiciona uma nova linha na planilha"""
    try:
        client = get_google_sheet_client()
        sheet = client.open("IntensivaDB").worksheet(sheet_tab_name)
        # Transforma dict em lista de valores na ordem certa (baseado nas colunas)
        # Isso é um pouco mais complexo, simplificando: Append direto
        sheet.append_row(list(row_data_dict.values()))
        return True
    except Exception as e:
        st.error(f"Erro ao salvar na nuvem: {e}")
        return False

def delete_row_from_sheet(sheet_tab_name, col_name_identifier, value_to_find):
    """Remove uma linha baseada no nome do medicamento"""
    try:
        client = get_google_sheet_client()
        sheet = client.open("IntensivaDB").worksheet(sheet_tab_name)
        cell = sheet.find(value_to_find)
        if cell:
            sheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")
        return False

# ==============================================================================
# 3. FUNÇÕES UTILITÁRIAS (FORMATAÇÃO BR)
# ==============================================================================
def format_br(valor):
    if valor is None: return ""
    if isinstance(valor, (int, float)):
        texto = f"{valor:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if "," in texto:
            texto = texto.rstrip("0")
            if texto.endswith(","): texto = texto[:-1]
        return texto
    return str(valor)

def parse_input_flex(valor_str):
    if not valor_str: return 0.0
    if isinstance(valor_str, (float, int)): return float(valor_str)
    v = str(valor_str).replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return 0.0

# ==============================================================================
# CARREGAMENTO INICIAL DOS DADOS (CACHEADO PARA PERFORMANCE)
# ==============================================================================
# Como ler do Google é mais lento que ler do HD, usamos cache do Streamlit
# Para recarregar ao salvar, usaremos st.cache_data.clear()

if "df_inf" not in st.session_state:
    st.session_state["df_inf"] = load_data_from_sheet(SHEET_NAME_INF)

if "df_iot" not in st.session_state:
    st.session_state["df_iot"] = load_data_from_sheet(SHEET_NAME_IOT)

# Helper para converter DF para Dict (para manter compatibilidade com seu código antigo)
def df_to_dict_inf(df):
    if df.empty: return {}
    df = df.drop_duplicates(subset=['nome_formatado'], keep='last')
    return df.set_index('nome_formatado').to_dict(orient='index')

def df_to_dict_iot(df):
    if df.empty: return {}
    df = df.drop_duplicates(subset=['nome_formatado'], keep='last')
    return df.set_index('nome_formatado').to_dict(orient='index')

MED_DB_INF = df_to_dict_inf(st.session_state["df_inf"])
MED_DB_IOT = df_to_dict_iot(st.session_state["df_iot"])

# ==============================================================================
# PÁGINA: INFUSÃO
# ==============================================================================
def calcular_infusao():
    st.header("💉 Calculadora de Infusão (Cloud)")
    
    col_input_1, col_input_2 = st.columns([1, 2.5])
    with col_input_1:
        peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.1, format="%.1f")
    with col_input_2:
        lista_drogas = sorted(list(MED_DB_INF.keys()))
        if not lista_drogas:
            st.warning("Banco de dados vazio ou erro de conexão.")
            return
        droga_nome = st.selectbox("Selecione a Medicação", lista_drogas)
    
    info = MED_DB_INF[droga_nome]
    
    st.markdown("### Preparo")
    c1, c2, c3 = st.columns(3)
    
    label_qtd = "Qtd. UI na Ampola" if "UI" in str(info['unidade']) else "Qtd. Mg na Ampola"
    
    with c1: n_ampolas = st.number_input("Número de Ampolas", value=1.0, step=0.1, format="%.1f")
    with c2: vol_diluente = st.number_input("Volume de Diluente (ml)", value=246.0, step=1.0, format="%.1f")
        
    qtd_total = n_ampolas * float(info['mg_amp'])
    vol_total = (n_ampolas * float(info['vol_amp'])) + vol_diluente
    if vol_total <= 0: vol_total = 1
    conc_principal = qtd_total / vol_total
    conc_secundaria = conc_principal * 1000
    
    unidade_str = str(info['unidade'])
    
    if "UI" in unidade_str:
        label_conc_1 = "UI/ml"
        label_conc_2 = "mUI/ml"
    else:
        label_conc_1 = "mg/ml"
        label_conc_2 = "mcg/ml"

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
        ml_h_atual = st.number_input("Velocidade Atual da Bomba (ml/h)", value=float(bomba_min), step=0.1, format="%.1f")
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
            if dose_real > float(info['dose_max_tol']): st.error("🚨 PERIGO")
            elif dose_real > float(info['dose_max_hab']): st.warning("⚠️ Atenção")
            else: st.success("✅ Segura")

    st.markdown("---")
    with st.expander("⚙️ Gerenciar Banco de Dados (Cloud)"):
        tab_add, tab_del = st.tabs(["➕ Adicionar", "❌ Excluir"])
        with tab_add:
            with st.form("form_add_cloud"):
                st.caption("Salva diretamente no Google Sheets.")
                fa1, fa2, fa3 = st.columns(3)
                with fa1: n_nome = st.text_input("Nome", key="add_nome")
                with fa2: n_mg_str = st.text_input("Qtd. Ampola", key="add_mg")
                with fa3: n_vol_str = st.text_input("Ml Ampola", key="add_vol")
                fa4, fa5, fa6 = st.columns(3)
                with fa4: n_min_str = st.text_input("Dose Min", key="add_min")
                with fa5: n_max_h_str = st.text_input("Máx Habitual", key="add_max_h")
                with fa6: n_max_t_str = st.text_input("Máx Tolerada", key="add_max_t")
                n_unid = st.selectbox("Unidade", ["mcg/kg/min", "mcg/kg/h", "mg/kg/h", "mg/h", "mg/min", "mcg/min", "UI/min", "UI/kg/h", "mg/kg/min"], key="add_unid")
                
                if st.form_submit_button("💾 Salvar na Nuvem"):
                    n_mg = parse_input_flex(n_mg_str)
                    n_vol = parse_input_flex(n_vol_str)
                    n_min = parse_input_flex(n_min_str)
                    n_max_h = parse_input_flex(n_max_h_str)
                    n_max_t = parse_input_flex(n_max_t_str)

                    if n_nome and n_mg > 0:
                        sufixo_conc = "UI" if "UI" in n_unid else "mg"
                        if n_vol > 0:
                            conc = n_mg/n_vol
                            conc_str = f"{int(conc)}" if conc.is_integer() else f"{conc:.1f}"
                            nome_final = f"{n_nome} {n_vol}ml ({conc_str}{sufixo_conc}/ml)"
                        else:
                            nome_final = f"{n_nome} (Pó)"
                            
                        # Dicionário na ordem exata das colunas do Sheets
                        # Ordem esperada: nome_formatado, mg_amp, vol_amp, dose_min, dose_max_hab, dose_max_tol, unidade
                        new_row = {
                            "nome_formatado": nome_final,
                            "mg_amp": n_mg, "vol_amp": n_vol, "dose_min": n_min,
                            "dose_max_hab": n_max_h, "dose_max_tol": n_max_t, "unidade": n_unid
                        }
                        
                        st.info("Salvando no Google Sheets...")
                        if save_row_to_sheet(SHEET_NAME_INF, new_row):
                            st.success("Salvo! Recarregando...")
                            st.session_state["df_inf"] = load_data_from_sheet(SHEET_NAME_INF)
                            st.rerun()
                    else:
                        st.error("Dados inválidos.")

        with tab_del:
            if st.button("🗑️ Excluir Medicamento Selecionado"):
                st.info("Deletando do Google Sheets...")
                if delete_row_from_sheet(SHEET_NAME_INF, "nome_formatado", droga_nome):
                    st.success("Deletado! Recarregando...")
                    st.session_state["df_inf"] = load_data_from_sheet(SHEET_NAME_INF)
                    st.rerun()

# ==============================================================================
# PÁGINA: IOT
# ==============================================================================
def page_iot():
    st.header("⚡ Intubação Orotraqueal (Cloud)")
    
    col_p, col_void = st.columns([1, 3])
    with col_p:
        peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.1, format="%.1f")
    
    st.markdown("### Tabela de Volumes")
    dados_tabela = []
    
    for nome_droga in sorted(MED_DB_IOT.keys()):
        dado = MED_DB_IOT[nome_droga]
        conc = float(dado['conc'])
        vol_min = (float(dado['dose_min']) * peso) / conc
        vol_hab = (float(dado['dose_hab']) * peso) / conc
        vol_max = (float(dado['dose_max']) * peso) / conc
        
        dados_tabela.append({
            "Medicação": nome_droga,
            "Vol. Mínimo": f"{format_br(vol_min)} ml",
            "Vol. Médio": f"**{format_br(vol_hab)} ml**", 
            "Vol. Máximo": f"{format_br(vol_max)} ml"
        })
        
    df_iot = pd.DataFrame(dados_tabela)
    st.dataframe(df_iot, use_container_width=True, hide_index=True)

    st.markdown("---")
    with st.expander("⚙️ Gerenciar Lista IOT (Cloud)"):
        t1, t2 = st.tabs(["➕ Adicionar", "❌ Remover"])
        with t1:
            with st.form("iot_add_cloud"):
                c1, c2 = st.columns(2)
                with c1: i_nome = st.text_input("Nome", key="iot_nome")
                with c2: i_conc_str = st.text_input("Conc. (mg/ml)", key="iot_conc")
                c3, c4, c5 = st.columns(3)
                with c3: i_min_str = st.text_input("Min", key="iot_min")
                with c4: i_hab_str = st.text_input("Hab", key="iot_hab")
                with c5: i_max_str = st.text_input("Max", key="iot_max")
                
                if st.form_submit_button("Salvar na Nuvem"):
                    i_conc = parse_input_flex(i_conc_str)
                    i_min = parse_input_flex(i_min_str)
                    i_hab = parse_input_flex(i_hab_str)
                    i_max = parse_input_flex(i_max_str)
                    
                    if i_nome and i_conc > 0:
                        # Ordem: nome_formatado, conc, dose_min, dose_hab, dose_max
                        new_row = {
                            "nome_formatado": i_nome, "conc": i_conc,
                            "dose_min": i_min, "dose_hab": i_hab, "dose_max": i_max
                        }
                        if save_row_to_sheet(SHEET_NAME_IOT, new_row):
                            st.success("Salvo!")
                            st.session_state["df_iot"] = load_data_from_sheet(SHEET_NAME_IOT)
                            st.rerun()

        with t2:
            droga_del = st.selectbox("Remover", sorted(MED_DB_IOT.keys()), key="del_iot_sel")
            if st.button("🗑️ Remover IOT"):
                if delete_row_from_sheet(SHEET_NAME_IOT, "nome_formatado", droga_del):
                    st.success("Removido!")
                    st.session_state["df_iot"] = load_data_from_sheet(SHEET_NAME_IOT)
                    st.rerun()

# ==============================================================================
# PÁGINA: CONVERSÃO (SEM DB)
# ==============================================================================
def page_conversao():
    st.header("🔄 Conversão Universal")
    
    st.markdown("##### 1. Configurar Solução")
    col_setup1, col_setup2 = st.columns([1, 3])
    with col_setup1:
        peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.1, key="conv_peso")
    
    with col_setup2:
        c_qtd, c_unid, c_vol = st.columns(3)
        with c_qtd: qtd = st.number_input("Qtd. Total", value=250.0, step=1.0, key="conv_qtd")
        with c_unid: unid = st.selectbox("Unidade", ["mg", "mcg", "g", "UI"], key="conv_unid")
        with c_vol: vol = st.number_input("Volume Total (ml)", value=250.0, step=1.0, key="conv_vol")

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
    with t2:
        # Simplificado para nuvem
        pass

# ==============================================================================
# NAVEGAÇÃO
# ==============================================================================
st.sidebar.title("Menu Principal")
nav = st.sidebar.radio("Ir para:", ["Infusão Contínua", "Intubação Orotraqueal", "Conversão Universal"])

if nav == "Infusão Contínua": calcular_infusao()
elif nav == "Intubação Orotraqueal": page_iot()
elif nav == "Conversão Universal": page_conversao()