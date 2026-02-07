import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    campos = {}
    
    # 4 Slots para Atuais
    for i in range(1, 5):
        campos.update({
            f'hd_atual_{i}_nome': '',
            f'hd_atual_{i}_class': '',
            f'hd_atual_{i}_conduta': '',
            f'hd_atual_{i}_data': '',
            f'hd_atual_{i}_obs': ''
        })
        
    # 4 Slots para Prévios
    for i in range(1, 5):
        campos.update({
            f'hd_prev_{i}_nome': '',
            f'hd_prev_{i}_class': '',
            f'hd_prev_{i}_conduta': '',
            f'hd_prev_{i}_data_ini': '',
            f'hd_prev_{i}_data_fim': '',
            f'hd_prev_{i}_obs': ''
        })
        
    return campos

# Função para gerenciar ordem das hipóteses
def _inicializar_ordem():
    """Inicializa a ordem das hipóteses se não existir"""
    if 'hd_ordem' not in st.session_state:
        st.session_state.hd_ordem = [1, 2, 3, 4]

def _trocar_ordem(idx1, idx2):
    """Troca a ordem de exibição de duas hipóteses"""
    _inicializar_ordem()
    ordem = st.session_state.hd_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.hd_ordem = ordem

# Função Card ATUAL
def _render_card_atual(idx_display, id_real):
    """
    Renderiza um card de hipótese.
    idx_display: posição de exibição (1, 2, 3, 4)
    id_real: ID real da hipótese nos dados (1, 2, 3, 4)
    """
    # Título com botões de reordenação
    col_titulo, col_up, col_down = st.columns([10, 1, 1])
    
    with col_titulo:
        st.markdown(f"**Hipótese Diagnóstica {idx_display}**")
    
    with col_up:
        if idx_display > 1:  # Só mostra se não for o primeiro
            if st.button("↑", key=f"up_pos_{idx_display}", help="Mover para cima"):
                _trocar_ordem(idx_display-1, idx_display-2)
                st.rerun()
    
    with col_down:
        if idx_display < 4:  # Só mostra se não for o último
            if st.button("↓", key=f"down_pos_{idx_display}", help="Mover para baixo"):
                _trocar_ordem(idx_display-1, idx_display)
                st.rerun()
    
    with st.container(border=True):
        # CSS compacto para borda verde
        st.markdown(f"<style>input[type='text'][id*='hd_atual_{id_real}_conduta']{{border-left:4px solid #28a745!important;padding-left:12px!important}}</style>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([3, 1.5, 1])
        with c1:
            st.text_input(f"Hipótese Diagnóstica Atual {idx_display}", key=f"hd_atual_{id_real}_nome", placeholder="Ex: Lesão Renal Aguda")
        with c2:
            st.text_input(f"Classificação {idx_display}", key=f"hd_atual_{id_real}_class", placeholder="Ex: KDIGO 3")
        with c3:
            st.text_input(f"Data Início (dd/mm/aaaa)", key=f"hd_atual_{id_real}_data", placeholder="01/01/2025")
        
        # LINHA 2: Observação
        st.text_area(f"Observação Hipótese Diagnóstica {idx_display}", key=f"hd_atual_{id_real}_obs", height=68, placeholder="Observações sobre a evolução da Hipótese Diagnóstica...")
        
        # LINHA 3: Conduta
        st.text_input(f"Conduta {idx_display}", key=f"hd_atual_{id_real}_conduta", placeholder="Digite a conduta aqui...")

# Função Card PRÉVIO
def _render_card_previo(i):
    st.markdown(f"**Hipótese Diagnóstica Resolvida {i}**")
    with st.container(border=True):
        # CSS compacto para borda verde
        st.markdown(f"<style>input[type='text'][id*='hd_prev_{i}_conduta']{{border-left:4px solid #28a745!important;padding-left:12px!important}}</style>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([3, 1.5, 1])
        c1.text_input(f"Hipótese Diagnóstica Prévia {i}", key=f"hd_prev_{i}_nome", placeholder="Ex: TEP")
        c2.text_input(f"Classificação {i}", key=f"hd_prev_{i}_class", placeholder="Ex: Risco Int.")
        c3.text_input(f"Resolvido em", key=f"hd_prev_{i}_data_fim", placeholder="DD/MM")

        st.text_area(f"Observação {i}", key=f"hd_prev_{i}_obs", height=68)

        # LINHA 3: Conduta Realizada
        st.text_input(f"✅ Conduta Realizada {i}", key=f"hd_prev_{i}_conduta", placeholder="Conduta que foi tomada...")

# 2. Renderização Principal
def render():
    st.markdown("##### 2. Diagnósticos Atuais & Prévios")
    
    # Inicializa ordem
    _inicializar_ordem()
    ordem = st.session_state.hd_ordem
    
    # --- A: HDS ATUAIS VISÍVEIS (1 e 2) ---
    _render_card_atual(1, ordem[0])
    st.write("") 
    _render_card_atual(2, ordem[1])
    
    # --- B: HIPÓTESES DIAGNÓSTICAS ATUAIS EXTRAS (3 e 4) - ESCONDIDOS ---
    st.write("")
    
    # Verifica se há conteúdo nas hipóteses 3 e 4
    tem_conteudo_extras = False
    for id_hd in [ordem[2], ordem[3]]:
        if (st.session_state.get(f"hd_atual_{id_hd}_nome", "") or 
            st.session_state.get(f"hd_atual_{id_hd}_class", "") or 
            st.session_state.get(f"hd_atual_{id_hd}_conduta", "") or 
            st.session_state.get(f"hd_atual_{id_hd}_data", "") or 
            st.session_state.get(f"hd_atual_{id_hd}_obs", "")):
            tem_conteudo_extras = True
            break
    
    with st.expander("Outras Hipóteses Diagnósticas Atuais", expanded=tem_conteudo_extras):
        _render_card_atual(3, ordem[2])
        st.write("")
        _render_card_atual(4, ordem[3])

    st.write("") 
    st.write("")

    # --- C: HIPÓTESES DIAGNÓSTICAS RESOLVIDAS - ESCONDIDOS ---
    # Verifica se há conteúdo nas hipóteses resolvidas
    tem_conteudo_resolvidas = False
    for i in range(1, 5):
        if (st.session_state.get(f"hd_prev_{i}_nome", "") or 
            st.session_state.get(f"hd_prev_{i}_class", "") or 
            st.session_state.get(f"hd_prev_{i}_conduta", "") or 
            st.session_state.get(f"hd_prev_{i}_data_fim", "") or 
            st.session_state.get(f"hd_prev_{i}_obs", "")):
            tem_conteudo_resolvidas = True
            break
    
    with st.expander("**Hipóteses Diagnósticas Resolvidas**", expanded=tem_conteudo_resolvidas):
        for i in range(1, 5):
            _render_card_previo(i)
            st.write("")