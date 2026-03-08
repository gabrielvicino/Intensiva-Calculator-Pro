# ==============================================================================
# modules/pacer/tab_laboratoriais.py
# Renderiza a aba "🧪 Laboratoriais" da página Laboratoriais & Controles.
# ==============================================================================

import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.secoes import laboratoriais as _lab_sec
from modules.pacer.pdf_extractor import _chamar_agente, _AGENTES
from modules.parsers.lab import parse_agentes_para_slot
from datetime import date as _date


# ==============================================================================
# Prontuário — busca e salvamento (espelho da Evolução Diária)
# ==============================================================================

_TITULOS_SLOT = {
    1: "Hoje", 2: "Ontem", 3: "Anteontem", 4: "Admissão/Externo",
    5: "Dia -4", 6: "Dia -5", 7: "Dia -6", 8: "Dia -7", 9: "Dia -8", 10: "Dia -9",
}


@st.fragment
def _fragment_prontuario() -> None:
    """Campo de prontuário + botão Buscar — idêntico ao da Evolução Diária."""
    from utils import load_evolucao
    from modules import fichas

    # Sincroniza com o prontuário sempre que ele for atualizado externamente
    # (ex.: carregado pelo tab Controles). Usa rastreador para não sobrescrever
    # o que o usuário está digitando manualmente.
    _pront_atual = st.session_state.get("prontuario", "")
    _last_sync   = st.session_state.get("_lab_pront_last_sync", None)
    if _pront_atual != _last_sync:
        st.session_state["_lab_pront_input"] = _pront_atual
        st.session_state["_lab_pront_last_sync"] = _pront_atual

    with st.form(key="form_busca_lab"):
        c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
        with c_input:
            busca_input = st.text_input(
                "Número do Prontuário",
                placeholder="Ex.: 1234567",
                key="_lab_pront_input",
            )
        with c_btn:
            btn_buscar = st.form_submit_button(
                "Buscar", use_container_width=True, type="primary"
            )

        busca = busca_input.strip() if busca_input else ""
        if btn_buscar:
            if not busca:
                st.warning("Informe o número do prontuário.")
            else:
                with st.spinner("Consultando banco de dados..."):
                    dados = load_evolucao(busca)
                if dados is not None:
                    _aplicar_dados_prontuario(dados, fichas)
                    st.rerun()
                else:
                    st.session_state["_lab_pront_pendente"] = busca
                    st.rerun()


def _aplicar_dados_prontuario(dados: dict, fichas_mod) -> None:
    """Aplica dados carregados ao session_state (igual à Evolução Diária)."""
    if not dados:
        return
    data_hora = dados.pop("_data_hora", "")
    dados = fichas_mod.migrar_schema_legado(dados)
    campos_validos = set(fichas_mod.get_todos_campos_keys())
    for k, v in dados.items():
        if k in campos_validos:
            # Preserva valores não-vazios já presentes no estado atual.
            # Só sobrescreve se o Sheets tiver valor, ou se o campo estiver vazio.
            if v or not st.session_state.get(k):
                st.session_state[k] = v
    st.session_state["_data_hora_carregado"] = data_hora
    st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")


def _confirmar_novo_prontuario() -> None:
    """Exibe opção de criar novo prontuário quando não encontrado."""
    from utils import save_evolucao

    if "_lab_pront_pendente" not in st.session_state:
        return

    pend = st.session_state["_lab_pront_pendente"]
    with st.container(border=True):
        st.markdown(
            f"**Prontuário {pend} não localizado.**  \n"
            "Nenhum registro encontrado. Deseja iniciar um novo prontuário?",
        )
        c_sim, c_nao, *_ = st.columns([2, 2, 8])
        with c_sim:
            if st.button(
                "Criar prontuário", type="primary",
                use_container_width=True, key="_lab_btn_criar",
            ):
                st.session_state.pop("_lab_pront_pendente", None)
                st.session_state["prontuario"] = pend
                with st.spinner("Registrando novo prontuário..."):
                    save_evolucao(pend, "", {"prontuario": pend})
                st.toast(f"Prontuário {pend} registrado com sucesso.", icon="✅")
                st.rerun()
        with c_nao:
            if st.button(
                "Cancelar", use_container_width=True, key="_lab_btn_cancelar_criar",
            ):
                st.session_state.pop("_lab_pront_pendente", None)
                st.rerun()


# ==============================================================================
# Campos de texto por slot
# ==============================================================================

def _render_texto_entrada(slots: list) -> None:
    """Campos de texto para colar o laudo bruto, um por slot."""
    cols = st.columns(len(slots))
    for col, slot in zip(cols, slots):
        with col:
            st.text_area(
                "Laudo",
                key=f"lab_{slot}_texto_entrada",
                placeholder="Cole o laudo aqui...",
                label_visibility="collapsed",
                height=68,
            )


# ==============================================================================
# Extração via IA — 7 agentes especializados + parser determinístico
# ==============================================================================

def _extrair_com_ia(api_key: str, modelo: str, placeholder=None) -> None:
    """
    Para cada slot com texto:
      1. Roda os 7 agentes especializados em paralelo (hematologia, hepático,
         coagulação, urina, gasometria, não transcritos) — mesmos do debug tab.
      2. Mapeia o texto estruturado para campos via parse_agentes_para_slot.
    placeholder: st.empty() no topo da página para mostrar o spinner lá.
    """
    slots_com_texto = [
        s for s in range(1, 11)
        if (st.session_state.get(f"lab_{s}_texto_entrada") or "").strip()
    ]

    if not slots_com_texto:
        st.session_state["_lab_avisos"] = ["⚠️ Cole o texto do laudo nos campos acima antes de extrair."]
        return

    # Lê textos ANTES de spawnar threads (session_state não é thread-safe)
    textos = {
        s: (st.session_state.get(f"lab_{s}_texto_entrada") or "").strip()
        for s in slots_com_texto
    }

    resultados_slots: dict[int, tuple[dict, int, str]] = {}

    def _processar(slot: int):
        texto = textos[slot]
        # Mesmos 7 agentes usados pelo debug tab — confirmados funcionando
        resultados_agentes: dict[str, str | None] = {}

        def _worker(nome: str, prompt: str):
            saida = _chamar_agente(prompt, texto, api_key, modelo, "OpenAI GPT")
            return nome, saida

        with ThreadPoolExecutor(max_workers=7) as ex:
            futures = {ex.submit(_worker, n, p): n for n, p in _AGENTES.items()}
            for f in as_completed(futures):
                nome, saida = f.result(timeout=90)
                resultados_agentes[nome] = saida

        if not any(v for v in resultados_agentes.values()):
            return slot, ({}, 0, "Nenhuma resposta dos agentes. Verifique a chave de API.")

        campos = parse_agentes_para_slot(resultados_agentes, slot)
        n = len([v for v in campos.values()
                 if v and str(v).strip() and not str(v).startswith("_")])
        return slot, (campos, n, "")

    if placeholder is not None:
        with placeholder.container():
            st.info(f"🔬 Extraindo {len(slots_com_texto)} laudo(s) com IA...")
    with ThreadPoolExecutor(max_workers=len(slots_com_texto)) as executor:
        futures = {executor.submit(_processar, s): s for s in slots_com_texto}
        for future in as_completed(futures):
            slot, resultado = future.result(timeout=120)
            resultados_slots[slot] = resultado
    if placeholder is not None:
        placeholder.empty()

    erros = []
    pending_campos: dict = {}
    pending_clear: list = []

    for slot in slots_com_texto:
        titulo = _TITULOS_SLOT.get(slot, f"Slot #{slot}")
        campos, n, erro_msg = resultados_slots.get(slot, ({}, 0, "sem retorno"))
        if n > 0:
            pending_campos.update(campos)
            pending_clear.append(slot)
            st.toast(f"✅ {titulo}: {n} campos preenchidos", icon="🧪")
        else:
            detalhe = f" — {erro_msg}" if erro_msg else ""
            erros.append(f"{titulo}: nenhum campo extraído{detalhe}")

    if pending_campos:
        st.session_state["_lab_pending_update"] = pending_campos
        st.session_state["_lab_pending_clear"] = pending_clear

    if erros:
        st.session_state["_lab_avisos"] = [f"⚠️ {erro}" for erro in erros]


# ==============================================================================
# render() — ponto de entrada da aba
# ==============================================================================

def render(api_key: str = "", modelo: str = "gpt-4o") -> None:
    """Renderiza a aba completa de Exames Laboratoriais."""
    from utils import save_evolucao, load_evolucao
    from modules import fichas

    # Aplica resultados pendentes de extração IA/parsing ANTES de renderizar widgets.
    # Preserva dados já preenchidos: sobrescreve só com valores não-vazios.
    if "_lab_pending_update" in st.session_state:
        pending_update = st.session_state.pop("_lab_pending_update")
        pending_clear_slots = st.session_state.pop("_lab_pending_clear", [])
        for k, v in pending_update.items():
            if v is not None and str(v).strip() != "":
                st.session_state[k] = v
        # Limpa apenas os campos de texto de entrada (laudos colados)
        for slot in pending_clear_slots:
            st.session_state[f"lab_{slot}_texto_entrada"] = ""

    st.subheader("🧪 Exames Laboratoriais")

    # ── Prontuário ────────────────────────────────────────────────────────────
    _fragment_prontuario()
    _confirmar_novo_prontuario()

    st.write("")

    prontuario = st.session_state.get("prontuario", "").strip()

    # Placeholder de avisos — fica no TOPO, antes do formulário
    _msg_avisos = st.empty()
    if "_lab_avisos" in st.session_state:
        with _msg_avisos.container():
            for aviso in st.session_state.pop("_lab_avisos"):
                st.warning(aviso)

    # Placeholder para mensagens de save — acima do formulário
    _msg_salvar = st.empty()

    # ── Form principal — sem rerender ao digitar ──────────────────────────────
    with st.form("form_laboratoriais_main"):
        b1, b2, b3 = st.columns(3)
        with b1:
            btn_evo = st.form_submit_button(
                "Evolução Hoje", use_container_width=True,
                help="Desloca resultados: Hoje→Ontem, Ontem→Anteontem, etc. Slot 1 fica vazio.",
            )
        with b2:
            btn_extrair = st.form_submit_button(
                "Extrair Exames", use_container_width=True,
                type="primary",
                help="Usa IA (GPT-4o) para extrair os exames do texto colado em cada coluna.",
                disabled=not api_key,
            )
        with b3:
            btn_salvar = st.form_submit_button(
                "💾 Salvar no Prontuário", use_container_width=True,
                type="primary", disabled=not prontuario,
                help="Salva todos os campos no Google Sheets",
            )

        # Tabela principal: slots 1–4
        _lab_sec._render_day_headers([1, 2, 3, 4])
        _render_texto_entrada([1, 2, 3, 4])
        _lab_sec._render_labs_table([1, 2, 3, 4], show_header=False, show_conduta=False)
        _lab_sec._render_gas_extras([1, 2, 3, 4])

        # Botões de apagar coluna — slots 1–4
        st.divider()
        _clr1, _clr2, _clr3, _clr4 = st.columns(4)
        for _col, _slot in zip((_clr1, _clr2, _clr3, _clr4), (1, 2, 3, 4)):
            with _col:
                _titulo = _TITULOS_SLOT.get(_slot, f"Slot #{_slot}")
                if st.form_submit_button(
                    f"Apagar exames {_titulo.lower()}", use_container_width=True,
                    help=f"Apaga todos os dados da coluna '{_titulo}'",
                ):
                    st.session_state[f"_lab_clear_slot_{_slot}"] = True

        # Demais exames: slots 5–10
        with st.expander("Demais exames", expanded=False):
            _lab_sec._render_day_headers([5, 6, 7, 8, 9, 10])
            _render_texto_entrada([5, 6, 7, 8, 9, 10])
            _lab_sec._render_labs_table([5, 6, 7, 8, 9, 10], show_header=False, show_conduta=False)
            _lab_sec._render_gas_extras([5, 6, 7, 8, 9, 10])

            # Botões de apagar coluna — slots 5–10
            st.divider()
            _clr_cols = st.columns(6)
            for _col, _slot in zip(_clr_cols, (5, 6, 7, 8, 9, 10)):
                with _col:
                    _titulo = _TITULOS_SLOT.get(_slot, f"Slot #{_slot}")
                    if st.form_submit_button(
                        f"Apagar exames {_titulo.lower()}", use_container_width=True,
                        help=f"Apaga todos os dados da coluna '{_titulo}'",
                    ):
                        st.session_state[f"_lab_clear_slot_{_slot}"] = True

    # ── Handlers de apagar coluna (antes de outros handlers para rerun imediato) ─
    for _slot in range(1, 11):
        if st.session_state.pop(f"_lab_clear_slot_{_slot}", False):
            _lab_sec.limpar_slot(_slot)
            _titulo = _TITULOS_SLOT.get(_slot, f"Slot #{_slot}")
            st.toast(f"🗑️ {_titulo} apagado.", icon="🗑️")
            st.rerun()

    # ── Handlers (fora do form, após submissão) ───────────────────────────────
    if btn_evo:
        _lab_sec._deslocar_laboratoriais()
        st.toast("✅ Resultados deslocados.", icon="✅")
        st.rerun()

    if btn_extrair:
        _extrair_com_ia(api_key, modelo, placeholder=_msg_avisos)
        st.rerun()

    if btn_salvar:
        _msg_salvar.info("💾 Salvando...")
        with st.spinner("💾 Salvando..."):
            # Carrega última versão salva para preservar seções fora do escopo desta aba
            base = load_evolucao(prontuario) or {}
            base.pop("_data_hora", None)
            todas_chaves = fichas.get_todos_campos_keys()
            # Campos lab_* vêm do session_state atual; todo o resto vem do último save
            dados = {
                k: (st.session_state.get(k) if k.startswith("lab_")
                    else base.get(k, st.session_state.get(k)))
                for k in todas_chaves
            }
            ok = save_evolucao(prontuario, st.session_state.get("nome", "").strip(), dados)
        if ok:
            _msg_salvar.success(f"✅ Salvo com sucesso! Prontuário: {prontuario}")
        else:
            _msg_salvar.error("❌ Erro ao salvar. Verifique a conexão.")

