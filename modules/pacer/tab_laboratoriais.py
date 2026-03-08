# ==============================================================================
# modules/pacer/tab_laboratoriais.py
# Renderiza a aba "🧪 Laboratoriais" da página Laboratoriais & Controles.
# ==============================================================================

import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.secoes import laboratoriais as _lab_sec
from modules.pacer.pdf_extractor import processar_texto_slot
from modules.parsers.lab import parse_lab_exames_dia
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
# Extração via IA — todos os slots simultaneamente
# ==============================================================================

def _extrair_com_ia(api_key: str, modelo: str) -> None:
    """
    Varre todos os slots (1–10), coleta os que têm texto e processa
    SIMULTANEAMENTE. Cada slot roda seus 7 agentes PACER em paralelo.
    """
    slots_com_texto = [
        s for s in range(1, 11)
        if (st.session_state.get(f"lab_{s}_texto_entrada") or "").strip()
    ]

    if not slots_com_texto:
        st.warning("⚠️ Cole o texto do laudo nos campos acima antes de extrair.")
        return

    entradas = {
        s: {
            "texto":      st.session_state.get(f"lab_{s}_texto_entrada", "").strip(),
            "data_atual": st.session_state.get(f"lab_{s}_data", ""),
        }
        for s in slots_com_texto
    }

    resultados_slots: dict[int, tuple[dict, int]] = {}

    def _processar(slot: int):
        e = entradas[slot]
        return slot, processar_texto_slot(
            slot, e["texto"], api_key, "OpenAI GPT", modelo, e["data_atual"]
        )

    with st.spinner(f"🔬 Extraindo {len(slots_com_texto)} laudo(s) simultaneamente..."):
        with ThreadPoolExecutor(max_workers=len(slots_com_texto)) as executor:
            futures = {executor.submit(_processar, s): s for s in slots_com_texto}
            for future in as_completed(futures):
                slot, resultado = future.result(timeout=120)
                resultados_slots[slot] = resultado

    total_campos = 0
    erros = []
    pending_campos: dict = {}
    pending_clear: list = []

    for slot in slots_com_texto:
        titulo = _TITULOS_SLOT.get(slot, f"Slot #{slot}")
        campos, n = resultados_slots.get(slot, ({}, 0))
        if n > 0:
            pending_campos.update(campos)
            pending_clear.append(slot)
            total_campos += n
            st.toast(f"✅ {titulo}: {n} campos preenchidos", icon="🧪")
        else:
            erros.append(f"{titulo}: nenhum campo extraído")

    # Armazena para aplicar no próximo rerun, antes dos widgets serem renderizados
    if pending_campos:
        st.session_state["_lab_pending_update"] = pending_campos
        st.session_state["_lab_pending_clear"] = pending_clear

    if erros:
        for erro in erros:
            st.warning(f"⚠️ {erro}")


# ==============================================================================
# render() — ponto de entrada da aba
# ==============================================================================

def render(api_key: str = "", modelo: str = "gpt-4o") -> None:
    """Renderiza a aba completa de Exames Laboratoriais."""
    from utils import save_evolucao, load_evolucao
    from modules import fichas

    # Aplica resultados pendentes de extração IA/parsing ANTES de renderizar widgets
    if "_lab_pending_update" in st.session_state:
        pending_update = st.session_state.pop("_lab_pending_update")
        pending_clear_slots = st.session_state.pop("_lab_pending_clear", [])
        # Limpa TODOS os campos do slot antes de aplicar os novos valores
        for slot in pending_clear_slots:
            for suf in _lab_sec._LAB_SUFIXOS:
                st.session_state[f"lab_{slot}_{suf}"] = ""
            st.session_state[f"lab_{slot}_texto_entrada"] = ""
        for k, v in pending_update.items():
            st.session_state[k] = v

    st.subheader("🧪 Exames Laboratoriais")

    # ── Prontuário ────────────────────────────────────────────────────────────
    _fragment_prontuario()
    _confirmar_novo_prontuario()

    st.write("")

    prontuario = st.session_state.get("prontuario", "").strip()

    # Placeholder para mensagens de save — aparece acima do formulário
    _msg_salvar = st.empty()

    # ── Form principal — sem rerender ao digitar ──────────────────────────────
    with st.form("form_laboratoriais_main"):
        b1, b2, b3, b4 = st.columns(4)
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
            btn_parse = st.form_submit_button(
                "Parsing Exames", use_container_width=True,
                help=(
                    "Extrai exames do texto colado em cada coluna.\n"
                    "Formato: DD/MM/YYYY – Hb 8,2 | Ht 25% | Cr 1,3 | ...\n"
                    "Linhas de continuação e gasometria (Gas Ven/Art ...) são reconhecidas automaticamente."
                ),
            )
        with b4:
            btn_salvar = st.form_submit_button(
                "💾 Salvar no Prontuário", use_container_width=True,
                type="primary", disabled=not prontuario,
                help="Salva todos os campos no Google Sheets",
            )

        # Tabela principal: slots 1–4
        _lab_sec._render_day_headers([1, 2, 3, 4])
        _render_texto_entrada([1, 2, 3, 4])
        _lab_sec._render_labs_table([1, 2, 3, 4], show_header=False)
        _lab_sec._render_gas_extras([1, 2, 3, 4])

        # Demais exames: slots 5–10
        with st.expander("Demais exames", expanded=False):
            _lab_sec._render_day_headers([5, 6, 7, 8, 9, 10])
            _render_texto_entrada([5, 6, 7, 8, 9, 10])
            _lab_sec._render_labs_table([5, 6, 7, 8, 9, 10], show_header=False)
            _lab_sec._render_gas_extras([5, 6, 7, 8, 9, 10])

    # ── Handlers (fora do form, após submissão) ───────────────────────────────
    if btn_evo:
        _lab_sec._deslocar_laboratoriais()
        st.toast("✅ Resultados deslocados.", icon="✅")
        st.rerun()

    if btn_parse:
        slots_com_texto = [
            s for s in range(1, 11)
            if (st.session_state.get(f"lab_{s}_texto_entrada") or "").strip()
        ]
        if not slots_com_texto:
            st.warning("⚠️ Cole o laudo nos campos de texto de cada coluna antes de parsear.")
        else:
            def _parse_slot(slot: int):
                texto = st.session_state.get(f"lab_{slot}_texto_entrada", "").strip()
                return slot, parse_lab_exames_dia(texto, slot)

            with st.spinner(f"🔬 Parseando {len(slots_com_texto)} coluna(s)..."):
                with ThreadPoolExecutor(max_workers=len(slots_com_texto)) as ex:
                    futures = {ex.submit(_parse_slot, s): s for s in slots_com_texto}
                    resultados = {}
                    for fut in as_completed(futures):
                        slot, dados = fut.result()
                        resultados[slot] = dados

            total = 0
            pending_parse: dict = {}
            pending_parse_clear: list = []
            for slot, dados in resultados.items():
                n = len([v for v in dados.values() if v])
                titulo = _TITULOS_SLOT.get(slot, f"Slot #{slot}")
                if n:
                    pending_parse.update(dados)
                    pending_parse_clear.append(slot)
                    total += n
                    st.toast(f"✅ {titulo}: {n} campos preenchidos", icon="🧪")
                else:
                    st.warning(f"⚠️ {titulo}: nenhum valor reconhecido. Verifique o formato.")
            if total:
                st.session_state["_lab_pending_update"] = pending_parse
                st.session_state["_lab_pending_clear"] = pending_parse_clear
                st.rerun()

    if btn_extrair:
        _extrair_com_ia(api_key, modelo)
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

