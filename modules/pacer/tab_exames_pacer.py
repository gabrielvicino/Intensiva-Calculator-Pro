# ==============================================================================
# modules/pacer/tab_exames_pacer.py
# Renderiza a aba "📋 Exames PACER" da página Laboratoriais & Controles.
# ==============================================================================

import streamlit as st
from utils import verificar_rate_limit

from .ia import processar_multi_agente, limpar_campos
from .prompts import AGENTES_EXAMES


def render(motor: str, api_key: str, modelo: str):
    """
    Renderiza a aba de extração multi-agente de exames laboratoriais.

    Parâmetros
    ----------
    motor   : "Google Gemini" ou "OpenAI GPT"
    api_key : chave da API ativa
    modelo  : nome do modelo escolhido na sidebar
    """
    st.subheader("🧪 Pacer - Exames Laboratoriais")

    agentes_ativos = list(AGENTES_EXAMES.keys())

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.markdown("**Entrada**")
        input_val = st.text_area(
            "Cole aqui:",
            height=300,
            key="input_exames",
            label_visibility="collapsed",
        )
        b_lim, b_proc = st.columns([1, 3])
        with b_lim:
            st.button(
                "Limpar",
                key="clr_input_exames",
                on_click=limpar_campos,
                args=(["input_exames", "output_exames", "output_analise"],),
            )
        with b_proc:
            processar = st.button(
                "✨ Processar",
                key="proc_input_exames",
                type="primary",
                use_container_width=True,
            )

    with col_out:
        st.markdown("**Resultado dos Exames**")
        if processar:
            ok, msg = verificar_rate_limit()
            if not ok:
                st.error(msg)
            else:
                with st.spinner("Processando exames laboratoriais..."):
                    resultado_exames, analise_clinica = processar_multi_agente(
                        motor,
                        api_key,
                        modelo,
                        agentes_ativos,
                        input_val,
                        executar_analise=st.session_state.get("usar_analise", False),
                    )
                    st.session_state["output_exames"] = resultado_exames
                    st.session_state["output_analise"] = (
                        analise_clinica
                        if st.session_state.get("usar_analise", False)
                        else ""
                    )

        # Exibição do resultado
        if st.session_state.get("output_exames"):
            res = st.session_state["output_exames"]
            if "❌" in res or "⚠️" in res:
                st.error(res)
            else:
                st.code(res, language="text")
        else:
            st.info("Aguardando entrada...")

        st.divider()
        st.session_state["usar_analise"] = st.checkbox(
            "🩺 Mostrar Análise Clínica (CDSS)",
            value=st.session_state.get("usar_analise", False),
            help="Gera hipóteses diagnósticas baseadas nos exames alterados",
        )

        if st.session_state.get("usar_analise"):
            analise = st.session_state.get("output_analise", "")
            if analise and len(analise.strip()) > 0:
                if "❌" in analise or "⚠️" in analise:
                    st.error(analise)
                else:
                    st.markdown(analise)
            elif st.session_state.get("output_exames"):
                st.warning("⚠️ Análise clínica não foi gerada. Verifique o terminal para logs.")
            else:
                st.info("Aguardando processamento ou sem dados alterados para análise.")
