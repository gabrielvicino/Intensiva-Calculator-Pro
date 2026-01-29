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
    st.markdown(f"**🔹 HD Atual #{i}**")
    
    with st.container(border=True):
        # LINHA 1: HD | Classificação | Data
        c1, c2, c3 = st.columns([3, 1.5, 1])
        with c1:
            st.text_input(f"Diagnóstico #{i}", key=f"hd_atual_{i}_nome", placeholder="Ex: LRA")
        with c2:
            st.text_input(f"Classificação #{i}", key=f"hd_atual_{i}_class", placeholder="Ex: KDIGO 3")
        with c3:
            st.text_input(f"Data Início", key=f"hd_atual_{i}_data", placeholder="DD/MM")
            
        # LINHA 2: Complemento
        st.text_area(f"Complemento / Evolução #{i}", key=f"hd_atual_{i}_obs", height=68, placeholder="> Aguarda teste de furosemida...")
        
        # LINHA 3: Conduta (CORREÇÃO DO ERRO AQUI)
        # Passamos o texto "Conduta #i" dentro do st.success para satisfazer o argumento 'body'
        with st.success(f"👉 Conduta #{i}"):
            st.text_input("Conduta", key=f"hd_atual_{i}_conduta", label_visibility="collapsed", placeholder="Digite a conduta aqui...")

# Função Card PRÉVIO
def _render_card_previo(i):
    st.markdown(f"**📜 Histórico / Resolvido #{i}**")
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
    st.markdown("##### 2. Diagnósticos (HD) & Condutas")
    
    # --- A: HDS ATUAIS VISÍVEIS (1 e 2) ---
    st.info("🔥 **Problemas Ativos**")
    _render_card_atual(1)
    st.write("") 
    _render_card_atual(2)
    
    # --- B: HDS ATUAIS EXTRAS (3 e 4) - ESCONDIDOS ---
    st.write("")
    with st.expander("➕ Ver mais HDs Atuais (Slots 3 e 4)"):
        _render_card_atual(3)
        st.write("")
        _render_card_atual(4)

    st.write("") 
    st.write("")

    # --- C: HDS RESOLVIDOS (TODOS) - ESCONDIDOS ---
    with st.expander("📂 **HDs Prévios / Resolvidos (Histórico Completo)**", expanded=False):
        for i in range(1, 5):
            _render_card_previo(i)
            st.write("")