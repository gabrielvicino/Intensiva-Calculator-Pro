import streamlit as st

# 1. Definição das Variáveis (8 Slots Total)
def get_campos():
    campos = {}
    for i in range(1, 9):
        campos.update({
            f'disp_{i}_nome': '',
            f'disp_{i}_local': '',
            f'disp_{i}_data_insercao': '',
            f'disp_{i}_data_retirada': '',
            f'disp_{i}_status': 'Ativo',
            f'disp_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de dispositivo
def _render_linha(i):
    with st.container(border=True):
        st.markdown(f"**Dispositivo {i}**")
        
        # LINHA 1: Dispositivo | Local | Data Inserção | Data Retirada
        c1, c2, c3, c4 = st.columns([2, 2, 1.2, 1.2], vertical_alignment="bottom")
        
        with c1:
            st.text_input(f"Dispositivo {i}", key=f"disp_{i}_nome", placeholder="Exemplo: CVC, PAM, SVD")
        with c2:
            st.text_input(f"Local {i}", key=f"disp_{i}_local", placeholder="Exemplo: Jugular Direita")
        with c3:
            st.text_input(f"Data da Inserção", key=f"disp_{i}_data_insercao", placeholder="dd/mm/aaaa")
        with c4:
            st.text_input(f"Data da Retirada", key=f"disp_{i}_data_retirada", placeholder="dd/mm/aaaa")

        # LINHA 2: Status | Conduta (tudo alinhado)
        s1, s2 = st.columns([1.5, 4], vertical_alignment="center")
        
        with s1:
            st.radio(
                f"Status {i}", 
                ["Ativo", "Removido"], 
                key=f"disp_{i}_status", 
                horizontal=True,
                label_visibility="collapsed"
            )

        with s2:
            st.markdown(f"**Conduta {i}:**")
            st.markdown(
                f"""
                <style>
                div[data-testid="stTextInput"] input[placeholder*="Trocar"] {{
                    border-left: 4px solid #28a745 !important;
                    padding-left: 12px !important;
                }}
                input[type="text"][id*="disp_{i}_conduta"] {{
                    border-left: 4px solid #28a745 !important;
                    padding-left: 12px !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
            st.text_input(
                "Conduta", 
                key=f"disp_{i}_conduta", 
                label_visibility="collapsed", 
                placeholder="Exemplo: Manter, Trocar curativo em 48h..."
            )

# 2. Renderização Principal
def render():
    st.markdown("##### 6. Dispositivos Invasivos")
    
    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i)
        
    # --- 4 Itens OCULTOS (abre automaticamente se houver conteúdo) ---
    st.write("")
    
    # Verifica se há conteúdo nos dispositivos 5 a 8
    tem_conteudo = False
    for i in range(5, 9):
        if (st.session_state.get(f"disp_{i}_nome", "") or 
            st.session_state.get(f"disp_{i}_local", "") or 
            st.session_state.get(f"disp_{i}_conduta", "")):
            tem_conteudo = True
            break
    
    with st.expander("Demais Dispositivos", expanded=tem_conteudo):
        for i in range(5, 9):
            _render_linha(i)