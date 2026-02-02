import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Link da sua planilha
SHEET_URL = "https://docs.google.com/spreadsheets/d/15Rxc1tYYmgG7Sikn2UOvz-GFN6jvneMHnA-l-O8keNs/edit?gid=0#gid=0"

def load_data(worksheet_name, csv_fallback=None):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # ttl=0 obriga a ler os dados novos AGORA, ignorando o cache antigo
        df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        return df
    except Exception as e:
        # Se falhar ao conectar no Sheets, tenta carregar do CSV local
        if csv_fallback:
            try:
                # Tenta diferentes encodings comuns
                # CSV brasileiro usa ; como separador e , como decimal
                for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        df = pd.read_csv(csv_fallback, encoding=encoding, sep=';', decimal=',')
                        st.warning(f"⚠️ Usando dados locais ({csv_fallback}). Conexão com Google Sheets indisponível.")
                        return df
                    except UnicodeDecodeError:
                        continue
                # Se nenhum encoding funcionou
                st.error(f"❌ Erro ao carregar CSV: problema de encoding")
                return pd.DataFrame()
            except Exception as csv_error:
                st.error(f"❌ Erro ao carregar CSV: {csv_error}")
                return pd.DataFrame()
        else:
            st.error(f"❌ Erro ao conectar com Google Sheets: {e}")
            return pd.DataFrame()

def save_data_append(worksheet_name, new_data_row):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Lê a planilha REAL agora (sem cache)
        existing_data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        
        # --- DIAGNÓSTICO DE ERRO (Para sabermos o que acontece) ---
        qtd_planilha = len(existing_data.columns)
        qtd_codigo = len(new_data_row)
        
        # Se os números não baterem, ele vai te contar exatamente o porquê
        if qtd_codigo != qtd_planilha:
            st.error(f"❌ ERRO DE CONTAGEM: O código está enviando {qtd_codigo} dados, mas o Python achou {qtd_planilha} colunas na planilha.")
            st.error("Motivo provável: O cache do Streamlit está lendo a versão antiga da planilha.")
            return False
            
        # Se passou no teste, salva
        new_df = pd.DataFrame([new_data_row], columns=existing_data.columns)
        updated_df = pd.concat([existing_data, new_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=updated_df)
        return True
        
    except Exception as e:
        st.error(f"Erro detalhado do Google: {e}")
        return False

def mostrar_rodape():
    """Exibe rodapé padrão com nota legal em todas as páginas"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 20px 0; color: #666; font-size: 0.88em; line-height: 1.4;'>
            <p style='margin: 0; color: #888; font-size: 0.98em;'>
                <strong>Intensiva Calculator Pro</strong> | Dr. Gabriel Valladão Vicino - CRM-SP 223.216
            </p>
            <p style='margin: 8px 0 0 0; font-size: 0.88em; font-style: italic;'>
                <strong>Nota Legal:</strong> Esta aplicação destina-se estritamente como ferramenta de auxílio à decisão clínica-assistencial. 
                Não substitui o julgamento clínico individualizado. A responsabilidade final pela decisão terapêutica 
                compete exclusivamente ao profissional habilitado.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )