"""
pagina_evolucao_base.py — Lógica compartilhada entre Evolução Diária e Plantonista.

Cada view chama render_pagina() passando apenas o que é diferente:
  - titulo, render_formulario, secoes_agentes, extras_pos_form, page_suffix
"""
import streamlit as st
import json
import time
import threading
import streamlit.components.v1 as components
from pathlib import Path
from modules import ui, fichas, gerador, fluxo, agentes_secoes
from utils import (
    save_evolucao, load_evolucao, mostrar_rodape,
    carregar_chave_api, verificar_rate_limit,
)

# ── Chaves de API ─────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass

OPENAI_API_KEY = carregar_chave_api("OPENAI_API_KEY", "OPENAI_API_KEY")
GOOGLE_API_KEY = carregar_chave_api("GOOGLE_API_KEY", "GOOGLE_API_KEY")


# ── Validação de chaves (cache 10 min) ────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PÚBLICA — cada view chama apenas isto
# ══════════════════════════════════════════════════════════════════════════════

def render_pagina(
    *,
    titulo: str,
    render_formulario,
    secoes_agentes: list[str] | None = None,
    extras_pre_form=None,
    extras_pos_form=None,
    page_suffix: str = "",
):
    """Renderiza uma página de evolução completa.

    Args:
        titulo: texto do st.title (ex: "Evolução Diária").
        render_formulario: callable que renderiza o formulário (chamado dentro de st.form).
        secoes_agentes: lista de seções para os agentes IA (None = todas).
        extras_pre_form: callable opcional antes do form (ex: guia de navegação).
        extras_pos_form: callable opcional após o form (ex: condutas registradas).
        page_suffix: sufixo para keys de widgets, evitando conflito entre páginas.
    """
    sfx = page_suffix

    # ── Setup ─────────────────────────────────────────────────────────────────
    ui.carregar_css()
    fichas.inicializar_estado()

    _secoes_ia = secoes_agentes or list(agentes_secoes._AGENTES.keys())

    # ── Sidebar ───────────────────────────────────────────────────────────────
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

    # ── Título + proteção ─────────────────────────────────────────────────────
    st.title(f"📝 {titulo}")
    st.write("")

    if st.session_state.get("prontuario", "").strip():
        components.html(
            '<script>window.onbeforeunload=function(){return"Dados não salvos serão perdidos."}</script>',
            height=0,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _aplicar_dados_prontuario(dados: dict, silencioso: bool = False) -> bool:
        if not dados:
            return False
        data_hora = dados.pop("_data_hora", "")
        dados = fichas.migrar_schema_legado(dados)

        defaults = fichas._get_campos_base_cached()
        for k, v in defaults.items():
            st.session_state[k] = v

        campos_validos = set(fichas.get_todos_campos_keys())
        for k, v in dados.items():
            if k not in campos_validos:
                continue
            if v:
                st.session_state[k] = v
        st.session_state["_data_hora_carregado"] = data_hora

        from modules import agentes_secoes as _as
        notas_com_conteudo = any(
            st.session_state.get(_as._NOTAS_MAP[sec], "").strip()
            for sec in _as._NOTAS_MAP if sec in _as._AGENTES
        )
        if notas_com_conteudo:
            st.session_state["_secoes_recortadas"] = {
                sec: bool(st.session_state.get(_as._NOTAS_MAP[sec], "").strip())
                for sec in _as._NOTAS_MAP if sec in _as._AGENTES
            }

        _pront_url = st.session_state.get("prontuario", "").strip()
        if _pront_url:
            try:
                st.query_params["p"] = _pront_url
            except Exception:
                pass

        if not silencioso:
            st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")
        return True

    # ── Busca de prontuário ───────────────────────────────────────────────────
    _busca_field_key = f"busca_input_field{sfx}"
    _busca_loading_key = f"_busca_loading{sfx}"
    _busca_criar_key = f"_busca_pendente_criar{sfx}"

    def _on_buscar_click():
        busca = st.session_state.get(_busca_field_key, "").strip()
        if busca:
            st.session_state[_busca_loading_key] = busca

    @st.fragment
    def _fragment_busca():
        if st.session_state.get(_busca_loading_key):
            busca = st.session_state.pop(_busca_loading_key)
            with st.spinner(f"🔍 Buscando prontuário {busca}..."):
                st.session_state.pop("_db_error", None)
                dados = load_evolucao(busca)
            if dados is not None:
                _aplicar_dados_prontuario(dados)
                st.rerun()
            elif st.session_state.pop("_db_error", False):
                return
            else:
                st.session_state[_busca_criar_key] = busca
                st.rerun()
            return

        with st.form(key=f"form_busca{sfx}"):
            c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
            with c_input:
                st.text_input(
                    "Número do Prontuário",
                    placeholder="Ex.: 1234567",
                    key=_busca_field_key,
                )
            with c_btn:
                st.form_submit_button(
                    "🔍 Buscar",
                    use_container_width=True,
                    type="primary",
                    on_click=_on_buscar_click,
                )

    _fragment_busca()

    # ── Auto-reload por URL ───────────────────────────────────────────────────
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

    # ── Confirmação de novo prontuário ────────────────────────────────────────
    if _busca_criar_key in st.session_state:
        pend = st.session_state[_busca_criar_key]
        with st.container(border=True):
            st.markdown(
                f"**Prontuário {pend} não localizado.**  \n"
                "Deseja iniciar um novo prontuário?",
            )
            c_sim, c_nao, *_ = st.columns([2, 2, 8])
            with c_sim:
                if st.button("Criar prontuário", type="primary",
                             use_container_width=True, key=f"_btn_criar_sim{sfx}"):
                    st.session_state.pop(_busca_criar_key, None)
                    for _k, _v in fichas._get_campos_base_cached().items():
                        st.session_state[_k] = _v
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
                if st.button("Cancelar", use_container_width=True, key=f"_btn_criar_nao{sfx}"):
                    st.session_state.pop(_busca_criar_key, None)
                    st.rerun()

    # ── Gate ──────────────────────────────────────────────────────────────────
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

    # ── Auto-save (60 s) ─────────────────────────────────────────────────────
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

    # ── Agentes em paralelo (helper) ──────────────────────────────────────────

    def _aplicar_agentes_paralelo(secoes: list[str]):
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
        ) as _st_agentes:
            progresso = st.progress(0, text="Iniciando...")

            def _on_progress(concluidos, total, nome):
                pct = concluidos / total
                txt = f"✅ {nome} — {concluidos}/{total}" if nome else f"{concluidos}/{total}"
                progresso.progress(pct, text=txt)

            n_ok, erros = fluxo.rodar_agentes_paralelo(
                secoes, GOOGLE_API_KEY, OPENAI_API_KEY,
                on_progress=_on_progress,
            )
            progresso.empty()
            if erros:
                _st_agentes.update(label=f"⚠️ {n_ok} seções — {len(erros)} com erro",
                                   state="error", expanded=True)
                for e in erros:
                    st.warning(e)
            else:
                _st_agentes.update(
                    label=f"✅ {n_ok} {'seção preenchida' if n_ok == 1 else 'seções preenchidas'} com IA",
                    state="complete", expanded=False,
                )
        st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 1: PRONTUÁRIO (textarea + extração + agentes)
    # ══════════════════════════════════════════════════════════════════════════
    ui.render_header_secao("1. Prontuário", "📄", ui.COLOR_BLUE)

    with st.container(border=True):
        _data_carg = st.session_state.get("_data_hora_carregado", "")
        _tem_texto_ant = bool(st.session_state.get("texto_bruto_original", "").strip())
        if _data_carg and _tem_texto_ant:
            st.info(
                f"Prontuário carregado — última evolução registrada em **{_data_carg}**.  \n"
                "Substitua pelo texto da nova evolução e clique em **Extrair Seções e Completar Campos**.",
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
            "⚡ Extrair Seções e Completar Campos",
            type="primary",
            use_container_width=True,
            help="Secciona o prontuário e preenche os campos com IA.",
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
                    with st.status("⚡ Extraindo e preenchendo campos...", expanded=True) as _status_box:
                        st.write("📄 **Fase 1/2** — Seccionando prontuário com IA...")
                        from modules.ia_config import get_ia_config
                        from modules import ia_extrator
                        _ext_key, _ext_prov, _ext_mod = get_ia_config(
                            "ia_extrator", GOOGLE_API_KEY, OPENAI_API_KEY)
                        dados_notas = ia_extrator.extrair_dados_prontuario(
                            texto_bruto=texto_input,
                            api_key=_ext_key, provider=_ext_prov, modelo=_ext_mod,
                        )
                        fluxo.atualizar_notas_ia(dados_notas)

                        _pront_fat = st.session_state.get("prontuario", "").strip()
                        if _pront_fat:
                            _dados_fat = {k: st.session_state.get(k)
                                          for k in fichas.get_todos_campos_keys()}
                            save_evolucao(_pront_fat,
                                          st.session_state.get("nome", "").strip(),
                                          _dados_fat)

                        st.write("✅ Seccionamento concluído.")

                        n_tarefas = sum(
                            1 for sec in _secoes_ia
                            if st.session_state.get(
                                agentes_secoes._NOTAS_MAP.get(sec, ""), "").strip()
                        )
                        if n_tarefas:
                            st.write(f"🤖 **Fase 2/2** — Preenchendo {n_tarefas} seções com IA...")
                            progresso = st.progress(0, text="Iniciando agentes...")

                            def _on_progress(c, t, n):
                                progresso.progress(
                                    c / t,
                                    text=f"✅ {n} — {c}/{t}" if n else f"{c}/{t}",
                                )

                            n_ok, erros = fluxo.rodar_agentes_paralelo(
                                _secoes_ia, GOOGLE_API_KEY, OPENAI_API_KEY,
                                on_progress=_on_progress,
                            )
                            progresso.empty()

                            if erros:
                                _status_box.update(
                                    label=f"⚠️ {n_ok} seções OK — {len(erros)} com erro",
                                    state="error", expanded=True)
                                for e in erros:
                                    st.warning(e)
                            else:
                                _status_box.update(
                                    label=f"✅ Extração completa — {n_ok} seções preenchidas",
                                    state="complete", expanded=False)
                        else:
                            _status_box.update(
                                label="✅ Seccionamento concluído (sem seções para agentes)",
                                state="complete", expanded=False)

                    st.session_state["_secoes_recortadas"] = {
                        sec: bool(st.session_state.get(
                            agentes_secoes._NOTAS_MAP[sec], "").strip())
                        for sec in agentes_secoes._NOTAS_MAP
                        if sec in agentes_secoes._AGENTES
                    }
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 2: FORMULÁRIO
    # ══════════════════════════════════════════════════════════════════════════
    ui.render_header_secao("2. Dados Clínicos", "✍️", "#f59e0b")

    if extras_pre_form:
        extras_pre_form()

    _inc_defaults = {k: v for k, v in fichas._get_campos_base_cached().items()
                     if k.startswith("inc_")}
    for _k, _v in _inc_defaults.items():
        if st.session_state.get(_k) is False and _v is True:
            if _k in st.session_state:
                del st.session_state[_k]
            st.session_state[_k] = True

    with st.form(f"form_dados{sfx}"):
        render_formulario()

    if extras_pos_form:
        extras_pos_form()

    st.write("")

    # ══════════════════════════════════════════════════════════════════════════
    # DIALOGS
    # ══════════════════════════════════════════════════════════════════════════

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
                          label_visibility="collapsed", disabled=True,
                          key=f"_cmp_bloco_orig{sfx}")
        with c2:
            st.markdown(f"**✅ Bloco {nome}** *(editável)*")
            editado = st.text_area("gen_bloco", value=gerado or "", height=520,
                                    label_visibility="collapsed",
                                    key=f"_cmp_bloco_gen{sfx}")
            if editado != gerado:
                st.session_state["_bloco_secao_texto"] = editado

    @st.dialog("🗑️ Confirmar limpeza", width="small")
    def _modal_limpar_tudo():
        st.warning("Isso limpará os dados **não salvos** do formulário. Tem certeza?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sim, limpar tudo", type="primary",
                         use_container_width=True, key=f"_btn_limpar_sim{sfx}"):
                fluxo.limpar_tudo()
                st.session_state.pop("_limpar_confirmar_pendente", None)
                st.rerun()
        with col2:
            if st.button("Cancelar", use_container_width=True,
                         key=f"_btn_limpar_nao{sfx}"):
                st.session_state.pop("_limpar_confirmar_pendente", None)
                st.rerun()

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
                          label_visibility="collapsed", disabled=True,
                          key=f"_cmp_orig{sfx}")
        with c2:
            st.markdown("**✅ Prontuário Completo** *(editável)*")
            editado = st.text_area("gen", value=gerado or "", height=520,
                                    label_visibility="collapsed",
                                    key=f"_cmp_gen{sfx}",
                                    placeholder="(vazio)")
            if editado != gerado:
                st.session_state["texto_final_gerado"] = editado

    # ══════════════════════════════════════════════════════════════════════════
    # HANDLERS DE FLAGS
    # ══════════════════════════════════════════════════════════════════════════

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
            _aplicar_agentes_paralelo([_agente_pendente])

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

    if st.session_state.pop("_salvar_form_pendente", False):
        _pront_sf = st.session_state.get("prontuario", "").strip()
        if _pront_sf:
            _dados_sf = {k: st.session_state.get(k) for k in fichas.get_todos_campos_keys()}
            with st.spinner("💾 Salvando evolução..."):
                _ok_sf = save_evolucao(_pront_sf, st.session_state.get("nome", "").strip(), _dados_sf)
            if _ok_sf:
                st.toast(f"✅ Evolução salva! Prontuário: {_pront_sf}", icon="💾")

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 3: PRONTUÁRIO COMPLETO
    # ══════════════════════════════════════════════════════════════════════════
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
        if st.button("📋 Copiar Texto", use_container_width=True,
                     key=f"btn_copiar{sfx}",
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

    # ══════════════════════════════════════════════════════════════════════════
    # RODAPÉ
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    col_comparar, col_salvar, col_limpar = st.columns([2, 3, 1])

    with col_comparar:
        tem_conteudo = bool(
            st.session_state.get("texto_bruto_original", "").strip()
            or st.session_state.get("texto_final_gerado", "").strip()
        )
        if st.button("🔍 Comparar Prontuário", use_container_width=True,
                     disabled=not tem_conteudo, key=f"btn_comparar{sfx}"):
            _modal_comparar()

    with col_salvar:
        if st.button("💾 Salvar no Prontuário", type="primary",
                     use_container_width=True, key=f"btn_salvar{sfx}"):
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
        if st.button("🗑️ Limpar Tudo", use_container_width=True,
                     key=f"btn_limpar{sfx}"):
            st.session_state["_limpar_confirmar_pendente"] = True
        if st.session_state.get("_limpar_confirmar_pendente"):
            _modal_limpar_tudo()

    mostrar_rodape()
