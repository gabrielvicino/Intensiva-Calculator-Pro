import streamlit as st

# Funções para gerenciar ordem dos exames complementares
def _inicializar_ordem():
    """Inicializa a ordem dos exames complementares se não existir"""
    if 'comp_ordem' not in st.session_state:
        st.session_state.comp_ordem = list(range(1, 9))

def _trocar_ordem(idx1, idx2):
    """Troca a ordem de exibição de dois exames"""
    _inicializar_ordem()
    ordem = st.session_state.comp_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.comp_ordem = ordem

# 1. Definição das Variáveis (8 Slots Total)
def get_campos():
    campos = {'complementares_notas': ''}
    for i in range(1, 9):
        campos.update({
            f'comp_{i}_exame': '',
            f'comp_{i}_data': '',
            f'comp_{i}_laudo': '',
            f'comp_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de exame complementar
def _render_linha(idx_display, id_real):
    """
    Renderiza um card de exame complementar.
    idx_display: posição de exibição (1-8)
    id_real: ID real do exame nos dados (1-8)
    """
    with st.container(border=True):
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        with col_titulo:
            st.markdown(f"**Exame Complementar {idx_display}**")
        with col_up:
            if idx_display > 1:
                st.form_submit_button("↑", key=f"comp_up_{idx_display}", help="Mover para cima",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display-2))
        with col_down:
            if idx_display < 8:
                st.form_submit_button("↓", key=f"comp_down_{idx_display}", help="Mover para baixo",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display))
        st.caption("Exame")
        ex_col, data_col = st.columns([3, 1])
        with ex_col:
            st.text_input(
                f"Exame {idx_display}",
                key=f"comp_{id_real}_exame",
                placeholder="Ex: Tomografia Computadorizada de Crânio Sem Contraste",
                label_visibility="collapsed"
            )
        with data_col:
            st.text_input(
                f"Data {idx_display}",
                key=f"comp_{id_real}_data",
                placeholder="DD/MM/AAAA",
                label_visibility="collapsed"
            )
        st.caption("Laudo")
        st.text_area(
            f"Laudo {idx_display}",
            key=f"comp_{id_real}_laudo",
            placeholder="Transcreva o laudo do exame...",
            height=120,
            label_visibility="collapsed"
        )
        st.text_input(
            f"Conduta {idx_display}",
            key=f"comp_{id_real}_conduta",
            placeholder="Escreva a conduta aqui...",
            label_visibility="collapsed"
        )

# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-9"></span>', unsafe_allow_html=True)
    st.markdown("##### 9. Exames Complementares")
    
    st.text_area("Notas", key="complementares_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()
    
    # Inicializa ordem
    _inicializar_ordem()
    ordem = st.session_state.comp_ordem
    
    # --- 3 Itens VISÍVEIS ---
    for i in range(1, 4):
        _render_linha(i, ordem[i-1])
        st.write("")
        
    # --- 5 Itens OCULTOS (abre automaticamente se houver conteúdo) ---
    st.write("")
    
    # Verifica se há conteúdo nos exames 4 a 8
    tem_conteudo = False
    for i in range(4, 9):
        id_real = ordem[i-1]
        if (st.session_state.get(f"comp_{id_real}_exame", "") or
            st.session_state.get(f"comp_{id_real}_laudo", "") or
            st.session_state.get(f"comp_{id_real}_conduta", "")):
            tem_conteudo = True
            break
    
    with st.expander("Demais Exames Complementares", expanded=tem_conteudo):
        for i in range(4, 9):
            _render_linha(i, ordem[i-1])
            st.write("")
