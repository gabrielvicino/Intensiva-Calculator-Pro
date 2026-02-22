import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    return {
        'identificacao_notas': '',
        # Identidade
        'departamento': '',
        'nome': '', 'idade': 0, 'sexo': '', 'prontuario': '', 'leito': '', 'origem': '', 'equipe': '',
        'di_hosp': '', 'di_uti': '', 'di_enf': '',
        # Scores
        'saps3': '', 'sofa_adm': 0, 'sofa_atual': 0, 
        'mrs': '', 'pps': '', 'cfs': '',
        'paliativo': False
    }

# 2. Renderização Visual
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-1"></span>', unsafe_allow_html=True)
    st.markdown("##### 1. Identificação & Scores")
    
    st.text_area("Notas", key="identificacao_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()
    
    with st.container(border=True):
        # --- PARTE A: IDENTIFICAÇÃO ---
        st.markdown("**Departamento**")
        st.text_input("Departamento", key="departamento",
                      placeholder="Ex: UTI Adulto, Sala Vermelha, Enfermaria...",
                      label_visibility="collapsed")

        c_leito, c_nome, c_pront = st.columns([1, 3, 1.2])
        c_leito.markdown("**Leito**")
        c_leito.text_input("Leito", key="leito", placeholder="Ex: 206A", label_visibility="collapsed")
        c_nome.markdown("**Nome Completo**")
        c_nome.text_input("Nome Completo", key="nome", label_visibility="collapsed")
        c_pront.markdown("**Prontuário**")
        c_pront.text_input("Prontuário", value=st.session_state.get('prontuario', ''), disabled=True, label_visibility="collapsed")
        
        c1, c2, c3, c4 = st.columns([1, 1.2, 1.5, 2])
        c1.markdown("**Idade**")
        c1.number_input("Idade", min_value=0, key="idade", label_visibility="collapsed")
        c2.markdown("**Sexo**")
        c2.selectbox("Sexo", ["", "Masculino", "Feminino"], key="sexo", label_visibility="collapsed")
        c3.markdown("**Origem**")
        c3.text_input("Origem", key="origem", placeholder="Ex: PS/CC", label_visibility="collapsed")
        c4.markdown("**Equipe Responsável**")
        c4.text_input("Equipe Responsável", key="equipe", label_visibility="collapsed")
        
        st.write("") 
        
        k1, k2, k3 = st.columns(3)
        k1.markdown("**Admissão Hospitalar**")
        k1.text_input("Admissão Hospitalar", key="di_hosp", placeholder="DD/MM/AAAA", label_visibility="collapsed")
        k2.markdown("**Admissão UTI**")
        k2.text_input("Admissão UTI", key="di_uti", placeholder="DD/MM/AAAA", label_visibility="collapsed")
        k3.markdown("**Admissão Enfermaria**")
        k3.text_input("Admissão Enfermaria", key="di_enf", placeholder="DD/MM/AAAA", label_visibility="collapsed")

        st.markdown("---")

        # --- PARTE B: SCORES CRÍTICOS ---
        s1, s2, s3 = st.columns(3)
        
        with s1:
            st.markdown("**SAPS 3**")
            st.text_input("SAPS 3", key="saps3", label_visibility="collapsed")
        
        with s2:
            st.markdown("**SOFA Admissão**")
            st.number_input("SOFA Admissão", min_value=0, max_value=24, key="sofa_adm", label_visibility="collapsed")
        
        with s3:
            st.markdown("**SOFA Atualizado**")
            st.number_input("SOFA Atualizado", min_value=0, max_value=24, key="sofa_atual", label_visibility="collapsed")

        st.write("") 

        # --- PARTE C: FUNCIONALIDADE EXPOSTA (PPS + Paliativo) ---
        f1, f2 = st.columns([1.5, 3])
        
        with f1:
            st.markdown("**PPS (%)**")
            st.text_input("PPS (%)", key="pps", placeholder="Ex: 80%", label_visibility="collapsed")
        
        with f2:
            # Ajuste de margem (padding-top) para o checkbox alinhar com o input de texto
            st.markdown('<div style="padding-top: 32px;"></div>', unsafe_allow_html=True)
            st.checkbox("Priorizar medidas para conforto (Paliativo)", key="paliativo")

        # --- PARTE D: OUTRAS ESCALAS (Expander) ---
        with st.expander("Outras Escalas (mRS, CFS)"):
            st.caption("Preenchimento via IA ou manual.")
            e1, e2 = st.columns(2)
            with e1:
                st.markdown("**mRS (Rankin Modificado)**")
                st.selectbox("mRS (Rankin Modificado)", ["", "0", "1", "2", "3", "4", "5", "6"], key="mrs", label_visibility="collapsed")
            with e2:
                st.markdown("**CFS (Fragilidade Clínica)**")
                st.selectbox("CFS (Fragilidade Clínica)", 
                             ["", "1 - Muito em forma", "2 - Bem", "3 - Controlando bem", 
                              "4 - Vulnerável", "5 - Levemente frágil", "6 - Moderadamente frágil", 
                              "7 - Severamente frágil", "8 - Muito severamente frágil", "9 - Doente terminal"], 
                             key="cfs", label_visibility="collapsed")