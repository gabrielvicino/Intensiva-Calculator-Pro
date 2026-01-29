import streamlit as st

# 1. Definição das Variáveis (10 Slots Total)
def get_campos():
    campos = {}
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
        # Layout: Nome (Maior), Classificação (Pequeno), Conduta (Médio)
        c1, c2, c3 = st.columns([2, 1, 2], vertical_alignment="bottom")
        
        with c1:
            st.text_input(f"Comorbidade #{i}", key=f"cmd_{i}_nome", placeholder="Ex: HAS")
        
        with c2:
            st.text_input(f"Classif. #{i}", key=f"cmd_{i}_class", placeholder="Ex: Estágio 2")
            
        with c3:
            st.text_input(f"Conduta #{i}", key=f"cmd_{i}_conduta", placeholder="Ex: Manter Losartana")

# 2. Renderização Principal
def render():
    st.markdown("##### 3. Comorbidades (Antecedentes)")
    
    # --- 3 Comorbidades VISÍVEIS (Ajuste Solicitado) ---
    for i in range(1, 4):
        _render_linha(i)
        
    # --- 7 Comorbidades ESCONDIDAS (Ajuste Solicitado) ---
    st.write("")
    with st.expander("➕ Ver mais Comorbidades (Slots 4 a 10)"):
        for i in range(4, 11):
            _render_linha(i)