import streamlit as st

# Funções para gerenciar ordem dos antibióticos (lista única, como diagnóstico)
def _inicializar_ordem():
    """Inicializa a ordem dos ATB se não existir"""
    if 'atb_ordem' not in st.session_state:
        st.session_state.atb_ordem = list(range(1, 9))

def _trocar_ordem(idx1, idx2):
    """Troca a ordem de exibição de dois ATB"""
    _inicializar_ordem()
    ordem = st.session_state.atb_ordem
    ordem[idx1], ordem[idx2] = ordem[idx2], ordem[idx1]
    st.session_state.atb_ordem = ordem

# 1. Definição das Variáveis (8 slots, modelo HD)
def get_campos():
    campos = {'antibioticos_notas': ''}
    for i in range(1, 9):
        campos.update({
            f'atb_{i}_nome': '',
            f'atb_{i}_foco': '',
            f'atb_{i}_tipo': None,
            f'atb_{i}_data_ini': '',
            f'atb_{i}_data_fim': '',      # Data de Término
            f'atb_{i}_num_dias': '',      # Número de dias
            f'atb_{i}_status': None,      # Atual | Prévio
            f'atb_{i}_obs': '',
            f'atb_{i}_conduta': ''
        })
    return campos

# Função Card ATB (unificado, como HD)
def _render_linha(idx_display, id_real):
    """
    Renderiza um card de antibiótico.
    idx_display: posição de exibição (1-8)
    id_real: ID real do ATB nos dados (1-8)
    """
    with st.container(border=True):
        col_titulo, col_up, col_down = st.columns([10, 1, 1])
        with col_titulo:
            st.markdown(f"**Antibiótico {idx_display}**")
        with col_up:
            if idx_display > 1:
                st.form_submit_button("↑", key=f"atb_up_{idx_display}", help="Mover para cima",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display-2))
        with col_down:
            if idx_display < 8:
                st.form_submit_button("↓", key=f"atb_down_{idx_display}", help="Mover para baixo",
                    on_click=_trocar_ordem, args=(idx_display-1, idx_display))
        c1, c2, c3 = st.columns([2, 2, 1.5], vertical_alignment="center")
        with c1:
            st.text_input(f"Antibiótico {idx_display}", key=f"atb_{id_real}_nome", placeholder="Exemplo: Meropenem")
        with c2:
            st.text_input(f"Foco {idx_display}", key=f"atb_{id_real}_foco", placeholder="Exemplo: PAV, ITU, Bacteremia")
        with c3:
            st.pills(
                f"Tipo {idx_display}",
                ["Empírico", "Guiado por Cultura"],
                key=f"atb_{id_real}_tipo",
                label_visibility="collapsed"
            )
        # LINHA 2: Data de início | Data de Término | Número de dias
        d1, d2, d3 = st.columns([1, 1, 1])
        with d1:
            st.text_input("Data de Início (dd/mm/aaaa)", key=f"atb_{id_real}_data_ini", placeholder="dd/mm/aaaa")
        with d2:
            st.text_input("Data de Término (dd/mm/aaaa)", key=f"atb_{id_real}_data_fim", placeholder="dd/mm/aaaa")
        with d3:
            st.text_input("Número de dias", key=f"atb_{id_real}_num_dias", placeholder="Ex: 7")
        # Pills Atual / Prévio abaixo da linha de datas
        st.pills(
            f"Status {idx_display}",
            ["Atual", "Prévio"],
            key=f"atb_{id_real}_status",
            label_visibility="collapsed"
        )
        st.text_area(
            f"Observação {idx_display}",
            key=f"atb_{id_real}_obs",
            placeholder="Exemplo: Motivo da suspensão, resposta ao tratamento...",
            height=68,
            label_visibility="collapsed"
        )
        st.text_input(
            f"Conduta {idx_display}",
            key=f"atb_{id_real}_conduta",
            placeholder="Escreva a conduta aqui...",
            label_visibility="collapsed"
        )

# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-10"></span>', unsafe_allow_html=True)
    st.markdown("##### 10. Antibióticos")

    st.text_area("Notas", key="antibioticos_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback:
        _agent_btn_callback()

    _inicializar_ordem()
    ordem = st.session_state.atb_ordem

    # --- 4 Itens VISÍVEIS ---
    for i in range(1, 5):
        _render_linha(i, ordem[i-1])

    # --- 4 Itens no expander ---
    st.write("")
    tem_conteudo_extras = False
    for i in range(5, 9):
        id_real = ordem[i-1]
        if (st.session_state.get(f"atb_{id_real}_nome", "") or
            st.session_state.get(f"atb_{id_real}_data_ini", "") or
            st.session_state.get(f"atb_{id_real}_conduta", "")):
            tem_conteudo_extras = True
            break

    with st.expander("Demais Antibióticos (5–8)", expanded=tem_conteudo_extras):
        for i in range(5, 9):
            _render_linha(i, ordem[i-1])
