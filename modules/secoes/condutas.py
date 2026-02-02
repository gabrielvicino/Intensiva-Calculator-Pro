import streamlit as st

def get_campos():
    return {
        'conduta_final_lista': '',
        'conduta_pendencias': ''
    }

def render():
    st.markdown("##### 13. Plano Terapêutico & Condutas")
    
    with st.container(border=True):
        st.text_area(
            "Listar condutas para hoje (uma por linha)", 
            key="conduta_final_lista", 
            height=150,
            placeholder="1. Manter antibiótico (D3/10)\n2. Desmame da ventilação mecânica\n3. Solicitar Parecer Cardiologia"
        )
        
        st.markdown("**Pendências / Checagens**")
        st.text_input(
            "O que não pode ser esquecido?", 
            key="conduta_pendencias", 
            placeholder="Ex: Cobrar resultado da TC, Checar cultura..."
        )