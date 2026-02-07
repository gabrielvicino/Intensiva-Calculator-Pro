import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    campos = {
        # Campo Único Global de Adesão
        'muc_adesao_global': 'Uso Regular'
    }
    
    # 10 Slots para medicamentos (sem o campo 'uso' individual)
    for i in range(1, 11):
        campos.update({
            f'muc_{i}_nome': '',
            f'muc_{i}_dose': '',
            f'muc_{i}_freq': '',
            f'muc_{i}_conduta': ''
        })
    return campos

# Função para gerenciar ordem das medicações
def _inicializar_ordem():
    """Inicializa a ordem das medicações se não existir"""
    if 'muc_ordem' not in st.session_state:
        st.session_state.muc_ordem = list(range(1, 11))

def _trocar_ordem(idx1, idx2):
    """Troca a ordem de exibição de duas medicações"""
    _inicializar_ordem()
    ordem = st.session_state.muc_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.muc_ordem = ordem

# Função auxiliar para desenhar UM card de medicação
def _render_linha(idx_display, id_real):
    """
    Renderiza um card de medicação.
    idx_display: posição de exibição (1-10)
    id_real: ID real da medicação nos dados (1-10)
    """
    with st.container(border=True):
        # CSS compacto para borda verde
        st.markdown(f"<style>input[type='text'][id*='muc_{id_real}_conduta']{{border-left:4px solid #28a745!important;padding-left:12px!important}}div[data-testid='stTextInput'] input[placeholder*='Suspender']{{border-left:4px solid #28a745!important;padding-left:12px!important}}</style>", unsafe_allow_html=True)
        
        # Título com botões de reordenação
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        
        with col_titulo:
            st.markdown(f"**Medicação {idx_display}**")
        
        with col_up:
            if idx_display > 1:
                if st.button("↑", key=f"muc_up_pos_{idx_display}", help="Mover para cima"):
                    _trocar_ordem(idx_display-1, idx_display-2)
                    st.rerun()
        
        with col_down:
            if idx_display < 10:
                if st.button("↓", key=f"muc_down_pos_{idx_display}", help="Mover para baixo"):
                    _trocar_ordem(idx_display-1, idx_display)
                    st.rerun()
        
        c1, c2, c3 = st.columns([3, 1, 1.2], vertical_alignment="bottom")
        
        with c1:
            st.text_input(f"Medicamento {idx_display}", key=f"muc_{id_real}_nome", placeholder="Exemplo: Enalapril")
        with c2:
            st.text_input(f"Dose {idx_display}", key=f"muc_{id_real}_dose", placeholder="Exemplo: 20mg")
        with c3:
            st.text_input(f"Frequência {idx_display}", key=f"muc_{id_real}_freq", placeholder="Exemplo: 12/12h")
        
        st.text_input(f"Conduta {idx_display}", key=f"muc_{id_real}_conduta", placeholder="Exemplo: Manter, Suspender ou Ajustar")

# 2. Renderização Principal
def render():
    st.markdown("##### 4. Medicações de Uso Contínuo")
    
    # Inicializa ordem
    _inicializar_ordem()
    ordem = st.session_state.muc_ordem
    
    with st.container(border=True):
        # --- CONFIGURAÇÃO GLOBAL DE ADESÃO (NO TOPO) ---
        st.markdown("**Uso de Medicação:**")
        st.radio(
            "Adesão Global",
            ["Uso Regular", "Uso Irregular", "Desconhecido"],
            key="muc_adesao_global",
            horizontal=True,
            label_visibility="collapsed"
        )
    
    st.write("")
    
    # --- 3 Itens VISÍVEIS ---
    for i in range(1, 4):
        _render_linha(i, ordem[i-1])
        
    # --- 7 Itens OCULTOS (abre automaticamente se houver conteúdo) ---
    st.write("")
    
    # Verifica se há conteúdo nas medicações 4 a 10
    tem_conteudo = False
    for i in range(4, 11):
        id_real = ordem[i-1]
        if (st.session_state.get(f"muc_{id_real}_nome", "") or 
            st.session_state.get(f"muc_{id_real}_dose", "") or 
            st.session_state.get(f"muc_{id_real}_conduta", "")):
            tem_conteudo = True
            break
    
    with st.expander("Demais Medicações de Uso Contínuo", expanded=tem_conteudo):
        for i in range(4, 11):
            _render_linha(i, ordem[i-1])