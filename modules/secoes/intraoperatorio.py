import streamlit as st


def get_campos() -> dict:
    campos = {
        'io_cirurgia':       '',
        'io_data':           '',
        'io_duracao':        '',
        'io_diurese':        '',
        'io_intercorrencias':'',
        'io_obs':            '',
        'io_conduta':        '',
    }
    for i in range(1, 6):
        campos[f'io_ent_{i}_sol'] = ''
        campos[f'io_ent_{i}_vol'] = ''
    for i in range(1, 5):  # 4 slots genéricos + 1 diurese dedicada = 5 linhas totais
        campos[f'io_sai_{i}_sol'] = ''
        campos[f'io_sai_{i}_vol'] = ''
    return campos


def render():
    """Renderiza o bloco 6 — Intraoperatório (dentro do st.form)."""
    st.markdown('<span id="sec-7"></span>', unsafe_allow_html=True)
    st.markdown("##### 7. Intraoperatório")

    # ── Cirurgia + Data ────────────────────────────────────────────────────────
    c_cir, c_data = st.columns([3, 1])
    with c_cir:
        st.text_input("Cirurgia", key="io_cirurgia",
                      placeholder="Ex.: Colecistectomia VLP + Hepatectomia à direita")
    with c_data:
        st.text_input("Data", key="io_data", placeholder="DD/MM/AAAA")

    # ── Duração ────────────────────────────────────────────────────────────────
    c_dur, *_ = st.columns([1, 3])
    with c_dur:
        st.text_input("Duração", key="io_duracao",
                      placeholder="Ex.: 06h / 20min / 06h 20min")

    st.write("")

    # ── Entradas e Saídas lado a lado ─────────────────────────────────────────
    col_ent, col_sai = st.columns(2)

    with col_ent:
        st.markdown("**Entradas**")
        for i in range(1, 6):
            c_sol, c_vol = st.columns([3, 1])
            with c_sol:
                st.text_input(
                    f"Entrada {i} — solução", key=f"io_ent_{i}_sol",
                    placeholder=f"Ex.: Ringer Lactato",
                    label_visibility="collapsed",
                )
            with c_vol:
                st.text_input(
                    f"Entrada {i} — volume", key=f"io_ent_{i}_vol",
                    placeholder="500",
                    label_visibility="collapsed",
                )

    with col_sai:
        st.markdown("**Saídas**")
        # Diurese: campo dedicado (linha 1 das saídas)
        c_sol_diu, c_vol_diu = st.columns([3, 1])
        with c_sol_diu:
            st.markdown(
                '<div style="padding:5px 0 3px 0;font-size:0.95rem;font-weight:600;color:#333;">Diurese</div>',
                unsafe_allow_html=True,
            )
        with c_vol_diu:
            st.text_input(
                "Diurese intraoperatória (ml)", key="io_diurese",
                placeholder="400",
                label_visibility="collapsed",
            )
        # Saídas genéricas (4 slots — total 5 linhas com diurese, proporcional às entradas)
        for i in range(1, 5):
            c_sol, c_vol = st.columns([3, 1])
            with c_sol:
                st.text_input(
                    f"Saída {i} — solução", key=f"io_sai_{i}_sol",
                    placeholder=f"Ex.: Sangramento",
                    label_visibility="collapsed",
                )
            with c_vol:
                st.text_input(
                    f"Saída {i} — volume", key=f"io_sai_{i}_vol",
                    placeholder="1000",
                    label_visibility="collapsed",
                )

    st.write("")

    # ── Intercorrências e Obs ──────────────────────────────────────────────────
    st.text_input("Intercorrências", key="io_intercorrencias",
                  placeholder="Ex.: Sangramento, distúrbio hidroeletrolítico, vasopressor")
    st.text_input("Obs", key="io_obs",
                  placeholder="Ex.: Tempo de isquemia 5h, tempo de CEC 3h")

    # ── Conduta (borda verde via CSS global — placeholder exato obrigatório) ───
    st.text_input(
        "Conduta",
        key="io_conduta",
        placeholder="Escreva a conduta aqui...",
        label_visibility="collapsed",
    )
