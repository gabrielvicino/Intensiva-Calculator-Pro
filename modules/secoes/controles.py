import streamlit as st

# Parâmetros: (chave, label, tem_min_max)
_PARAMS = [
    ("pas",     "Pressão Arterial Sistólica (mmHg)",   True),
    ("pad",     "Pressão Arterial Diastólica (mmHg)",  True),
    ("pam",     "Pressão Arterial Média (mmHg)",       True),
    ("fc",      "Frequência Cardíaca (bpm)",           True),
    ("fr",      "Frequência Respiratória (irpm)",      True),
    ("sato2",   "Saturação de O₂ (%)",                 True),
    ("temp",    "Temperatura (°C)",                    True),
    ("glic",    "Glicemia (mg/dL)",                    True),
    ("diurese", "Diurese",                             False),
    ("balanco", "Balanço Hídrico",                     False),
]

_DIAS = ["hoje", "ontem", "anteontem", "ant4", "ant5"]

_COLS_HEADER = [1.5, 1, 1, 1, 1, 1]
_COLS_DATA   = [1.5, 1, 1, 1, 1, 1]

_LABEL_DIA = {
    "hoje":      "Hoje",
    "ontem":     "Ontem",
    "anteontem": "Anteontem",
    "ant4":      "4º dia",
    "ant5":      "5º dia",
}


def _deslocar_dias():
    """
    Desloca 5 slots: ant5 some | ant4→ant5 | anteontem→ant4 | ontem→anteontem | hoje→ontem | hoje vazio.
    """
    ordem = ["ant5", "ant4", "anteontem", "ontem", "hoje"]
    for chave, _, min_max in _PARAMS:
        if min_max:
            for i in range(len(ordem) - 1):
                dst, src = ordem[i], ordem[i + 1]
                st.session_state[f"ctrl_{dst}_{chave}_min"] = st.session_state.get(f"ctrl_{src}_{chave}_min", "")
                st.session_state[f"ctrl_{dst}_{chave}_max"] = st.session_state.get(f"ctrl_{src}_{chave}_max", "")
            st.session_state[f"ctrl_hoje_{chave}_min"] = ""
            st.session_state[f"ctrl_hoje_{chave}_max"] = ""
        else:
            for i in range(len(ordem) - 1):
                dst, src = ordem[i], ordem[i + 1]
                st.session_state[f"ctrl_{dst}_{chave}"] = st.session_state.get(f"ctrl_{src}_{chave}", "")
            st.session_state[f"ctrl_hoje_{chave}"] = ""
    for i in range(len(ordem) - 1):
        dst, src = ordem[i], ordem[i + 1]
        st.session_state[f"ctrl_{dst}_data"] = st.session_state.get(f"ctrl_{src}_data", "")
    st.session_state["ctrl_hoje_data"] = ""


def get_campos():
    campos = {"controles_notas": "", "ctrl_conduta": "", "ctrl_periodo": "24 horas"}
    for dia in ["hoje", "ontem", "anteontem", "ant4", "ant5"]:
        campos[f"ctrl_{dia}_data"] = ""
        for chave, _, min_max in _PARAMS:
            if min_max:
                campos[f"ctrl_{dia}_{chave}_min"] = ""
                campos[f"ctrl_{dia}_{chave}_max"] = ""
            else:
                campos[f"ctrl_{dia}_{chave}"] = ""
    return campos


def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-11"></span>', unsafe_allow_html=True)
    st.markdown("##### 11. Controles & Balanço Hídrico")

    # Campo notas para extração da IA
    st.text_area(
        "controles_notas",
        key="controles_notas",
        height=None,
        placeholder="Cole neste campo os controles do prontuário...",
        label_visibility="collapsed",
    )

    st.markdown("""
    <style>
        input[id*="ctrl_hoje_data"], input[id*="ctrl_ontem_data"],
        input[id*="ctrl_anteontem_data"], input[id*="ctrl_ant4_data"], input[id*="ctrl_ant5_data"] {
            text-align: center;
        }
        input[id*="ctrl_hoje_data"]::placeholder, input[id*="ctrl_ontem_data"]::placeholder,
        input[id*="ctrl_anteontem_data"]::placeholder, input[id*="ctrl_ant4_data"]::placeholder,
        input[id*="ctrl_ant5_data"]::placeholder { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        # Botão Evolução Hoje | Parsing Controles | Completar Campos | Comparar | Período
        _col_evo, _col_parse, _col_agente, _col_cmp, _col_periodo = st.columns([1, 1, 1, 1, 1])
        with _col_evo:
            if st.form_submit_button(
                "Evolução Hoje",
                use_container_width=True,
                help="Anteontem some; ontem vira anteontem; hoje vira ontem; hoje fica em branco para novos dados.",
            ):
                _deslocar_dias()
                st.toast("Evolução Hoje: hoje está em branco para novos dados.", icon="📅")
        with _col_parse:
            if st.form_submit_button(
                "Parsing Controles",
                use_container_width=True,
                help="Preenche deterministicamente (# Controles - 24h, > DD/MM, PAS: min - max...). Não perde dados.",
            ):
                st.session_state["_ctrl_deterministico_pendente"] = True
        with _col_agente:
            if _agent_btn_callback:
                _agent_btn_callback()
        with _col_cmp:
            if st.form_submit_button(
                "Comparar",
                key="_fsbtn_comparar_ctrl",
                use_container_width=True,
                help="Tabela comparativa dos controles: vitais e balanço por dia",
            ):
                st.session_state["_comparar_ctrl_pendente"] = True
        with _col_periodo:
            st.pills(
                "Período",
                ["24 horas", "12 horas"],
                key="ctrl_periodo",
                label_visibility="collapsed",
            )

        # ── Cabeçalho: 5 colunas (hoje | ontem | anteontem | 4º | 5º) ──────────
        h = st.columns(_COLS_HEADER)
        with h[0]:
            st.markdown("**Parâmetro**")
        for col_idx, dia in enumerate(_DIAS, start=1):
            with h[col_idx]:
                st.markdown(f"**{_LABEL_DIA[dia]}**")
                st.text_input(f"data_{dia}", key=f"ctrl_{dia}_data",
                              placeholder="dd/mm", label_visibility="collapsed")

        # ── Linhas de parâmetros: 5 colunas ───────────────────────────────────
        for chave, label, min_max in _PARAMS:
            r = st.columns(_COLS_DATA)
            with r[0]:
                st.markdown(f"**{label}**")

            if min_max:
                for col_idx, dia in enumerate(_DIAS, start=1):
                    with r[col_idx]:
                        c_min, c_max = st.columns(2)
                        with c_min:
                            st.text_input(f"{dia}_{chave}_min", key=f"ctrl_{dia}_{chave}_min",
                                          placeholder="Mín", label_visibility="collapsed")
                        with c_max:
                            st.text_input(f"{dia}_{chave}_max", key=f"ctrl_{dia}_{chave}_max",
                                          placeholder="Máx", label_visibility="collapsed")
            else:
                for col_idx, dia in enumerate(_DIAS, start=1):
                    with r[col_idx]:
                        st.text_input(f"{dia}_{chave}", key=f"ctrl_{dia}_{chave}",
                                      placeholder="Valor", label_visibility="collapsed")

    st.text_input(
        "Conduta",
        key="ctrl_conduta",
        placeholder="Escreva a conduta aqui...",
        label_visibility="collapsed"
    )
