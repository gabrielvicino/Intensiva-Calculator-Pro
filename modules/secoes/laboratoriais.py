import streamlit as st

# 1. Definição das Variáveis (10 Slots de Data)
def get_campos():
    campos = {}
    
    for i in range(1, 11):
        campos.update({
            f'lab_{i}_data': '',
            
            # Linha 1: Hemato
            f'lab_{i}_hb': '', f'lab_{i}_ht': '', f'lab_{i}_vcm': '', f'lab_{i}_hcm': '', 
            f'lab_{i}_rdw': '', f'lab_{i}_leuco': '', f'lab_{i}_plaq': '',
            
            # Linha 2: Renal/Eletrolitos
            f'lab_{i}_cr': '', f'lab_{i}_ur': '', f'lab_{i}_na': '', f'lab_{i}_k': '', 
            f'lab_{i}_mg': '', f'lab_{i}_pi': '', f'lab_{i}_cat': '',
            
            # Linha 3: Hepático/Panc
            f'lab_{i}_tgp': '', f'lab_{i}_tgo': '', f'lab_{i}_fal': '', f'lab_{i}_ggt': '', 
            f'lab_{i}_bt': '', f'lab_{i}_alb': '', f'lab_{i}_amil': '', f'lab_{i}_lipas': '',
            
            # Linha 4: Cardio/Coag/Inflam
            f'lab_{i}_cpk': '', f'lab_{i}_pcr': '', f'lab_{i}_trop': '', 
            f'lab_{i}_tp': '', f'lab_{i}_ttpa': '',
            
            # Linha 5: Urina
            f'lab_{i}_ur_dens': '', f'lab_{i}_ur_le': '', f'lab_{i}_ur_nit': '', f'lab_{i}_ur_leu': '',
            f'lab_{i}_ur_hm': '', f'lab_{i}_ur_prot': '', f'lab_{i}_ur_cet': '', f'lab_{i}_ur_glic': '',
            
            # Linha 6: Gasometria
            f'lab_{i}_gas_tipo': 'Arterial', 
            f'lab_{i}_gas_ph': '', f'lab_{i}_gas_pco2': '', f'lab_{i}_gas_po2': '', f'lab_{i}_gas_hco3': '',
            f'lab_{i}_gas_be': '', f'lab_{i}_gas_sat': '', f'lab_{i}_gas_lac': '', f'lab_{i}_gas_ag': '',
            f'lab_{i}_gas_cl': '', f'lab_{i}_gas_na': '', f'lab_{i}_gas_k': '', f'lab_{i}_gas_cai': '',

            # Linha 7: Gaso Venosa
            f'lab_{i}_gasv_pco2': '', f'lab_{i}_svo2': '',

            # Linha 8: Outros
            f'lab_{i}_outros': '',
            
            # Linha 9: Conduta Específica desta data
            f'lab_{i}_conduta': ''
        })
    return campos

# Função auxiliar para desenhar UM card de data
def _render_slot(i):
    titulo = "Último Resultado" if i == 1 else f"Resultado Anterior #{i}"
    
    with st.container(border=True):
        # Cabeçalho: Data
        c_tit, c_date = st.columns([2, 1], vertical_alignment="center")
        c_tit.markdown(f"**📅 {titulo}**")
        c_date.text_input(f"Data #{i}", key=f'lab_{i}_data', placeholder="DD/MM", label_visibility="collapsed")
        
        # Removi o "---" daqui para não quebrar o visual
        
        # LINHA 1: Hemato
        cols1 = st.columns([1, 1, 1, 1, 1, 2.5, 1.2])
        with cols1[0]: st.text_input("Hb", key=f'lab_{i}_hb', placeholder="g/dL")
        with cols1[1]: st.text_input("Ht", key=f'lab_{i}_ht', placeholder="%")
        with cols1[2]: st.text_input("VCM", key=f'lab_{i}_vcm')
        with cols1[3]: st.text_input("HCM", key=f'lab_{i}_hcm')
        with cols1[4]: st.text_input("RDW", key=f'lab_{i}_rdw')
        with cols1[5]: st.text_input("Leuco (Dif)", key=f'lab_{i}_leuco', placeholder="Total (Seg/Bast)")
        with cols1[6]: st.text_input("Plaq", key=f'lab_{i}_plaq', placeholder="x10³")
        
        # LINHA 2: Renal
        cols2 = st.columns(7)
        with cols2[0]: st.text_input("Cr", key=f'lab_{i}_cr')
        with cols2[1]: st.text_input("Ur", key=f'lab_{i}_ur')
        with cols2[2]: st.text_input("Na", key=f'lab_{i}_na')
        with cols2[3]: st.text_input("K", key=f'lab_{i}_k')
        with cols2[4]: st.text_input("Mg", key=f'lab_{i}_mg')
        with cols2[5]: st.text_input("Pi", key=f'lab_{i}_pi')
        with cols2[6]: st.text_input("CaT", key=f'lab_{i}_cat')

        # LINHA 3: Hepático
        cols3 = st.columns(8)
        with cols3[0]: st.text_input("TGP", key=f'lab_{i}_tgp')
        with cols3[1]: st.text_input("TGO", key=f'lab_{i}_tgo')
        with cols3[2]: st.text_input("FAL", key=f'lab_{i}_fal')
        with cols3[3]: st.text_input("GGT", key=f'lab_{i}_ggt')
        with cols3[4]: st.text_input("BT", key=f'lab_{i}_bt')
        with cols3[5]: st.text_input("Alb", key=f'lab_{i}_alb')
        with cols3[6]: st.text_input("Amil", key=f'lab_{i}_amil')
        with cols3[7]: st.text_input("Lipas", key=f'lab_{i}_lipas')

        # LINHA 4: Cardio/Coag
        cols4 = st.columns(5)
        with cols4[0]: st.text_input("CPK", key=f'lab_{i}_cpk')
        with cols4[1]: st.text_input("PCR", key=f'lab_{i}_pcr')
        with cols4[2]: st.text_input("Trop", key=f'lab_{i}_trop')
        with cols4[3]: st.text_input("TP", key=f'lab_{i}_tp')
        with cols4[4]: st.text_input("TTPa", key=f'lab_{i}_ttpa')

        # LINHA 5: Urina (Sem separador visual, apenas label discreto)
        st.caption("🧪 Urina (EAS)")
        u1, u2, u3, u4, u5, u6, u7, u8 = st.columns(8)
        with u1: st.text_input("Dens", key=f'lab_{i}_ur_dens', placeholder="1035")
        with u2: st.text_input("L.Est", key=f'lab_{i}_ur_le', placeholder="Neg")
        with u3: st.text_input("Nit", key=f'lab_{i}_ur_nit', placeholder="Neg")
        with u4: st.text_input("Leuco", key=f'lab_{i}_ur_leu', placeholder="4k")
        with u5: st.text_input("Hm", key=f'lab_{i}_ur_hm', placeholder="2k")
        with u6: st.text_input("Prot", key=f'lab_{i}_ur_prot', placeholder="Neg")
        with u7: st.text_input("Cet", key=f'lab_{i}_ur_cet', placeholder="Neg")
        with u8: st.text_input("Glic", key=f'lab_{i}_ur_glic', placeholder="Neg")

        # LINHA 6: Gasometria
        st.caption("🫁 Gasometria")
        # Botão inline
        st.radio(f"Gaso #{i}", ["Arterial", "Venosa"], key=f'lab_{i}_gas_tipo', horizontal=True, label_visibility="collapsed")
        
        g1 = st.columns(6)
        with g1[0]: st.text_input("pH", key=f'lab_{i}_gas_ph')
        with g1[1]: st.text_input("pCO2", key=f'lab_{i}_gas_pco2')
        with g1[2]: st.text_input("pO2", key=f'lab_{i}_gas_po2')
        with g1[3]: st.text_input("HCO3", key=f'lab_{i}_gas_hco3')
        with g1[4]: st.text_input("BE", key=f'lab_{i}_gas_be')
        with g1[5]: st.text_input("SatO2", key=f'lab_{i}_gas_sat')
        
        g2 = st.columns(6)
        with g2[0]: st.text_input("Lac", key=f'lab_{i}_gas_lac')
        with g2[1]: st.text_input("AG", key=f'lab_{i}_gas_ag')
        with g2[2]: st.text_input("Cl", key=f'lab_{i}_gas_cl')
        with g2[3]: st.text_input("Na", key=f'lab_{i}_gas_na')
        with g2[4]: st.text_input("K", key=f'lab_{i}_gas_k')
        with g2[5]: st.text_input("Cai", key=f'lab_{i}_gas_cai')

        # LINHA 7: Gasometria Venosa / Perfusão
        st.caption("🩸 Perfusão")
        gp1, gp2, gp3 = st.columns([1, 1, 4])
        with gp1: st.text_input("pCO2(v)", key=f'lab_{i}_gasv_pco2')
        with gp2: st.text_input("SvO2", key=f'lab_{i}_svo2')
        with gp3: st.write("")

        # LINHA 8: Outros
        st.text_input(
            "➕ Outros", 
            key=f'lab_{i}_outros', 
            placeholder="Ex: Culturas parciais, Níveis séricos, etc."
        )

        # LINHA 9: Conduta (EM LINHA, dentro do bloco)
        with st.success("👉 Conduta / Análise"):
            st.text_input(
                "Conduta Laboratorial", 
                key=f"lab_{i}_conduta", 
                label_visibility="collapsed",
                placeholder="Ex: Repor K+, solicitar nova gasometria..."
            )

# 2. Renderização Principal
def render():
    st.markdown("##### 10. Laboratoriais (Curva)")
    
    # --- 2 Datas VISÍVEIS ---
    _render_slot(1)
    st.write("")
    _render_slot(2)
    
    # --- 8 Datas OCULTAS ---
    st.write("")
    with st.expander("➕ Ver histórico laboratorial antigo (Slots 3 a 10)"):
        for i in range(3, 11):
            _render_slot(i)
            st.write("")