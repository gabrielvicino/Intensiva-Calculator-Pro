import streamlit as st

# Função para gerenciar ordem dos dispositivos
def _inicializar_ordem():
    """Inicializa a ordem dos dispositivos se não existir"""
    if 'disp_ordem' not in st.session_state:
        st.session_state.disp_ordem = list(range(1, 9))

def _trocar_ordem(idx1, idx2):
    """Troca a ordem de exibição de dois dispositivos"""
    _inicializar_ordem()
    ordem = st.session_state.disp_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.disp_ordem = ordem

# 1. Definição das Variáveis (8 Slots Total)
def get_campos():
    campos = {'dispositivos_notas': ''}
    for i in range(1, 9):
        campos.update({
            f'disp_{i}_nome': '',
            f'disp_{i}_local': '',
            f'disp_{i}_data_insercao': '',
            f'disp_{i}_data_retirada': '',
            f'disp_{i}_status': None,
            f'disp_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de dispositivo
def _render_linha(idx_display, id_real):
    """
    Renderiza um card de dispositivo.
    idx_display: posição de exibição (1-8)
    id_real: ID real do dispositivo nos dados (1-8)
    """
    with st.container(border=True):
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        with col_titulo:
            st.markdown(f"**Dispositivo {idx_display}**")
        with col_up:
            if idx_display > 1:
                st.form_submit_button("↑", key=f"disp_up_{idx_display}", help="Mover para cima",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display-2))
        with col_down:
            if idx_display < 8:
                st.form_submit_button("↓", key=f"disp_down_{idx_display}", help="Mover para baixo",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display))
        c1, c2, c3, c4 = st.columns([2, 2, 1.2, 1.2], vertical_alignment="bottom")
        with c1:
            st.text_input(f"Dispositivo {idx_display}", key=f"disp_{id_real}_nome", placeholder="Exemplo: CVC, PAM, SVD")
        with c2:
            st.text_input(f"Local {idx_display}", key=f"disp_{id_real}_local", placeholder="Exemplo: Jugular Direita")
        with c3:
            st.text_input(f"Data da Inserção", key=f"disp_{id_real}_data_insercao", placeholder="dd/mm/aaaa")
        with c4:
            st.text_input(f"Data da Retirada", key=f"disp_{id_real}_data_retirada", placeholder="dd/mm/aaaa")
        st.pills(
            f"Status {idx_display}",
            ["Ativo", "Removido"],
            key=f"disp_{id_real}_status",
            label_visibility="collapsed"
        )
        st.text_input(
                f"Conduta {idx_display}",
                key=f"disp_{id_real}_conduta",
                placeholder="Escreva a conduta aqui...",
                label_visibility="collapsed"
            )

# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-6"></span>', unsafe_allow_html=True)
    st.markdown("##### 6. Dispositivos Invasivos")
    
    st.text_area("Notas", key="dispositivos_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()
    
    # Inicializa ordem
    _inicializar_ordem()
    ordem = st.session_state.disp_ordem
    
    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i, ordem[i-1])
        
    # --- 4 Itens OCULTOS (abre automaticamente se houver conteúdo) ---
    st.write("")
    
    # Verifica se há conteúdo nos dispositivos 5 a 8
    tem_conteudo = False
    for i in range(5, 9):
        id_real = ordem[i-1]
        if (st.session_state.get(f"disp_{id_real}_nome", "") or 
            st.session_state.get(f"disp_{id_real}_local", "") or 
            st.session_state.get(f"disp_{id_real}_conduta", "")):
            tem_conteudo = True
            break
    
    with st.expander("Demais Dispositivos", expanded=tem_conteudo):
        for i in range(5, 9):
            _render_linha(i, ordem[i-1])