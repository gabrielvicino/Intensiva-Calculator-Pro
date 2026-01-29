import streamlit as st

# 1. Definição das Variáveis (8 Slots Total)
def get_campos():
    campos = {}
    for i in range(1, 9):
        campos.update({
            f'disp_{i}_nome': '',
            f'disp_{i}_desc': '',
            f'disp_{i}_data': '',
            f'disp_{i}_origem': 'Interno',
            f'disp_{i}_status': 'Ativo',
            f'disp_{i}_data_fim': '', # <--- NOVO CAMPO (Data ao lado do status)
            f'disp_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de dispositivo
def _render_linha(i):
    with st.container(border=True):
        # LINHA 1: Dados Técnicos
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1.5], vertical_alignment="center")
        
        with c1:
            st.text_input(f"Dispositivo #{i}", key=f"disp_{i}_nome", placeholder="Ex: CVC, PAM")
        with c2:
            st.text_input(f"Descrição/Local #{i}", key=f"disp_{i}_desc", placeholder="Ex: Jugular D")
        with c3:
            st.text_input(f"Data Ins.", key=f"disp_{i}_data", placeholder="DD/MM")
        with c4:
            st.radio(
                f"Inserção #{i}", 
                ["Interno", "Externo"], 
                key=f"disp_{i}_origem",
                horizontal=True
            )

        # LINHA 2: Status | Data (Novo) | Conduta
        # Dividi o espaço para caber a data ao lado do status
        s1, s2, s3 = st.columns([1.6, 1.2, 3], vertical_alignment="center")
        
        with s1:
            st.radio(
                f"Status #{i}", 
                ["Ativo", "Removido"], 
                key=f"disp_{i}_status", 
                horizontal=True,
                label_visibility="collapsed"
            )
            
        with s2:
            # Novo campo de data
            st.text_input(
                "Data Status", 
                key=f"disp_{i}_data_fim", 
                placeholder="Data", 
                label_visibility="collapsed" # Fica alinhado com o botão
            )

        with s3:
            with st.success(f"👉 Conduta #{i}"):
                st.text_input(
                    "Conduta", 
                    key=f"disp_{i}_conduta", 
                    label_visibility="collapsed", 
                    placeholder="Ex: Manter, Trocar curativo..."
                )

# 2. Renderização Principal
def render():
    st.markdown("##### 6. Dispositivos Invasivos")
    
    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i)
        
    # --- 4 Itens OCULTOS ---
    st.write("")
    with st.expander("➕ Ver mais Dispositivos (Slots 5 a 8)"):
        for i in range(5, 9):
            _render_linha(i)