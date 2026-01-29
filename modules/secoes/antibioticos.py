import streamlit as st

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
            f'atb_prev_{i}_conduta': ''
        })
        
    return campos

# Função Card ATUAL
def _render_atual(i):
    st.markdown(f"**💊 Antibiótico Atual #{i}**")
    with st.container(border=True):
        # LINHA 1: Nome | Tipo (Bola)
        c1, c2 = st.columns([2, 1.5], vertical_alignment="center")
        with c1:
            st.text_input(f"Nome do ATB #{i}", key=f"atb_curr_{i}_nome", placeholder="Ex: Meropenem")
        with c2:
            st.radio(
                f"Tipo #{i}", 
                ["Empírico", "Guiado"], 
                key=f"atb_curr_{i}_tipo", 
                horizontal=True,
                label_visibility="collapsed"
            )
            
        # LINHA 2: Datas (Início | Término Previsto)
        d1, d2 = st.columns([1, 1])
        with d1:
            st.text_input("Data Início", key=f"atb_curr_{i}_data_ini", placeholder="DD/MM (ou D3)")
        with d2:
            st.text_input("Término Previsto", key=f"atb_curr_{i}_data_fim", placeholder="DD/MM (Planejado)")
            
        # LINHA 3: Conduta (Verde)
        with st.success(f"👉 Conduta #{i}"):
            st.text_input(
                "Conduta", 
                key=f"atb_curr_{i}_conduta", 
                label_visibility="collapsed", 
                placeholder="Ex: Ajustar para dose renal, Descalonar..."
            )

# Função Card PRÉVIO
def _render_previo(i):
    st.markdown(f"**📜 Antibiótico Prévio #{i}**")
    with st.container(border=True):
        # LINHA 1: Nome | Tipo
        c1, c2 = st.columns([2, 1.5], vertical_alignment="center")
        with c1:
            st.text_input(f"Nome do ATB #{i}", key=f"atb_prev_{i}_nome", placeholder="Ex: Ceftriaxone")
        with c2:
            st.radio(
                f"Tipo #{i}", 
                ["Empírico", "Guiado"], 
                key=f"atb_prev_{i}_tipo", 
                horizontal=True,
                label_visibility="collapsed"
            )

        # LINHA 2: Datas (Início | Fim Real)
        d1, d2 = st.columns([1, 1])
        with d1:
            st.text_input("Data Início", key=f"atb_prev_{i}_data_ini", placeholder="DD/MM")
        with d2:
            st.text_input("Data Término", key=f"atb_prev_{i}_data_fim", placeholder="DD/MM (Suspenso em)")

        # LINHA 3: Conduta
        with st.success(f"✅ Motivo/Conduta #{i}"):
            st.text_input(
                "Conduta", 
                key=f"atb_prev_{i}_conduta", 
                label_visibility="collapsed", 
                placeholder="Ex: Suspenso por escalonamento, Fim de tratamento..."
            )

# 2. Renderização Principal
def render():
    st.markdown("##### 8. Antibióticos (Prévios e Atuais)")
    
    # --- SEÇÃO ATUAIS ---
    st.info("🔥 **Em Uso (Atuais)**")
    # 3 Visíveis
    for i in range(1, 4):
        _render_atual(i)
        st.write("")
        
    with st.expander("➕ Ver mais ATB Atuais (Slots 4 e 5)"):
        _render_atual(4)
        st.write("")
        _render_atual(5)

    st.write("")
    st.markdown("---")

    # --- SEÇÃO PRÉVIOS ---
    st.warning("📂 **Histórico (Prévios)**")
    # 2 Visíveis
    for i in range(1, 3):
        _render_previo(i)
        st.write("")
        
    with st.expander("➕ Ver mais ATB Prévios (Slots 3 a 5)"):
        for i in range(3, 6):
            _render_previo(i)