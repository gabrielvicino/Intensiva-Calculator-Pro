import streamlit as st

# 1. Definição das Variáveis (10 Slots Total)
def get_campos():
    campos = {'comorbidades_notas': ''}
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
    st.markdown('<span id="sec-3"></span>', unsafe_allow_html=True)
    st.markdown("##### 3. Comorbidades")
    
    st.text_area("Notas", key="comorbidades_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()
    
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