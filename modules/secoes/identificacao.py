import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    return {
        'identificacao_notas': '',
        # Identidade
        'departamento': '',
        'nome': '', 'idade': 0, 'sexo': '', 'prontuario': '', 'leito': '', 'origem': '', 'equipe': '', 'interconsultora': '',
        'di_hosp': '', 'di_uti': '', 'di_enf': '',
        'alergias_status': None,
        'alergias': '',
        'paliativo': False,
    }

# 2. Renderização Visual
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-1"></span>', unsafe_allow_html=True)
    st.markdown("##### 1. Identificação")
    
    st.text_area("Notas", key="identificacao_notas", height="content", placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback: _agent_btn_callback()
    
    with st.container(border=True):
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
        
        c1, c2, c3, c4, c5 = st.columns([1, 1.2, 1.5, 1.5, 1.5])
        c1.markdown("**Idade**")
        c1.number_input("Idade", min_value=0, key="idade", label_visibility="collapsed")
        c2.markdown("**Sexo**")
        c2.selectbox("Sexo", ["", "Masculino", "Feminino"], key="sexo", label_visibility="collapsed")
        c3.markdown("**Origem**")
        c3.text_input("Origem", key="origem", placeholder="Ex: PS/CC", label_visibility="collapsed")
        c4.markdown("**Equipe Titular**")
        c4.text_input("Equipe Titular", key="equipe", label_visibility="collapsed")
        c5.markdown("**Interconsultora**")
        c5.text_input("Interconsultora", key="interconsultora", placeholder="Ex: Cardiologia", label_visibility="collapsed")
        
        st.write("")
        
        k1, k2, k3 = st.columns(3)
        k1.markdown("**Admissão Hospitalar**")
        k1.text_input("Admissão Hospitalar", key="di_hosp", placeholder="DD/MM/AAAA", label_visibility="collapsed")
        k2.markdown("**Admissão UTI**")
        k2.text_input("Admissão UTI", key="di_uti", placeholder="DD/MM/AAAA", label_visibility="collapsed")
        k3.markdown("**Admissão Enfermaria**")
        k3.text_input("Admissão Enfermaria", key="di_enf", placeholder="DD/MM/AAAA", label_visibility="collapsed")

        st.write("")

        st.markdown("**Alergias**")
        st.pills("Alergias status", ["Desconhecido", "Nega", "Presente"],
                 key="alergias_status", default=None, label_visibility="collapsed")
        st.text_input("Alergias", key="alergias",
                      placeholder="Ex: Penicilina, Dipirona",
                      label_visibility="collapsed")

        st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
        st.checkbox("Priorizar medidas de conforto — Cuidados Proporcionais", key="paliativo")