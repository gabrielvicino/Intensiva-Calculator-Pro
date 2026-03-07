"""
bridge.py -- copia de dados entre blocos: Lab/Ctrl/ATB/Culturas -> Sistemas (bloco 13).
"""
import streamlit as st
from .state import _limpar, _limpar_leuco, _extrair_parenteses


def completar_sistemas_de_outros_blocos() -> None:
    """
    Copia dados de Laboratoriais (bloco 10), Controles (bloco 11),
    Antibioticos e Culturas para os campos sis_* do Bloco 13 (Sistemas).

    Regra: so preenche se o campo de destino estiver vazio -- preserva dados manuais.
    """
    # Tuplas (sis_suf, ctrl_suf, lab_idx) para os 5 slots historicos
    _SLOTS = [
        ("hoje",    "hoje",       1),
        ("ult",     "ontem",      2),
        ("antepen", "anteontem",  3),
        ("ant4",    "ant4",       4),
        ("ant5",    "ant5",       5),
    ]

    staging = st.session_state.get("_agent_staging", {})
    cnt = [0]

    def _set(sis_key: str, val: str) -> None:
        dest = st.session_state.get(sis_key, "") or ""
        if val and not str(dest).strip():
            staging[sis_key] = val
            cnt[0] += 1

    # 1. Controles -> Renal (campos fixos de hoje)
    _set("sis_renal_diurese", _limpar(st.session_state.get("ctrl_hoje_diurese", "")))
    _set("sis_renal_balanco",  _limpar(st.session_state.get("ctrl_hoje_balanco", "")))

    # 2. Controles -> Renal (evolucao 5 slots)
    for sis_suf, ctrl_suf, _ in _SLOTS:
        _set(f"sis_renal_diu_{sis_suf}", _limpar(st.session_state.get(f"ctrl_{ctrl_suf}_diurese", "")))
        _set(f"sis_renal_bh_{sis_suf}",  _limpar(st.session_state.get(f"ctrl_{ctrl_suf}_balanco", "")))

    # 3. Laboratoriais -> Renal (Cr, Ur, Na, K, Mg, Fos, CaI -- 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_renal_cr_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_cr",  "")))
        _set(f"sis_renal_ur_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_ur",  "")))
        _set(f"sis_renal_na_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_na",  "")))
        _set(f"sis_renal_k_{sis_suf}",   _limpar(st.session_state.get(f"lab_{lab_idx}_k",   "")))
        _set(f"sis_renal_mg_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_mg",  "")))
        _set(f"sis_renal_fos_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_pi",  "")))
        _set(f"sis_renal_cai_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_cai", "")))

    # 4. Antibioticos atuais -> Infeccioso (ate 3 ATBs com status "Atual")
    ordem_atb = st.session_state.get("atb_ordem", list(range(1, 9)))
    atuais = [
        st.session_state.get(f"atb_{idx}_nome", "")
        for idx in ordem_atb
        if st.session_state.get(f"atb_{idx}_status") == "Atual"
    ]
    for i in range(1, 4):
        _set(f"sis_infec_atb_{i}", _limpar(atuais[i - 1] if i <= len(atuais) else ""))

    # 5. Culturas -> Infeccioso (sitio e data de coleta, slots 1-4)
    for i in range(1, 5):
        _set(f"sis_infec_cult_{i}_sitio", _limpar(st.session_state.get(f"cult_{i}_sitio",       "")))
        _set(f"sis_infec_cult_{i}_data",  _limpar(st.session_state.get(f"cult_{i}_data_coleta", "")))

    # 6. Laboratoriais -> Infeccioso (PCR, Leucocitos, VHS -- 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_infec_pcr_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_pcr",   "")))
        _set(f"sis_infec_leuc_{sis_suf}", _limpar_leuco(st.session_state.get(f"lab_{lab_idx}_leuco", "")))
        _set(f"sis_infec_vhs_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_vhs",   "")))

    # 7. Laboratoriais -> Hematologico (Hb, Plaq, INR, TTPa -- 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_hemato_hb_{sis_suf}",   _limpar(st.session_state.get(f"lab_{lab_idx}_hb",   "")))
        _set(f"sis_hemato_plaq_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_plaq", "")))
        _set(f"sis_hemato_inr_{sis_suf}",  _extrair_parenteses(st.session_state.get(f"lab_{lab_idx}_tp",   "")))
        _set(f"sis_hemato_ttpa_{sis_suf}", _extrair_parenteses(st.session_state.get(f"lab_{lab_idx}_ttpa", "")))

    # 8. Laboratoriais -> Gastro/TGI (TGO, TGP, FAL, GGT, BT -- 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_gastro_tgo_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_tgo", "")))
        _set(f"sis_gastro_tgp_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_tgp", "")))
        _set(f"sis_gastro_fal_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_fal", "")))
        _set(f"sis_gastro_ggt_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_ggt", "")))
        _set(f"sis_gastro_bt_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_bt",  "")))

    # 9. Laboratoriais -> Cardiovascular (Troponina e Lactato -- 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_cardio_trop_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_trop", "")))
        # Lactato: primeiro gas disponivel do dia (gas > gas2 > gas3)
        lac = next(
            (_limpar(st.session_state.get(f"lab_{lab_idx}_{gn}_lac", ""))
             for gn in ("gas", "gas2", "gas3")
             if _limpar(st.session_state.get(f"lab_{lab_idx}_{gn}_lac", ""))),
            ""
        )
        _set(f"sis_cardio_lac_{sis_suf}", lac)

    # 10. Laboratoriais -> Pele/Musculoesqueletico (CPK -- 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_pele_cpk_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_cpk", "")))

    st.session_state["_agent_staging"] = staging
    if cnt[0]:
        st.toast(f"{cnt[0]} campos preenchidos a partir dos Blocos Anteriores!", icon="📋")
    else:
        st.warning("Nenhum valor encontrado nos blocos de origem. Preencha Controles, Lab, Antibioticos e Culturas primeiro.")
    st.rerun()
