import streamlit as st

def calcular_ckd_epi(creatinina, idade, sexo, raca_negra):
    # Lógica matemática pura (exemplo simplificado)
    # CKD-EPI 2021 (fórmula oficial sem fator racial, mas mantendo a lógica de código)
    k = 0.7 if sexo == "Mulher" else 0.9
    alpha = -0.329 if sexo == "Mulher" else -0.411
    fator_sexo = 1.018 if sexo == "Mulher" else 1.0
    
    eGFR = 141 * (min(creatinina/k, 1)**alpha) * \
           (max(creatinina/k, 1)**-1.209) * \
           (0.993**idade) * fator_sexo
    
    return eGFR

def render_renal():
    st.header("🫘 Função Renal e Ajuste de Dose")
    
    # Abas internas da pílula renal
    tab1, tab2 = st.tabs(["CKD-EPI (TFG)", "Cockcroft-Gault"])
    
    with tab1:
        st.caption("Padrão ouro atual para estimativa de filtração glomerular.")
        c1, c2 = st.columns(2)
        with c1:
            scr = st.number_input("Creatinina Sérica (mg/dL)", value=1.0, step=0.1, format="%.2f")
            idade = st.number_input("Idade (anos)", value=50, step=1)
        with c2:
            sexo = st.selectbox("Sexo Biológico", ["Homem", "Mulher"])
            # raca = st.checkbox("Raça Negra (Apenas para fórmulas antigas)")
        
        if st.button("Calcular TFG", type="primary"):
            resultado = calcular_ckd_epi(scr, idade, sexo, False)
            
            st.markdown("### Resultado")
            if resultado > 90:
                cor = "green"
                estagio = "G1 (Normal)"
            elif resultado > 60:
                cor = "orange"
                estagio = "G2 (Levemente diminuída)"
            else:
                cor = "red"
                estagio = "G3a a G5 (Disfunção Moderada/Grave)"
                
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:#f0f2f6; border-left: 5px solid {cor}">
                <h2 style="margin:0; color: {cor}">{resultado:.1f} ml/min/1.73m²</h2>
                <p style="margin:0">Estadiamento: <b>{estagio}</b></p>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.info("Aqui virá a calculadora de Cockcroft-Gault...")