import streamlit as st

# 1. Definição das Variáveis (8 Slots Total)
def get_campos():
    campos = {}
    for i in range(1, 9):
        campos.update({
            f'cult_{i}_sitio': '',
            f'cult_{i}_data': '',
            # Padrão alterado para corresponder à primeira opção solicitada
            f'cult_{i}_status': 'Parcial Negativo', 
            f'cult_{i}_micro': '',
            f'cult_{i}_sensib': '',
            f'cult_{i}_check': False, 
            f'cult_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de cultura
def _render_linha(i):
    with st.container(border=True):
        # LINHA 1: Sítio | Data | Checkbox
        c1, c2, c3 = st.columns([3, 1.2, 1.5], vertical_alignment="center")
        
        with c1:
            st.text_input(f"Material / Sítio #{i}", key=f"cult_{i}_sitio", placeholder="Ex: Hemocultura, Urocultura")
        with c2:
            st.text_input(f"Data Coleta", key=f"cult_{i}_data", placeholder="DD/MM")
        with c3:
            st.checkbox(f"✅ Checado Hoje", key=f"cult_{i}_check")

        # LINHA 2: Status (Ordem Reajustada)
        st.markdown(f"<small style='color:#666'>Status da Cultura #{i}</small>", unsafe_allow_html=True)
        st.radio(
            f"Status #{i}", 
            # AQUI ESTÁ A MUDANÇA DA ORDEM:
            ["Parcial Negativo", "Pendente", "Negativa", "Positiva"], 
            key=f"cult_{i}_status", 
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.write("") 

        # LINHA 3: Micro-organismo | Sensibilidade
        m1, m2 = st.columns([2, 2])
        with m1:
            st.text_input(f"Micro-organismo Isolado #{i}", key=f"cult_{i}_micro", placeholder="Ex: K. pneumoniae KPC+")
        with m2:
            st.text_input(f"Perfil Sensibilidade #{i}", key=f"cult_{i}_sensib", placeholder="Ex: Sensível a Polimixina B")

        # LINHA 4: Conduta
        with st.success(f"👉 Conduta #{i}"):
            st.text_input(
                "Conduta", 
                key=f"cult_{i}_conduta", 
                label_visibility="collapsed", 
                placeholder="Ex: Escalonar antibiótico..."
            )

# 2. Renderização Principal
def render():
    st.markdown("##### 7. Culturas & Resultados")
    
    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i)
        
    # --- 4 Itens OCULTOS ---
    st.write("")
    with st.expander("➕ Ver mais Culturas (Slots 5 a 8)"):
        for i in range(5, 9):
            _render_linha(i)