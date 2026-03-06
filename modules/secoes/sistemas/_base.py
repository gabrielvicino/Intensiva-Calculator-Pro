import streamlit as st


def _evo_header():
    """Cabeçalho das colunas de evolução (5 slots)."""
    _, lbl_c, v1, v2, v3, v4, v5 = st.columns([0.5, 1.5, 1, 1, 1, 1, 1])
    with lbl_c: st.caption("Campo")
    with v1:    st.caption("Hoje")
    with v2:    st.caption("Ontem")
    with v3:    st.caption("Anteontem")
    with v4:    st.caption("4º")
    with v5:    st.caption("5º")


def _evo_row(label, prefix):
    """Linha de evolução: checkbox prontuário | label | 5 inputs (hoje→5º)."""
    cb_c, lbl_c, v1, v2, v3, v4, v5 = st.columns([0.5, 1.5, 1, 1, 1, 1, 1])
    with cb_c:
        st.checkbox("📋", key=f"{prefix}_show", help="Colocar no prontuário", label_visibility="collapsed")
    with lbl_c:
        st.markdown(f"**{label}**")
    with v1: st.text_input(f"{label} hoje",    key=f"{prefix}_hoje",    placeholder="Hoje",    label_visibility="collapsed")
    with v2: st.text_input(f"{label} ontem",   key=f"{prefix}_ult",     placeholder="Ontem",   label_visibility="collapsed")
    with v3: st.text_input(f"{label} antepen", key=f"{prefix}_antepen", placeholder="Antepen", label_visibility="collapsed")
    with v4: st.text_input(f"{label} 4o",      key=f"{prefix}_ant4",    placeholder="4º",      label_visibility="collapsed")
    with v5: st.text_input(f"{label} 5o",      key=f"{prefix}_ant5",    placeholder="5º",      label_visibility="collapsed")
