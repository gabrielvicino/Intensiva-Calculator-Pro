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
        # --- NOVA PÁGINA ADICIONADA ---
        st.Page("views/calculadoras.py", title="Calculadoras Médicas [EM CONSTRUÇÃO]", icon="🖥️"),
    ],
})

# ==============================================================================
# EXECUÇÃO
# ==============================================================================
pg.run()