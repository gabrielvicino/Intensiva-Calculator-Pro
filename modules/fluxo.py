import streamlit as st

def limpar_tudo():
    """Reseta todos os campos do formulário para o estado inicial."""
    keys_texto = [
        'nome', 'prontuario', 'leito', 'origem', 'equipe', 
        'di_hosp', 'di_uti', 'di_enf', 'hd_principal', 'texto_final_gerado',
        'saps3', 'mrs', 'pps', 'cfs'
    ]
    for k in keys_texto:
        if k in st.session_state: st.session_state[k] = ""
            
    # Resets específicos
    st.session_state['idade'] = 0
    st.session_state['sofa_adm'] = 0
    st.session_state['sofa_atual'] = 0
    st.session_state['paliativo'] = False
    st.session_state['hd_status'] = "Estável"
    st.session_state['sexo'] = "Masculino"
    
    st.toast("Formulário reiniciado.", icon="🔄")

def atualizar_dados_ia(dados):
    """Recebe o JSON da IA e atualiza o session_state com segurança."""
    if not dados: return

    # 1. Identidade
    identidade = dados.get('identidade', {})
    st.session_state.update(identidade)
    
    # 2. Datas (se vierem aninhadas)
    datas = identidade.get('datas', {})
    if datas:
        st.session_state['di_hosp'] = datas.get('hospital', '')
        st.session_state['di_uti'] = datas.get('uti', '')
        st.session_state['di_enf'] = datas.get('enf', '')
    
    # 3. Scores
    scores = dados.get('scores', {})
    if scores:
        st.session_state['saps3'] = scores.get('saps3', '')
        st.session_state['sofa_adm'] = scores.get('sofa_adm', 0)
        st.session_state['sofa_atual'] = scores.get('sofa_atual', 0)
        st.session_state['mrs'] = str(scores.get('mrs', ''))
        st.session_state['pps'] = scores.get('pps', '')
        st.session_state['paliativo'] = scores.get('paliativo', False)
        
    st.toast("Sucesso! Dados preenchidos.", icon="✅")