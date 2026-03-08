# ==============================================================================
# modules/pacer/tab_prescricao.py
# Renderiza a aba "💊 Prescrição" da página Laboratoriais & Controles.
# ==============================================================================

import streamlit as st
from utils import verificar_rate_limit

from .ia import processar_multi_agente_prescricao, limpar_campos


def render(motor: str, api_key: str, modelo: str):
    """
    Renderiza a aba de extração multi-agente de prescrição médica.

    Parâmetros
    ----------
    motor   : "Google Gemini" ou "OpenAI GPT"
    api_key : chave da API ativa
    modelo  : nome do modelo escolhido na sidebar
    """
    st.subheader("💊 Pacer - Prescrição Médica")

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
