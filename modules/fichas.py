import streamlit as st
from modules import ui

# --- IMPORTAÇÃO DAS SEÇÕES ---
from modules.secoes import identificacao      # 1
from modules.secoes import hd                 # 2
from modules.secoes import comorbidades       # 3
from modules.secoes import muc                # 4
from modules.secoes import hmpa               # 5
from modules.secoes import dispositivos       # 6
from modules.secoes import culturas           # 7
from modules.secoes import antibioticos       # 8
from modules.secoes import complementares     # 9
from modules.secoes import laboratoriais      # 10
from modules.secoes import evolucao_clinica   # 11
from modules.secoes import sistemas           # 12
from modules.secoes import condutas           # 13

def inicializar_estado():
    campos = {}
    
    # Carrega variáveis
    campos.update(identificacao.get_campos())
    campos.update(hd.get_campos())
    campos.update(comorbidades.get_campos())
    campos.update(muc.get_campos())
    campos.update(hmpa.get_campos())
    campos.update(dispositivos.get_campos())
    campos.update(culturas.get_campos())
    campos.update(antibioticos.get_campos())
    campos.update(complementares.get_campos())
    campos.update(laboratoriais.get_campos())
    campos.update(evolucao_clinica.get_campos())
    campos.update(sistemas.get_campos())
    campos.update(condutas.get_campos())
    
    campos.update({'texto_final_gerado': ''})
    
    for k, v in campos.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_formulario_completo():
    
    # --- CSS: ESTILO DISCRETO PARA EXPANDERS E DESTAQUE VERDE PARA CONDUTAS ---
    st.markdown("""
    <style>
        /* ================= EXPANDERS DISCRETOS ================= */
        [data-testid="stExpander"] { 
            border: none !important; 
            box-shadow: none !important; 
            background: transparent !important;
        }
        
        [data-testid="stExpander"] details {
            border-radius: 4px !important;
            border: 1px solid #f0f0f0 !important;
            background-color: #fafafa;
            box-shadow: none;
            margin-bottom: 8px !important; 
        }

        /* Texto do Título - Menor e mais discreto */
        [data-testid="stExpander"] details summary p {
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            margin: 0 !important;
            color: #666 !important;
        }
        
        /* Base da Barra de Título - Mais compacta */
        [data-testid="stExpander"] details summary {
            background-color: transparent !important;
            padding: 0.6rem 0.8rem !important;
            transition: all 0.15s ease;
            border-left: 3px solid #e8e8e8; 
            min-height: auto !important;
        }
        
        /* Hover sutil */
        [data-testid="stExpander"] details:hover summary {
            background-color: #f5f5f5 !important;
        }
        
        /* ================= DESTAQUE VERDE PARA CONDUTAS ================= */
        /* Estiliza containers de sucesso (st.success) que contêm condutas */
        [data-testid="stAlert"][data-baseweb="notification"] {
            background-color: #e8f5e9 !important;
            border-left: 4px solid #4caf50 !important;
            padding: 0.5rem 0.75rem !important;
        }
        
        /* Inputs dentro de containers de sucesso */
        [data-testid="stAlert"] input,
        [data-testid="stAlert"] textarea {
            background-color: #f1f8f4 !important;
            border: 1px solid #81c784 !important;
        }
        
        [data-testid="stAlert"] input:focus,
        [data-testid="stAlert"] textarea:focus {
            border-color: #4caf50 !important;
            box-shadow: 0 0 0 1px #4caf50 !important;
        }

    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # 1. DADOS DO PACIENTE
    # ==========================================
    with st.expander("Dados do Paciente", expanded=False):
        identificacao.render()      
        st.write("") 
        hd.render()                 
        st.write("")
        comorbidades.render()       
        st.write("")
        muc.render()                
        st.write("")
        hmpa.render()               
        st.write("")
    
    st.write("") # Espaço visual

    # ==========================================
    # 2. DADOS CLÍNICOS
    # ==========================================
    with st.expander("Evolução Horizontal", expanded=False):
        dispositivos.render()       
        st.write("")
        culturas.render()           
        st.write("")
        antibioticos.render()       
        st.write("")
        complementares.render()     
        st.write("")

    st.write("") # Espaço visual

    # ==========================================
    # 3. EVOLUÇÃO DIÁRIA
    # ==========================================
    with st.expander("Evolução Diária", expanded=True):
        laboratoriais.render()      
        st.write("")
        evolucao_clinica.render()   
        st.write("")
        sistemas.render()           
        st.write("")
        condutas.render()
