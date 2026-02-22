import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
from datetime import datetime

# Link da sua planilha
SHEET_URL = "https://docs.google.com/spreadsheets/d/15Rxc1tYYmgG7Sikn2UOvz-GFN6jvneMHnA-l-O8keNs/edit?gid=0#gid=0"

# Nome da aba de evoluções na planilha
_ABA_EVOLUCOES = "EVOLUCOES"

# Dados padrão de infusão (pré-carregamento: ampolas + diluente) - enviados ao Sheet via sync
_DADOS_INFUSAO_PADRAO = [
    {"nome_formatado": "Amiodarona 3ml (50mg/ml)", "mg_amp": 150.0, "vol_amp": 3.0, "dose_min": 0.0, "dose_max_hab": 0.0, "dose_max_tol": 0.0, "unidade": "mg/min", "qtd_amp_padrao": 2, "diluente_padrao": 244},
    {"nome_formatado": "Atracúrio 2.5ml (10mg/ml)", "mg_amp": 25.0, "vol_amp": 2.5, "dose_min": 5.0, "dose_max_hab": 20.0, "dose_max_tol": 20.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 4, "diluente_padrao": 90},
    {"nome_formatado": "Atracúrio 5ml (10mg/ml)", "mg_amp": 50.0, "vol_amp": 5.0, "dose_min": 5.0, "dose_max_hab": 20.0, "dose_max_tol": 20.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 2, "diluente_padrao": 90},
    {"nome_formatado": "Cisatracúrio 5ml (2mg/ml)", "mg_amp": 10.0, "vol_amp": 5.0, "dose_min": 1.0, "dose_max_hab": 3.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 10, "diluente_padrao": 50},
    {"nome_formatado": "Dexmedetomidina 2ml (100mcg/ml)", "mg_amp": 0.2, "vol_amp": 2.0, "dose_min": 0.1, "dose_max_hab": 0.7, "dose_max_tol": 1.5, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 48},
    {"nome_formatado": "Dobutamina 20ml (12.5mg/ml)", "mg_amp": 250.0, "vol_amp": 20.0, "dose_min": 2.5, "dose_max_hab": 20.0, "dose_max_tol": 40.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 230},
    {"nome_formatado": "Dopamina 10ml (5mg/ml)", "mg_amp": 50.0, "vol_amp": 10.0, "dose_min": 5.0, "dose_max_hab": 20.0, "dose_max_tol": 50.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 5, "diluente_padrao": 200},
    {"nome_formatado": "Esmolol 10ml (10mg/ml)", "mg_amp": 100.0, "vol_amp": 10.0, "dose_min": 50.0, "dose_max_hab": 200.0, "dose_max_tol": 300.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Esmolol 250ml (10mg/ml)", "mg_amp": 2500.0, "vol_amp": 250.0, "dose_min": 50.0, "dose_max_hab": 200.0, "dose_max_tol": 300.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Fentanil 2ml (50mcg/ml)", "mg_amp": 0.1, "vol_amp": 2.0, "dose_min": 0.5, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Fentanil 5ml (50mcg/ml)", "mg_amp": 0.25, "vol_amp": 5.0, "dose_min": 0.5, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Fentanil 10ml (50mcg/ml)", "mg_amp": 0.5, "vol_amp": 10.0, "dose_min": 0.5, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Lidocaína 20ml (20mg/ml)", "mg_amp": 400.0, "vol_amp": 20.0, "dose_min": 1.0, "dose_max_hab": 4.0, "dose_max_tol": 4.0, "unidade": "mg/min", "qtd_amp_padrao": 2, "diluente_padrao": 210},
    {"nome_formatado": "Midazolam 3ml (5mg/ml)", "mg_amp": 15.0, "vol_amp": 3.0, "dose_min": 0.02, "dose_max_hab": 0.2, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 7, "diluente_padrao": 79},
    {"nome_formatado": "Midazolam 5ml (1mg/ml)", "mg_amp": 5.0, "vol_amp": 5.0, "dose_min": 0.02, "dose_max_hab": 0.2, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 20, "diluente_padrao": 0},
    {"nome_formatado": "Midazolam 10ml (5mg/ml)", "mg_amp": 50.0, "vol_amp": 10.0, "dose_min": 0.02, "dose_max_hab": 0.2, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 2, "diluente_padrao": 80},
    {"nome_formatado": "Morfina 1ml (10mg/ml)", "mg_amp": 10.0, "vol_amp": 1.0, "dose_min": 2.0, "dose_max_hab": 4.0, "dose_max_tol": 10.0, "unidade": "mg/h", "qtd_amp_padrao": 10, "diluente_padrao": 90},
    {"nome_formatado": "Nitroglicerina 5ml (5mg/ml)", "mg_amp": 25.0, "vol_amp": 5.0, "dose_min": 5.0, "dose_max_hab": 200.0, "dose_max_tol": 400.0, "unidade": "mcg/min", "qtd_amp_padrao": 2, "diluente_padrao": 240},
    {"nome_formatado": "Nitroprussiato 2ml (25mg/ml)", "mg_amp": 50.0, "vol_amp": 2.0, "dose_min": 0.25, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 248},
    {"nome_formatado": "Norepinefrina 4ml (1mg/ml)", "mg_amp": 4.0, "vol_amp": 4.0, "dose_min": 0.01, "dose_max_hab": 1.0, "dose_max_tol": 2.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 4, "diluente_padrao": 234},
    {"nome_formatado": "Norepinefrina 4ml (2mg/ml)", "mg_amp": 8.0, "vol_amp": 4.0, "dose_min": 0.01, "dose_max_hab": 1.0, "dose_max_tol": 2.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 2, "diluente_padrao": 242},
    {"nome_formatado": "Propofol 1% 20ml (10mg/ml)", "mg_amp": 200.0, "vol_amp": 20.0, "dose_min": 5.0, "dose_max_hab": 50.0, "dose_max_tol": 80.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Propofol 1% 50ml (10mg/ml)", "mg_amp": 500.0, "vol_amp": 50.0, "dose_min": 5.0, "dose_max_hab": 50.0, "dose_max_tol": 80.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Propofol 2% 50ml (20mg/ml)", "mg_amp": 1000.0, "vol_amp": 50.0, "dose_min": 5.0, "dose_max_hab": 50.0, "dose_max_tol": 80.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Remifentanil 2mg (Pó)", "mg_amp": 2.0, "vol_amp": 0.0, "dose_min": 0.01, "dose_max_hab": 0.5, "dose_max_tol": 1.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 50},
    {"nome_formatado": "Remifentanil 5mg (Pó)", "mg_amp": 5.0, "vol_amp": 0.0, "dose_min": 0.01, "dose_max_hab": 0.5, "dose_max_tol": 1.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 50},
    {"nome_formatado": "Rocurônio 5ml (10mg/ml)", "mg_amp": 50.0, "vol_amp": 5.0, "dose_min": 3.0, "dose_max_hab": 12.0, "dose_max_tol": 16.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 2, "diluente_padrao": 90},
    {"nome_formatado": "Vasopressina 1ml (20UI/ml)", "mg_amp": 20.0, "vol_amp": 1.0, "dose_min": 0.01, "dose_max_hab": 0.04, "dose_max_tol": 0.06, "unidade": "UI/min", "qtd_amp_padrao": 1, "diluente_padrao": 99},
    {"nome_formatado": "Cetamina 2ml (50mg/ml)", "mg_amp": 100.0, "vol_amp": 2.0, "dose_min": 0.05, "dose_max_hab": 0.5, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 5, "diluente_padrao": 40},
    {"nome_formatado": "Adrenalina 1ml (1mg/ml)", "mg_amp": 1.0, "vol_amp": 1.0, "dose_min": 0.01, "dose_max_hab": 1.0, "dose_max_tol": 2.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 4, "diluente_padrao": 246},
    {"nome_formatado": "Terbutalina 1ml (0.5mg/ml)", "mg_amp": 0.5, "vol_amp": 1.0, "dose_min": 0.1, "dose_max_hab": 0.4, "dose_max_tol": 0.6, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 49},
    {"nome_formatado": "Octreotida 1ml (0,1mg/ml)", "mg_amp": 0.1, "vol_amp": 1.0, "dose_min": 50.0, "dose_max_hab": 50.0, "dose_max_tol": 50.0, "unidade": "mcg/h", "qtd_amp_padrao": 5, "diluente_padrao": 95},
]


def sync_infusao_to_sheet() -> bool:
    """
    Envia os dados padrão de infusão para a aba DB_INFUSAO no Google Sheets.
    Usa os valores embutidos no código (pré-carregamento: ampolas + diluente).
    """
    try:
        df = pd.DataFrame(_DADOS_INFUSAO_PADRAO)
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(spreadsheet=SHEET_URL, worksheet="DB_INFUSAO", data=df)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao sincronizar: {e}")
        return False


def load_data(worksheet_name):
    """Carrega dados do Google Sheets. Sempre usa Sheets (sem fallback CSV)."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # ttl=0 obriga a ler os dados novos AGORA, ignorando o cache antigo
        df = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        return df
    except Exception as e:
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

def save_evolucao(prontuario: str, nome: str, dados: dict) -> bool:
    """
    Salva uma evolução diária na aba EVOLUCOES do Google Sheets.
    Cada chamada ACRESCENTA uma nova linha — o histórico é mantido.
    Estrutura da planilha: prontuario | nome | data_hora | dados_json
    """
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)

        nova_linha = pd.DataFrame([{
            "prontuario": str(prontuario).strip().replace(".0", ""),
            "nome":       str(nome).strip(),
            "data_hora":  datetime.now().strftime("%d/%m/%Y %H:%M"),
            "dados_json": json.dumps(dados, ensure_ascii=False, default=str),
        }])

        try:
            existing = conn.read(
                spreadsheet=SHEET_URL,
                worksheet=_ABA_EVOLUCOES,
                ttl=0,
            )
            if existing is not None and not existing.empty:
                updated = pd.concat([existing, nova_linha], ignore_index=True)
            else:
                updated = nova_linha
        except Exception:
            # Aba ainda não existe ou está vazia — inicia com a primeira linha
            updated = nova_linha

        conn.update(
            spreadsheet=SHEET_URL,
            worksheet=_ABA_EVOLUCOES,
            data=updated,
        )
        return True

    except Exception as e:
        st.error(f"❌ Erro ao salvar no Google Sheets: {e}")
        return False


def check_evolucao_exists(prontuario: str) -> bool:
    """
    Verifica se já existe ao menos uma evolução cadastrada para o prontuário.
    """
    try:
        df = load_data(_ABA_EVOLUCOES)
        if df is None or df.empty:
            return False
        df["prontuario"] = (
            df["prontuario"]
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        busca = str(prontuario).strip().replace(".0", "")
        return not df[df["prontuario"] == busca].empty
    except Exception:
        return False


def load_evolucao(prontuario: str) -> dict | None:
    """
    Carrega a ÚLTIMA evolução de um paciente pelo número do prontuário.
    Retorna um dict com todos os campos salvos, ou None se não encontrado.
    O campo '_data_hora' indica quando a evolução foi salva.
    """
    try:
        df = load_data(_ABA_EVOLUCOES)

        if df is None or df.empty:
            return None

        # O Sheets pode entregar o número como float (ex.: "5251511.0")
        # → removemos o sufixo ".0" para garantir a comparação correta
        df["prontuario"] = (
            df["prontuario"]
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        busca_normalizada = str(prontuario).strip().replace(".0", "")
        matches = df[df["prontuario"] == busca_normalizada]

        if matches.empty:
            return None

        # Última linha = evolução mais recente
        latest = matches.iloc[-1]
        dados = json.loads(latest["dados_json"])
        dados["_data_hora"] = str(latest.get("data_hora", ""))
        return dados

    except Exception as e:
        st.error(f"❌ Erro ao buscar no Google Sheets: {e}")
        return None


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