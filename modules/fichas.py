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
    
    # --- CSS: ESTILO ÚNICO "AMARELO PROFISSIONAL" (UNIFICADO) ---
    st.markdown("""
    <style>
        /* ================= GERAL ================= */
        [data-testid="stExpander"] { 
            border: none !important; 
            box-shadow: none !important; 
            background: transparent !important;
        }
        
        [data-testid="stExpander"] details {
            border-radius: 8px !important;
            border: 1px solid #e5e7eb !important;
            background-color: #ffffff;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            margin-bottom: 0px !important; 
        }

        /* Texto do Título */
        [data-testid="stExpander"] details summary p {
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            margin: 0 !important;
        }
        
        /* Base da Barra de Título (Fallback) */
        [data-testid="stExpander"] details summary {
            background-color: #f9fafb !important;
            padding: 1rem 1.2rem !important;
            transition: all 0.2s ease;
            border-left: 6px solid #ccc; 
        }

        /* ================= A MÁGICA DO AMARELO ================= */
        /* Aplica o estilo a qualquer expander precedido pela tag .yellow-tag */
        
        /* 1. Borda Lateral Amarela (Âmbar Suave) */
        div:has(.yellow-tag) + div details summary {
            border-left-color: #f59e0b !important; /* Âmbar 500 */
        }
        
        /* 2. Texto Marrom/Dourado (Legível) */
        div:has(.yellow-tag) + div details summary p {
            color: #92400e !important; /* Âmbar 800 */
        }
        
        /* 3. Ícone da Seta Amarelo */
        div:has(.yellow-tag) + div details summary svg {
            fill: #f59e0b !important; 
            color: #f59e0b !important;
        }
        
        /* 4. Fundo ao passar o mouse ou abrir (Creme Suave) */
        div:has(.yellow-tag) + div details[open] summary,
        div:has(.yellow-tag) + div details:hover summary {
            background-color: #fffbeb !important; /* Âmbar 50 */
        }

    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # 1. DADOS DO PACIENTE
    # ==========================================
    st.markdown('<div class="yellow-tag" style="display:none;"></div>', unsafe_allow_html=True)
    with st.expander("Dados do Paciente", expanded=False):
        st.caption("Dados estáticos de entrada.")
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
    # Marcador AMARELO
    st.markdown('<div class="yellow-tag" style="display:none;"></div>', unsafe_allow_html=True)
    
    # Título Alterado: "Dados Clínicos"
    with st.expander("Evolução Horizontal", expanded=False):
        st.caption("Visão longitudinal: Dispositivos, Infectologia e Exames Complementares.")
        
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
    st.markdown('<div class="yellow-tag" style="display:none;"></div>', unsafe_allow_html=True)
    with st.expander("Evolução Diária", expanded=True):
        st.caption("Rotina de hoje.")
        
        laboratoriais.render()      
        st.write("")
        evolucao_clinica.render()   
        st.write("")
        sistemas.render()           
        st.write("")
        condutas.render()
