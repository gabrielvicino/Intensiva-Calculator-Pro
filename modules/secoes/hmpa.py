import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    return {
        'hmpa_texto': ''
    }

# 2. Renderização Visual
def render():
    st.markdown("##### 5. HMPA / Internação Atual")
    
    with st.container(border=True):
        st.text_area(
            "História da Moléstia Pregressa e Atual",
            key="hmpa_texto",
            height=120,
            placeholder="Ex: Paciente deu entrada no PS com quadro de dispneia há 3 dias..."
        )
