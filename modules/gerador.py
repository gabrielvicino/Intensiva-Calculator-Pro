import streamlit as st

def gerar_texto_final():
    """
    Lê os dados do st.session_state e monta o texto final do prontuário.
    Retorna uma string formatada.
    """
    linhas = []

    # --- 1. Identidade ---
    l1 = f"Nome: {st.session_state.get('nome', '')}"
    if st.session_state.get('idade'): l1 += f", {st.session_state['idade']} anos"
    if st.session_state.get('sexo'): l1 += f", {st.session_state['sexo']}"
    if st.session_state.get('origem'): l1 += f", {st.session_state['origem']}"
    if st.session_state.get('leito'): l1 += f" - {st.session_state['leito']}"
    linhas.append(l1)

    # --- 2. Datas ---
    if st.session_state.get('di_hosp'): linhas.append(f"DIH: {st.session_state['di_hosp']}")
    if st.session_state.get('di_enf'): linhas.append(f"DI-ENF: {st.session_state['di_enf']}")
    if st.session_state.get('di_uti'): linhas.append(f"DI-UTI: {st.session_state['di_uti']}")

    # --- 3. Equipe ---
    if st.session_state.get('equipe'): linhas.append(f"Equipe Responsável: {st.session_state['equipe']}")

    # --- 4. SAPS ---
    if st.session_state.get('saps3'): linhas.append(f"SAPS-3: {st.session_state['saps3']}")

    # --- 5. SOFA ---
    linha_sofa = []
    sofa_atual = int(st.session_state.get('sofa_atual') or 0)
    sofa_adm = int(st.session_state.get('sofa_adm') or 0)

    if sofa_atual: linha_sofa.append(f"SOFA Atual: {sofa_atual}")
    if sofa_adm: linha_sofa.append(f"Sofa Adm: {sofa_adm}")

    if sofa_adm > 0:
        delta = sofa_atual - sofa_adm
        sinal = "+" if delta > 0 else ""
        linha_sofa.append(f"Delta SOFA: {sinal}{delta}")

    if linha_sofa: linhas.append(" | ".join(linha_sofa))

    # --- 6. Funcionalidade ---
    linha_func = []
    if st.session_state.get('mrs'): linha_func.append(f"mRs: {st.session_state['mrs']}")
    if st.session_state.get('cfs'): linha_func.append(f"CFS: {st.session_state['cfs']}")
    if st.session_state.get('pps'): linha_func.append(f"PPS: {st.session_state['pps']}")
    if linha_func: linhas.append(" ".join(linha_func))

    # --- 7. Diagnósticos ---
    if st.session_state.get('hd_principal'):
        linhas.append(f"HD: {st.session_state['hd_principal']} ({st.session_state.get('hd_status', '')})")

    # --- 8. Paliativo ---
    if st.session_state.get('paliativo'): linhas.append("[Priorizar medidas para conforto]")

    # Montagem Final
    return "# Identidade\n" + "\n".join(linhas)