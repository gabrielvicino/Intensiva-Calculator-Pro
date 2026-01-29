import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    return {
        'compl_texto': '',
        'compl_conduta': ''
    }

# 2. Renderização Principal
def render():
    st.markdown("##### 9. Complementares")
    
    with st.container(border=True):
        # Bloco único para descrição
        st.text_area(
            "Descrição dos Exames / Laudos Relevantes",
            key="compl_texto",
            height=150, 
            placeholder="Descreva aqui os exames de imagem, biópsias ou outros achados relevantes..."
        )
        
        # Conduta em linha única (com destaque verde)
        with st.success("👉 Conduta"):
            st.text_input(
                "Conduta", 
                key="compl_conduta", 
                label_visibility="collapsed",
                placeholder="Ex: Solicitar avaliação da especialidade..."
            )