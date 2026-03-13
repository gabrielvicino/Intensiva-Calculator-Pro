import os
import time
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from calculos.infusao_data import _DADOS_INFUSAO_PADRAO

# ── Conexão PostgreSQL (Supabase direto) ──────────────────────────────────────

def _get_supabase_url() -> str:
    """Lê SUPABASE_DB_URL de st.secrets, variável de ambiente ou secrets.toml direto."""
    # 1. st.secrets
    try:
        val = st.secrets["SUPABASE_DB_URL"]
        if val:
            return str(val)
    except Exception:
        pass

    # 2. Variável de ambiente
    val = os.getenv("SUPABASE_DB_URL", "")
    if val:
        return val

    # 3. Leitura direta do secrets.toml (fallback para casos de cache/path)
    try:
        from pathlib import Path
        for base in (Path(__file__).parent, Path.cwd()):
            p = base / ".streamlit" / "secrets.toml"
            if p.exists():
                text = p.read_text(encoding="utf-8")
                for line in text.splitlines():
                    line = line.strip()
                    if line.startswith("SUPABASE_DB_URL"):
                        _, _, v = line.partition("=")
                        v = v.strip().strip('"').strip("'")
                        if v:
                            return v
    except Exception:
        pass

    return ""


def _get_conn():
    """Retorna conexão psycopg2 ao Supabase."""
    import psycopg2
    url = _get_supabase_url()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL não configurada em secrets.toml")
    return psycopg2.connect(url, connect_timeout=10)


# ── Helpers de serialização ───────────────────────────────────────────────────

def _limpar_dados(dados: dict) -> dict:
    """Remove chaves com valores vazios — armazena apenas campos preenchidos."""
    return {
        k: v for k, v in dados.items()
        if v is not None and v != "" and v is not False and v != []
    }


# ── Rate Limiting ──────────────────────────────────────────────────────────────

def _rate_config() -> tuple[int, int]:
    """Lê limites de st.secrets ou usa defaults: (max_calls, janela_minutos)."""
    try:
        max_calls  = int(st.secrets.get("RATE_MAX_CALLS",  15))
        janela_min = int(st.secrets.get("RATE_JANELA_MIN",  8))
        return max_calls, janela_min
    except Exception:
        return 15, 8


def verificar_rate_limit() -> tuple[bool, str]:
    """Verifica se a sessão excedeu o limite de chamadas à IA no período."""
    max_calls, janela_min = _rate_config()
    janela_seg = janela_min * 60
    agora = time.time()

    if "_rate_timestamps" not in st.session_state:
        st.session_state["_rate_timestamps"] = []

    st.session_state["_rate_timestamps"] = [
        t for t in st.session_state["_rate_timestamps"]
        if agora - t < janela_seg
    ]

    contagem = len(st.session_state["_rate_timestamps"])

    if contagem >= max_calls:
        mais_antigo = st.session_state["_rate_timestamps"][0]
        restante    = int(janela_seg - (agora - mais_antigo))
        minutos     = restante // 60
        segundos    = restante % 60
        return False, (
            f"Limite de {max_calls} chamadas por {janela_min} min atingido. "
            f"Aguarde {minutos}m {segundos}s antes de nova chamada à IA."
        )

    st.session_state["_rate_timestamps"].append(agora)
    return True, ""


def uso_rate_limit() -> tuple[int, int, int]:
    """Retorna (chamadas_na_janela, max_calls, segundos_ate_reset) para exibição."""
    max_calls, janela_min = _rate_config()
    janela_seg = janela_min * 60
    agora = time.time()

    timestamps = [
        t for t in st.session_state.get("_rate_timestamps", [])
        if agora - t < janela_seg
    ]
    contagem = len(timestamps)
    segundos_reset = int(janela_seg - (agora - timestamps[0])) if timestamps else 0
    return contagem, max_calls, segundos_reset


def carregar_chave_api(nome_secret: str, nome_env: str) -> str:
    """Carrega chave de API dos secrets do Streamlit ou variável de ambiente."""
    try:
        if hasattr(st, "secrets") and nome_secret in st.secrets:
            return st.secrets[nome_secret]
    except Exception:
        pass
    return os.getenv(nome_env, "")


# ── Evoluções — save / load ───────────────────────────────────────────────────

def save_evolucao(prontuario: str, nome: str, dados: dict) -> bool:
    """
    Salva evolução no Supabase (PostgreSQL).
    - Tabela `evolucoes`: upsert — mantém sempre o estado mais recente.
    - Tabela `evolucoes_historico`: append — preserva histórico completo.
    Apenas campos não-vazios são armazenados (compacto, sem gzip).
    """
    pront      = str(prontuario).strip().replace(".0", "")
    nome_      = str(nome).strip()
    data_hora  = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados_limpos = _limpar_dados(dados)
    dados_json   = json.dumps(dados_limpos, ensure_ascii=False, default=str)

    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                # Upsert na tabela principal
                cur.execute(
                    """
                    INSERT INTO evolucoes (prontuario, nome, dados, atualizado)
                    VALUES (%s, %s, %s::jsonb, now())
                    ON CONFLICT (prontuario)
                    DO UPDATE SET
                        nome      = EXCLUDED.nome,
                        dados     = EXCLUDED.dados,
                        atualizado = now()
                    """,
                    (pront, nome_, dados_json),
                )
                # Append no histórico
                cur.execute(
                    """
                    INSERT INTO evolucoes_historico (prontuario, dados, salvo_em)
                    VALUES (%s, %s::jsonb, now())
                    """,
                    (pront, dados_json),
                )
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar no banco: {e}")
        return False


def load_evolucao(prontuario: str) -> dict | None:
    """
    Carrega o estado mais recente de um paciente.
    Retorna dict com todos os campos, ou None se não encontrado.
    O campo '_data_hora' indica quando foi salvo.
    """
    pront = str(prontuario).strip().replace(".0", "")
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT dados, atualizado FROM evolucoes WHERE prontuario = %s",
                (pront,),
            )
            row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        dados = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        dados["_data_hora"] = (
            row[1].strftime("%d/%m/%Y %H:%M") if hasattr(row[1], "strftime") else str(row[1])
        )
        return dados

    except Exception as e:
        st.error(f"❌ Erro ao buscar no banco: {e}")
        return None


def check_evolucao_exists(prontuario: str) -> bool:
    """Verifica se já existe registro para o prontuário."""
    pront = str(prontuario).strip().replace(".0", "")
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM evolucoes WHERE prontuario = %s LIMIT 1",
                (pront,),
            )
            exists = cur.fetchone() is not None
        conn.close()
        return exists
    except Exception:
        return False


# ── Supabase — dados de referência (IOT e Infusão) ───────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_db_iot() -> pd.DataFrame:
    """Carrega tabela db_iot do Supabase com cache de 1 hora."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nome_formatado, conc, dose_min, dose_hab, dose_max "
                "FROM db_iot ORDER BY id"
            )
            rows = cur.fetchall()
            cols = ["nome_formatado", "conc", "dose_min", "dose_hab", "dose_max"]
        conn.close()
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        st.error(f"❌ Erro ao carregar DB_IOT: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_db_infusao() -> pd.DataFrame:
    """Carrega tabela db_infusao do Supabase com cache de 1 hora."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nome_formatado, mg_amp, vol_amp, dose_min, dose_max_hab, "
                "       dose_max_tol, unidade, qtd_amp_padrao, diluente_padrao "
                "FROM db_infusao ORDER BY id"
            )
            rows = cur.fetchall()
            cols = [
                "nome_formatado", "mg_amp", "vol_amp", "dose_min",
                "dose_max_hab", "dose_max_tol", "unidade",
                "qtd_amp_padrao", "diluente_padrao",
            ]
        conn.close()
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        st.error(f"❌ Erro ao carregar DB_INFUSAO: {e}")
        return pd.DataFrame()


# ── Google Sheets — mantido apenas para save_data_append legado ───────────────

from streamlit_gsheets import GSheetsConnection
from gspread import service_account_from_dict

SHEET_URL = "https://docs.google.com/spreadsheets/d/15Rxc1tYYmgG7Sikn2UOvz-GFN6jvneMHnA-l-O8keNs/edit?gid=0#gid=0"


def sync_infusao_to_sheet() -> bool:
    """Envia dados padrão de infusão para a aba DB_INFUSAO no Google Sheets."""
    try:
        df = pd.DataFrame(_DADOS_INFUSAO_PADRAO)
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(spreadsheet=SHEET_URL, worksheet="DB_INFUSAO", data=df)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao sincronizar: {e}")
        return False


@st.cache_data(ttl=600, show_spinner=False)
def load_data(worksheet_name: str) -> pd.DataFrame:
    """Carrega dados do Google Sheets com cache de 10 minutos."""
    try:
        df = _read_worksheet_gspread(worksheet_name)
        if df is not None:
            return df
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=600)
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Google Sheets: {e}")
        return pd.DataFrame()


def _read_worksheet_gspread(worksheet_name: str) -> pd.DataFrame | None:
    """Lê qualquer aba do Sheets via gspread. Retorna DataFrame ou None."""
    try:
        gs = st.secrets.get("connections", {}).get("gsheets", {})
        if not gs or gs.get("type") != "service_account":
            return None
        creds = {k: v for k, v in gs.items() if k not in ("spreadsheet", "worksheet")}
        gc = service_account_from_dict(creds)
        sh = gc.open_by_url(SHEET_URL)
        ws = sh.worksheet(worksheet_name)
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame()
    except Exception:
        return None


def save_data_append(worksheet_name, new_data_row):
    try:
        existing_data = _read_worksheet_gspread(worksheet_name)
        if existing_data is None:
            conn = st.connection("gsheets", type=GSheetsConnection)
            existing_data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)

        qtd_planilha = len(existing_data.columns)
        qtd_codigo   = len(new_data_row)

        if qtd_codigo != qtd_planilha:
            st.error(
                f"❌ ERRO DE CONTAGEM: O código está enviando {qtd_codigo} dados, "
                f"mas o Python achou {qtd_planilha} colunas na planilha."
            )
            return False

        new_df   = pd.DataFrame([new_data_row], columns=existing_data.columns)
        updated  = pd.concat([existing_data, new_df], ignore_index=True)
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=updated)
        return True
    except Exception as e:
        st.error(f"Erro detalhado do Google: {e}")
        return False


def mostrar_rodape():
    """Exibe rodapé padrão com nota legal em todas as páginas."""
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
        unsafe_allow_html=True,
    )
