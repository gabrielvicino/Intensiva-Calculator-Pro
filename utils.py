import pandas as pd
import streamlit as st
import base64
import unicodedata

# --- Tenta importar GSheets. Se não tiver instalado, apenas ignora. ---
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSHEETS_DISPONIVEL = True
except ImportError:
    GSHEETS_DISPONIVEL = False

# --- 1. CONFIGURAÇÃO VISUAL ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

def set_background(png_file):
    try:
        bin_str = get_base64_of_bin_file(png_file)
        if bin_str:
            page_bg_img = '''
            <style>
            .stApp {
            background-image: url("data:image/png;base64,%s");
            background-size: cover;
            }
            </style>
            ''' % bin_str
            st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        pass

# --- 2. FUNÇÕES DE NORMALIZAÇÃO ---
def normalize_col_name(col_name):
    if not isinstance(col_name, str):
        return str(col_name)
    nfkd_form = unicodedata.normalize('NFKD', col_name)
    without_accents = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return without_accents.lower().strip().replace(' ', '_').replace('/', '_').replace('.', '')

def clean_dataframe(df):
    if df.empty: return df
    df.columns = [normalize_col_name(c) for c in df.columns]
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        if 'nome' not in col and 'apresentacao' not in col:
            df[col] = pd.to_numeric(df[col], errors='ignore')
    return df

# --- 3. CARREGAMENTO INTELIGENTE ---
@st.cache_data(ttl=600)
def load_data(sheet_name, csv_fallback):
    df = pd.DataFrame()
    source = "Nenhum"

    # TENTATIVA 1: GOOGLE SHEETS (Só tenta se a biblioteca estiver instalada)
    if GSHEETS_DISPONIVEL:
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            # Verifica se existe segredo configurado
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                client = gspread.authorize(creds)
                sheet = client.open("IntensivaDB").worksheet(sheet_name)
                data = sheet.get_all_records()
                df = pd.DataFrame(data)
                source = "Google Sheets ☁️"
        except Exception as e:
            # Falha silenciosa no GSheets, vai pro CSV
            pass
    
    # TENTATIVA 2: CSV LOCAL
    if df.empty:
        try:
            for enc in ['utf-8', 'latin1', 'iso-8859-1']:
                try:
                    df = pd.read_csv(csv_fallback, sep=';', decimal=',', encoding=enc)
                    source = "Backup Local 📂"
                    break
                except UnicodeDecodeError:
                    continue
        except Exception:
            st.error(f"Erro fatal: Não foi possível carregar dados ({csv_fallback}).")
            return pd.DataFrame()

    return clean_dataframe(df)