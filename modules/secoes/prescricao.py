import streamlit as st


def get_campos():
    return {
        'prescricao_formatada': '',
        'prescricao_conduta': '',
    }


def render():
    """Renderiza o bloco 14 — Prescrição (dentro do st.form)."""
    st.markdown('<span id="sec-15"></span>', unsafe_allow_html=True)
    st.markdown("##### 15. Prescrição")

    st.caption(
        "Processe a prescrição na página **Laboratoriais & Controles → aba 💊 Prescrição** "
        "e salve para que o texto apareça aqui."
    )

    st.text_area(
        "Prescrição formatada",
        key="prescricao_formatada",
        height=200,
        placeholder="A prescrição processada no PACER aparecerá aqui após salvar...",
        label_visibility="collapsed",
    )

    st.text_input(
        "Conduta",
        key="prescricao_conduta",
        placeholder="Escreva a conduta aqui...",
        label_visibility="collapsed",
    )
