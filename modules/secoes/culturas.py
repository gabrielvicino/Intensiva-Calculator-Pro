import streamlit as st

# Função para gerenciar ordem das culturas
def _inicializar_ordem():
    """Inicializa a ordem das culturas se não existir"""
    if 'cult_ordem' not in st.session_state:
        st.session_state.cult_ordem = list(range(1, 9))

def _trocar_ordem(idx1, idx2):
    """Troca a ordem de exibição de duas culturas"""
    _inicializar_ordem()
    ordem = st.session_state.cult_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.cult_ordem = ordem

# 1. Definição das Variáveis (8 Slots Total)
def get_campos():
    campos = {'culturas_notas': ''}
    for i in range(1, 9):
        campos.update({
            f'cult_{i}_sitio': '',
            f'cult_{i}_data_coleta': '',
            f'cult_{i}_data_resultado': '',
            f'cult_{i}_status': None,
            f'cult_{i}_micro': '',
            f'cult_{i}_sensib': '',
            f'cult_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de cultura
def _render_linha(idx_display, id_real):
    """
    Renderiza um card de cultura.
    idx_display: posição de exibição (1-8)
    id_real: ID real da cultura nos dados (1-8)
    """
    with st.container(border=True):
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        with col_titulo:
            st.markdown(f"**Cultura {idx_display}**")
        with col_up:
            if idx_display > 1:
                st.form_submit_button("↑", key=f"cult_up_{idx_display}", help="Mover para cima",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display-2))
        with col_down:
            if idx_display < 8:
                st.form_submit_button("↓", key=f"cult_down_{idx_display}", help="Mover para baixo",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display))
        c1, c2, c3 = st.columns([2.5, 1.2, 1.2], vertical_alignment="bottom")
        with c1:
            st.text_input(f"Sítio {idx_display}", key=f"cult_{id_real}_sitio", placeholder="Exemplo: Hemocultura, Urocultura")
        with c2:
            st.text_input(f"Data da Coleta", key=f"cult_{id_real}_data_coleta", placeholder="dd/mm/aaaa")
        with c3:
            st.text_input(f"Data do Resultado", key=f"cult_{id_real}_data_resultado", placeholder="dd/mm/aaaa")

        # LINHA 2: Status da Cultura
        st.markdown(f"<small style='color:#666'>Status da Cultura:</small>", unsafe_allow_html=True)
        opcoes_status = ["Pendente negativo", "Negativo", "Positivo aguarda isolamento", "Positivo com Antibiograma"]
        key_status = f"cult_{id_real}_status"
        # Garante que o valor em session_state seja válido (evita erro quando dados vêm de IA ou sessão antiga)
        if key_status in st.session_state and st.session_state[key_status] not in opcoes_status:
            st.session_state[key_status] = None
        st.pills(
            f"Status {idx_display}", 
            opcoes_status, 
            key=key_status,
            label_visibility="collapsed"
        )

        # LINHA 3: Micro-organismo | Sensibilidade
        m1, m2 = st.columns([2, 2])
        with m1:
            st.text_input(f"Micro-organismo Isolado {idx_display}", key=f"cult_{id_real}_micro", placeholder="Exemplo: K. pneumoniae KPC+")
        with m2:
            st.text_input(f"Perfil Sensibilidade {idx_display}", key=f"cult_{id_real}_sensib", placeholder="Exemplo: Sensível a Polimixina B")

        st.text_input(
                f"Conduta {idx_display}",
                key=f"cult_{id_real}_conduta",
                placeholder="Escreva a conduta aqui...",
                label_visibility="collapsed"
            )

# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-7"></span>', unsafe_allow_html=True)
    st.markdown("##### 7. Culturas")
    
    st.text_area("Notas", key="culturas_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()
    
    # Inicializa ordem
    _inicializar_ordem()
    ordem = st.session_state.cult_ordem
    
    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i, ordem[i-1])
        
    # --- 4 Itens OCULTOS (abre automaticamente se houver conteúdo) ---
    st.write("")
    
    # Verifica se há conteúdo nas culturas 5 a 8
    tem_conteudo = False
    for i in range(5, 9):
        id_real = ordem[i-1]
        if (st.session_state.get(f"cult_{id_real}_sitio", "") or 
            st.session_state.get(f"cult_{id_real}_micro", "") or 
            st.session_state.get(f"cult_{id_real}_conduta", "")):
            tem_conteudo = True
            break
    
    with st.expander("Demais Culturas", expanded=tem_conteudo):
        for i in range(5, 9):
            _render_linha(i, ordem[i-1])