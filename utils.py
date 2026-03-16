import os
import time
import threading
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

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
_ENV_CACHE: dict[str, str] = {}

def _load_env_key(name: str) -> str:
    """Lê uma chave de todos os locais possíveis (resultado cacheado por nome)."""
    if name in _ENV_CACHE:
        return _ENV_CACHE[name]
    # 1) st.secrets
    try:
        v = st.secrets[name]
        if v:
            _ENV_CACHE[name] = str(v)
            return _ENV_CACHE[name]
    except Exception:
        pass
    # 2) os.environ (populado pelo load_dotenv acima)
    v = os.environ.get(name, "")
    if v:
        _ENV_CACHE[name] = v
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
                    _ENV_CACHE[name] = val.strip().strip('"').strip("'")
                    return _ENV_CACHE[name]
        except Exception:
            continue
    _ENV_CACHE[name] = ""
    return ""

_SB_URL = _load_env_key("SUPABASE_URL")
_SB_KEY = _load_env_key("SUPABASE_KEY")

# Cria o cliente no import — elimina cold start na primeira busca
if _SB_URL and _SB_KEY:
    try:
        from supabase import create_client as _create_client
        _SB_CLIENT = _create_client(_SB_URL, _SB_KEY)
    except Exception:
        _SB_CLIENT = None


def _resolve_key(key: str) -> str:
    """Resolve chave de configuração genérica."""
    return _load_env_key(key)


def _get_sb():
    """Retorna cliente Supabase (singleton)."""
    global _SB_CLIENT
    if _SB_CLIENT is not None:
        return _SB_CLIENT

    if not _SB_URL or not _SB_KEY:
        raise RuntimeError(
            "Supabase não configurado.\n"
            f"  SUPABASE_URL: {'OK' if _SB_URL else 'VAZIA'}\n"
            f"  SUPABASE_KEY: {'OK' if _SB_KEY else 'VAZIA'}\n"
            f"  .env: {(_PROJECT_DIR / '.env').exists()}\n"
            f"  secrets.toml: {(_PROJECT_DIR / '.streamlit' / 'secrets.toml').exists()}\n"
            f"  Diretório: {_PROJECT_DIR}"
        )

    from supabase import create_client
    _SB_CLIENT = create_client(_SB_URL, _SB_KEY)
    return _SB_CLIENT


# ── Helpers ───────────────────────────────────────────────────────────────────

def _limpar_dados(dados: dict) -> dict:
    """Remove chaves com valores vazios — armazena apenas campos preenchidos.
    Preserva False para chaves inc_* (toggles de inclusão de seção)."""
    return {
        k: v for k, v in dados.items()
        if v is not None and v != "" and v != []
        and (v is not False or k.startswith("inc_"))
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

def _inserir_historico(pront: str, dados_limpos: dict) -> None:
    """Insere no histórico em background — não bloqueia o save principal."""
    try:
        _get_sb().table("evolucoes_historico").insert({
            "prontuario": pront,
            "dados": dados_limpos,
        }).execute()
    except Exception:
        pass


def _load_dados_db_direto(pront: str) -> dict:
    """Carrega dados do banco diretamente, sem cache de session_state.
    Usado internamente pelo merge em save_evolucao (thread-safe)."""
    try:
        sb = _get_sb()
        resp = (
            sb.table("evolucoes")
            .select("dados")
            .eq("prontuario", pront)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return {}
        row = resp.data[0]
        raw = row["dados"]
        return raw if isinstance(raw, dict) else json.loads(raw)
    except Exception:
        return {}


def save_evolucao(prontuario: str, nome: str, dados: dict) -> bool:
    """
    Salva evolução no Supabase via REST com MERGE.
    - Carrega dados existentes e mescla: campos do banco que não estão
      no novo save (ex: lab_*/ctrl_* salvos pelo PACER) são preservados.
    - Novos dados têm prioridade sobre os existentes.
    - Tabela `evolucoes`: upsert síncrono (estado mais recente).
    - Tabela `evolucoes_historico`: insert assíncrono em thread (não bloqueia).
    """
    pront = str(prontuario).strip().replace(".0", "")
    nome_ = str(nome).strip()
    dados_limpos = _limpar_dados(dados)

    # ── MERGE: preserva campos do banco que não estão neste save ─────────────
    # Caso de uso crítico: auto-save da Evolução Diária pode não ter lab_*/ctrl_*
    # no session_state, mas eles já existem no banco (salvos pelo PACER).
    # Sem o merge, o upsert apagaria esses campos.
    try:
        existing = {}
        try:
            cache_key = f"_cache_evolucao_{pront}"
            _cached = st.session_state.get(cache_key)
            if _cached and time.time() - _cached.get("_ts", 0) < 60:
                existing = {k: v for k, v in _cached.items() if k not in ("_ts", "_data_hora")}
            else:
                existing = _load_dados_db_direto(pront)
        except Exception:
            # st.session_state indisponível (background thread) — vai direto ao banco
            existing = _load_dados_db_direto(pront)

        if existing:
            base = _limpar_dados(existing)
            base.update(dados_limpos)
            dados_limpos = base
    except Exception:
        pass

    try:
        sb = _get_sb()
        sb.table("evolucoes").upsert({
            "prontuario": pront,
            "nome": nome_,
            "dados": dados_limpos,
            "atualizado": datetime.now().isoformat(),
        }).execute()
        # Histórico em background — não adiciona latência perceptível
        threading.Thread(
            target=_inserir_historico, args=(pront, dados_limpos), daemon=True
        ).start()
        # Invalida cache local para este prontuário
        try:
            st.session_state.pop(f"_cache_evolucao_{pront}", None)
        except Exception:
            pass
        return True
    except Exception as e:
        try:
            st.error(f"❌ Erro ao salvar no banco: {e}")
            st.session_state["_db_error"] = True
        except Exception:
            pass
        return False


def load_evolucao(prontuario: str) -> dict | None:
    """
    Carrega o estado mais recente de um paciente.
    Usa cache em session_state (TTL 60s) para evitar roundtrips redundantes.
    """
    pront = str(prontuario).strip().replace(".0", "")
    cache_key = f"_cache_evolucao_{pront}"
    cached = st.session_state.get(cache_key)
    if cached and time.time() - cached.get("_ts", 0) < 60:
        return {k: v for k, v in cached.items() if k != "_ts"}

    try:
        sb = _get_sb()
        resp = (
            sb.table("evolucoes")
            .select("dados, atualizado")
            .eq("prontuario", pront)
            .limit(1)
            .execute()
        )
        if not resp.data:
            return None
        row = resp.data[0]
        dados = row["dados"] if isinstance(row["dados"], dict) else json.loads(row["dados"])
        atualizado = row.get("atualizado", "")
        if atualizado and "T" in str(atualizado):
            try:
                dt = datetime.fromisoformat(str(atualizado).replace("Z", "+00:00"))
                atualizado = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass
        dados["_data_hora"] = str(atualizado)
        # Salva no cache com timestamp
        st.session_state[cache_key] = {**dados, "_ts": time.time()}
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


@st.cache_data(ttl=3600, show_spinner=False)
def load_db_atb() -> pd.DataFrame:
    """Carrega tabela db_atb (antibióticos - ajuste renal) do Supabase."""
    try:
        sb = _get_sb()
        resp = sb.table("db_atb").select(
            "farmaco, condicao_clinica, tfg_min, tfg_max, "
            "modalidade_dialise, dose_1, dose_2, dose_3, dose_4, dose_5"
        ).execute()
        return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar DB_ATB: {e}")
        return pd.DataFrame()


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
