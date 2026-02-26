import streamlit as st
import google.generativeai as genai
import os
from pathlib import Path

# Importa os módulos
from modules import ui, fichas, gerador, fluxo, ia_extrator, agentes_secoes, extrator_exames
from utils import load_data, save_evolucao, load_evolucao, check_evolucao_exists, mostrar_rodape

# ==============================================================================
# CARREGAMENTO DE CHAVES DE API (secrets.toml → .env → vazio)
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

OPENAI_API_KEY  = _carregar_chave("OPENAI_API_KEY",  "OPENAI_API_KEY")
GOOGLE_API_KEY  = _carregar_chave("GOOGLE_API_KEY",  "GOOGLE_API_KEY")

# ==============================================================================
# MODELOS DISPONÍVEIS
# ==============================================================================
MODELOS_GEMINI = ["gemini-2.5-flash", "gemini-2.5-pro"]

# ==============================================================================
# SETUP
# ==============================================================================
ui.carregar_css()
fichas.inicializar_estado()

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.header("Configurações")

    provider = st.radio("IA:", ["OpenAI GPT", "Google Gemini"], index=0)

    if provider == "OpenAI GPT":
        api_key      = OPENAI_API_KEY
        modelo_escolhido = "gpt-4o"
        st.success("IA: OpenAI - GPT-4o")
        if api_key and len(api_key) > 10:
            st.success(f"✅ API Key: ...{api_key[-8:]}")
        else:
            st.error("❌ API Key não carregada!")

    else:  # Google Gemini
        api_key = GOOGLE_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
        modelo_escolhido = st.selectbox("Modelo:", MODELOS_GEMINI, index=0)
        st.success(f"IA: Google - {modelo_escolhido}")
        if api_key and len(api_key) > 10:
            st.success(f"✅ API Key: ...{api_key[-8:]}")
        else:
            st.error("❌ API Key não carregada!")

# Disponibiliza configurações de IA para fichas.py usar nos botões por seção
# (provider calculado inline — _provider_completo() é definido mais abaixo)
_provider_str = f"{provider} {modelo_escolhido}" if provider == "Google Gemini" else provider
st.session_state["_ia_api_key"]  = api_key
st.session_state["_ia_provider"] = _provider_str
st.session_state["_ia_modelo"]   = modelo_escolhido

# ==============================================================================
# TÍTULO E BUSCA
# ==============================================================================
st.title("📝 Evolução Diária")
st.write("") 

with st.container():
    with st.form(key="form_busca_paciente"):
        c_input, c_btn_criar, c_btn_carregar = st.columns([4, 1, 1], vertical_alignment="bottom")

        with c_input:
            st.markdown('<label style="font-size: 1.2rem; font-weight: 600; color: #444; margin-bottom: 5px; display: block;">Número de Prontuário:</label>', unsafe_allow_html=True)
            busca_input = st.text_input("Label Oculta", placeholder="Digite número do prontuário...", key="busca_input_field", label_visibility="collapsed")

        with c_btn_criar:
            btn_criar = st.form_submit_button("➕ Criar Novo", use_container_width=True)

        with c_btn_carregar:
            btn_carregar = st.form_submit_button("📂 Carregar Prontuário", use_container_width=True)

        busca = busca_input.strip() if busca_input else ""

        # ── CRIAR NOVO ──────────────────────────────────────────────────────────
        if btn_criar:
            if not busca:
                st.warning("Digite o número do prontuário.")
            elif busca.upper() == "TESTE":
                st.session_state.update({
                    'nome': 'João da Silva (Paciente Teste)',
                    'idade': 68,
                    'prontuario': 'TESTE-001',
                    'leito': 'UTI-05',
                    'origem': 'PS / Emergência',
                    'di_hosp': '12 dias',
                    'di_uti': '4 dias',
                    'saps3': '55',
                    'sofa_adm': 8,
                })
                st.toast("Modo Treinamento Ativado! 🧪", icon="✅")
            else:
                with st.spinner("Verificando prontuário..."):
                    ja_existe = check_evolucao_exists(busca)
                if ja_existe:
                    st.warning(
                        f"⚠️ Prontuário **{busca}** já cadastrado. "
                        "Carregue as informações no botão **\"Carregar Prontuário\"**."
                    )
                else:
                    # Cria registro inicial vazio para reservar o número
                    st.session_state["prontuario"] = busca
                    with st.spinner("Criando prontuário..."):
                        save_evolucao(busca, "", {"prontuario": busca})
                    st.toast(f"✅ Prontuário {busca} criado! Preencha os dados e salve.", icon="✨")

        # ── CARREGAR PRONTUÁRIO ─────────────────────────────────────────────────
        if btn_carregar:
            if not busca:
                st.warning("Digite o número do prontuário.")
            else:
                with st.spinner("🔍 Carregando prontuário..."):
                    dados = load_evolucao(busca)
                if dados:
                    data_hora = dados.pop("_data_hora", "")
                    # Migração: hd_atual_* / hd_prev_* → hd_* (schema unificado)
                    if "hd_atual_1_nome" in dados:
                        for i in range(1, 5):
                            dados[f"hd_{i}_nome"] = dados.get(f"hd_atual_{i}_nome", "")
                            dados[f"hd_{i}_class"] = dados.get(f"hd_atual_{i}_class", "")
                            dados[f"hd_{i}_data_inicio"] = dados.get(f"hd_atual_{i}_data", "")
                            dados[f"hd_{i}_data_resolvido"] = ""
                            dados[f"hd_{i}_status"] = "Atual"
                            dados[f"hd_{i}_obs"] = dados.get(f"hd_atual_{i}_obs", "")
                            dados[f"hd_{i}_conduta"] = dados.get(f"hd_atual_{i}_conduta", "")
                        for i in range(1, 5):
                            j = i + 4
                            dados[f"hd_{j}_nome"] = dados.get(f"hd_prev_{i}_nome", "")
                            dados[f"hd_{j}_class"] = dados.get(f"hd_prev_{i}_class", "")
                            dados[f"hd_{j}_data_inicio"] = dados.get(f"hd_prev_{i}_data_ini", "")
                            dados[f"hd_{j}_data_resolvido"] = dados.get(f"hd_prev_{i}_data_fim", "")
                            dados[f"hd_{j}_status"] = "Resolvida"
                            dados[f"hd_{j}_obs"] = dados.get(f"hd_prev_{i}_obs", "")
                            dados[f"hd_{j}_conduta"] = dados.get(f"hd_prev_{i}_conduta", "")
                        dados["hd_ordem"] = list(range(1, 9))
                    campos_validos = fichas.get_todos_campos_keys()
                    st.session_state.update(
                        {k: v for k, v in dados.items() if k in campos_validos}
                    )
                    st.toast(f"✅ Prontuário carregado! Última evolução: {data_hora}", icon="📂")
                else:
                    st.warning(
                        f"⚠️ Prontuário **{busca}** não encontrado. "
                        "Use o botão **\"Criar Novo\"** para cadastrá-lo."
                    )

# ==============================================================================
# PAINEL DE IDENTIFICAÇÃO
# ==============================================================================
ui.render_barra_paciente()

# ==============================================================================
# HELPER: monta string do provider para as funções de IA
# ==============================================================================
def _provider_completo():
    return f"{provider} {modelo_escolhido}" if provider == "Google Gemini" else provider


def _aplicar_agentes_paralelo(secoes: list[str]):
    """
    Roda os agentes das seções fornecidas em paralelo (uma thread por agente).
    Atualiza o session_state com os resultados ao final.
    """
    import concurrent.futures

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

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tarefas)) as executor:
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

    # Acumula resultados no staging para serem aplicados ANTES dos widgets no próximo ciclo
    # Nunca sobrescreve com string vazia — preserva dados manuais já preenchidos
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

    # Força rerender para os campos aparecerem preenchidos imediatamente
    st.rerun()


# ==============================================================================
# BLOCO 1: PRONTUÁRIO — recortador + checklist + agentes
# ==============================================================================
ui.render_header_secao("1. Prontuário", "📄", ui.COLOR_BLUE)

# ── Input + Extrair ────────────────────────────────────────────────────────────
with st.container(border=True):
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

            # Persiste o status de cada seção para o checklist sobreviver ao rerun
            st.session_state["_secoes_recortadas"] = {
                sec: bool(st.session_state.get(agentes_secoes._NOTAS_MAP[sec], "").strip())
                for sec in agentes_secoes._NOTAS_MAP
                if sec in agentes_secoes._AGENTES
            }

# ── Checklist persistente + botão de agentes ──────────────────────────────────
if "_secoes_recortadas" in st.session_state:
    _status = st.session_state["_secoes_recortadas"]
    _com_texto = sum(_status.values())

    with st.container(border=True):
        st.markdown("**Seções Preenchidas**")
        st.write("")

        # Grid 4 colunas — ✅ com conteúdo / ⬜ vazia
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
# st.form bate zero rerun em qualquer widget — só recarrega no submit
# ==============================================================================
ui.render_header_secao("2. Dados Clínicos", "✍️", "#f59e0b")
ui.render_guia_navegacao()

with st.form("form_dados_clinicos"):
    fichas.render_formulario_completo()

    st.write("")
    submitted = st.form_submit_button(
        "📋 Prontuário Completo", type="primary", use_container_width=True
    )

# "Condutas Registradas" fica FORA do form: atualiza após qualquer submit (Enter ou botão)
from modules.secoes import condutas as _condutas_mod
_condutas_mod.render_condutas_registradas()
st.write("")

if submitted:
    st.session_state.texto_final_gerado = gerador.gerar_texto_final()

# Processa agente individual disparado via form_submit_button dentro do form
_agente_pendente = st.session_state.pop("_agente_pendente", None)
if _agente_pendente:
    if not api_key:
        st.warning("⚠️ Configure a chave de API na barra lateral para usar o Completar Campos.")
    elif _agente_pendente == "laboratoriais" and not st.session_state.get("laboratoriais_notas", "").strip():
        st.warning("⚠️ Cole os exames no campo de notas do Bloco 10 (Exames Laboratoriais) antes de clicar em Completar Campos.")
    else:
        _aplicar_agentes_paralelo([_agente_pendente])

# ── Extrair Exames (PACER) + Agente Lab automático ─────────────────────────
_lab_extrair = st.session_state.pop("_lab_extrair_pendente", False)
if _lab_extrair and api_key:
    texto_lab = st.session_state.get("laboratoriais_notas", "").strip()
    if not texto_lab:
        st.warning("Cole os exames no campo de notas do Bloco 10 primeiro.")
    else:
        # Passo 1: PACER formata os exames brutos
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

            # Passo 2: Agente de laboratoriais usa o resultado PACER como input
            with st.spinner("🤖 Aplicando agente de laboratoriais..."):
                fn_lab = agentes_secoes._AGENTES["laboratoriais"]
                dados_lab = fn_lab(
                    resultado_pacer, api_key, _provider_completo(), modelo_escolhido
                )

            if "_erro" in dados_lab:
                st.warning(f"⚠️ Erro no agente de laboratoriais: {dados_lab['_erro']}")
            else:
                # Staging: só atualiza campos com valor não vazio — NUNCA apaga dados já preenchidos
                staging = st.session_state.get("_agent_staging", {})
                for k, v in dados_lab.items():
                    if v is not None and str(v).strip() != "":
                        staging[k] = v
                st.session_state["_agent_staging"] = staging
                # Força rerender para os campos aparecerem preenchidos imediatamente
                st.rerun()

# ── Completar Seção 13 a partir de Blocos Anteriores ─────────────────────────
if st.session_state.pop("_completar_blocos_sistemas", False):

    def _limpar(v):
        """Remove barra e tudo após (ex: '1.2/72s' → '1.2')."""
        return str(v or "").split("/")[0].strip()

    def _limpar_leuco(v):
        """Remove diferencial entre parênteses (ex: '12.500 (Seg 70%)' → '12.500')."""
        return _limpar(v).split("(")[0].strip()

    def _extrair_inr(v):
        """Extrai valor entre parênteses do TP (ex: '14.2s (1.10)' → '1.10'). Retorna o valor original se não houver parênteses."""
        s = str(v or "").strip()
        if "(" in s and ")" in s:
            return s.split("(")[1].split(")")[0].strip()
        return _limpar(s)

    staging = st.session_state.get("_agent_staging", {})
    _cnt = [0]

    def _set(sis_key, val):
        # Só preenche se a origem tem valor E o destino está vazio (preserva dados manuais)
        if val and not str(st.session_state.get(sis_key, "") or "").strip():
            staging[sis_key] = val
            _cnt[0] += 1

    # 1. Controles → Renal (diurese e balanço de hoje)
    _set("sis_renal_diurese", _limpar(st.session_state.get("ctrl_hoje_diurese", "")))
    _set("sis_renal_balanco",  _limpar(st.session_state.get("ctrl_hoje_balanco", "")))

    # 2. Laboratoriais → Renal (Cr e Ur, 3 datas)
    for sis_suf, lab_idx in [("hoje", 1), ("ult", 2), ("antepen", 3)]:
        _set(f"sis_renal_cr_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_cr", "")))
        _set(f"sis_renal_ur_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_ur", "")))

    # 3. Antibióticos atuais → Infeccioso (nomes 1, 2, 3)
    for i in range(1, 4):
        _set(f"sis_infec_atb_{i}", _limpar(st.session_state.get(f"atb_curr_{i}_nome", "")))

    # 4. Culturas → Infeccioso (sítio e data de coleta, slots 1–4)
    for i in range(1, 5):
        sitio = _limpar(st.session_state.get(f"cult_{i}_sitio", ""))
        data  = _limpar(st.session_state.get(f"cult_{i}_data_coleta", ""))
        _set(f"sis_infec_cult_{i}_sitio", sitio)
        _set(f"sis_infec_cult_{i}_data",  data)

    # 5. Laboratoriais → Infeccioso (PCR e Leucócitos, 3 datas)
    for sis_suf, lab_idx in [("hoje", 1), ("ult", 2), ("antepen", 3)]:
        _set(f"sis_infec_pcr_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_pcr", "")))
        _set(f"sis_infec_leuc_{sis_suf}", _limpar_leuco(st.session_state.get(f"lab_{lab_idx}_leuco", "")))

    # 6. Laboratoriais → Hematológico (Hb, Plaq, INR, 3 datas)
    for sis_suf, lab_idx in [("hoje", 1), ("ult", 2), ("antepen", 3)]:
        _set(f"sis_hemato_hb_{sis_suf}",   _limpar(st.session_state.get(f"lab_{lab_idx}_hb", "")))
        _set(f"sis_hemato_plaq_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_plaq", "")))
        _set(f"sis_hemato_inr_{sis_suf}",  _extrair_inr(st.session_state.get(f"lab_{lab_idx}_tp", "")))

    st.session_state["_agent_staging"] = staging
    if _cnt[0]:
        st.toast(f"✅ {_cnt[0]} campos preenchidos a partir dos Blocos Anteriores!", icon="📋")
    else:
        st.warning("⚠️ Nenhum valor encontrado nos blocos de origem. Preencha Controles, Lab, Antibióticos e Culturas primeiro.")
    st.rerun()

# ── Extrair Prescrição (PACER Prescrição) ────────────────────────────────────
_prescricao_extrair = st.session_state.pop("_prescricao_extrair_pendente", False)
if _prescricao_extrair and api_key:
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
            staging = st.session_state.get("_agent_staging", {})
            staging["prescricao_formatada"] = resultado_presc
            st.session_state["_agent_staging"] = staging
            st.rerun()

# ==============================================================================
# BLOCO 3: PRONTUÁRIO COMPLETO
# ==============================================================================
c_head_1, c_head_2 = st.columns([3.5, 1.5], vertical_alignment="bottom")

with c_head_1:
    ui.render_header_secao("3. Prontuário Completo", "✅", ui.COLOR_GREEN)

with c_head_2:
    if st.button("📋 Copiar Texto", use_container_width=True, help="Copia o prontuário completo (gerado pelo modelo determinístico) para a área de transferência"):
        import json
        import streamlit.components.v1 as components
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
# MODAL: Comparar Prontuário Original × Gerado
# ==============================================================================
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
        nome       = st.session_state.get("nome", "").strip()

        if not prontuario:
            st.error("❌ Preencha o número do prontuário antes de salvar.")
        else:
            campos_keys = fichas.get_todos_campos_keys()
            dados = {k: st.session_state.get(k) for k in campos_keys}
            with st.spinner("💾 Salvando evolução..."):
                ok = save_evolucao(prontuario, nome, dados)
            if ok:
                st.success(f"✅ Evolução salva com sucesso! Prontuário: {prontuario}")

with col_limpar:
    st.button("🗑️ Limpar Tudo", on_click=fluxo.limpar_tudo, use_container_width=True)


# Rodapé com nota legal
mostrar_rodape()