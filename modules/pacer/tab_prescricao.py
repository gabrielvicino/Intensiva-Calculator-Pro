# ==============================================================================
# modules/pacer/tab_prescricao.py
# Renderiza a aba "💊 Prescrição" da página Laboratoriais & Controles.
# ==============================================================================

import streamlit as st
from utils import verificar_rate_limit

from .ia import processar_multi_agente_prescricao, limpar_campos


# ==============================================================================
# Prontuário — busca e salvamento (espelho dos tabs Laboratoriais e Controles)
# ==============================================================================

@st.fragment
def _fragment_prontuario_presc() -> None:
    """Campo de prontuário + botão Buscar — compartilha estado com os demais tabs."""
    from utils import load_evolucao
    from modules import fichas

    # Sincroniza com o prontuário sempre que ele for atualizado externamente
    _pront_atual = st.session_state.get("prontuario", "")
    _last_sync   = st.session_state.get("_presc_pront_last_sync", None)
    if _pront_atual != _last_sync:
        st.session_state["_presc_pront_input"] = _pront_atual
        st.session_state["_presc_pront_last_sync"] = _pront_atual

    with st.form(key="form_busca_presc"):
        c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
        with c_input:
            busca_input = st.text_input(
                "Número do Prontuário",
                placeholder="Ex.: 1234567",
                key="_presc_pront_input",
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
                    _aplicar_dados_prontuario_presc(dados, fichas)
                    st.rerun()
                else:
                    st.session_state["_presc_pront_pendente"] = busca
                    st.rerun()


def _aplicar_dados_prontuario_presc(dados: dict, fichas_mod) -> None:
    """Aplica dados carregados ao session_state preservando valores não-vazios existentes."""
    if not dados:
        return
    data_hora = dados.pop("_data_hora", "")
    dados = fichas_mod.migrar_schema_legado(dados)
    campos_validos = set(fichas_mod.get_todos_campos_keys())
    for k, v in dados.items():
        if k in campos_validos:
            if v or not st.session_state.get(k):
                st.session_state[k] = v
    st.session_state["_data_hora_carregado"] = data_hora
    st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")


def _confirmar_novo_prontuario_presc() -> None:
    """Exibe opção de criar novo prontuário quando não encontrado."""
    from utils import save_evolucao

    if "_presc_pront_pendente" not in st.session_state:
        return

    pend = st.session_state["_presc_pront_pendente"]
    with st.container(border=True):
        st.markdown(
            f"**Prontuário {pend} não localizado.**  \n"
            "Nenhum registro encontrado. Deseja iniciar um novo prontuário?",
        )
        c_sim, c_nao, *_ = st.columns([2, 2, 8])
        with c_sim:
            if st.button(
                "Criar prontuário", type="primary",
                use_container_width=True, key="_presc_btn_criar",
            ):
                st.session_state.pop("_presc_pront_pendente", None)
                st.session_state["prontuario"] = pend
                with st.spinner("Registrando novo prontuário..."):
                    save_evolucao(pend, "", {"prontuario": pend})
                st.toast(f"Prontuário {pend} registrado com sucesso.", icon="✅")
                st.rerun()
        with c_nao:
            if st.button(
                "Cancelar", use_container_width=True, key="_presc_btn_cancelar_criar",
            ):
                st.session_state.pop("_presc_pront_pendente", None)
                st.rerun()


def render(motor: str, api_key: str, modelo: str):
    """
    Renderiza a aba de extração multi-agente de prescrição médica.

    Parâmetros
    ----------
    motor   : "Google Gemini" ou "OpenAI GPT"
    api_key : chave da API ativa
    modelo  : nome do modelo escolhido na sidebar
    """
    from utils import save_evolucao, load_evolucao
    from modules import fichas

    # ── Auto-load: recupera prescrição salva ao iniciar nova sessão ──────────
    _pront_autoload = st.session_state.get("prontuario", "").strip()
    _presc_vazia = not st.session_state.get("prescricao_formatada", "").strip()
    _ultimo_reload_presc = st.session_state.get("_presc_ultimo_reload", "")

    if _pront_autoload and _presc_vazia and _ultimo_reload_presc != _pront_autoload:
        with st.spinner("Carregando prescrição salva..."):
            _dados_autoload = load_evolucao(_pront_autoload)
        if _dados_autoload:
            _dados_autoload.pop("_data_hora", None)
            _dados_autoload = fichas.migrar_schema_legado(_dados_autoload)
            campos_validos = set(fichas.get_todos_campos_keys())
            for k, v in _dados_autoload.items():
                if k in campos_validos and (v or not st.session_state.get(k)):
                    st.session_state[k] = v
            if st.session_state.get("prescricao_formatada", "").strip():
                st.toast("Prescrição carregada do prontuário.", icon="💊")
        st.session_state["_presc_ultimo_reload"] = _pront_autoload

    st.subheader("💊 Pacer - Prescrição Médica")

    # ── Prontuário ────────────────────────────────────────────────────────────
    _fragment_prontuario_presc()
    _confirmar_novo_prontuario_presc()

    st.write("")
    prontuario = st.session_state.get("prontuario", "").strip()

    # Placeholder para mensagens de save — aparece acima do conteúdo
    _msg_salvar = st.empty()

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.markdown("**Entrada**")
        input_val = st.text_area(
            "Cole aqui:",
            height=300,
            key="input_presc",
            label_visibility="collapsed",
        )
        b_lim, b_proc = st.columns([1, 3])
        with b_lim:
            st.button(
                "Limpar",
                key="clr_input_presc",
                on_click=limpar_campos,
                args=(["input_presc", "output_presc"],),
            )
        with b_proc:
            processar = st.button(
                "✨ Processar",
                key="proc_input_presc",
                type="primary",
                use_container_width=True,
            )

    with col_out:
        st.markdown("**Resultado da Prescrição**")
        if processar:
            ok, msg = verificar_rate_limit()
            if not ok:
                st.error(msg)
            else:
                with st.spinner("Processando prescrição..."):
                    resultado = processar_multi_agente_prescricao(
                        motor, api_key, modelo, input_val
                    )
                    st.session_state["output_presc"] = resultado

        if st.session_state.get("output_presc"):
            res = st.session_state["output_presc"]
            if "❌" in res or "⚠️" in res:
                st.error(res)
            else:
                st.code(res, language="text")
        else:
            st.info("Aguardando entrada...")

    # ── Salvar tudo (Labs + Controles + Prescrição) ───────────────────────────
    st.divider()
    output_presc = st.session_state.get("output_presc", "")
    pode_salvar = bool(prontuario and output_presc
                       and "❌" not in output_presc and "⚠️" not in output_presc)

    if st.button(
        "💾 Salvar no Prontuário",
        type="primary",
        use_container_width=True,
        disabled=not prontuario,
        help=(
            "Salva prescrição processada, exames laboratoriais e controles & BH "
            "no prontuário ativo em uma única operação."
        ),
    ):
        if not output_presc:
            _msg_salvar.warning("⚠️ Nenhuma prescrição processada. Salvando apenas Labs e Controles...")
        elif "❌" in output_presc or "⚠️" in output_presc:
            _msg_salvar.error("❌ Prescrição com erro — não será salva. Salvando apenas Labs e Controles...")

        _msg_salvar.info("💾 Salvando...")
        with st.spinner("💾 Salvando..."):
            base = load_evolucao(prontuario) or {}
            base.pop("_data_hora", None)
            todas_chaves = fichas.get_todos_campos_keys()

            # Lab, Ctrl e Prescrição vêm do session_state; o resto preserva o último save
            dados = {}
            for k in todas_chaves:
                if k.startswith("lab_") or k.startswith("ctrl_") or k.startswith("prescricao_"):
                    dados[k] = st.session_state.get(k)
                else:
                    dados[k] = base.get(k, st.session_state.get(k))

            # Prescrição processada sobrescreve o campo formatado
            if pode_salvar:
                dados["prescricao_formatada"] = output_presc.strip()
                st.session_state["prescricao_formatada"] = output_presc.strip()

            ok = save_evolucao(
                prontuario,
                st.session_state.get("nome", "").strip(),
                dados,
            )

        if ok:
            _msg_salvar.success(
                f"✅ Salvo com sucesso! Prontuário: {prontuario}"
                + (" — Prescrição, Labs e Controles atualizados." if pode_salvar
                   else " — Labs e Controles atualizados.")
            )
        else:
            _msg_salvar.error("❌ Erro ao salvar. Verifique a conexão com o banco de dados.")
