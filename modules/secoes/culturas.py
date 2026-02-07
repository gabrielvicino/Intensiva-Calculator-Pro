import streamlit as st

# 1. Definição das Variáveis (8 Slots Total)
def get_campos():
    campos = {}
    for i in range(1, 9):
        campos.update({
            f'cult_{i}_sitio': '',
            f'cult_{i}_data_coleta': '',
            f'cult_{i}_data_resultado': '',
            f'cult_{i}_status': 'Pendente negativo', 
            f'cult_{i}_micro': '',
            f'cult_{i}_sensib': '',
            f'cult_{i}_check': False, 
            f'cult_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de cultura
def _render_linha(i):
    with st.container(border=True):
        st.markdown(f"**Cultura {i}**")
        
        # LINHA 1: Sítio | Data Coleta | Data Resultado | Checkbox
        c1, c2, c3, c4 = st.columns([2.5, 1.2, 1.2, 1.2], vertical_alignment="bottom")
        
        with c1:
            st.text_input(f"Sítio {i}", key=f"cult_{i}_sitio", placeholder="Exemplo: Hemocultura, Urocultura")
        with c2:
            st.text_input(f"Data da Coleta", key=f"cult_{i}_data_coleta", placeholder="dd/mm/aaaa")
        with c3:
            st.text_input(f"Data do Resultado", key=f"cult_{i}_data_resultado", placeholder="dd/mm/aaaa")
        with c4:
            st.checkbox(f"✅ Checado Hoje", key=f"cult_{i}_check")

        # LINHA 2: Status da Cultura
        st.markdown(f"<small style='color:#666'>Status da Cultura:</small>", unsafe_allow_html=True)
        st.radio(
            f"Status {i}", 
            ["Pendente negativo", "Negativo", "Positivo Aguarda Antibiograma", "Positivo com Antibiograma"], 
            key=f"cult_{i}_status", 
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.write("") 

        # LINHA 3: Micro-organismo | Sensibilidade
        m1, m2 = st.columns([2, 2])
        with m1:
            st.text_input(f"Micro-organismo Isolado {i}", key=f"cult_{i}_micro", placeholder="Exemplo: K. pneumoniae KPC+")
        with m2:
            st.text_input(f"Perfil Sensibilidade {i}", key=f"cult_{i}_sensib", placeholder="Exemplo: Sensível a Polimixina B")

        # LINHA 4: Conduta (com borda verde)
        st.markdown(f"**Conduta {i}:**")
        st.markdown(
            f"""
            <style>
            div[data-testid="stTextInput"] input[placeholder*="Escalonar"] {{
                border-left: 4px solid #28a745 !important;
                padding-left: 12px !important;
            }}
            input[type="text"][id*="cult_{i}_conduta"] {{
                border-left: 4px solid #28a745 !important;
                padding-left: 12px !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        st.text_input(
            "Conduta", 
            key=f"cult_{i}_conduta", 
            label_visibility="collapsed", 
            placeholder="Exemplo: Escalonar antibiótico..."
        )

# 2. Renderização Principal
def render():
    st.markdown("##### 7. Culturas")
    
    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i)
        
    # --- 4 Itens OCULTOS (abre automaticamente se houver conteúdo) ---
    st.write("")
    
    # Verifica se há conteúdo nas culturas 5 a 8
    tem_conteudo = False
    for i in range(5, 9):
        if (st.session_state.get(f"cult_{i}_sitio", "") or 
            st.session_state.get(f"cult_{i}_micro", "") or 
            st.session_state.get(f"cult_{i}_conduta", "")):
            tem_conteudo = True
            break
    
    with st.expander("Demais Culturas", expanded=tem_conteudo):
        for i in range(5, 9):
            _render_linha(i)