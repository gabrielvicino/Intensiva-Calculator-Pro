import streamlit as st

# 1. Definição das Variáveis (10 Slots Total)
_OPCOES_ETIL_TBG_SPA = ["Desconhecido", "Ausente", "Presente"]

def get_campos():
    campos = {
        'comorbidades_notas': '',
        'cmd_etilismo': None,
        'cmd_etilismo_obs': '',
        'cmd_tabagismo': None,
        'cmd_tabagismo_obs': '',
        'cmd_spa': None,
        'cmd_spa_obs': '',
    }
    for i in range(1, 11):
        campos.update({
            f'cmd_{i}_nome': '',
            f'cmd_{i}_class': '',
            f'cmd_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar uma linha de comorbidade
def _render_linha(i):
    # Container com borda fina para agrupar a linha
    with st.container(border=True):
        c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
        with c1:
            st.text_input(f"Comorbidade {i}", key=f"cmd_{i}_nome", placeholder="Ex: HAS")
        with c2:
            st.text_input(f"Classificação {i}", key=f"cmd_{i}_class", placeholder="Ex: Estágio 2")
        st.text_input(f"Conduta {i}", key=f"cmd_{i}_conduta", placeholder="Escreva a conduta aqui...", label_visibility="collapsed")

# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-4"></span>', unsafe_allow_html=True)
    st.markdown("##### 4. Comorbidades")
    
    st.text_area("Notas", key="comorbidades_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()

    # --- Etilismo, Tabagismo, SPA (entre Comorbidades e Comorbidade 1) ---
    with st.container(border=True):
        col_etil, col_tbg, col_spa = st.columns(3)
        with col_etil:
            st.markdown("**Etilismo**")
            st.pills("Etilismo", _OPCOES_ETIL_TBG_SPA, key="cmd_etilismo", default=None, label_visibility="collapsed")
            st.text_input("Obs Etilismo", key="cmd_etilismo_obs", placeholder="Observação...", label_visibility="collapsed")
        with col_tbg:
            st.markdown("**Tabagismo**")
            st.pills("Tabagismo", _OPCOES_ETIL_TBG_SPA, key="cmd_tabagismo", default=None, label_visibility="collapsed")
            st.text_input("Obs Tabagismo", key="cmd_tabagismo_obs", placeholder="Observação...", label_visibility="collapsed")
        with col_spa:
            st.markdown("**Substâncias Psicoativas**")
            st.pills("SPA", _OPCOES_ETIL_TBG_SPA, key="cmd_spa", default=None, label_visibility="collapsed")
            st.text_input("Obs SPA", key="cmd_spa_obs", placeholder="Observação...", label_visibility="collapsed")
    st.write("")
    
    # --- 3 Comorbidades VISÍVEIS ---
    for i in range(1, 4):
        _render_linha(i)
        
    # --- 7 Comorbidades ESCONDIDAS (abre automaticamente se houver conteúdo) ---
    st.write("")
    
    # Verifica se há conteúdo nas comorbidades 4 a 10
    tem_conteudo = False
    for i in range(4, 11):
        if (st.session_state.get(f"cmd_{i}_nome", "") or 
            st.session_state.get(f"cmd_{i}_class", "") or 
            st.session_state.get(f"cmd_{i}_conduta", "")):
            tem_conteudo = True
            break
    
    with st.expander("Demais Comorbidades", expanded=tem_conteudo):
        for i in range(4, 11):
            _render_linha(i)