import streamlit as st

# 1. Definição das Variáveis (8 slots, mesmo modelo de dispositivos)
def get_campos():
    campos = {'hd_notas': ''}
    for i in range(1, 9):
        campos.update({
            f'hd_{i}_nome': '',
            f'hd_{i}_class': '',
            f'hd_{i}_data_inicio': '',
            f'hd_{i}_data_resolvido': '',
            f'hd_{i}_status': None,
            f'hd_{i}_obs': '',
            f'hd_{i}_conduta': ''
        })
    return campos

# Função para gerenciar ordem das hipóteses
def _inicializar_ordem():
    """Inicializa a ordem das hipóteses se não existir"""
    if 'hd_ordem' not in st.session_state:
        st.session_state.hd_ordem = list(range(1, 9))

def _trocar_ordem(idx1, idx2):
    """Troca a ordem de exibição de duas hipóteses"""
    _inicializar_ordem()
    ordem = st.session_state.hd_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.hd_ordem = ordem

# Função auxiliar para desenhar UM card de hipótese (mesmo design de dispositivos)
def _render_linha(idx_display, id_real):
    """
    Renderiza um card de hipótese diagnóstica.
    idx_display: posição de exibição (1-8)
    id_real: ID real da hipótese nos dados (1-8)
    """
    with st.container(border=True):
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        with col_titulo:
            st.markdown(f"**Hipótese Diagnóstica {idx_display}**")
        with col_up:
            if idx_display > 1:
                st.form_submit_button("↑", key=f"hd_up_{idx_display}", help="Mover para cima",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display-2))
        with col_down:
            if idx_display < 8:
                st.form_submit_button("↓", key=f"hd_down_{idx_display}", help="Mover para baixo",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display))
        c1, c2, c3, c4 = st.columns([2, 2, 1.2, 1.2], vertical_alignment="bottom")
        with c1:
            st.text_input(f"Hipótese {idx_display}", key=f"hd_{id_real}_nome", placeholder="Ex: Lesão Renal Aguda")
        with c2:
            st.text_input(f"Classificação {idx_display}", key=f"hd_{id_real}_class", placeholder="Ex: KDIGO 3")
        with c3:
            st.text_input(f"Início", key=f"hd_{id_real}_data_inicio", placeholder="dd/mm/aaaa")
        with c4:
            st.text_input(f"Resolvido", key=f"hd_{id_real}_data_resolvido", placeholder="dd/mm/aaaa")
        st.pills(
            f"Status {idx_display}",
            ["Atual", "Resolvida"],
            key=f"hd_{id_real}_status",
            label_visibility="collapsed"
        )
        st.text_area(f"Observação {idx_display}", key=f"hd_{id_real}_obs", height=68, label_visibility="collapsed", placeholder="Observações sobre a evolução...")
        st.text_input(
            f"Conduta {idx_display}",
            key=f"hd_{id_real}_conduta",
            placeholder="Escreva a conduta aqui...",
            label_visibility="collapsed"
        )

# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-2"></span>', unsafe_allow_html=True)
    st.markdown("##### 2. Diagnósticos Atuais & Prévios")

    st.text_area("Notas", key="hd_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()

    _inicializar_ordem()
    ordem = st.session_state.hd_ordem

    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i, ordem[i-1])

    # --- 4 Itens no expander (fechado ao abrir) ---
    st.write("")

    with st.expander("Demais Hipóteses Diagnósticas (5–8)", expanded=False):
        for i in range(5, 9):
            _render_linha(i, ordem[i-1])
