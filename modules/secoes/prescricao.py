import streamlit as st


def get_campos():
    return {
        'prescricao_bruta': '',
        'prescricao_formatada': '',
        'prescricao_conduta': '',
    }


def render():
    """Renderiza o bloco 14 — Prescrição (dentro do st.form)."""
    st.markdown('<span id="sec-14"></span>', unsafe_allow_html=True)
    st.markdown("##### 14. Prescrição")

    with st.container(border=True):
        st.text_area(
            "Prescrição não padronizada (cole aqui)",
            key="prescricao_bruta",
            height=120,
            placeholder="Cole aqui a prescrição bruta/não padronizada...",
            label_visibility="collapsed",
        )

        st.text_area(
            "Prescrição formatada",
            key="prescricao_formatada",
            height=120,
            placeholder="A prescrição formatada aparecerá aqui após clicar em Extrair Prescrição...",
            label_visibility="collapsed",
        )

        st.form_submit_button(
            "Extrair Prescrição",
            use_container_width=True,
            help="Formata a prescrição colada acima usando IA",
            on_click=_marcar_pendente,
        )

        st.text_input(
            "Conduta",
            key="prescricao_conduta",
            placeholder="Escreva a conduta aqui...",
            label_visibility="collapsed",
        )


def _marcar_pendente():
    st.session_state["_prescricao_extrair_pendente"] = True
