import streamlit as st

# 1. Definição das Variáveis
def get_campos():
    return {
        # Identidade
        'nome': '', 'idade': 0, 'sexo': 'Masculino', 'prontuario': '', 'leito': '', 'origem': '', 'equipe': '',
        'di_hosp': '', 'di_uti': '', 'di_enf': '',
        # Scores
        'saps3': '', 'sofa_adm': 0, 'sofa_atual': 0, 
        'mrs': '', 'pps': '', 'cfs': '',
        'paliativo': False
    }

# 2. Renderização Visual
def render():
    st.markdown("##### 1. Identificação & Scores")
    
    with st.container(border=True):
        # --- PARTE A: IDENTIFICAÇÃO ---
        c_leito, c_nome, c_pront = st.columns([1, 3, 1.2])
        c_leito.text_input("Leito", key="leito", placeholder="Ex: 206A")
        c_nome.text_input("Nome Completo", key="nome")
        c_pront.text_input("Prontuário", value=st.session_state.get('prontuario', ''), disabled=True)
        
        c1, c2, c3, c4 = st.columns([1, 1.2, 1.5, 2])
        c1.number_input("Idade", min_value=0, key="idade")
        c2.selectbox("Sexo", ["Masculino", "Feminino"], key="sexo")
        c3.text_input("Origem", key="origem", placeholder="Ex: PS/CC")
        c4.text_input("Equipe Resp.", key="equipe")
        
        st.write("") 
        
        k1, k2, k3 = st.columns(3)
        k1.text_input("Admissão Hosp (DIH)", key="di_hosp", placeholder="DD/MM/AAAA")
        k2.text_input("Admissão UTI", key="di_uti", placeholder="DD/MM/AAAA")
        k3.text_input("Admissão Enf", key="di_enf", placeholder="DD/MM/AAAA")

        st.markdown("---")

        # --- PARTE B: SCORES CRÍTICOS (ALINHAMENTO CORRIGIDO) ---
        # Removi o vertical_alignment para controlar manualmente o HTML do Delta
        s1, s2, s3, s4 = st.columns([2, 1.2, 1.2, 1.2])
        
        with s1:
            st.text_input("SAPS 3", key="saps3")
        
        with s2:
            st.number_input("SOFA Adm", min_value=0, max_value=24, key="sofa_adm")
        
        with s3:
            st.number_input("SOFA Atual", min_value=0, max_value=24, key="sofa_atual")
            
        with s4:
            # Lógica do Delta
            atual = int(st.session_state.get('sofa_atual') or 0)
            adm = int(st.session_state.get('sofa_adm') or 0)
            delta = atual - adm
            
            # Cores do Texto
            if delta > 0:
                cor_bg = "#fce8e6" # Fundo avermelhado leve
                cor_texto = "#c5221f" # Vermelho escuro
                sinal = "+"
            elif delta < 0:
                cor_bg = "#e6f4ea" # Fundo esverdeado leve
                cor_texto = "#137333" # Verde escuro
                sinal = ""
            else:
                cor_bg = "#f0f2f6" # Cinza padrão do Streamlit
                cor_texto = "#31333F"
                sinal = ""

            # HTML Ajustado para imitar a altura exata do st.number_input
            # A label tem margem e tamanho específico. A caixa tem altura fixa.
            st.markdown(f"""
            <div style="margin-bottom: 0.5rem;">
                <label style="font-size: 14px; color: rgb(49, 51, 63);">Δ SOFA</label>
            </div>
            <div style="
                background-color: {cor_bg}; 
                border: 1px solid #dadce0;
                border-radius: 0.5rem;
                height: 42px; /* Altura exata dos inputs padrão */
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                color: {cor_texto};
                font-size: 1.1rem;
            ">
                {sinal}{delta}
            </div>
            """, unsafe_allow_html=True)

        st.write("") 

        # --- PARTE C: FUNCIONALIDADE EXPOSTA (PPS + Paliativo) ---
        f1, f2 = st.columns([1.5, 3])
        
        with f1:
            # ALTERADO PARA TEXT_INPUT: Mais seguro para a IA preencher (aceita "50", "50%", etc)
            st.text_input("PPS (%)", key="pps", placeholder="Ex: 80%")
        
        with f2:
            # Ajuste de margem (padding-top) para o checkbox alinhar com o input de texto
            st.markdown('<div style="padding-top: 10px;"></div>', unsafe_allow_html=True)
            st.checkbox("Priorizar medidas para conforto (Paliativo)", key="paliativo")

        # --- PARTE D: OUTRAS ESCALAS (Expander) ---
        with st.expander("⬇️ Outras Escalas (mRS, CFS)"):
            st.caption("Preenchimento via IA ou manual.")
            e1, e2 = st.columns(2)
            with e1:
                # mRS mantive selectbox pois são números inteiros simples (0-6)
                st.selectbox("mRS (Rankin Modificado)", ["", "0", "1", "2", "3", "4", "5", "6"], key="mrs")
            with e2:
                # CFS mantive selectbox para o médico ver a descrição, mas requer prompt bom
                st.selectbox("CFS (Fragilidade Clínica)", 
                             ["", "1 - Muito em forma", "2 - Bem", "3 - Controlando bem", 
                              "4 - Vulnerável", "5 - Levemente frágil", "6 - Moderadamente frágil", 
                              "7 - Severamente frágil", "8 - Muito severamente frágil", "9 - Doente terminal"], 
                             key="cfs")