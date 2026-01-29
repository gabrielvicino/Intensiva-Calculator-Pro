import streamlit as st

def get_campos():
    return {
        'evolucao_texto': ''
    }

def render():
    st.markdown("##### 11. Evolução Clínica (Texto Livre)")
    
    with st.container(border=True):
        st.text_area(
            "Narrativa (S.O.A.P.)",
            key="evolucao_texto",
            height=250, 
            placeholder="Descreva a evolução do paciente, intercorrências da noite, exame físico geral..."
        )