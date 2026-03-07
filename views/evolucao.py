import streamlit as st
import json
import streamlit.components.v1 as components
from pathlib import Path
from datetime import date

from modules import ui, fichas, gerador, fluxo, ia_extrator, agentes_secoes, extrator_exames
from modules.ia_config import get_ia_config
from modules.parsers import parse_lab_deterministico, parse_controles_deterministico
from modules.secoes.condutas import render_condutas_registradas as _render_condutas_reg
from utils import load_data, save_evolucao, load_evolucao, mostrar_rodape, carregar_chave_api, verificar_rate_limit, uso_rate_limit

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

# ── Sidebar: status das chaves de API ─────────────────────────────────────────
with st.sidebar:
    with st.popover("​", use_container_width=True):
        if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
            st.success(f"✅ Google: ...{GOOGLE_API_KEY[-8:]}")
        else:
            st.error("❌ Google API Key não carregada!")
        if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
            st.success(f"✅ OpenAI: ...{OPENAI_API_KEY[-8:]}")
        else:
            st.error("❌ OpenAI API Key não carregada!")

# ── Título ─────────────────────────────────────────────────────────────────────
st.title("📝 Evolução Diária")
st.write("")


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

def _aplicar_dados_prontuario(dados: dict) -> bool:
    """Aplica os dados carregados ao session_state."""
    if not dados:
        return False
    data_hora = dados.pop("_data_hora", "")
    dados = fichas.migrar_schema_legado(dados)
    campos_validos = fichas.get_todos_campos_keys()
    st.session_state.update({k: v for k, v in dados.items() if k in campos_validos})
    st.session_state["_data_hora_carregado"] = data_hora
    st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")
    return True


@st.fragment
def _fragment_busca():
    with st.form(key="form_busca_paciente"):
        c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
        with c_input:
            busca_input = st.text_input(
                "Número do Prontuário",
                placeholder="Ex.: 1234567",
                key="busca_input_field",
            )
        with c_btn:
            btn_buscar = st.form_submit_button(
                "Buscar", use_container_width=True, type="primary"
            )

        busca = busca_input.strip() if busca_input else ""
        if btn_buscar:
            if not busca:
                st.warning("Informe o número do prontuário para continuar.")
            else:
                with st.spinner("Consultando banco de dados..."):
                    dados = load_evolucao(busca)
                if dados is not None:
                    _aplicar_dados_prontuario(dados)
                    st.rerun()
                else:
                    st.session_state["_busca_pendente_criar"] = busca
                    st.rerun()

_fragment_busca()

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
        f"Processando {n_tarefas} {'seção' if n_tarefas == 1 else 'seções'} com IA...",
        expanded=False,
    ) as _status_agentes:
        progresso  = st.progress(0, text="Aguardando resposta...")

        def _on_progress(concluidos, total, nome):
            pct  = int(concluidos / total * 100)
            txt  = f"{nome} — {concluidos}/{total}" if nome else f"{concluidos}/{total} concluídos"
            progresso.progress(concluidos / total, text=txt)

        n_ok, erros = fluxo.rodar_agentes_paralelo(
            secoes, GOOGLE_API_KEY, OPENAI_API_KEY,
            on_progress=_on_progress,
        )

        progresso.empty()

        if erros:
            _status_agentes.update(
                label=f"Concluído com {len(erros)} {'erro' if len(erros) == 1 else 'erros'} — {n_ok} {'seção preenchida' if n_ok == 1 else 'seções preenchidas'}",
                state="error",
                expanded=True,
            )
            for e in erros:
                st.warning(e)
        else:
            _status_agentes.update(
                label=f"{n_ok} {'seção preenchida' if n_ok == 1 else 'seções preenchidas'} com IA",
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
                    _ext_key, _ext_prov, _ext_mod = get_ia_config("ia_extrator", GOOGLE_API_KEY, OPENAI_API_KEY)
                    dados_notas = ia_extrator.extrair_dados_prontuario(
                        texto_bruto=texto_input,
                        api_key=_ext_key,
                        provider=_ext_prov,
                        modelo=_ext_mod,
                    )
                    fluxo.atualizar_notas_ia(dados_notas)
                st.toast("Seções extraídas com sucesso.", icon="✅")
                st.session_state["_secoes_recortadas"] = {
                    sec: bool(st.session_state.get(agentes_secoes._NOTAS_MAP[sec], "").strip())
                    for sec in agentes_secoes._NOTAS_MAP
                    if sec in agentes_secoes._AGENTES
                }

# ── Checklist persistente + botão de agentes ──────────────────────────────────
if "_secoes_recortadas" in st.session_state:
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

with st.form("form_dados_clinicos"):
    fichas.render_formulario_completo()
    st.write("")
    submitted = st.form_submit_button(
        "📋 Gerar Prontuário Completo", type="primary", use_container_width=True
    )

_render_condutas_reg()
st.write("")

# ==============================================================================
# DIALOGS (definidos antes dos handlers que os chamam)
# ==============================================================================

@st.dialog("🔍 Gerar Bloco", width="large")
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

if submitted:
    st.session_state.texto_final_gerado = gerador.gerar_texto_final()

# ── Gerar Bloco individual ─────────────────────────────────────────────────────
_gerar_bloco_pendente = st.session_state.pop("_gerar_bloco_pendente", None)
if _gerar_bloco_pendente:
    st.session_state["_bloco_secao_key"]   = _gerar_bloco_pendente
    st.session_state["_bloco_secao_texto"] = gerador.gerar_secao(_gerar_bloco_pendente)
    _modal_gerar_bloco()

# ── Comparar Labs + Controles ──────────────────────────────────────────────────
if st.session_state.pop("_comparar_lab_pendente", False) or st.session_state.pop("_comparar_ctrl_pendente", False):
    _modal_comparar_labs()

# ── Agente individual ──────────────────────────────────────────────────────────
_agente_pendente = st.session_state.pop("_agente_pendente", None)
if _agente_pendente:
    if not GOOGLE_API_KEY and not OPENAI_API_KEY:
        st.warning("⚠️ Configure as chaves de API para usar o Completar Campos.")
    elif _agente_pendente == "laboratoriais" and not st.session_state.get("laboratoriais_notas", "").strip():
        st.warning("⚠️ Cole os exames no campo de notas do Bloco 10 (Exames Laboratoriais) antes de clicar em Completar Campos.")
    else:
        _aplicar_agentes_paralelo([_agente_pendente])

# ── Parsing Controles (determinístico) ────────────────────────────────────────
if st.session_state.pop("_ctrl_deterministico_pendente", False):
    texto_ctrl = st.session_state.get("controles_notas", "").strip()
    if not texto_ctrl:
        st.warning("Cole os controles no campo de notas do Bloco 11 primeiro.")
    else:
        dados = parse_controles_deterministico(texto_ctrl, data_hoje=date.today())
        if dados:
            st.toast(f"✅ {len(dados)} campos de controles preenchidos.", icon="📊")
            _para_staging(dados)
        else:
            st.warning("⚠️ Nenhum controle no formato esperado. Use: # Controles - 24 horas, > DD/MM/YYYY, PAS: min - max...")

# ── Parsing Laboratoriais (determinístico) ────────────────────────────────────
if st.session_state.pop("_lab_deterministico_pendente", False):
    texto_lab = st.session_state.get("laboratoriais_notas", "").strip()
    if not texto_lab:
        st.warning("Cole os exames no campo de notas do Bloco 10 primeiro.")
    else:
        dados = parse_lab_deterministico(texto_lab, data_hoje=date.today())
        if dados:
            st.toast(f"✅ {len(dados)} campos preenchidos (determinístico).", icon="🧪")
            _para_staging(dados)
        else:
            st.warning("⚠️ Nenhum exame no formato esperado. Use: DD/MM/YYYY – Hb x | Ht x | ...")

# ── Extrair Exames via PACER + Agente Lab ─────────────────────────────────────
if st.session_state.pop("_lab_extrair_pendente", False):
    texto_lab = st.session_state.get("laboratoriais_notas", "").strip()
    if not texto_lab:
        st.warning("Cole os exames no campo de notas do Bloco 10 primeiro.")
    else:
        _ok, _msg = verificar_rate_limit()
        if not _ok:
            st.error(f"🚫 {_msg}")
        else:
            _pacer_key, _pacer_prov, _pacer_mod = get_ia_config("pacer_exames", GOOGLE_API_KEY, OPENAI_API_KEY)
            with st.spinner("Extraindo exames laboratoriais com IA..."):
                resultado_pacer = extrator_exames.extrair_exames(
                    texto_lab, _pacer_key, _pacer_prov, _pacer_mod
                )
            if resultado_pacer.startswith("❌"):
                st.error(resultado_pacer)
            elif not resultado_pacer.strip():
                st.warning("Nenhum dado laboratorial extraído. Verifique o formato dos exames.")
            else:
                _lab_key, _lab_prov, _lab_mod = get_ia_config("laboratoriais", GOOGLE_API_KEY, OPENAI_API_KEY)
                with st.spinner("Aplicando dados aos campos..."):
                    dados_lab = agentes_secoes._AGENTES["laboratoriais"](
                        resultado_pacer, _lab_key, _lab_prov, _lab_mod
                    )
                if "_erro" in dados_lab:
                    st.error(f"Erro no agente: {dados_lab['_erro']}")
                else:
                    st.toast("Exames extraídos e aplicados.", icon="🧪")
                    _para_staging(dados_lab)

# ── Parsing Sistemas (determinístico) ─────────────────────────────────────────
if st.session_state.pop("_sistemas_deterministico_pendente", False):
    texto_sist = st.session_state.get("sistemas_notas", "").strip()
    if not texto_sist:
        st.warning("Cole a evolução por sistemas no campo de notas do Bloco 13 primeiro.")
    else:
        fluxo.aplicar_sistemas_deterministico(texto_sist)

# ── Completar Bloco 13 a partir dos Blocos Anteriores ─────────────────────────
if st.session_state.pop("_completar_blocos_sistemas", False):
    fluxo.completar_sistemas_de_outros_blocos()

# ── Extrair Prescrição via PACER ───────────────────────────────────────────────
if st.session_state.pop("_prescricao_extrair_pendente", False):
    texto_presc = st.session_state.get("prescricao_bruta", "").strip()
    if not texto_presc:
        st.warning("Cole a prescrição no campo do Bloco 14 primeiro.")
    else:
        _ok, _msg = verificar_rate_limit()
        if not _ok:
            st.error(f"🚫 {_msg}")
        else:
            _presc_key, _presc_prov, _presc_mod = get_ia_config("prescricao", GOOGLE_API_KEY, OPENAI_API_KEY)
            with st.spinner("Formatando prescrição com IA..."):
                resultado_presc = extrator_exames.extrair_prescricao(
                    texto_presc, _presc_key, _presc_prov, _presc_mod
                )
            if resultado_presc.startswith("❌"):
                st.error(resultado_presc)
            else:
                st.toast("Prescrição formatada.", icon="💊")
                _para_staging({"prescricao_formatada": resultado_presc})

# ==============================================================================
# BLOCO 3: PRONTUÁRIO COMPLETO
# ==============================================================================
c_head_1, c_head_2 = st.columns([3.5, 1.5], vertical_alignment="bottom")
with c_head_1:
    ui.render_header_secao("3. Prontuário Completo", "✅", ui.COLOR_GREEN)
with c_head_2:
    if st.button("📋 Copiar Texto", use_container_width=True, help="Copia o prontuário completo para a área de transferência"):
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
    st.markdown('<div style="height: 12px"></div>', unsafe_allow_html=True)

with st.container(border=True):
    st.text_area(
        "Final",
        key="texto_final_gerado",
        height=200,
        label_visibility="collapsed",
        placeholder="Clique em Prontuário Completo para gerar o texto.",
    )

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
    st.button("🗑️ Limpar Tudo", on_click=fluxo.limpar_tudo, use_container_width=True)

mostrar_rodape()
