import re
import streamlit as st
from modules import ui
from modules import agentes_secoes

# ---------------------------------------------------------------------------
# Formatação automática de datas
# ---------------------------------------------------------------------------
_PAT_CHAVE_DATA = re.compile(
    r"(_data|_ultima|_proxima|_antepen|_ini$|_fim$|di_hosp$|di_uti$|di_enf$)",
    re.IGNORECASE,
)


def _fmt_data(val: str) -> str:
    """
    Converte dígitos para formato de data com barras.
    Formatação fluida: 01 → 01/, 0101 → 01/01/, 01012026 → 01/01/2026
    Aceita valores com ou sem barras. Só formata se o valor contiver apenas dígitos e barras.
    """
    if not isinstance(val, str):
        return val
    stripped = val.strip()
    if not stripped:
        return val
    # Só formata se contiver apenas dígitos e barras (evita sobrescrever texto extra)
    if not all(c.isdigit() or c == "/" for c in stripped):
        return val
    digitos = "".join(c for c in stripped if c.isdigit())
    if not digitos:
        return val
    n = len(digitos)
    if n <= 2:
        return f"{digitos}/"
    if n <= 4:
        return f"{digitos[0:2]}/{digitos[2:4]}/"
    if n <= 6:
        return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:6]}"
    if n <= 8:
        return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"
    # Mais de 8 dígitos: formata só os 8 primeiros
    return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"


def _normalizar_datas():
    """
    Percorre todos os campos de session_state com chave de data e
    reformata valores que sejam sequências puras de dígitos.
    Executado a cada rerender (junto com _sanitizar_radios).
    """
    for k, v in list(st.session_state.items()):
        if _PAT_CHAVE_DATA.search(k):
            novo = _fmt_data(v)
            if novo != v:
                st.session_state[k] = novo

# --- IMPORTAÇÃO DAS SEÇÕES ---
from modules.secoes import identificacao      # 1
from modules.secoes import hd                 # 2
from modules.secoes import comorbidades       # 3
from modules.secoes import muc                # 4
from modules.secoes import hmpa               # 5
from modules.secoes import dispositivos       # 6
from modules.secoes import culturas           # 7
from modules.secoes import antibioticos       # 8
from modules.secoes import complementares     # 9
from modules.secoes import laboratoriais      # 10
from modules.secoes import evolucao_clinica   # 11
from modules.secoes import sistemas           # 12
from modules.secoes import controles          # 13
from modules.secoes import prescricao         # 14
from modules.secoes import condutas           # 15

def _campos_base() -> dict:
    """Retorna o dicionário com TODOS os campos do formulário e seus valores padrão."""
    campos = {}
    campos.update(identificacao.get_campos())
    campos.update(hd.get_campos())
    campos.update(comorbidades.get_campos())
    campos.update(muc.get_campos())
    campos.update(hmpa.get_campos())
    campos.update(dispositivos.get_campos())
    campos.update(culturas.get_campos())
    campos.update(antibioticos.get_campos())
    campos.update(complementares.get_campos())
    campos.update(laboratoriais.get_campos())
    campos.update(evolucao_clinica.get_campos())
    campos.update(sistemas.get_campos())
    campos.update(controles.get_campos())
    campos.update(prescricao.get_campos())
    campos.update(condutas.get_campos())
    campos.update({
        'texto_final_gerado': '',
        # campos _notas preenchidos pelo ia_extrator
        'identificacao_notas': '', 'hd_notas': '', 'comorbidades_notas': '',
        'muc_notas': '', 'hmpa_texto': '', 'dispositivos_notas': '',
        'culturas_notas': '', 'antibioticos_notas': '', 'complementares_notas': '',
        'laboratoriais_notas': '', 'controles_notas': '', 'evolucao_notas': '',
        'sistemas_notas': '',
    })
    return campos


def get_todos_campos_keys() -> list:
    """
    Retorna a lista de chaves de todos os campos do formulário.
    Usada para salvar/carregar dados no Google Sheets.
    """
    return list(_campos_base().keys())


def inicializar_estado():
    for k, v in _campos_base().items():
        if k not in st.session_state:
            st.session_state[k] = v


# Cache dos campos padrão — rebuilt apenas uma vez por sessão (não a cada render)
_CAMPOS_BASE_CACHE: dict | None = None

def _get_campos_base_cached() -> dict:
    global _CAMPOS_BASE_CACHE
    if _CAMPOS_BASE_CACHE is None:
        _CAMPOS_BASE_CACHE = _campos_base()
    return _CAMPOS_BASE_CACHE


def _sanitizar_radios():
    """
    Corrige campos de radio com index=None que receberam '' (string vazia) vinda de
    agentes de IA ou do carregamento do Google Sheets.
    Regra: se o valor padrão do campo é None e o atual é '', reseta para None.
    Usa cache dos defaults — não reconstrói _campos_base() a cada render.
    """
    defaults = _get_campos_base_cached()
    for k, v_default in defaults.items():
        if v_default is None and st.session_state.get(k) == "":
            st.session_state[k] = None

def _btn_agente(secao_key: str):
    """
    Retorna uma função que, quando chamada, renderiza o botão
    'Completar Campos' para a seção indicada.
    O botão roda apenas o agente daquela seção sem afetar o restante.
    """
    def _render():
        nome_secao = agentes_secoes.NOMES_SECOES.get(secao_key, secao_key)

        clicked = st.form_submit_button(
            "Completar Campos",
            key=f"_fsbtn_ag_{secao_key}",
            help=f"Preenche apenas '{nome_secao}' com IA",
            use_container_width=True,
        )
        if clicked:
            st.session_state["_agente_pendente"] = secao_key
    return _render


def render_formulario_completo():
    # Aplica resultados de agentes pendentes ANTES de instanciar qualquer widget
    if "_agent_staging" in st.session_state:
        staging = st.session_state.pop("_agent_staging")
        for k, v in staging.items():
            st.session_state[k] = v

    # Corrige campos de radio que receberam "" em vez de None
    _sanitizar_radios()
    # Reformata campos de data digitados sem barras (ex.: 10022026 → 10/02/2026)
    _normalizar_datas()

    # --- CSS: ESTILO DISCRETO PARA EXPANDERS E DESTAQUE VERDE PARA CONDUTAS ---
    st.markdown("""
    <style>
        /* ================= EXPANDERS DISCRETOS ================= */
        [data-testid="stExpander"] { 
            border: none !important; 
            box-shadow: none !important; 
            background: transparent !important;
        }
        
        [data-testid="stExpander"] details {
            border-radius: 4px !important;
            border: 1px solid #f0f0f0 !important;
            background-color: #fafafa;
            box-shadow: none;
            margin-bottom: 8px !important; 
        }

        /* Texto do Título - Menor e mais discreto */
        [data-testid="stExpander"] details summary p {
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            margin: 0 !important;
            color: #666 !important;
        }
        
        /* Base da Barra de Título - Mais compacta */
        [data-testid="stExpander"] details summary {
            background-color: transparent !important;
            padding: 0.6rem 0.8rem !important;
            transition: all 0.15s ease;
            border-left: 3px solid #e8e8e8; 
            min-height: auto !important;
        }
        
        /* Hover sutil */
        [data-testid="stExpander"] details:hover summary {
            background-color: #f5f5f5 !important;
        }
        
        /* ================= DESTAQUE VERDE PARA CONDUTAS ================= */
        /* Apenas marca verde discreta na borda esquerda — resto igual aos demais campos */
        div[data-testid="stTextInput"]:has(input[placeholder="Escreva a conduta aqui..."]) {
            border-left: 3px solid #43a047;
            padding-left: 8px;
        }
        
        /* ================= CHECKBOX LABELS SEM QUEBRA ================= */
        /* Evita que "Manhã" e outros labels quebrem em múltiplas linhas */
        div[data-testid="stCheckbox"] label {
            white-space: nowrap !important;
        }
        
        /* ================= EFEITO ZEBRADO NOS TÍTULOS DAS SEÇÕES ================= */
        /* Títulos h5 das seções - efeito alternado com barra lateral */
        
        /* Seções ímpares (1, 3, 5, 7, 9, 11, 13): Amarelo/Âmbar discreto */
        h5:nth-of-type(odd) {
            background: linear-gradient(90deg, #FFF8E1 0%, #FFFFFF 100%) !important;
            padding: 0.6rem 1rem !important;
            border-left: 4px solid #FFA726 !important;
            border-radius: 4px !important;
            margin-bottom: 1rem !important;
        }
        
        /* Seções pares (2, 4, 6, 8, 10, 12): Verde discreto */
        h5:nth-of-type(even) {
            background: linear-gradient(90deg, #E8F5E9 0%, #FFFFFF 100%) !important;
            padding: 0.6rem 1rem !important;
            border-left: 4px solid #4CAF50 !important;
            border-radius: 4px !important;
            margin-bottom: 1rem !important;
        }

    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # 1. DADOS DO PACIENTE
    # ==========================================
    with st.expander("Dados do Paciente", expanded=False):
        identificacao.render(_agent_btn_callback=_btn_agente("identificacao"))
        st.write("")
        hd.render(_agent_btn_callback=_btn_agente("hd"))
        st.write("")
        comorbidades.render(_agent_btn_callback=_btn_agente("comorbidades"))
        st.write("")
        muc.render(_agent_btn_callback=_btn_agente("muc"))
        st.write("")
        hmpa.render(_agent_btn_callback=_btn_agente("hmpa"))
        st.write("")

    st.write("") # Espaço visual

    # ==========================================
    # 2. DADOS CLÍNICOS
    # ==========================================
    with st.expander("Evolução Horizontal", expanded=False):
        dispositivos.render(_agent_btn_callback=_btn_agente("dispositivos"))
        st.write("")
        culturas.render(_agent_btn_callback=_btn_agente("culturas"))
        st.write("")
        antibioticos.render(_agent_btn_callback=_btn_agente("antibioticos"))
        st.write("")
        complementares.render(_agent_btn_callback=_btn_agente("complementares"))
        st.write("")

    st.write("") # Espaço visual

    # ==========================================
    # 3. EVOLUÇÃO DIÁRIA
    # ==========================================
    with st.expander("Evolução Diária", expanded=True):
        laboratoriais.render(_agent_btn_callback=_btn_agente("laboratoriais"))
        st.write("")
        controles.render(_agent_btn_callback=_btn_agente("controles"))
        st.write("")
        evolucao_clinica.render()
        st.write("")
        sistemas.render(_agent_btn_callback=_btn_agente("sistemas"))
        st.write("")
        prescricao.render()
        st.write("")
        condutas.render()
