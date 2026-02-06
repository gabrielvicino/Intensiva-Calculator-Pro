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

# Função Card ATUAL
def _render_card_atual(i):
    st.markdown(f"**Hipótese Diagnóstica {i}**")
    
    with st.container(border=True):
        # LINHA 1: HD | Classificação | Data
        c1, c2, c3 = st.columns([3, 1.5, 1])
        with c1:
            st.text_input(f"HD Atual#{i}", key=f"hd_atual_{i}_nome", placeholder="Ex: Lesão Renal Aguda")
        with c2:
            st.text_input(f"Classificação #{i}", key=f"hd_atual_{i}_class", placeholder="Ex: KDIGO 3")
        with c3:
            st.text_input(f"Data Início (dd/mm/aaaa)", key=f"hd_atual_{i}_data", placeholder="01/01/2025")
            
        # LINHA 2: Complemento/Evolução
        st.text_area(f"Complemento/Evolução#{i} = Observação Hipótese Diagnóstica {i}", key=f"hd_atual_{i}_obs", height=68, placeholder="Observações sobre a evolução da HD...")
        
        # LINHA 3: Conduta (destacada em verde - discreto)
        st.markdown("**Digite a conduta:**")
        # CSS para adicionar borda verde no campo de input
        st.markdown(
            f"""
            <style>
            input[aria-label="Conduta"]:not([value=""]) {{
                border-left: 4px solid #28a745 !important;
            }}
            div[data-testid="stTextInput"] input[placeholder*="conduta"] {{
                border-left: 4px solid #28a745 !important;
                padding-left: 12px !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        st.text_input("Conduta", key=f"hd_atual_{i}_conduta", label_visibility="collapsed", placeholder="Digite a conduta aqui...")

# Função Card PRÉVIO
def _render_card_previo(i):
    st.markdown(f"**Histórico / Resolvido #{i}**")
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1.5, 1])
        c1.text_input(f"Diagnóstico Prévio #{i}", key=f"hd_prev_{i}_nome", placeholder="Ex: TEP")
        c2.text_input(f"Classificação #{i}", key=f"hd_prev_{i}_class", placeholder="Ex: Risco Int.")
        c3.text_input(f"Resolvido em", key=f"hd_prev_{i}_data_fim", placeholder="DD/MM")

        st.text_area(f"Notas Históricas #{i}", key=f"hd_prev_{i}_obs", height=68)

        # LINHA 3: Conduta Realizada (CORREÇÃO DO ERRO AQUI)
        with st.success(f"✅ Conduta Realizada #{i}"):
            st.text_input("Conduta", key=f"hd_prev_{i}_conduta", label_visibility="collapsed", placeholder="Conduta que foi tomada...")

# 2. Renderização Principal
def render():
    st.markdown("##### 2. Diagnósticos Atuais & Prévios")
    
    # --- A: HDS ATUAIS VISÍVEIS (1 e 2) ---
    _render_card_atual(1)
    st.write("") 
    _render_card_atual(2)
    
    # --- B: HDS ATUAIS EXTRAS (3 e 4) - ESCONDIDOS ---
    st.write("")
    with st.expander("Ver mais HDs Atuais (Slots 3 e 4)"):
        _render_card_atual(3)
        st.write("")
        _render_card_atual(4)

    st.write("") 
    st.write("")

    # --- C: HDS RESOLVIDOS (TODOS) - ESCONDIDOS ---
    with st.expander("**HDs Prévios / Resolvidos (Histórico Completo)**", expanded=False):
        for i in range(1, 5):
            _render_card_previo(i)
            st.write("")