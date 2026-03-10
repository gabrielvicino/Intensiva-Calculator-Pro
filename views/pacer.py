import streamlit as st
import os
from pathlib import Path
from utils import mostrar_rodape

from modules import fichas as _fichas
from modules.pacer import (
    tab_laboratoriais,
    tab_controles,
    tab_prescricao,
)

# ==============================================================================
# CONFIGURAÇÕES VISUAIS
# ==============================================================================
st.markdown("""
<style>
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #1a73e8;
        border-color: #1a73e8;
        color: white;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #1557b0;
        border-color: #1557b0;
    }
    code {
        font-size: 1.1em !important;
        font-family: 'Courier New', monospace !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button {
        all: unset !important;
        display: block !important;
        width: 100% !important;
        height: 3px !important;
        background: #dee2e6 !important;
        border-radius: 2px !important;
        cursor: pointer !important;
        transition: background 0.2s !important;
        margin: 6px 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {
        background: #adb5bd !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button * {
        display: none !important;
    }
    [data-testid="stStatusWidget"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SETUP — chaves de API e estado
# ==============================================================================
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass


def _carregar_chave(nome_secret: str, nome_env: str) -> str:
    try:
        if hasattr(st, "secrets") and nome_secret in st.secrets:
            return st.secrets[nome_secret]
    except Exception:
        pass
    return os.getenv(nome_env, "")


OPENAI_API_KEY = _carregar_chave("OPENAI_API_KEY", "OPENAI_API_KEY")
GOOGLE_API_KEY = _carregar_chave("GOOGLE_API_KEY", "GOOGLE_API_KEY")

st.session_state.setdefault("usar_analise", False)

_fichas.inicializar_estado()
_fichas._normalizar_datas()   # formata datas digitadas sem barras (ex.: 20022026 → 20/02/2026)

# ==============================================================================
# IA — Google Gemini 2.5 Pro (máxima qualidade para extração de exames)
# ==============================================================================
motor_escolhido = "Google Gemini"
modelo_escolhido = "gemini-2.5-pro"
api_key = GOOGLE_API_KEY

# ==============================================================================
# PÁGINA — cabeçalho e abas
# ==============================================================================
st.header("🔬 Laboratoriais & Controles")

tab_lab, tab_ctrl, tab_presc, tab_cmp = st.tabs([
    "🧪 Laboratoriais",
    "💧 Controles & BH",
    "💊 Prescrição",
    "📊 Análise Clínica",
])

with tab_lab:
    tab_laboratoriais.render(api_key, modelo_escolhido, openai_api_key=OPENAI_API_KEY)

with tab_ctrl:
    tab_controles.render(api_key, modelo_escolhido)

with tab_cmp:
    from modules.gerador.html import gerar_html_comparativo

    _CSS_CMP = (
        "<style>"
        ".cmp-section{"
        "background:#fff;border:1px solid #e0e0e0;border-radius:10px;"
        "padding:16px 20px 10px;margin-bottom:20px;"
        "box-shadow:0 1px 4px rgba(60,64,67,.15)}"
        ".cmp-title{"
        "font-size:.95rem;font-weight:600;color:#1a73e8;"
        "letter-spacing:.01em;display:block;margin-bottom:10px}"
        ".cmp-empty{color:#888;font-size:.88rem;padding:8px 0}"
        "</style>"
    )
    st.markdown(_CSS_CMP, unsafe_allow_html=True)

    html_labs, html_ctrl = gerar_html_comparativo()

    st.markdown(
        "<div class='cmp-section'>"
        "<span class='cmp-title'>🧪 Exames Laboratoriais</span>"
        + (html_labs if html_labs else "<p class='cmp-empty'>Nenhum exame preenchido.</p>")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='cmp-section'>"
        "<span class='cmp-title'>💧 Controles & Balanço Hídrico</span>"
        + (html_ctrl if html_ctrl else "<p class='cmp-empty'>Nenhum controle preenchido.</p>")
        + "</div>",
        unsafe_allow_html=True,
    )

with tab_presc:
    tab_prescricao.render(motor_escolhido, api_key, modelo_escolhido)

mostrar_rodape()
