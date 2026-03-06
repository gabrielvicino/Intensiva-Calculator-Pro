import streamlit as st
import os
import json
import concurrent.futures
import streamlit.components.v1 as components
from pathlib import Path
from datetime import date

from modules import ui, fichas, gerador, fluxo, ia_extrator, agentes_secoes, extrator_exames
from modules.parser_lab import parse_lab_deterministico
from modules.parser_controles import parse_controles_deterministico
from modules.parser_sistemas import parse_sistemas_deterministico
from modules.secoes.condutas import render_condutas_registradas as _render_condutas_reg
from utils import load_data, save_evolucao, load_evolucao, check_evolucao_exists, mostrar_rodape

# ── Chaves de API (secrets.toml → .env → vazio) ───────────────────────────────
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

MODELOS_GEMINI = ["gemini-2.5-flash", "gemini-2.5-pro"]


def _provider_completo() -> str:
    return f"{provider} {modelo_escolhido}" if provider == "Google Gemini" else provider


# ── Setup ──────────────────────────────────────────────────────────────────────
ui.carregar_css()
fichas.inicializar_estado()

# ── Sidebar: configuração de IA ────────────────────────────────────────────────
with st.sidebar:
    with st.popover("​", use_container_width=True):
        provider = st.radio(
            "Provedor:",
            ["Google Gemini", "OpenAI GPT"],
            index=0,
            key="_ia_provider_radio",
        )
        if provider == "Google Gemini":
            api_key = GOOGLE_API_KEY
            modelo_escolhido = st.selectbox("Modelo:", MODELOS_GEMINI, index=1, key="_ia_modelo_gemini")
            st.success(f"IA: Google — {modelo_escolhido}")
        else:
            api_key = OPENAI_API_KEY
            modelo_escolhido = "gpt-4o"
            st.success("IA: OpenAI — GPT-4o")

        if api_key and len(api_key) > 10:
            st.success(f"✅ API Key: ...{api_key[-8:]}")
        else:
            st.error("❌ API Key não carregada!")

st.session_state["_ia_api_key"]  = api_key
st.session_state["_ia_provider"] = _provider_completo()
st.session_state["_ia_modelo"]   = modelo_escolhido

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

def _carregar_dados_prontuario(busca: str) -> bool:
    """Carrega e aplica os dados de um prontuário existente no session_state."""
    dados = load_evolucao(busca)
    if not dados:
        return False
    data_hora = dados.pop("_data_hora", "")
    # Migração: hd_atual_* / hd_prev_* → hd_* (schema unificado)
    if "hd_atual_1_nome" in dados:
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
    campos_validos = fichas.get_todos_campos_keys()
    st.session_state.update({k: v for k, v in dados.items() if k in campos_validos})
    st.session_state["_data_hora_carregado"] = data_hora
    st.toast(f"✅ Prontuário carregado! Última evolução: {data_hora}", icon="📂")
    return True


@st.fragment
def _fragment_busca():
    with st.container():
        with st.form(key="form_busca_paciente"):
            c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
            with c_input:
                st.markdown('<label style="font-size: 1.2rem; font-weight: 600; color: #444; margin-bottom: 5px; display: block;">Número de Prontuário:</label>', unsafe_allow_html=True)
                busca_input = st.text_input(
                    "Label Oculta",
                    placeholder="Digite o número e pressione Enter...",
                    key="busca_input_field",
                    label_visibility="collapsed",
                )
            with c_btn:
                btn_buscar = st.form_submit_button("🔍 Buscar", use_container_width=True, type="primary")

            busca = busca_input.strip() if busca_input else ""
            if btn_buscar:
                if not busca:
                    st.warning("Digite o número do prontuário.")
                else:
                    if check_evolucao_exists(busca):
                        with st.spinner("Carregando..."):
                            _carregar_dados_prontuario(busca)
                        st.rerun()
                    else:
                        st.session_state["_busca_pendente_criar"] = busca

_fragment_busca()

# ── Confirmação de criação de novo prontuário ──────────────────────────────────
if "_busca_pendente_criar" in st.session_state:
    pend = st.session_state["_busca_pendente_criar"]
    st.warning(f"Prontuário **{pend}** não encontrado no banco de dados.")
    st.markdown("**Deseja criar um novo prontuário?**")
    c_sim, c_nao, _c_esp = st.columns([1, 1, 4])
    with c_sim:
        if st.button("✅ Sim, criar", type="primary", use_container_width=True, key="_btn_criar_sim"):
            st.session_state.pop("_busca_pendente_criar", None)
            st.session_state["prontuario"] = pend
            with st.spinner("Criando..."):
                save_evolucao(pend, "", {"prontuario": pend})
            st.toast(f"✅ Prontuário {pend} criado! Preencha os dados e salve.", icon="✨")
            st.rerun()
    with c_nao:
        if st.button("✖ Não", use_container_width=True, key="_btn_criar_nao"):
            st.session_state.pop("_busca_pendente_criar", None)
            st.rerun()

# ── Barra de identificação do paciente ────────────────────────────────────────
ui.render_barra_paciente()


# ── Agentes em paralelo ────────────────────────────────────────────────────────

def _aplicar_agentes_paralelo(secoes: list[str]):
    """Roda os agentes das seções fornecidas em paralelo e aplica resultados via staging."""
    tarefas = [
        (sec, st.session_state.get(agentes_secoes._NOTAS_MAP[sec], "").strip())
        for sec in secoes
        if st.session_state.get(agentes_secoes._NOTAS_MAP[sec], "").strip()
    ]
    if not tarefas:
        st.warning("Nenhuma seção tem texto para processar.")
        return

    progresso  = st.progress(0, text=f"🤖 Processando {len(tarefas)} agentes em paralelo...")
    status_txt = st.empty()
    concluidos = 0
    erros      = []
    resultados = {}

    def _rodar(secao, texto):
        fn = agentes_secoes._AGENTES[secao]
        return secao, fn(texto, api_key, _provider_completo(), modelo_escolhido)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tarefas), 8)) as executor:
        futures = {executor.submit(_rodar, s, t): s for s, t in tarefas}
        for future in concurrent.futures.as_completed(futures):
            concluidos += 1
            try:
                secao, dados = future.result()
                nome = agentes_secoes.NOMES_SECOES[secao]
                if "_erro" in dados:
                    erros.append(f"{nome}: {dados['_erro']}")
                else:
                    resultados[secao] = dados
                status_txt.caption(f"✅ {nome} ({concluidos}/{len(tarefas)})")
            except Exception as exc:
                sec = futures[future]
                erros.append(f"{agentes_secoes.NOMES_SECOES[sec]}: {exc}")
            progresso.progress(concluidos / len(tarefas))

    # Acumula no staging; nunca sobrescreve com string vazia
    staging = st.session_state.get("_agent_staging", {})
    for dados in resultados.values():
        for k, v in dados.items():
            if not (isinstance(v, str) and v.strip() == ""):
                staging[k] = v
    st.session_state["_agent_staging"] = staging

    progresso.progress(1.0, text="✅ Concluído!")
    status_txt.empty()

    if erros:
        for e in erros:
            st.warning(f"⚠️ {e}")
    else:
        st.success(f"✅ {len(resultados)} seções preenchidas com sucesso!")
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
            f"📂 **Prontuário anterior carregado** (salvo em {_data_carg})  \n"
            "O texto abaixo foi o último colado neste prontuário. "
            "Substitua por uma nova evolução ou clique em **Extrair Seções** para reprocessar.",
        )
    elif _data_carg and not _tem_texto_ant:
        st.info(
            f"📂 **Prontuário carregado** (salvo em {_data_carg})  \n"
            "Cole uma nova evolução abaixo para extrair os dados.",
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
        if not api_key:
            st.error("Sem chave API.")
        elif not texto_input:
            st.warning("Cole o texto do prontuário primeiro.")
        else:
            with st.spinner("Processando prontuário para seções 1 a 14..."):
                dados_notas = ia_extrator.extrair_dados_prontuario(
                    texto_bruto=texto_input,
                    api_key=api_key,
                    provider=_provider_completo(),
                    modelo=modelo_escolhido,
                )
                fluxo.atualizar_notas_ia(dados_notas)
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
                if not api_key:
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
    if not api_key:
        st.warning("⚠️ Configure a chave de API na barra lateral para usar o Completar Campos.")
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
if st.session_state.pop("_lab_extrair_pendente", False) and api_key:
    texto_lab = st.session_state.get("laboratoriais_notas", "").strip()
    if not texto_lab:
        st.warning("Cole os exames no campo de notas do Bloco 10 primeiro.")
    else:
        with st.spinner("🧪 Extraindo e formatando exames (PACER)..."):
            resultado_pacer = extrator_exames.extrair_exames(
                texto_lab, api_key, _provider_completo(), modelo_escolhido
            )
        if resultado_pacer.startswith("❌"):
            st.error(resultado_pacer)
        elif not resultado_pacer.strip():
            st.warning("⚠️ Nenhum dado laboratorial foi extraído do texto. Verifique o formato dos exames.")
        else:
            st.toast("✅ Exames formatados! Aplicando ao prontuário...", icon="🧪")
            with st.spinner("🤖 Aplicando agente de laboratoriais..."):
                dados_lab = agentes_secoes._AGENTES["laboratoriais"](
                    resultado_pacer, api_key, _provider_completo(), modelo_escolhido
                )
            if "_erro" in dados_lab:
                st.warning(f"⚠️ Erro no agente de laboratoriais: {dados_lab['_erro']}")
            else:
                _para_staging(dados_lab)

# ── Parsing Sistemas (determinístico) ─────────────────────────────────────────
if st.session_state.pop("_sistemas_deterministico_pendente", False):
    texto_sist = st.session_state.get("sistemas_notas", "").strip()
    if not texto_sist:
        st.warning("Cole a evolução por sistemas no campo de notas do Bloco 13 primeiro.")
    else:
        dados = parse_sistemas_deterministico(texto_sist)
        staging = st.session_state.get("_agent_staging", {})
        for k, v in dados.items():
            if v is not None and str(v).strip() != "":
                staging[k] = v
        # Aplica defaults de sistemas que ainda estão vazios
        from modules.secoes.sistemas import get_campos as _get_campos_sistemas
        for k, v in _get_campos_sistemas().items():
            if k.startswith("sis_") and k not in staging and v and str(v).strip():
                staging[k] = v
        st.session_state["_agent_staging"] = staging
        cnt = sum(1 for k in staging if k.startswith("sis_") and staging.get(k))
        st.toast(f"✅ {cnt} campos de sistemas preenchidos (determinístico + defaults).", icon="📋")
        st.rerun()

# ── Completar Bloco 13 a partir dos Blocos Anteriores ─────────────────────────
if st.session_state.pop("_completar_blocos_sistemas", False):
    fluxo.completar_sistemas_de_outros_blocos()

# ── Extrair Prescrição via PACER ───────────────────────────────────────────────
if st.session_state.pop("_prescricao_extrair_pendente", False) and api_key:
    texto_presc = st.session_state.get("prescricao_bruta", "").strip()
    if not texto_presc:
        st.warning("Cole a prescrição no campo do Bloco 14 primeiro.")
    else:
        with st.spinner("💊 Formatando prescrição com IA..."):
            resultado_presc = extrator_exames.extrair_prescricao(
                texto_presc, api_key, _provider_completo(), modelo_escolhido
            )
        if resultado_presc.startswith("❌"):
            st.error(resultado_presc)
        else:
            st.toast("✅ Prescrição formatada!", icon="💊")
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
