import streamlit as st
import json
import time
import threading
import streamlit.components.v1 as components
from pathlib import Path
from modules import ui, fichas, gerador, fluxo, agentes_secoes
from modules.secoes.condutas import render_condutas_registradas as _render_condutas_reg
from utils import save_evolucao, load_evolucao, mostrar_rodape, carregar_chave_api, verificar_rate_limit, uso_rate_limit

# ── Chaves de API (secrets.toml → .env → vazio) ───────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass

OPENAI_API_KEY = carregar_chave_api("OPENAI_API_KEY", "OPENAI_API_KEY")
GOOGLE_API_KEY = carregar_chave_api("GOOGLE_API_KEY", "GOOGLE_API_KEY")

# ── Setup ──────────────────────────────────────────────────────────────────────
ui.carregar_css()
fichas.inicializar_estado()

# ── Validação de chaves de API (cache de 10 min — evita chamada a cada rerun) ──

@st.cache_data(ttl=600, show_spinner=False)
def _testar_openai(key: str) -> tuple[bool, str]:
    if not key or len(key) < 10:
        return False, "Chave não configurada"
    try:
        from openai import OpenAI
        OpenAI(api_key=key).models.list()
        return True, ""
    except Exception as e:
        msg = str(e)
        if "401" in msg or "Incorrect API key" in msg:
            return False, "Chave inválida (401)"
        if "429" in msg or "quota" in msg.lower() or "billing" in msg.lower():
            return False, "Créditos esgotados (429)"
        return False, msg[:60]

@st.cache_data(ttl=600, show_spinner=False)
def _testar_google(key: str) -> tuple[bool, str]:
    if not key or len(key) < 10:
        return False, "Chave não configurada"
    try:
        from google import genai as _g
        _g.Client(api_key=key).models.list()
        return True, ""
    except Exception as e:
        msg = str(e)
        if "401" in msg or "403" in msg or "API_KEY_INVALID" in msg:
            return False, "Chave inválida"
        if "429" in msg or "quota" in msg.lower():
            return False, "Cota esgotada (429)"
        return False, msg[:60]

# ── Sidebar: status das chaves de API ─────────────────────────────────────────
with st.sidebar:
    with st.popover("​", use_container_width=True):
        _ok_google, _err_google = _testar_google(GOOGLE_API_KEY)
        if _ok_google:
            st.success(f"✅ Google: ...{GOOGLE_API_KEY[-8:]}")
        else:
            st.error(f"❌ Google: {_err_google}")

        _ok_openai, _err_openai = _testar_openai(OPENAI_API_KEY)
        if _ok_openai:
            st.success(f"✅ OpenAI: ...{OPENAI_API_KEY[-8:]}")
        else:
            st.error(f"❌ OpenAI: {_err_openai}")

# ── Título ─────────────────────────────────────────────────────────────────────
st.title("📝 Evolução Diária")
st.write("")

# ── Proteção contra perda de dados ────────────────────────────────────────────
if st.session_state.get("prontuario", "").strip():
    components.html(
        '<script>window.onbeforeunload=function(){return"Dados não salvos serão perdidos."}</script>',
        height=0,
    )


# ── Helpers de staging ─────────────────────────────────────────────────────────

def _para_staging(dados: dict) -> None:
    """Aplica dicionário ao _agent_staging (somente valores não-vazios) e faz rerun."""
    staging = st.session_state.get("_agent_staging", {})
    for k, v in dados.items():
        if v is not None and str(v).strip() != "":
            staging[k] = v
    st.session_state["_agent_staging"] = staging
    st.rerun()


# ── Busca / carregamento de prontuário ────────────────────────────────────────

def _aplicar_dados_prontuario(dados: dict, silencioso: bool = False) -> bool:
    """Aplica os dados carregados ao session_state (merge seguro).

    Regra: só sobrescreve se o DB tem valor, OU se session_state está vazio para essa chave.
    Garante que dados preenchidos no PACER e ainda não salvos não sejam apagados.
    """
    if not dados:
        return False
    data_hora = dados.pop("_data_hora", "")
    dados = fichas.migrar_schema_legado(dados)
    campos_validos = set(fichas.get_todos_campos_keys())
    for k, v in dados.items():
        if k not in campos_validos:
            continue
        if v or not st.session_state.get(k):
            st.session_state[k] = v
    st.session_state["_data_hora_carregado"] = data_hora

    # Reconstrói _secoes_recortadas se algum *_notas tiver conteúdo —
    # garante que o checklist e o botão "Completar Campos" reapareçam após reload.
    from modules import agentes_secoes as _as
    notas_com_conteudo = any(
        st.session_state.get(_as._NOTAS_MAP[sec], "").strip()
        for sec in _as._NOTAS_MAP
        if sec in _as._AGENTES
    )
    if notas_com_conteudo:
        st.session_state["_secoes_recortadas"] = {
            sec: bool(st.session_state.get(_as._NOTAS_MAP[sec], "").strip())
            for sec in _as._NOTAS_MAP
            if sec in _as._AGENTES
        }

    # Persiste prontuário na URL para sobreviver a reconexões do Streamlit Cloud
    _pront_url = st.session_state.get("prontuario", "").strip()
    if _pront_url:
        try:
            st.query_params["p"] = _pront_url
        except Exception:
            pass

    if not silencioso:
        st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")
    return True


def _on_buscar_click():
    """Callback executado ANTES do rerun — garante resposta imediata do botão."""
    busca = st.session_state.get("busca_input_field", "").strip()
    if busca:
        st.session_state["_busca_loading"] = busca


@st.fragment
def _fragment_busca():
    # Fase 2 — executa a busca com spinner visível
    if st.session_state.get("_busca_loading"):
        busca = st.session_state.pop("_busca_loading")
        with st.spinner(f"🔍 Buscando prontuário {busca}..."):
            st.session_state.pop("_db_error", None)
            dados = load_evolucao(busca)
        if dados is not None:
            _aplicar_dados_prontuario(dados)
            st.rerun()
        elif st.session_state.pop("_db_error", False):
            return
        else:
            st.session_state["_busca_pendente_criar"] = busca
            st.rerun()
        return

    with st.form(key="form_busca_paciente"):
        c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
        with c_input:
            st.text_input(
                "Número do Prontuário",
                placeholder="Ex.: 1234567",
                key="busca_input_field",
            )
        with c_btn:
            st.form_submit_button(
                "🔍 Buscar",
                use_container_width=True,
                type="primary",
                on_click=_on_buscar_click,
            )

_fragment_busca()

# ── Auto-reload: recupera dados se sessão reiniciou (ex: Streamlit Cloud restart) ──
# Condição 1: prontuário ainda no session_state mas nome sumiu (reconexão parcial)
# Condição 2: session_state zerado, mas prontuário salvo na URL (?p=XXXXX)
_pront_autoload = st.session_state.get("prontuario", "").strip()
if not _pront_autoload:
    # Fallback: tenta recuperar da URL (sobrevive a reconexões completas)
    try:
        _pront_autoload = st.query_params.get("p", "").strip()
    except Exception:
        _pront_autoload = ""
    if _pront_autoload:
        st.session_state["prontuario"] = _pront_autoload

if (_pront_autoload
        and not st.session_state.get("nome", "").strip()
        and not st.session_state.get("_autoload_feito")):
    st.session_state["_autoload_feito"] = True
    with st.spinner(f"🔍 Recarregando prontuário {_pront_autoload}..."):
        _dados_auto = load_evolucao(_pront_autoload)
    if _dados_auto and _aplicar_dados_prontuario(_dados_auto, silencioso=True):
        st.rerun()

# ── Sincronizar ?p= na URL a cada render ──────────────────────────────────────
# Garante que reconexões/reloads sempre encontrem o prontuário na URL.
_p_sync = st.session_state.get("prontuario", "").strip()
if _p_sync:
    try:
        if st.query_params.get("p", "") != _p_sync:
            st.query_params["p"] = _p_sync
    except Exception:
        pass

# ── Confirmação de criação de novo prontuário ──────────────────────────────────
if "_busca_pendente_criar" in st.session_state:
    pend = st.session_state["_busca_pendente_criar"]
    with st.container(border=True):
        st.markdown(
            f"**Prontuário {pend} não localizado.**  \n"
            "Nenhum registro encontrado para este número. "
            "Deseja iniciar um novo prontuário?",
        )
        c_sim, c_nao, *_ = st.columns([2, 2, 8])
        with c_sim:
            if st.button(
                "Criar prontuário", type="primary",
                use_container_width=True, key="_btn_criar_sim",
            ):
                st.session_state.pop("_busca_pendente_criar", None)
                st.session_state["prontuario"] = pend
                try:
                    st.query_params["p"] = str(pend).strip()
                except Exception:
                    pass
                with st.spinner("Registrando novo prontuário..."):
                    save_evolucao(pend, "", {"prontuario": pend})
                st.toast(f"Prontuário {pend} registrado com sucesso.", icon="✅")
                st.rerun()
        with c_nao:
            if st.button(
                "Cancelar", use_container_width=True, key="_btn_criar_nao",
            ):
                st.session_state.pop("_busca_pendente_criar", None)
                st.rerun()

# ── Gate: bloqueia o restante da página até um prontuário ser informado ───────
if not st.session_state.get("prontuario", "").strip():
    # Pré-importa módulos pesados em background enquanto o usuário vê a tela de cadeado.
    # Python cacheia em sys.modules — quando o prontuário for digitado, estarão prontos.
    if not st.session_state.get("_preload_started"):
        def _preload():
            try:
                from modules import ia_extrator
                from modules.ia_config import get_ia_config
            except Exception:
                pass
        threading.Thread(target=_preload, daemon=True).start()
        st.session_state["_preload_started"] = True

    st.markdown(
        '<div style="text-align:center;padding:80px 20px;color:#9e9e9e">'
        '<p style="font-size:2.5rem;margin-bottom:4px">🔒</p>'
        '<p style="font-size:1.1rem;font-weight:600;color:#666">Digite o número do prontuário para começar</p>'
        '<p style="font-size:0.85rem">Busque um prontuário existente ou crie um novo acima.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    mostrar_rodape()
    st.stop()

# ── Auto-save periódico (a cada 60 s de atividade, sem bloquear a UI) ─────────
# Roda em background thread — zero impacto no rerun do usuário.
_as_pront = st.session_state.get("prontuario", "").strip()
if _as_pront:
    _agora_as = time.time()
    if (_agora_as - st.session_state.get("_ultimo_autosave", 0)) >= 60:
        st.session_state["_ultimo_autosave"] = _agora_as
        _as_dados = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
        threading.Thread(
            target=save_evolucao,
            args=(_as_pront, st.session_state.get("nome", "").strip(), _as_dados),
            daemon=True,
        ).start()

# ── Barra de identificação do paciente ────────────────────────────────────────
ui.render_barra_paciente()


# ── Agentes em paralelo ────────────────────────────────────────────────────────

def _aplicar_agentes_paralelo(secoes: list[str]):
    """Wrapper de UI: exibe progresso e delega a orquestração para fluxo.rodar_agentes_paralelo."""
    n_tarefas = sum(
        1 for sec in secoes
        if st.session_state.get(agentes_secoes._NOTAS_MAP.get(sec, ""), "").strip()
    )
    if not n_tarefas:
        st.warning("Nenhuma seção tem texto para processar.")
        return

    with st.status(
        f"⚡ Processando {n_tarefas} {'seção' if n_tarefas == 1 else 'seções'} em paralelo...",
        expanded=False,
    ) as _status_agentes:
        progresso = st.progress(0, text="Iniciando...")
        concluidas: list[str] = []

        def _on_progress(concluidos, total, nome):
            if nome:
                concluidas.append(nome)
            pct = concluidos / total
            txt = f"✅ {nome} concluída — {concluidos}/{total}" if nome else f"{concluidos}/{total} concluídas"
            progresso.progress(pct, text=txt)

        n_ok, erros = fluxo.rodar_agentes_paralelo(
            secoes, GOOGLE_API_KEY, OPENAI_API_KEY,
            on_progress=_on_progress,
        )

        progresso.empty()

        if erros:
            _status_agentes.update(
                label=f"⚠️ {n_ok} seções preenchidas — {len(erros)} com erro",
                state="error",
                expanded=True,
            )
            for e in erros:
                st.warning(e)
        else:
            _status_agentes.update(
                label=f"✅ {n_ok} {'seção preenchida' if n_ok == 1 else 'seções preenchidas'} com IA",
                state="complete",
                expanded=False,
            )

    st.rerun()


# ==============================================================================
# BLOCO 1: PRONTUÁRIO — recortador + checklist + agentes
# ==============================================================================
ui.render_header_secao("1. Prontuário", "📄", ui.COLOR_BLUE)

with st.container(border=True):
    _data_carg    = st.session_state.get("_data_hora_carregado", "")
    _tem_texto_ant = bool(st.session_state.get("texto_bruto_original", "").strip())
    if _data_carg and _tem_texto_ant:
        st.info(
            f"Prontuário carregado — última evolução registrada em **{_data_carg}**.  \n"
            "O texto abaixo corresponde ao último input processado. "
            "Substitua pelo texto da nova evolução ou clique em **Extrair Seções** para reprocessar.",
        )
    elif _data_carg and not _tem_texto_ant:
        st.info(
            f"Prontuário carregado — última evolução registrada em **{_data_carg}**.  \n"
            "Cole o texto da nova evolução abaixo para iniciar a extração.",
        )

    texto_input = st.text_area(
        "Input", height=150,
        label_visibility="collapsed",
        placeholder="Cole a evolução aqui...",
        key="texto_bruto_original",
    )
    st.write("")
    extrair_btn = st.button("✨ Extrair Seções", type="primary", use_container_width=True)

    if extrair_btn:
        if not GOOGLE_API_KEY and not OPENAI_API_KEY:
            st.error("Sem chave API.")
        elif not texto_input:
            st.warning("Cole o texto do prontuário primeiro.")
        else:
            _ok, _msg = verificar_rate_limit()
            if not _ok:
                st.error(f"🚫 {_msg}")
            else:
                with st.spinner("Extraindo seções com IA..."):
                    from modules.ia_config import get_ia_config
                    from modules import ia_extrator
                    _ext_key, _ext_prov, _ext_mod = get_ia_config("ia_extrator", GOOGLE_API_KEY, OPENAI_API_KEY)
                    dados_notas = ia_extrator.extrair_dados_prontuario(
                        texto_bruto=texto_input,
                        api_key=_ext_key,
                        provider=_ext_prov,
                        modelo=_ext_mod,
                    )
                    fluxo.atualizar_notas_ia(dados_notas)
                    # Auto-save: persiste o texto original + notas fatiadas no banco
                    _pront_fat = st.session_state.get("prontuario", "").strip()
                    if _pront_fat:
                        _dados_fat = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
                        save_evolucao(_pront_fat, st.session_state.get("nome", "").strip(), _dados_fat)
                st.toast("Seções extraídas e salvas com sucesso.", icon="✅")
                st.session_state["_secoes_recortadas"] = {
                    sec: bool(st.session_state.get(agentes_secoes._NOTAS_MAP[sec], "").strip())
                    for sec in agentes_secoes._NOTAS_MAP
                    if sec in agentes_secoes._AGENTES
                }

# ── Checklist dinâmico + botão de agentes ─────────────────────────────────────
# Só exibe o checklist se já foi feita ao menos uma extração (_secoes_recortadas
# inicializado). A cada render, recalcula ao vivo para refletir o estado atual
# das notas — evita a mensagem "Processando N seções" ficar desatualizada.
if "_secoes_recortadas" in st.session_state:
    st.session_state["_secoes_recortadas"] = {
        sec: bool(st.session_state.get(agentes_secoes._NOTAS_MAP[sec], "").strip())
        for sec in agentes_secoes._NOTAS_MAP
        if sec in agentes_secoes._AGENTES
    }
    _status    = st.session_state["_secoes_recortadas"]
    _com_texto = sum(_status.values())

    with st.container(border=True):
        st.markdown("**Seções Preenchidas**")
        st.write("")
        _items = list(_status.items())
        _cols  = st.columns(4)
        for _i, (_sec, _tem) in enumerate(_items):
            _nome = agentes_secoes.NOMES_SECOES.get(_sec, _sec)
            with _cols[_i % 4]:
                st.write(("✅" if _tem else "⬜") + f" {_nome}")
        st.write("")
        _ci, _cb = st.columns([3, 4])
        with _ci:
            st.caption(f"**{_com_texto}** de {len(_status)} seções com conteúdo")
        with _cb:
            if st.button(
                f"Completar Todos os Campos  ({_com_texto})",
                type="primary",
                use_container_width=True,
                disabled=(_com_texto == 0),
                key="btn_aplicar_agentes",
            ):
                if not GOOGLE_API_KEY and not OPENAI_API_KEY:
                    st.error("Sem chave API.")
                else:
                    _aplicar_agentes_paralelo(list(agentes_secoes._AGENTES.keys()))

# ==============================================================================
# BLOCO 2: DADOS CLÍNICOS
# ==============================================================================
ui.render_header_secao("2. Dados Clínicos", "✍️", "#f59e0b")
ui.render_guia_navegacao()

_inc_defaults = {k: v for k, v in fichas._get_campos_base_cached().items() if k.startswith("inc_")}
for _k, _v in _inc_defaults.items():
    if st.session_state.get(_k) is False and _v is True:
        if _k in st.session_state:
            del st.session_state[_k]
        st.session_state[_k] = True

with st.form("form_dados_clinicos"):
    fichas.render_formulario_completo()

_render_condutas_reg()
st.write("")

# ==============================================================================
# DIALOGS (definidos antes dos handlers que os chamam)
# ==============================================================================

@st.dialog("🔍 Comparar Seção", width="large")
def _modal_gerar_bloco():
    from modules import agentes_secoes as _as
    key     = st.session_state.get("_bloco_secao_key", "")
    nome    = _as.NOMES_SECOES.get(key, key.capitalize())
    notas_field = _as._NOTAS_MAP.get(key, "")
    original = st.session_state.get(notas_field, "").strip() if notas_field else ""
    gerado   = st.session_state.get("_bloco_secao_texto", "").strip()

    if not gerado:
        st.warning("Nenhum texto gerado para esta seção.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**📄 Notas — {nome}** *(colado)*")
        st.text_area(
            "orig_bloco", value=original or "(sem notas)",
            height=520, label_visibility="collapsed", disabled=True,
            key="_cmp_bloco_original",
        )
    with c2:
        st.markdown(f"**✅ Bloco {nome}** *(gerado — editável)*")
        editado = st.text_area(
            "gen_bloco", value=gerado or "",
            height=520, label_visibility="collapsed",
            key="_cmp_bloco_gerado",
            placeholder="(vazio)",
        )
        if editado != gerado:
            st.session_state["_bloco_secao_texto"] = editado


@st.dialog("Comparativo — Exames & Balanço Hídrico", width="large")
def _modal_comparar_labs():
    aba_lab, aba_ctrl = st.tabs(["🧪 Exames Laboratoriais", "💧 Controles & Balanço Hídrico"])
    with aba_lab:
        html_lab = gerador.gerar_html_labs()
        if html_lab:
            st.markdown(html_lab, unsafe_allow_html=True)
        else:
            st.info("Nenhum dado laboratorial preenchido.")
    with aba_ctrl:
        html_ctrl = gerador.gerar_html_controles()
        if html_ctrl:
            st.markdown(html_ctrl, unsafe_allow_html=True)
        else:
            st.info("Nenhum dado de controles preenchido.")


@st.dialog("🗑️ Confirmar limpeza", width="small")
def _modal_limpar_tudo():
    st.warning("Isso limpará os dados **não salvos** do formulário. Tem certeza?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sim, limpar tudo", type="primary", use_container_width=True):
            fluxo.limpar_tudo()
            st.session_state.pop("_limpar_confirmar_pendente", None)
            st.rerun()
    with col2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop("_limpar_confirmar_pendente", None)
            st.rerun()


@st.dialog("🔍 Comparar Prontuário", width="large")
def _modal_comparar():
    original = st.session_state.get("texto_bruto_original", "").strip()
    gerado   = st.session_state.get("texto_final_gerado", "").strip()

    if not original and not gerado:
        st.warning("Nenhum texto disponível para comparação.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📄 Prontuário Original** *(colado)*")
        st.text_area(
            "orig", value=original or "(vazio)",
            height=520, label_visibility="collapsed", disabled=True,
            key="_cmp_original",
        )
    with c2:
        st.markdown("**✅ Prontuário Completo** *(gerado — editável)*")
        editado = st.text_area(
            "gen", value=gerado or "",
            height=520, label_visibility="collapsed",
            key="_cmp_gerado",
            placeholder="(vazio — clique em Prontuário Completo primeiro)",
        )
        if editado != gerado:
            st.session_state["texto_final_gerado"] = editado


# ==============================================================================
# HANDLERS DE FLAGS (processados fora do form, após render)
# ==============================================================================

# ── Gerar Bloco individual ─────────────────────────────────────────────────────
_gerar_bloco_pendente = st.session_state.pop("_gerar_bloco_pendente", None)
if _gerar_bloco_pendente:
    st.session_state["_bloco_secao_key"]   = _gerar_bloco_pendente
    st.session_state["_bloco_secao_texto"] = gerador.gerar_secao(_gerar_bloco_pendente)
    _modal_gerar_bloco()

# ── Agente individual ──────────────────────────────────────────────────────────
_agente_pendente = st.session_state.pop("_agente_pendente", None)
if _agente_pendente:
    if not GOOGLE_API_KEY and not OPENAI_API_KEY:
        st.warning("⚠️ Configure as chaves de API para usar o Completar Campos.")
    else:
        _aplicar_agentes_paralelo([_agente_pendente])

# ── Handler: Gerar Prontuário (flag vinda do form_submit_button) ──────────────
if st.session_state.pop("_gerar_pront_pendente", False):
    _pront_gerar = st.session_state.get("prontuario", "").strip()
    if _pront_gerar:
        _dados_gerar = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
        threading.Thread(
            target=save_evolucao,
            args=(_pront_gerar, st.session_state.get("nome", "").strip(), _dados_gerar),
            daemon=True,
        ).start()
    st.session_state["texto_final_gerado"] = gerador.gerar_texto_final()

# ── Handler: Salvar via form ─────────────────────────────────────────────────
if st.session_state.pop("_salvar_form_pendente", False):
    _pront_sf = st.session_state.get("prontuario", "").strip()
    if _pront_sf:
        _dados_sf = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
        with st.spinner("💾 Salvando evolução..."):
            _ok_sf = save_evolucao(_pront_sf, st.session_state.get("nome", "").strip(), _dados_sf)
        if _ok_sf:
            st.toast(f"✅ Evolução salva! Prontuário: {_pront_sf}", icon="💾")

# ==============================================================================
# BLOCO 3: PRONTUÁRIO COMPLETO
# ==============================================================================
ui.render_header_secao("3. Prontuário Completo", "✅", ui.COLOR_GREEN)

_texto_gerado = st.session_state.get("texto_final_gerado", "")
with st.container(border=True):
    _editado = st.text_area(
        "Prontuário Gerado", value=_texto_gerado, height=250,
        label_visibility="collapsed",
        placeholder="Clique em Prontuário Completo para gerar o texto.",
    )
    if _editado != _texto_gerado:
        st.session_state["texto_final_gerado"] = _editado

_c_copy_esp, _c_copy_btn = st.columns([4, 1])
with _c_copy_btn:
    if st.button("📋 Copiar Texto", use_container_width=True,
                 help="Copia o prontuário completo para a área de transferência"):
        texto = st.session_state.get("texto_final_gerado", "")
        if texto:
            components.html(
                f"""<script>
                const text = {json.dumps(texto)};
                navigator.clipboard.writeText(text).then(() => {{}});
                </script>""",
                height=0,
            )
            st.toast("✅ Prontuário completo copiado para a área de transferência!", icon="📋")
        else:
            st.warning("Gere o prontuário primeiro (clique em **Prontuário Completo**).")

# ==============================================================================
# RODAPÉ
# ==============================================================================
st.markdown("---")
col_comparar, col_salvar, col_limpar = st.columns([2, 3, 1])

with col_comparar:
    tem_conteudo = bool(
        st.session_state.get("texto_bruto_original", "").strip()
        or st.session_state.get("texto_final_gerado", "").strip()
    )
    if st.button(
        "🔍 Comparar Prontuário",
        use_container_width=True,
        disabled=not tem_conteudo,
        help="Abre o prontuário original e o gerado lado a lado para comparação",
    ):
        _modal_comparar()

with col_salvar:
    if st.button("💾 Salvar no Prontuário", type="primary", use_container_width=True):
        prontuario = st.session_state.get("prontuario", "").strip()
        if not prontuario:
            st.error("❌ Preencha o número do prontuário antes de salvar.")
        else:
            dados = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
            with st.spinner("💾 Salvando evolução..."):
                ok = save_evolucao(prontuario, st.session_state.get("nome", "").strip(), dados)
            if ok:
                st.success(f"✅ Evolução salva com sucesso! Prontuário: {prontuario}")

with col_limpar:
    if st.button("🗑️ Limpar Tudo", use_container_width=True, help="Limpa todos os dados do formulário"):
        st.session_state["_limpar_confirmar_pendente"] = True
    if st.session_state.get("_limpar_confirmar_pendente"):
        _modal_limpar_tudo()

mostrar_rodape()
