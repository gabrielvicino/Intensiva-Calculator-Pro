import streamlit as st
from . import neuro, resp, cardio, gastro, renal, infec, hemato, pele

# Sistemas sem render dedicado (apenas campos genéricos)
_SISTEMAS_GENERICOS = ["metab", "nutri"]

# Campos com esquema 5→4→3→2→1 (ant5=mais antigo, hoje=mais recente)
_CAMPOS_ANTE_ONTEM_HOJE = [
    # Renal
    ("sis_renal_cr",    "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_ur",    "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_diu",   "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_bh",    "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_na",    "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_k",     "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_mg",    "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_fos",   "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_renal_cai",   "ant5", "ant4", "antepen", "ult", "hoje"),
    # Infeccioso
    ("sis_infec_pcr",   "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_infec_leuc",  "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_infec_vhs",   "ant5", "ant4", "antepen", "ult", "hoje"),
    # TGI / Gastro
    ("sis_gastro_tgo",  "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_gastro_tgp",  "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_gastro_fal",  "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_gastro_ggt",  "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_gastro_bt",   "ant5", "ant4", "antepen", "ult", "hoje"),
    # Cardiológico
    ("sis_cardio_lac",  "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_cardio_trop", "ant5", "ant4", "antepen", "ult", "hoje"),
    # Hematológico
    ("sis_hemato_hb",   "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_hemato_plaq", "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_hemato_inr",  "ant5", "ant4", "antepen", "ult", "hoje"),
    ("sis_hemato_ttpa", "ant5", "ant4", "antepen", "ult", "hoje"),
    # Pele / Musculoesquelético
    ("sis_pele_cpk",    "ant5", "ant4", "antepen", "ult", "hoje"),
]


def _deslocar_sistemas():
    """Desloca 5 slots: ant5 some, ant4→ant5, antepen→ant4, ult→antepen, hoje→ult, hoje fica vazio."""
    for prefix, s5, s4, s3, s2, s1 in _CAMPOS_ANTE_ONTEM_HOJE:
        v4 = st.session_state.get(f"{prefix}_{s4}", "") or ""
        v3 = st.session_state.get(f"{prefix}_{s3}", "") or ""
        v2 = st.session_state.get(f"{prefix}_{s2}", "") or ""
        v1 = st.session_state.get(f"{prefix}_{s1}", "") or ""
        st.session_state[f"{prefix}_{s5}"] = v4
        st.session_state[f"{prefix}_{s4}"] = v3
        st.session_state[f"{prefix}_{s3}"] = v2
        st.session_state[f"{prefix}_{s2}"] = v1
        st.session_state[f"{prefix}_{s1}"] = ""


def get_campos():
    """Retorna todos os campos de todos os sistemas com seus valores padrão."""
    campos = {"sistemas_notas": ""}
    # Campos genéricos (pocus, obs, conduta) para sistemas sem render dedicado
    for s in _SISTEMAS_GENERICOS:
        campos[f"sis_{s}_pocus"]   = ""
        campos[f"sis_{s}_obs"]     = ""
        campos[f"sis_{s}_conduta"] = ""
    # Campos específicos de cada sistema
    for mod in (neuro, resp, cardio, gastro, renal, infec, hemato, pele):
        campos.update(mod._campos())
    return campos


def render(_agent_btn_callback=None, *, show_toolbar: bool = True, show_notas: bool = True):
    """Renderiza o bloco completo de Evolução por Sistemas."""
    st.markdown('<span id="sec-14"></span>', unsafe_allow_html=True)
    st.markdown("##### 14. Evolução por Sistemas")

    if show_notas:
        st.text_area("Notas", key="sistemas_notas", height="content",
                     placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
        st.write("")

    if show_toolbar:
        col_evo, col_ag, _ = st.columns([1, 1, 8])
        with col_evo:
            evo_clicked = st.form_submit_button(
                "Evolução Hoje", key="btn_evolucao_hoje_sistemas",
                use_container_width=True,
                help="Anteontem some; ontem vira anteontem; hoje vira ontem; hoje fica vazio.",
            )
            if evo_clicked:
                _deslocar_sistemas()
                st.toast("✅ Dados deslocados. Ontem → anteontem, hoje → ontem. Campos de hoje prontos para preenchimento.", icon="✅")
        with col_ag:
            if _agent_btn_callback:
                _agent_btn_callback()

    neuro.render()
    resp.render()
    cardio.render()
    gastro.render()
    renal.render()
    infec.render()
    hemato.render()
    pele.render()
