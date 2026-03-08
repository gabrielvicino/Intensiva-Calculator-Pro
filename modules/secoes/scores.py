import streamlit as st


def get_campos() -> dict:
    return {
        'scores_notas': '',
        # SAPS
        'saps3':    '',
        'saps2':    '',
        # APACHE
        'apache3':  '',
        'apache2':  '',
        'apache4':  '',
        # SOFA: admissão (fixo) + janela deslizante de 4 slots (0 = vazio)
        'sofa_adm': 0,
        'sofa_d1':  0,
        'sofa_d2':  0,
        'sofa_d3':  0,
        'sofa_d4':  0,
        # Funcionalidade / prognóstico
        'pps':  '',
        'mrs':  '',
        'cfs':  '',
    }


def _shift_sofa():
    """
    Desloca a janela de SOFA:
      d1 (mais antigo) é descartado
      d2 → d1, d3 → d2, d4 → d3
      d4 fica vazio (0) para o novo valor do dia
    sofa_adm nunca é alterado.
    """
    ss = st.session_state
    new_vals = [
        ss.get("sofa_d2", 0),
        ss.get("sofa_d3", 0),
        ss.get("sofa_d4", 0),
        0,
    ]
    for i, v in enumerate(new_vals, 1):
        k = f"sofa_d{i}"
        if k in ss:
            del ss[k]
        ss[k] = v


def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-2"></span>', unsafe_allow_html=True)
    st.markdown("##### 2. Scores Clínicos")

    st.text_area("Notas", key="scores_notas", height="content",
                 placeholder="Cole neste campo a evolução...",
                 label_visibility="collapsed")
    st.write("")
    if _agent_btn_callback:
        _agent_btn_callback()

    with st.container(border=True):
        # ── Linha 1: SAPS 3 | SAPS 2 | APACHE 3 | APACHE 2 | APACHE 4 (5 colunas iguais)
        s1, s2, a1, a2, a4 = st.columns(5)
        with s1:
            st.markdown("**SAPS 3**")
            st.text_input("SAPS 3", key="saps3", label_visibility="collapsed",
                          placeholder="Ex: 72")
        with s2:
            st.markdown("**SAPS 2**")
            st.text_input("SAPS 2", key="saps2", label_visibility="collapsed",
                          placeholder="Ex: 40")
        with a1:
            st.markdown("**APACHE 3**")
            st.text_input("APACHE 3", key="apache3", label_visibility="collapsed",
                          placeholder="Ex: 60")
        with a2:
            st.markdown("**APACHE 2**")
            st.text_input("APACHE 2", key="apache2", label_visibility="collapsed",
                          placeholder="Ex: 18")
        with a4:
            st.markdown("**APACHE 4**")
            st.text_input("APACHE 4", key="apache4", label_visibility="collapsed",
                          placeholder="Ex: 55")

        st.write("")

        # ── Linha 2: SOFA Admissão | SOFA 1 | SOFA 2 | SOFA 3 | SOFA 4 (5 colunas iguais)
        c_adm, c_d1, c_d2, c_d3, c_d4 = st.columns(5)

        with c_adm:
            st.markdown("**SOFA Admissão**")
            st.number_input("SOFA Admissão", min_value=0, max_value=24,
                            key="sofa_adm", label_visibility="collapsed")

        for col, idx, lbl in [
            (c_d1, 1, "SOFA 1"),
            (c_d2, 2, "SOFA 2"),
            (c_d3, 3, "SOFA 3"),
            (c_d4, 4, "SOFA 4"),
        ]:
            with col:
                st.markdown(f"**{lbl}**")
                st.number_input(lbl, min_value=0, max_value=24,
                                key=f"sofa_d{idx}", label_visibility="collapsed")

        # ── Linha 3: botão "Novo SOFA" embaixo do SOFA Admissão ─────────────
        c_btn, _ = st.columns([1, 4])
        with c_btn:
            if st.form_submit_button(
                "Novo SOFA",
                key="_fsbtn_sofa_shift",
                help="Descarta o SOFA 1 (mais antigo), desloca 2→1, 3→2, 4→3 e libera o SOFA 4 para o novo valor",
                use_container_width=True,
            ):
                st.session_state["_sofa_registrar_pendente"] = True

        st.write("")

        # ── Linha 4: PPS | mRS | CFS ─────────────────────────────────────────
        p1, p2, p3 = st.columns(3)

        with p1:
            st.markdown("**PPS (%)**")
            st.text_input("PPS (%)", key="pps", placeholder="Ex: 80%",
                          label_visibility="collapsed")

        with p2:
            st.markdown("**mRS (Rankin Modificado)**")
            st.selectbox(
                "mRS (Rankin Modificado)",
                ["", "0", "1", "2", "3", "4", "5", "6"],
                key="mrs",
                label_visibility="collapsed",
            )

        with p3:
            st.markdown("**CFS (Fragilidade Clínica)**")
            st.selectbox(
                "CFS (Fragilidade Clínica)",
                [
                    "",
                    "1 - Muito em forma", "2 - Bem", "3 - Controlando bem",
                    "4 - Vulnerável", "5 - Levemente frágil",
                    "6 - Moderadamente frágil", "7 - Severamente frágil",
                    "8 - Muito severamente frágil", "9 - Doente terminal",
                ],
                key="cfs",
                label_visibility="collapsed",
            )
