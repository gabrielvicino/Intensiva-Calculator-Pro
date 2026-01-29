import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    campos = {
        # Campo Único Global de Adesão
        'muc_adesao_global': 'Uso Regular'
    }
    
    # 10 Slots para medicamentos (sem o campo 'uso' individual)
    for i in range(1, 11):
        campos.update({
            f'muc_{i}_nome': '',
            f'muc_{i}_dose': '',
            f'muc_{i}_freq': '',
            f'muc_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de medicação (Mais limpo agora)
def _render_linha(i):
    with st.container(border=True):
        st.markdown(f"**💊 Medicação #{i}**")
        
        # LINHA 1: Medicamento | Dose | Frequência
        c1, c2, c3 = st.columns([3, 1, 1.2], vertical_alignment="bottom")
        
        with c1:
            st.text_input(f"Nome do Fármaco #{i}", key=f"muc_{i}_nome", placeholder="Ex: Enalapril")
        with c2:
            st.text_input(f"Dose #{i}", key=f"muc_{i}_dose", placeholder="Ex: 20mg")
        with c3:
            st.text_input(f"Freq #{i}", key=f"muc_{i}_freq", placeholder="Ex: 12/12h")
            
        # LINHA 2: Conduta
        st.text_input(f"Conduta #{i}", key=f"muc_{i}_conduta", placeholder="Ex: Manter, Suspender ou Ajustar")

# 2. Renderização Principal
def render():
    st.markdown("##### 4. MUC – Medicações de Uso Crônico")
    
    with st.container(border=True):
        # --- CONFIGURAÇÃO GLOBAL DE ADESÃO (NO TOPO) ---
        st.markdown("**📊 Status de Adesão Prévia (Global):**")
        st.radio(
            "Adesão Global", # Label oculta visualmente, usada internamente
            ["Uso Regular", "Uso Irregular / Falha Terapêutica"],
            key="muc_adesao_global",
            horizontal=True,
            label_visibility="collapsed"
        )
    
    st.write("") # Espaço entre o cabeçalho global e a lista
    
    # --- 3 Itens VISÍVEIS ---
    for i in range(1, 4):
        _render_linha(i)
        
    # --- 7 Itens OCULTOS ---
    st.write("")
    with st.expander("➕ Ver mais MUC (Slots 4 a 10)"):
        for i in range(4, 11):
            _render_linha(i)