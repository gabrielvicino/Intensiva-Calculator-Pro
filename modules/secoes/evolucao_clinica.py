import streamlit as st

def get_campos():
    return {
        'evolucao_notas': ''
    }

def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-12"></span>', unsafe_allow_html=True)
    st.markdown("##### 12. Evolução Clínica")
    
    st.text_area("Notas", key="evolucao_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    if _agent_btn_callback: _agent_btn_callback()