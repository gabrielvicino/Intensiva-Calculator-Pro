import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    campos = {
        'muc_notas': '',
        'muc_adesao_global': None
    }
    for i in range(1, 21):
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
        st.session_state.muc_ordem = list(range(1, 21))

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
        # Título com botões de reordenação
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        
        with col_titulo:
            st.markdown(f"**Medicação {idx_display}**")
        
        with col_up:
            if idx_display > 1:
                st.form_submit_button("↑", key=f"muc_up_{idx_display}", help="Mover para cima",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display-2))

        with col_down:
            if idx_display < 20:
                st.form_submit_button("↓", key=f"muc_down_{idx_display}", help="Mover para baixo",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display))
        
        c1, c2, c3 = st.columns([3, 1, 1.2], vertical_alignment="bottom")
        
        with c1:
            st.text_input(f"Medicamento {idx_display}", key=f"muc_{id_real}_nome", placeholder="Exemplo: Enalapril")
        with c2:
            st.text_input(f"Dose {idx_display}", key=f"muc_{id_real}_dose", placeholder="Exemplo: 20mg")
        with c3:
            st.text_input(f"Frequência {idx_display}", key=f"muc_{id_real}_freq", placeholder="Exemplo: 12/12h")
        
        st.text_input(f"Conduta {idx_display}", key=f"muc_{id_real}_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-4"></span>', unsafe_allow_html=True)
    st.markdown("##### 4. Medicações de Uso Contínuo")
    
    st.text_area("Notas", key="muc_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()
    
    # Inicializa ordem
    _inicializar_ordem()
    ordem = st.session_state.muc_ordem
    
    with st.container(border=True):
        # --- CONFIGURAÇÃO GLOBAL DE ADESÃO (NO TOPO) ---
        st.markdown("**Uso de Medicação:**")
        st.pills(
            "Adesão Global",
            ["Uso Regular", "Uso Irregular", "Desconhecido"],
            key="muc_adesao_global",
            label_visibility="collapsed"
        )
    
    st.write("")
    
    # --- 3 Itens VISÍVEIS ---
    for i in range(1, 4):
        _render_linha(i, ordem[i-1])
        
    # --- 17 Itens OCULTOS (abre automaticamente se houver conteúdo) ---
    st.write("")

    tem_conteudo = False
    for i in range(4, 21):
        id_real = ordem[i-1]
        if (st.session_state.get(f"muc_{id_real}_nome", "") or
                st.session_state.get(f"muc_{id_real}_dose", "") or
                st.session_state.get(f"muc_{id_real}_conduta", "")):
            tem_conteudo = True
            break

    with st.expander("Demais Medicações de Uso Contínuo", expanded=tem_conteudo):
        for i in range(4, 21):
            _render_linha(i, ordem[i-1])