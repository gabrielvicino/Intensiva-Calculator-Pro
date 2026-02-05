import streamlit as st

# ==============================================================================
# CONFIGURAÇÃO GERAL
# ==============================================================================
st.set_page_config(
    page_title="Intensiva Calculator",
    page_icon="⚕️",
    layout="wide"
)

# ==============================================================================
# SISTEMA DE AUTENTICAÇÃO SIMPLES
# ==============================================================================
PIN_CORRETO = "7894"

def verificar_autenticacao():
    """
    Verifica se o usuário está autenticado.
    Se não estiver, mostra tela de login simples com PIN.
    """
    # Inicializa estado de autenticação
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    
    # Se já está autenticado, retorna True
    if st.session_state.autenticado:
        return True
    
    # Tela de login
    st.markdown("""
        <div style='text-align: center; padding: 100px 20px;'>
            <h1 style='color: #1f77b4;'>⚕️ Intensiva Calculator</h1>
            <p style='font-size: 18px; color: #666; margin-top: 20px;'>
                Sistema de Apoio à Decisão Clínica
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Centraliza o formulário
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("### 🔒 Acesso Restrito")
        st.info("Digite o PIN para acessar o sistema")
        
        pin_digitado = st.text_input(
            "PIN de Acesso:",
            type="password",
            max_chars=4,
            placeholder="••••",
            label_visibility="collapsed"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("🔓 Acessar", type="primary", use_container_width=True):
                if pin_digitado == PIN_CORRETO:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("❌ PIN incorreto. Tente novamente.")
        
        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; font-size: 0.8rem; color: #808495; white-space: nowrap;'>"
            "Sistema desenvolvido para uso interno por <em>Dr. Gabriel Valladão Vicino - CRM-SP 223.216</em>"
            "</p>",
            unsafe_allow_html=True
        )
    
    return False

# Verifica autenticação antes de carregar a aplicação
if not verificar_autenticacao():
    st.stop()  # Para a execução se não estiver autenticado

# ==============================================================================
# SISTEMA DE NAVEGAÇÃO (ROUTER)
# ==============================================================================
pg = st.navigation({
    "Principal": [
        st.Page("views/home.py", title="Home", icon="⚕️", default=True),
    ],
    "Ferramentas Clínicas": [
        st.Page("views/infusao.py", title="Infusão Contínua", icon="💉"),
        st.Page("views/intubacao.py", title="Intubação Orotraqueal", icon="⚡"),
        st.Page("views/conversao.py", title="Conversor Universal", icon="🔄"),
        st.Page("views/pacer.py", title="Pacer - Exames & Prescrição", icon="📃"),
        # --- PÁGINA NOVA ---
        st.Page("views/evolucao.py", title="[EM CONSTRUÇÃO] Evolução Diária", icon="🚧"),
        # -------------------
        st.Page("views/calculadoras.py", title="[EM CONSTRUÇÃO] Calculadoras Médicas", icon="🚧"),
    ],
})

# ==============================================================================
# EXECUÇÃO
# ==============================================================================
pg.run()