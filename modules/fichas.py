import re
import streamlit as st
from modules import ui

# ---------------------------------------------------------------------------
# Formatação automática de datas
# ---------------------------------------------------------------------------
_PAT_CHAVE_DATA = re.compile(
    r"(_data|_ultima|_proxima|_ini$|_fim$|di_hosp$|di_uti$|di_enf$)",
    re.IGNORECASE,
)

_PAT_CHAVE_HORA = re.compile(r"_dt$", re.IGNORECASE)


def _fmt_hora(val: str) -> str:
    """
    Formata campo de hora para os campos _dt (ex: lactato).
    - "18"        → "18h"
    - "04/03 18"  → "04/03 18h"
    - "18h"       → sem alteração
    """
    if not isinstance(val, str):
        return val
    stripped = val.strip()
    if not stripped or stripped.endswith("h"):
        return val
    # Apenas dígitos (ex: "18") → hora pura
    if re.fullmatch(r"\d{1,2}", stripped):
        return f"{stripped}h"
    # Data + espaço + dígitos no final (ex: "04/03 18")
    m = re.match(r"^(.+\s)(\d{1,2})$", stripped)
    if m:
        return f"{m.group(1)}{m.group(2)}h"
    return val


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
    if n == 6:
        # DD/MM/AA → DD/MM/20AA (ex: 040326 → 04/03/2026)
        return f"{digitos[0:2]}/{digitos[2:4]}/20{digitos[4:6]}"
    if n <= 8:
        return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"
    # Mais de 8 dígitos: formata só os 8 primeiros
    return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"


def _normalizar_datas():
    """
    Reformata automaticamente apenas as chaves conhecidas de data/_dt.
    Usa sets pré-computados — não faz regex sobre todo o session_state a cada render.
    """
    data_keys, hora_keys = _get_campos_data_hora_cached()
    ss = st.session_state
    for k in data_keys:
        v = ss.get(k)
        if isinstance(v, str) and v:
            novo = _fmt_data(v)
            if novo != v:
                ss[k] = novo
    for k in hora_keys:
        v = ss.get(k)
        if isinstance(v, str) and v:
            novo = _fmt_hora(v)
            if novo != v:
                ss[k] = novo

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
        'texto_bruto_original': '',  # Bloco 1: texto colado antes do processamento
        'texto_final_gerado': '',    # Bloco 3: prontuário gerado pelo modelo
        # campos _notas preenchidos pelo ia_extrator
        'identificacao_notas': '', 'hd_notas': '', 'comorbidades_notas': '',
        'muc_notas': '', 'hmpa_texto': '', 'dispositivos_notas': '',
        'culturas_notas': '', 'antibioticos_notas': '', 'complementares_notas': '',
        'laboratoriais_notas': '', 'controles_notas': '', 'evolucao_notas': '',
        'sistemas_notas': '',
    })
    return campos


# ===========================================================================
# CACHES DE MÓDULO — calculados uma única vez por processo, não por render
# ===========================================================================
_CAMPOS_BASE_CACHE: dict | None = None
_CAMPOS_KEYS_CACHE: list | None = None
_CAMPOS_NONE_CACHE: set | None = None   # chaves cujo default é None (radio/pills)
_CAMPOS_DATA_CACHE: frozenset | None = None   # chaves de data
_CAMPOS_HORA_CACHE: frozenset | None = None   # chaves de hora (_dt)


def _get_campos_base_cached() -> dict:
    global _CAMPOS_BASE_CACHE
    if _CAMPOS_BASE_CACHE is None:
        _CAMPOS_BASE_CACHE = _campos_base()
    return _CAMPOS_BASE_CACHE


def _get_campos_keys_cached() -> list:
    global _CAMPOS_KEYS_CACHE
    if _CAMPOS_KEYS_CACHE is None:
        _CAMPOS_KEYS_CACHE = list(_get_campos_base_cached().keys())
    return _CAMPOS_KEYS_CACHE


def _get_campos_none_cached() -> set:
    """Retorna set de chaves cujo valor padrão é None (radios/pills)."""
    global _CAMPOS_NONE_CACHE
    if _CAMPOS_NONE_CACHE is None:
        _CAMPOS_NONE_CACHE = {k for k, v in _get_campos_base_cached().items() if v is None}
    return _CAMPOS_NONE_CACHE


def _get_campos_data_hora_cached() -> tuple[frozenset, frozenset]:
    """Retorna (data_keys, hora_keys) precomputados a partir dos campos conhecidos."""
    global _CAMPOS_DATA_CACHE, _CAMPOS_HORA_CACHE
    if _CAMPOS_DATA_CACHE is None:
        campos = _get_campos_base_cached()
        _CAMPOS_DATA_CACHE = frozenset(k for k in campos if _PAT_CHAVE_DATA.search(k))
        _CAMPOS_HORA_CACHE = frozenset(k for k in campos if _PAT_CHAVE_HORA.search(k))
    return _CAMPOS_DATA_CACHE, _CAMPOS_HORA_CACHE


def get_todos_campos_keys() -> list:
    """
    Retorna a lista de chaves de todos os campos do formulário.
    Usada para salvar/carregar dados no Google Sheets.
    """
    return _get_campos_keys_cached()


def inicializar_estado():
    """Garante que todos os campos estão no session_state com seu valor padrão."""
    defaults = _get_campos_base_cached()
    ss = st.session_state
    for k, v in defaults.items():
        if k not in ss:
            ss[k] = v


def _sanitizar_radios():
    """
    Corrige campos de radio/pills com default None que receberam '' (string vazia)
    vinda de agentes de IA ou do carregamento do Google Sheets.
    Usa set pré-computado — não itera o dict completo.
    """
    ss = st.session_state
    for k in _get_campos_none_cached():
        if ss.get(k) == "":
            ss[k] = None

def _btn_gerar_bloco(secao_key: str):
    """Renderiza o botão 'Gerar Bloco' para uma seção específica (dentro de um form)."""
    from modules import agentes_secoes
    nome = agentes_secoes.NOMES_SECOES.get(secao_key, secao_key.capitalize())
    if st.form_submit_button(
        f"✨ Gerar Bloco {nome}",
        key=f"_fsbtn_gerar_{secao_key}",
        help="Gera o texto desta seção e abre para visualização/edição",
        use_container_width=True,
        type="primary",
    ):
        st.session_state["_gerar_bloco_pendente"] = secao_key


def _btn_agente(secao_key: str):
    """
    Retorna uma função que, quando chamada, renderiza o botão
    'Completar Campos' para a seção indicada.
    O botão roda apenas o agente daquela seção sem afetar o restante.
    """
    def _render():
        from modules import agentes_secoes
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


_CSS_FORMULARIO = """<style>
    [data-testid="stExpander"] { border: none !important; box-shadow: none !important; background: transparent !important; }
    [data-testid="stExpander"] details { border-radius: 4px !important; border: 1px solid #f0f0f0 !important; background-color: #fafafa; box-shadow: none; margin-bottom: 8px !important; }
    [data-testid="stExpander"] details summary p { font-size: 0.95rem !important; font-weight: 500 !important; margin: 0 !important; color: #666 !important; }
    [data-testid="stExpander"] details summary { background-color: transparent !important; padding: 0.6rem 0.8rem !important; transition: background-color 0.12s ease, box-shadow 0.12s ease; border-left: 3px solid #e8e8e8; min-height: auto !important; }
    [data-testid="stExpander"] details[open] summary { border-left-color: #1E88E5; }
    [data-testid="stExpander"] details:hover summary { background-color: #f5f5f5 !important; }
    div[data-testid="stTextInput"]:has(input[placeholder="Escreva a conduta aqui..."]) { border-left: 3px solid #43a047; padding-left: 8px; }
    div[data-testid="stCheckbox"] label { white-space: nowrap !important; }
    hr { border: none !important; border-top: 2px solid #9ca3af !important; box-shadow: 0 4px 0 0 #9ca3af !important; margin: 1.6rem 0 1.8rem 0 !important; opacity: 1 !important; }
    h5:nth-of-type(odd) { background: linear-gradient(90deg, #FFF3CD 0%, #FFFDF5 60%, #FFFFFF 100%) !important; padding: 0.7rem 1.1rem !important; border-left: 5px solid #F59E0B !important; border-radius: 0 6px 6px 0 !important; margin-top: 0.4rem !important; margin-bottom: 1rem !important; font-size: 0.97rem !important; font-weight: 700 !important; letter-spacing: 0.01em !important; box-shadow: 0 1px 4px rgba(245,158,11,0.10) !important; }
    h5:nth-of-type(even) { background: linear-gradient(90deg, #D1FAE5 0%, #F0FDF8 60%, #FFFFFF 100%) !important; padding: 0.7rem 1.1rem !important; border-left: 5px solid #10B981 !important; border-radius: 0 6px 6px 0 !important; margin-top: 0.4rem !important; margin-bottom: 1rem !important; font-size: 0.97rem !important; font-weight: 700 !important; letter-spacing: 0.01em !important; box-shadow: 0 1px 4px rgba(16,185,129,0.10) !important; }
</style>"""


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

    st.markdown(_CSS_FORMULARIO, unsafe_allow_html=True)

    # ==========================================
    # 1. DADOS DO PACIENTE
    # ==========================================
    with st.expander("Dados do Paciente", expanded=False):
        identificacao.render(_agent_btn_callback=_btn_agente("identificacao"))
        _btn_gerar_bloco("identificacao")
        st.divider()
        hd.render(_agent_btn_callback=_btn_agente("hd"))
        _btn_gerar_bloco("hd")
        st.divider()
        comorbidades.render(_agent_btn_callback=_btn_agente("comorbidades"))
        _btn_gerar_bloco("comorbidades")
        st.divider()
        muc.render(_agent_btn_callback=_btn_agente("muc"))
        _btn_gerar_bloco("muc")
        st.divider()
        hmpa.render(_agent_btn_callback=_btn_agente("hmpa"))
        _btn_gerar_bloco("hmpa")

    st.write("")

    # ==========================================
    # 2. DADOS CLÍNICOS
    # ==========================================
    with st.expander("Evolução Horizontal", expanded=False):
        dispositivos.render(_agent_btn_callback=_btn_agente("dispositivos"))
        _btn_gerar_bloco("dispositivos")
        st.divider()
        culturas.render(_agent_btn_callback=_btn_agente("culturas"))
        _btn_gerar_bloco("culturas")
        st.divider()
        antibioticos.render(_agent_btn_callback=_btn_agente("antibioticos"))
        _btn_gerar_bloco("antibioticos")
        st.divider()
        complementares.render(_agent_btn_callback=_btn_agente("complementares"))
        _btn_gerar_bloco("complementares")

    st.write("")

    # ==========================================
    # 3. EVOLUÇÃO DIÁRIA
    # ==========================================
    with st.expander("Evolução Diária", expanded=True):
        # ── Botão global: Evolução Hoje para todos os blocos diários ──────────
        if st.form_submit_button(
            "📅 Evolução Diária",
            key="_fsbtn_evo_hoje_global",
            use_container_width=True,
            help="Desloca os slots de Laboratoriais, Controles e Sistemas (hoje→ontem→anteontem) e executa o Parsing dos três blocos.",
        ):
            laboratoriais._deslocar_laboratoriais()
            controles._deslocar_dias()
            sistemas._deslocar_sistemas()
            st.session_state["_lab_deterministico_pendente"]      = True
            st.session_state["_ctrl_deterministico_pendente"]     = True
            st.session_state["_sistemas_deterministico_pendente"] = True
            st.toast("✅ Evolução Hoje aplicada em Labs, Controles e Sistemas — Parsing em andamento.", icon="📅")

        st.divider()
        laboratoriais.render(_agent_btn_callback=_btn_agente("laboratoriais"))
        _btn_gerar_bloco("laboratoriais")
        st.divider()
        controles.render(_agent_btn_callback=_btn_agente("controles"))
        _btn_gerar_bloco("controles")
        st.divider()
        evolucao_clinica.render()
        _btn_gerar_bloco("evolucao")
        st.divider()
        sistemas.render(_agent_btn_callback=_btn_agente("sistemas"))
        _btn_gerar_bloco("sistemas")
        st.divider()
        prescricao.render()
        _btn_gerar_bloco("prescricao")
        st.divider()
        condutas.render()
        _btn_gerar_bloco("condutas")


def migrar_schema_legado(dados: dict) -> dict:
    """Migra prontuários com schema antigo (hd_atual_*/hd_prev_*) para o schema atual (hd_*).

    Seguro chamar sempre: retorna o dict intacto se não há campos legados.
    """
    if "hd_atual_1_nome" not in dados:
        return dados
    for i in range(1, 5):
        dados[f"hd_{i}_nome"]           = dados.get(f"hd_atual_{i}_nome", "")
        dados[f"hd_{i}_class"]          = dados.get(f"hd_atual_{i}_class", "")
        dados[f"hd_{i}_data_inicio"]    = dados.get(f"hd_atual_{i}_data", "")
        dados[f"hd_{i}_data_resolvido"] = ""
        dados[f"hd_{i}_status"]         = "Atual"
        dados[f"hd_{i}_obs"]            = dados.get(f"hd_atual_{i}_obs", "")
        dados[f"hd_{i}_conduta"]        = dados.get(f"hd_atual_{i}_conduta", "")
    for i in range(1, 5):
        j = i + 4
        dados[f"hd_{j}_nome"]           = dados.get(f"hd_prev_{i}_nome", "")
        dados[f"hd_{j}_class"]          = dados.get(f"hd_prev_{i}_class", "")
        dados[f"hd_{j}_data_inicio"]    = dados.get(f"hd_prev_{i}_data_ini", "")
        dados[f"hd_{j}_data_resolvido"] = dados.get(f"hd_prev_{i}_data_fim", "")
        dados[f"hd_{j}_status"]         = "Resolvida"
        dados[f"hd_{j}_obs"]            = dados.get(f"hd_prev_{i}_obs", "")
        dados[f"hd_{j}_conduta"]        = dados.get(f"hd_prev_{i}_conduta", "")
    dados["hd_ordem"] = list(range(1, 9))
    return dados
