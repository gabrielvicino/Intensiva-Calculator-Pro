import os
import time
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from calculos.infusao_data import _DADOS_INFUSAO_PADRAO

_PROJECT_DIR = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_PROJECT_DIR / ".env", override=True)
except ImportError:
    pass

# ── Supabase — resolução de chaves no nível do módulo (mais robusto) ──────────

_SB_CLIENT = None
_SB_URL = ""
_SB_KEY = ""

def _load_env_key(name: str) -> str:
    """Lê uma chave de todos os locais possíveis."""
    # 1) st.secrets
    try:
        v = st.secrets[name]
        if v:
            return str(v)
    except Exception:
        pass
    # 2) os.environ (populado pelo load_dotenv acima)
    v = os.environ.get(name, "")
    if v:
        return v
    # 3) Leitura direta dos arquivos
    for fpath in [_PROJECT_DIR / ".env", _PROJECT_DIR / ".streamlit" / "secrets.toml"]:
        try:
            if not fpath.exists():
                continue
            for line in fpath.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s.startswith("#") or "=" not in s:
                    continue
                k, _, val = s.partition("=")
                if k.strip().strip('"').strip("'") == name:
                    return val.strip().strip('"').strip("'")
        except Exception:
            continue
    return ""

_SB_URL = _load_env_key("SUPABASE_URL")
_SB_KEY = _load_env_key("SUPABASE_KEY")


def _resolve_key(key: str) -> str:
    """Resolve chave de configuração genérica."""
    return _load_env_key(key)


def _get_sb():
    """Retorna cliente Supabase (singleton)."""
    global _SB_CLIENT
    if _SB_CLIENT is not None:
        return _SB_CLIENT

    url = _SB_URL
    key = _SB_KEY

    if not url or not key:
        raise RuntimeError(
            "Supabase não configurado.\n"
            f"  SUPABASE_URL: {'OK' if url else 'VAZIA'}\n"
            f"  SUPABASE_KEY: {'OK' if key else 'VAZIA'}\n"
            f"  .env: {(_PROJECT_DIR / '.env').exists()}\n"
            f"  secrets.toml: {(_PROJECT_DIR / '.streamlit' / 'secrets.toml').exists()}\n"
            f"  Diretório: {_PROJECT_DIR}"
        )

    from supabase import create_client
    _SB_CLIENT = create_client(url, key)
    return _SB_CLIENT


# ── Helpers ───────────────────────────────────────────────────────────────────

def _limpar_dados(dados: dict) -> dict:
    """Remove chaves com valores vazios — armazena apenas campos preenchidos."""
    return {
        k: v for k, v in dados.items()
        if v is not None and v != "" and v is not False and v != []
    }


# ── Rate Limiting ──────────────────────────────────────────────────────────────

def _rate_config() -> tuple[int, int]:
    try:
        max_calls = int(_resolve_key("RATE_MAX_CALLS") or 15)
        janela_min = int(_resolve_key("RATE_JANELA_MIN") or 8)
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
        restante = int(janela_seg - (agora - mais_antigo))
        minutos = restante // 60
        segundos = restante % 60
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
    return _resolve_key(nome_secret) or _resolve_key(nome_env) or ""


# ── Evoluções — save / load (Supabase REST API) ──────────────────────────────

def save_evolucao(prontuario: str, nome: str, dados: dict) -> bool:
    """
    Salva evolução no Supabase via REST.
    - Tabela `evolucoes`: upsert (mantém estado mais recente).
    - Tabela `evolucoes_historico`: append (preserva histórico completo).
    """
    pront = str(prontuario).strip().replace(".0", "")
    nome_ = str(nome).strip()
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados_limpos = _limpar_dados(dados)

    try:
        sb = _get_sb()
        sb.table("evolucoes").upsert({
            "prontuario": pront,
            "nome": nome_,
            "dados": dados_limpos,
            "atualizado": datetime.now().isoformat(),
        }).execute()
        sb.table("evolucoes_historico").insert({
            "prontuario": pront,
            "dados": dados_limpos,
        }).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar no banco: {e}")
        st.session_state["_db_error"] = True
        return False


def load_evolucao(prontuario: str) -> dict | None:
    """Carrega o estado mais recente de um paciente. Retorna None se não encontrado."""
    pront = str(prontuario).strip().replace(".0", "")
    try:
        sb = _get_sb()
        resp = (
            sb.table("evolucoes")
            .select("dados, atualizado")
            .eq("prontuario", pront)
            .maybe_single()
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data
        dados = row["dados"] if isinstance(row["dados"], dict) else json.loads(row["dados"])
        atualizado = row.get("atualizado", "")
        if atualizado and "T" in str(atualizado):
            try:
                dt = datetime.fromisoformat(str(atualizado).replace("Z", "+00:00"))
                atualizado = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass
        dados["_data_hora"] = str(atualizado)
        return dados
    except Exception as e:
        st.error(f"❌ Erro ao buscar no banco: {e}")
        st.session_state["_db_error"] = True
        return None


def check_evolucao_exists(prontuario: str) -> bool:
    """Verifica se já existe registro para o prontuário."""
    pront = str(prontuario).strip().replace(".0", "")
    try:
        sb = _get_sb()
        resp = (
            sb.table("evolucoes")
            .select("prontuario")
            .eq("prontuario", pront)
            .limit(1)
            .execute()
        )
        return bool(resp.data)
    except Exception:
        return False


# ── Dados de referência (IOT e Infusão) via Supabase REST ────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_db_iot() -> pd.DataFrame:
    """Carrega tabela db_iot do Supabase com cache de 1 hora."""
    try:
        sb = _get_sb()
        resp = sb.table("db_iot").select("nome_formatado, conc, dose_min, dose_hab, dose_max").execute()
        return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar DB_IOT: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_db_infusao() -> pd.DataFrame:
    """Carrega tabela db_infusao do Supabase com cache de 1 hora."""
    try:
        sb = _get_sb()
        resp = sb.table("db_infusao").select(
            "nome_formatado, mg_amp, vol_amp, dose_min, dose_max_hab, "
            "dose_max_tol, unidade, qtd_amp_padrao, diluente_padrao"
        ).execute()
        return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar DB_INFUSAO: {e}")
        return pd.DataFrame()


# ── Google Sheets — mantido apenas para save_data_append legado ───────────────

try:
    from streamlit_gsheets import GSheetsConnection
    from gspread import service_account_from_dict
    _GSHEETS_OK = True
except ImportError:
    _GSHEETS_OK = False

SHEET_URL = "https://docs.google.com/spreadsheets/d/15Rxc1tYYmgG7Sikn2UOvz-GFN6jvneMHnA-l-O8keNs/edit?gid=0#gid=0"


def sync_infusao_to_sheet() -> bool:
    """Envia dados padrão de infusão para a aba DB_INFUSAO no Google Sheets."""
    if not _GSHEETS_OK:
        st.warning("Google Sheets não disponível (pacotes não instalados).")
        return False
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
    """Carrega dados do Google Sheets com cache de 10 minutos (legado)."""
    if not _GSHEETS_OK:
        st.warning("Google Sheets não disponível.")
        return pd.DataFrame()
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
    if not _GSHEETS_OK:
        return None
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
    if not _GSHEETS_OK:
        st.warning("Google Sheets não disponível.")
        return False
    try:
        existing_data = _read_worksheet_gspread(worksheet_name)
        if existing_data is None:
            conn = st.connection("gsheets", type=GSheetsConnection)
            existing_data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)

        qtd_planilha = len(existing_data.columns)
        qtd_codigo = len(new_data_row)

        if qtd_codigo != qtd_planilha:
            st.error(
                f"❌ ERRO DE CONTAGEM: O código está enviando {qtd_codigo} dados, "
                f"mas o Python achou {qtd_planilha} colunas na planilha."
            )
            return False

        new_df = pd.DataFrame([new_data_row], columns=existing_data.columns)
        updated = pd.concat([existing_data, new_df], ignore_index=True)
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
