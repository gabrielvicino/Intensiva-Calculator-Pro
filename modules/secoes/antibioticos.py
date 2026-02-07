import streamlit as st

# Funções para gerenciar ordem dos antibióticos
def _inicializar_ordem_atual():
    """Inicializa a ordem dos ATB atuais se não existir"""
    if 'atb_curr_ordem' not in st.session_state:
        st.session_state.atb_curr_ordem = list(range(1, 6))

def _inicializar_ordem_previo():
    """Inicializa a ordem dos ATB prévios se não existir"""
    if 'atb_prev_ordem' not in st.session_state:
        st.session_state.atb_prev_ordem = list(range(1, 6))

def _trocar_ordem_atual(idx1, idx2):
    """Troca a ordem de exibição de dois ATB atuais"""
    _inicializar_ordem_atual()
    ordem = st.session_state.atb_curr_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.atb_curr_ordem = ordem

def _trocar_ordem_previo(idx1, idx2):
    """Troca a ordem de exibição de dois ATB prévios"""
    _inicializar_ordem_previo()
    ordem = st.session_state.atb_prev_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.atb_prev_ordem = ordem

# 1. Definição das Variáveis
def get_campos():
    campos = {}
    
    # --- 5 Slots para ATUAIS ---
    for i in range(1, 6):
        campos.update({
            f'atb_curr_{i}_nome': '',
            f'atb_curr_{i}_tipo': 'Empírico', # Padrão
            f'atb_curr_{i}_data_ini': '',
            f'atb_curr_{i}_data_fim': '',     # Término Previsto
            f'atb_curr_{i}_conduta': ''
        })
        
    # --- 5 Slots para PRÉVIOS ---
    for i in range(1, 6):
        campos.update({
            f'atb_prev_{i}_nome': '',
            f'atb_prev_{i}_tipo': 'Empírico',
            f'atb_prev_{i}_data_ini': '',
            f'atb_prev_{i}_data_fim': '',     # Término Real
            f'atb_prev_{i}_obs': '',          # Observação
            f'atb_prev_{i}_conduta': ''
        })
        
    return campos

# Função Card ATUAL
def _render_atual(idx_display, id_real):
    """
    Renderiza um card de antibiótico atual.
    idx_display: posição de exibição (1-5)
    id_real: ID real do ATB nos dados (1-5)
    """
    with st.container(border=True):
        # Título com botões de reordenação no canto superior direito
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        
        with col_titulo:
            st.markdown(f"**Antibiótico {idx_display}**")
        
        with col_up:
            if idx_display > 1:
                if st.button("↑", key=f"atb_curr_up_pos_{idx_display}", help="Mover para cima"):
                    _trocar_ordem_atual(idx_display-1, idx_display-2)
                    st.rerun()
        
        with col_down:
            if idx_display < 5:
                if st.button("↓", key=f"atb_curr_down_pos_{idx_display}", help="Mover para baixo"):
                    _trocar_ordem_atual(idx_display-1, idx_display)
                    st.rerun()
        
        c1, c2 = st.columns([2, 1.5], vertical_alignment="center")
        with c1:
            st.text_input(f"Antibiótico {idx_display}", key=f"atb_curr_{id_real}_nome", placeholder="Exemplo: Meropenem")
        with c2:
            st.radio(
                f"Tipo {idx_display}", 
                ["Empírico", "Guiado"], 
                key=f"atb_curr_{id_real}_tipo", 
                horizontal=True,
                label_visibility="collapsed"
            )
            
        # LINHA 2: Datas (Início | Término Previsto)
        d1, d2 = st.columns([1, 1])
        with d1:
            st.text_input("Data de Início (dd/mm/aaaa)", key=f"atb_curr_{id_real}_data_ini", placeholder="dd/mm/aaaa")
        with d2:
            st.text_input("Término Previsto (dd/mm/aaaa)", key=f"atb_curr_{id_real}_data_fim", placeholder="dd/mm/aaaa")
            
        # LINHA 3: Conduta (com borda verde)
        st.markdown(f"<style>input[type='text'][id*='atb_curr_{id_real}_conduta']{{border-left:4px solid #28a745!important;padding-left:12px!important}}</style>", unsafe_allow_html=True)
        st.text_input(
            f"Conduta {idx_display}", 
            key=f"atb_curr_{id_real}_conduta", 
            placeholder="Exemplo: Ajustar para dose renal, Descalonar..."
        )

# Função Card PRÉVIO
def _render_previo(idx_display, id_real):
    """
    Renderiza um card de antibiótico prévio.
    idx_display: posição de exibição (1-5)
    id_real: ID real do ATB nos dados (1-5)
    """
    with st.container(border=True):
        # Título com botões de reordenação no canto superior direito
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        
        with col_titulo:
            st.markdown(f"**Antibiótico Prévio {idx_display}**")
        
        with col_up:
            if idx_display > 1:
                if st.button("↑", key=f"atb_prev_up_pos_{idx_display}", help="Mover para cima"):
                    _trocar_ordem_previo(idx_display-1, idx_display-2)
                    st.rerun()
        
        with col_down:
            if idx_display < 5:
                if st.button("↓", key=f"atb_prev_down_pos_{idx_display}", help="Mover para baixo"):
                    _trocar_ordem_previo(idx_display-1, idx_display)
                    st.rerun()
        
        c1, c2 = st.columns([2, 1.5], vertical_alignment="center")
        with c1:
            st.text_input(f"Antibiótico Prévio {idx_display}", key=f"atb_prev_{id_real}_nome", placeholder="Exemplo: Ceftriaxone")
        with c2:
            st.radio(
                f"Tipo {idx_display}", 
                ["Empírico", "Guiado"], 
                key=f"atb_prev_{id_real}_tipo", 
                horizontal=True,
                label_visibility="collapsed"
            )

        # LINHA 2: Datas (Início | Fim Real)
        d1, d2 = st.columns([1, 1])
        with d1:
            st.text_input("Data de Início (dd/mm/aaaa)", key=f"atb_prev_{id_real}_data_ini", placeholder="dd/mm/aaaa")
        with d2:
            st.text_input("Data Término (dd/mm/aaaa)", key=f"atb_prev_{id_real}_data_fim", placeholder="dd/mm/aaaa")

        # LINHA 3: Observação
        st.text_area(
            f"Observação", 
            key=f"atb_prev_{id_real}_obs",
            placeholder="Exemplo: Motivo da suspensão, resposta ao tratamento...",
            height=80
        )

        # LINHA 4: Conduta (com borda verde)
        st.markdown(f"<style>input[type='text'][id*='atb_prev_{id_real}_conduta']{{border-left:4px solid #28a745!important;padding-left:12px!important}}</style>", unsafe_allow_html=True)
        st.text_input(
            f"Conduta {idx_display}", 
            key=f"atb_prev_{id_real}_conduta", 
            placeholder="Exemplo: Suspenso por escalonamento, Fim de tratamento..."
        )

# 2. Renderização Principal
def render():
    st.markdown("##### 8. Antibióticos")
    
    # Inicializa ordens
    _inicializar_ordem_atual()
    ordem_atual = st.session_state.atb_curr_ordem
    
    # --- SEÇÃO ATUAIS ---
    st.info("**Em Uso (Atuais)**")
    # 3 Visíveis
    for i in range(1, 4):
        _render_atual(i, ordem_atual[i-1])
        st.write("")
        
    # Verifica se há conteúdo nos ATB 4 e 5
    tem_conteudo_extras = False
    for i in [4, 5]:
        id_real = ordem_atual[i-1]
        if (st.session_state.get(f"atb_curr_{id_real}_nome", "") or 
            st.session_state.get(f"atb_curr_{id_real}_data_ini", "") or 
            st.session_state.get(f"atb_curr_{id_real}_conduta", "")):
            tem_conteudo_extras = True
            break
    
    with st.expander("Demais Antibióticos Atuais", expanded=tem_conteudo_extras):
        _render_atual(4, ordem_atual[3])
        st.write("")
        _render_atual(5, ordem_atual[4])

    st.write("")
    st.markdown("---")

    # Inicializa ordem prévios
    _inicializar_ordem_previo()
    ordem_previo = st.session_state.atb_prev_ordem
    
    # --- SEÇÃO PRÉVIOS ---
    st.warning("**Histórico (Prévios)**")
    # 2 Visíveis
    for i in range(1, 3):
        _render_previo(i, ordem_previo[i-1])
        st.write("")
        
    # Verifica se há conteúdo nos ATB prévios 3 a 5
    tem_conteudo_previos = False
    for i in range(3, 6):
        id_real = ordem_previo[i-1]
        if (st.session_state.get(f"atb_prev_{id_real}_nome", "") or 
            st.session_state.get(f"atb_prev_{id_real}_data_ini", "") or 
            st.session_state.get(f"atb_prev_{id_real}_data_fim", "")):
            tem_conteudo_previos = True
            break
    
    with st.expander("Demais ATB Prévios", expanded=tem_conteudo_previos):
        for i in range(3, 6):
            _render_previo(i, ordem_previo[i-1])
            st.write("")