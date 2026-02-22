import streamlit as st

def get_campos():
    return {
        'hmpa_texto':     '',
        'hmpa_reescrito': ''
    }

def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-5"></span>', unsafe_allow_html=True)
    st.markdown("##### 5. História da Moléstia Pregressa Atual")

    with st.container(border=True):
        st.caption("Texto extraído do prontuário")
        st.text_area(
            "hmpa_texto_label",
            key="hmpa_texto",
            height=120,
            placeholder="Texto fatiado pela IA (ou cole manualmente)...",
            label_visibility="collapsed"
        )
    if _agent_btn_callback: _agent_btn_callback()

    with st.container(border=True):
        st.caption("Texto reescrito pelo agente")
        st.text_area(
            "hmpa_reescrito_label",
            key="hmpa_reescrito",
            height=120,
            placeholder="A IA irá reescrever a HMA/HMP aqui após aplicar o agente...",
            label_visibility="collapsed"
        )
