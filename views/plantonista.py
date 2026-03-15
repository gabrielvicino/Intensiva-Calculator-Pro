import streamlit as st
import json
import time
import threading
import streamlit.components.v1 as components
from pathlib import Path
from modules import ui, fichas, gerador, fluxo, agentes_secoes
from utils import save_evolucao, load_evolucao, mostrar_rodape, carregar_chave_api, verificar_rate_limit

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass

OPENAI_API_KEY = carregar_chave_api("OPENAI_API_KEY", "OPENAI_API_KEY")
GOOGLE_API_KEY = carregar_chave_api("GOOGLE_API_KEY", "GOOGLE_API_KEY")

ui.carregar_css()
fichas.inicializar_estado()

# Seções que o plantonista preenche via IA (extração + agentes)
_SECOES_PLANTONISTA = ["identificacao", "hd", "comorbidades", "dispositivos"]

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

st.title("📝 Evolução Plantonista")
st.caption("Versão simplificada — preencha apenas o essencial.")
st.write("")

# ── Proteção contra perda de dados ────────────────────────────────────────────
if st.session_state.get("prontuario", "").strip():
    components.html(
        '<script>window.onbeforeunload=function(){return"Dados não salvos serão perdidos."}</script>',
        height=0,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _para_staging(dados: dict) -> None:
    staging = st.session_state.get("_agent_staging", {})
    for k, v in dados.items():
        if v is not None and str(v).strip() != "":
            staging[k] = v
    st.session_state["_agent_staging"] = staging
    st.rerun()


def _aplicar_dados_prontuario(dados: dict, silencioso: bool = False) -> bool:
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

    _pront_url = st.session_state.get("prontuario", "").strip()
    if _pront_url:
        try:
            st.query_params["p"] = _pront_url
        except Exception:
            pass

    if not silencioso:
        st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")
    return True


# ── Busca de prontuário ──────────────────────────────────────────────────────

def _on_buscar_click():
    busca = st.session_state.get("busca_input_field_plan", "").strip()
    if busca:
        st.session_state["_busca_loading_plan"] = busca


@st.fragment
def _fragment_busca():
    if st.session_state.get("_busca_loading_plan"):
        busca = st.session_state.pop("_busca_loading_plan")
        with st.spinner(f"🔍 Buscando prontuário {busca}..."):
            st.session_state.pop("_db_error", None)
            dados = load_evolucao(busca)
        if dados is not None:
            _aplicar_dados_prontuario(dados)
            st.rerun()
        elif st.session_state.pop("_db_error", False):
            return
        else:
            st.session_state["_busca_pendente_criar_plan"] = busca
            st.rerun()
        return

    with st.form(key="form_busca_plantonista"):
        c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
        with c_input:
            st.text_input(
                "Número do Prontuário",
                placeholder="Ex.: 1234567",
                key="busca_input_field_plan",
            )
        with c_btn:
            st.form_submit_button(
                "🔍 Buscar",
                use_container_width=True,
                type="primary",
                on_click=_on_buscar_click,
            )

_fragment_busca()

# ── Auto-reload por URL ──────────────────────────────────────────────────────
_pront_autoload = st.session_state.get("prontuario", "").strip()
if not _pront_autoload:
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

_p_sync = st.session_state.get("prontuario", "").strip()
if _p_sync:
    try:
        if st.query_params.get("p", "") != _p_sync:
            st.query_params["p"] = _p_sync
    except Exception:
        pass

# ── Confirmação de criação de novo prontuário ────────────────────────────────
if "_busca_pendente_criar_plan" in st.session_state:
    pend = st.session_state["_busca_pendente_criar_plan"]
    with st.container(border=True):
        st.markdown(
            f"**Prontuário {pend} não localizado.**  \n"
            "Deseja iniciar um novo prontuário?",
        )
        c_sim, c_nao, *_ = st.columns([2, 2, 8])
        with c_sim:
            if st.button("Criar prontuário", type="primary", use_container_width=True, key="_btn_criar_sim_plan"):
                st.session_state.pop("_busca_pendente_criar_plan", None)
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
            if st.button("Cancelar", use_container_width=True, key="_btn_criar_nao_plan"):
                st.session_state.pop("_busca_pendente_criar_plan", None)
                st.rerun()

# ── Gate ──────────────────────────────────────────────────────────────────────
if not st.session_state.get("prontuario", "").strip():
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

# ── Auto-save periódico (60 s) ───────────────────────────────────────────────
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

ui.render_barra_paciente()


# ==============================================================================
# BLOCO 1: PRONTUÁRIO (fatiamento + agentes em um clique)
# ==============================================================================
ui.render_header_secao("1. Prontuário", "📄", ui.COLOR_BLUE)

with st.container(border=True):
    _data_carg = st.session_state.get("_data_hora_carregado", "")
    _tem_texto_ant = bool(st.session_state.get("texto_bruto_original", "").strip())
    if _data_carg and _tem_texto_ant:
        st.info(
            f"Prontuário carregado — última evolução registrada em **{_data_carg}**.  \n"
            "Substitua pelo texto da nova evolução e clique em **Extrair e Preencher**.",
        )
    elif _data_carg and not _tem_texto_ant:
        st.info(
            f"Prontuário carregado — última evolução registrada em **{_data_carg}**.  \n"
            "Cole o texto da evolução abaixo.",
        )

    texto_input = st.text_area(
        "Input", height=150,
        label_visibility="collapsed",
        placeholder="Cole a evolução aqui...",
        key="texto_bruto_original",
    )
    st.write("")
    extrair_btn = st.button(
        "⚡ Extrair e Preencher",
        type="primary",
        use_container_width=True,
        help="Extrai seções e preenche automaticamente Identificação, Diagnósticos, Comorbidades e Dispositivos.",
    )

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
                with st.status("⚡ Extraindo e preenchendo campos...", expanded=True) as _status:
                    # Fase 1: fatiamento
                    st.write("🔪 Fatiando prontuário com IA...")
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

                    _pront_fat = st.session_state.get("prontuario", "").strip()
                    if _pront_fat:
                        _dados_fat = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
                        save_evolucao(_pront_fat, st.session_state.get("nome", "").strip(), _dados_fat)

                    # Fase 2: agentes em paralelo (só seções do plantonista)
                    st.write("🤖 Preenchendo campos com IA...")
                    n_tarefas = sum(
                        1 for sec in _SECOES_PLANTONISTA
                        if st.session_state.get(agentes_secoes._NOTAS_MAP.get(sec, ""), "").strip()
                    )
                    if n_tarefas:
                        progresso = st.progress(0, text="Iniciando agentes...")
                        concluidas = []

                        def _on_progress(concluidos_n, total, nome):
                            if nome:
                                concluidas.append(nome)
                            pct = concluidos_n / total
                            txt = f"✅ {nome} — {concluidos_n}/{total}" if nome else f"{concluidos_n}/{total}"
                            progresso.progress(pct, text=txt)

                        n_ok, erros = fluxo.rodar_agentes_paralelo(
                            _SECOES_PLANTONISTA, GOOGLE_API_KEY, OPENAI_API_KEY,
                            on_progress=_on_progress,
                        )
                        progresso.empty()

                        if erros:
                            _status.update(label=f"⚠️ {n_ok} seções OK — {len(erros)} com erro", state="error")
                            for e in erros:
                                st.warning(e)
                        else:
                            _status.update(label=f"✅ Extração completa — {n_ok} seções preenchidas", state="complete")
                    else:
                        _status.update(label="✅ Fatiamento concluído (sem seções para agentes)", state="complete")

                st.rerun()


# ==============================================================================
# BLOCO 2: FORMULÁRIO SIMPLIFICADO
# ==============================================================================
ui.render_header_secao("2. Dados Clínicos", "✍️", "#f59e0b")

_inc_defaults = {k: v for k, v in fichas._get_campos_base_cached().items() if k.startswith("inc_")}
for _k, _v in _inc_defaults.items():
    if st.session_state.get(_k) is False and _v is True:
        if _k in st.session_state:
            del st.session_state[_k]
        st.session_state[_k] = True

with st.form("form_plantonista"):
    fichas.render_formulario_plantonista()


# ==============================================================================
# DIALOGS (definidos antes dos handlers que os chamam)
# ==============================================================================

@st.dialog("🔍 Comparar Seção", width="large")
def _modal_gerar_bloco():
    from modules import agentes_secoes as _as
    key = st.session_state.get("_bloco_secao_key", "")
    nome = _as.NOMES_SECOES.get(key, key.capitalize())
    notas_field = _as._NOTAS_MAP.get(key, "")
    original = st.session_state.get(notas_field, "").strip() if notas_field else ""
    gerado = st.session_state.get("_bloco_secao_texto", "").strip()
    if not gerado:
        st.warning("Nenhum texto gerado para esta seção.")
        return
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**📄 Notas — {nome}**")
        st.text_area("orig_bloco", value=original or "(sem notas)", height=520,
                      label_visibility="collapsed", disabled=True, key="_cmp_bloco_orig_plan")
    with c2:
        st.markdown(f"**✅ Bloco {nome}** *(editável)*")
        editado = st.text_area("gen_bloco", value=gerado or "", height=520,
                                label_visibility="collapsed", key="_cmp_bloco_gen_plan")
        if editado != gerado:
            st.session_state["_bloco_secao_texto"] = editado


@st.dialog("🔍 Comparar Prontuário", width="large")
def _modal_comparar():
    original = st.session_state.get("texto_bruto_original", "").strip()
    gerado = st.session_state.get("texto_final_gerado", "").strip()
    if not original and not gerado:
        st.warning("Nenhum texto disponível para comparação.")
        return
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📄 Prontuário Original**")
        st.text_area("orig", value=original or "(vazio)", height=520,
                      label_visibility="collapsed", disabled=True, key="_cmp_orig_plan")
    with c2:
        st.markdown("**✅ Prontuário Completo** *(editável)*")
        editado = st.text_area("gen", value=gerado or "", height=520,
                                label_visibility="collapsed", key="_cmp_gen_plan",
                                placeholder="(vazio)")
        if editado != gerado:
            st.session_state["texto_final_gerado"] = editado


@st.dialog("🗑️ Confirmar limpeza", width="small")
def _modal_limpar_tudo():
    st.warning("Isso limpará os dados **não salvos** do formulário. Tem certeza?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sim, limpar tudo", type="primary", use_container_width=True, key="_btn_limpar_sim_plan"):
            fluxo.limpar_tudo()
            st.session_state.pop("_limpar_confirmar_pendente", None)
            st.rerun()
    with col2:
        if st.button("Cancelar", use_container_width=True, key="_btn_limpar_nao_plan"):
            st.session_state.pop("_limpar_confirmar_pendente", None)
            st.rerun()


# ── Handlers de flags (fora do form) ─────────────────────────────────────────
_gerar_bloco_pendente = st.session_state.pop("_gerar_bloco_pendente", None)
if _gerar_bloco_pendente:
    st.session_state["_bloco_secao_key"] = _gerar_bloco_pendente
    st.session_state["_bloco_secao_texto"] = gerador.gerar_secao(_gerar_bloco_pendente)
    _modal_gerar_bloco()

_agente_pendente = st.session_state.pop("_agente_pendente", None)
if _agente_pendente:
    if not GOOGLE_API_KEY and not OPENAI_API_KEY:
        st.warning("⚠️ Configure as chaves de API para usar o Completar Campos.")
    else:
        with st.status("⚡ Processando seção...", expanded=False) as _sa:
            progresso_a = st.progress(0, text="Iniciando...")

            def _on_p(c, t, n):
                progresso_a.progress(c / t, text=f"✅ {n}" if n else f"{c}/{t}")

            n_ok_a, erros_a = fluxo.rodar_agentes_paralelo(
                [_agente_pendente], GOOGLE_API_KEY, OPENAI_API_KEY,
                on_progress=_on_p,
            )
            progresso_a.empty()
            if erros_a:
                _sa.update(label="⚠️ Erro", state="error")
                for e in erros_a:
                    st.warning(e)
            else:
                _sa.update(label="✅ Concluído", state="complete")
        st.rerun()

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
    _texto_gen = gerador.gerar_texto_final()
    if "texto_final_gerado" in st.session_state:
        del st.session_state["texto_final_gerado"]
    st.session_state["texto_final_gerado"] = _texto_gen
    st.rerun()

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

with st.container(border=True):
    st.text_area(
        "Prontuário Gerado", height=250,
        label_visibility="collapsed",
        placeholder="Clique em Gerar Prontuário Completo.",
        key="texto_final_gerado",
    )

_c_copy_esp, _c_copy_btn = st.columns([4, 1])
with _c_copy_btn:
    if st.button("📋 Copiar Texto", use_container_width=True, key="btn_copiar_plan",
                 help="Copia o prontuário para a área de transferência"):
        texto = st.session_state.get("texto_final_gerado", "")
        if texto:
            components.html(
                f"""<script>
                const text = {json.dumps(texto)};
                navigator.clipboard.writeText(text).then(() => {{}});
                </script>""",
                height=0,
            )
            st.toast("✅ Copiado!", icon="📋")
        else:
            st.warning("Gere o prontuário primeiro.")


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
    if st.button("🔍 Comparar Prontuário", use_container_width=True,
                 disabled=not tem_conteudo, key="btn_comparar_plan"):
        _modal_comparar()

with col_salvar:
    if st.button("💾 Salvar no Prontuário", type="primary", use_container_width=True, key="btn_salvar_plan"):
        prontuario = st.session_state.get("prontuario", "").strip()
        if not prontuario:
            st.error("❌ Preencha o número do prontuário antes de salvar.")
        else:
            dados = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
            with st.spinner("💾 Salvando evolução..."):
                ok = save_evolucao(prontuario, st.session_state.get("nome", "").strip(), dados)
            if ok:
                st.success(f"✅ Evolução salva! Prontuário: {prontuario}")

with col_limpar:
    if st.button("🗑️ Limpar Tudo", use_container_width=True, key="btn_limpar_plan"):
        st.session_state["_limpar_confirmar_pendente"] = True
    if st.session_state.get("_limpar_confirmar_pendente"):
        _modal_limpar_tudo()

mostrar_rodape()
