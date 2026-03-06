import streamlit as st
from modules import fichas

# ── Helpers de limpeza de valores (usados em completar_sistemas_de_outros_blocos) ──

def _limpar(v) -> str:
    """Remove barra e tudo após (ex: '1.2/72s' → '1.2')."""
    return str(v or "").split("/")[0].strip()

def _limpar_leuco(v) -> str:
    """Remove diferencial entre parênteses (ex: '12.500 (Seg 70%)' → '12.500')."""
    return _limpar(v).split("(")[0].strip()

def _extrair_parenteses(v) -> str:
    """Extrai valor entre parênteses; se ausente, aplica _limpar.
    Ex: '14.2s (1.10)' → '1.10'  |  '39,6s (1,41)' → '1,41'
    """
    s = str(v or "").strip()
    if "(" in s and ")" in s:
        return s.split("(")[1].split(")")[0].strip()
    return _limpar(s)


# Mapeamento: chave do JSON retornado pela IA → chave do session_state
_MAPA_NOTAS = {
    "identificacao": "identificacao_notas",
    "hd":            "hd_notas",
    "comorbidades":  "comorbidades_notas",
    "muc":           "muc_notas",
    "hmpa":          "hmpa_texto",
    "dispositivos":  "dispositivos_notas",
    "culturas":      "culturas_notas",
    "antibioticos":  "antibioticos_notas",
    "complementares":"complementares_notas",
    "laboratoriais": "laboratoriais_notas",
    "controles":     "controles_notas",
    "evolucao":      "evolucao_notas",
    "sistemas":      "sistemas_notas",
    "conduta":       "conduta_final_lista",
}

def atualizar_notas_ia(dados: dict):
    """Recebe o JSON do ia_extrator e preenche os campos _notas de cada seção."""
    if not dados:
        return

    erro = dados.get("_erro")
    if erro:
        st.error(f"Erro na extração: {erro}")
        return

    preenchidos = 0
    for chave_json, chave_estado in _MAPA_NOTAS.items():
        valor = dados.get(chave_json, "")
        if valor and valor.strip():
            st.session_state[chave_estado] = valor.strip()
            preenchidos += 1

    if preenchidos:
        st.toast(f"✅ {preenchidos} seções preenchidas com sucesso!", icon="🧬")
    else:
        st.warning("A IA não encontrou dados para preencher. Verifique o texto colado.")

def limpar_tudo():
    """Reseta TODOS os campos do formulário para o estado inicial."""
    defaults = fichas._campos_base()
    for k, v in defaults.items():
        st.session_state[k] = v
    st.session_state["idade"] = 0
    st.session_state["sofa_adm"] = 0
    st.session_state["sofa_atual"] = 0
    st.session_state["paliativo"] = False
    st.session_state["texto_final_gerado"] = ""
    st.session_state["texto_bruto_original"] = ""
    st.session_state.pop("_agent_staging", None)
    st.session_state.pop("_secoes_recortadas", None)
    st.session_state.pop("_data_hora_carregado", None)
    st.session_state["hd_ordem"] = list(range(1, 9))
    st.session_state["cult_ordem"] = list(range(1, 9))
    st.session_state["disp_ordem"] = list(range(1, 9))
    st.session_state["comp_ordem"] = list(range(1, 9))
    st.session_state["muc_ordem"] = list(range(1, 21))
    st.session_state["atb_ordem"] = list(range(1, 9))
    st.toast("✅ Todos os campos foram limpos.", icon="🗑️")
    st.rerun()


def completar_sistemas_de_outros_blocos() -> None:
    """
    Copia dados de Laboratoriais (bloco 10), Controles (bloco 11),
    Antibióticos e Culturas para os campos sis_* do Bloco 13 (Sistemas).

    Regra: só preenche se o campo de destino estiver vazio — preserva dados manuais.
    """
    # Tuplas (sis_suf, ctrl_suf, lab_idx) para os 5 slots históricos
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

    # 1. Controles → Renal (campos fixos de hoje)
    _set("sis_renal_diurese", _limpar(st.session_state.get("ctrl_hoje_diurese", "")))
    _set("sis_renal_balanco",  _limpar(st.session_state.get("ctrl_hoje_balanco", "")))

    # 2. Controles → Renal (evolução 5 slots)
    for sis_suf, ctrl_suf, _ in _SLOTS:
        _set(f"sis_renal_diu_{sis_suf}", _limpar(st.session_state.get(f"ctrl_{ctrl_suf}_diurese", "")))
        _set(f"sis_renal_bh_{sis_suf}",  _limpar(st.session_state.get(f"ctrl_{ctrl_suf}_balanco", "")))

    # 3. Laboratoriais → Renal (Cr, Ur, Na, K, Mg, Fos, CaI — 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_renal_cr_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_cr",  "")))
        _set(f"sis_renal_ur_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_ur",  "")))
        _set(f"sis_renal_na_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_na",  "")))
        _set(f"sis_renal_k_{sis_suf}",   _limpar(st.session_state.get(f"lab_{lab_idx}_k",   "")))
        _set(f"sis_renal_mg_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_mg",  "")))
        _set(f"sis_renal_fos_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_pi",  "")))
        _set(f"sis_renal_cai_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_cai", "")))

    # 4. Antibióticos atuais → Infeccioso (até 3 ATBs com status "Atual")
    ordem_atb = st.session_state.get("atb_ordem", list(range(1, 9)))
    atuais = [
        st.session_state.get(f"atb_{idx}_nome", "")
        for idx in ordem_atb
        if st.session_state.get(f"atb_{idx}_status") == "Atual"
    ]
    for i in range(1, 4):
        _set(f"sis_infec_atb_{i}", _limpar(atuais[i - 1] if i <= len(atuais) else ""))

    # 5. Culturas → Infeccioso (sítio e data de coleta, slots 1–4)
    for i in range(1, 5):
        _set(f"sis_infec_cult_{i}_sitio", _limpar(st.session_state.get(f"cult_{i}_sitio",       "")))
        _set(f"sis_infec_cult_{i}_data",  _limpar(st.session_state.get(f"cult_{i}_data_coleta", "")))

    # 6. Laboratoriais → Infeccioso (PCR, Leucócitos, VHS — 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_infec_pcr_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_pcr",   "")))
        _set(f"sis_infec_leuc_{sis_suf}", _limpar_leuco(st.session_state.get(f"lab_{lab_idx}_leuco", "")))
        _set(f"sis_infec_vhs_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_vhs",   "")))

    # 7. Laboratoriais → Hematológico (Hb, Plaq, INR, TTPa — 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_hemato_hb_{sis_suf}",   _limpar(st.session_state.get(f"lab_{lab_idx}_hb",   "")))
        _set(f"sis_hemato_plaq_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_plaq", "")))
        _set(f"sis_hemato_inr_{sis_suf}",  _extrair_parenteses(st.session_state.get(f"lab_{lab_idx}_tp",   "")))
        _set(f"sis_hemato_ttpa_{sis_suf}", _extrair_parenteses(st.session_state.get(f"lab_{lab_idx}_ttpa", "")))

    # 8. Laboratoriais → Gastro/TGI (TGO, TGP, FAL, GGT, BT — 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_gastro_tgo_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_tgo", "")))
        _set(f"sis_gastro_tgp_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_tgp", "")))
        _set(f"sis_gastro_fal_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_fal", "")))
        _set(f"sis_gastro_ggt_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_ggt", "")))
        _set(f"sis_gastro_bt_{sis_suf}",  _limpar(st.session_state.get(f"lab_{lab_idx}_bt",  "")))

    # 9. Laboratoriais → Cardiovascular (Troponina e Lactato — 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_cardio_trop_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_trop", "")))
        # Lactato: primeiro gas disponível do dia (gas > gas2 > gas3)
        lac = next(
            (_limpar(st.session_state.get(f"lab_{lab_idx}_{gn}_lac", ""))
             for gn in ("gas", "gas2", "gas3")
             if _limpar(st.session_state.get(f"lab_{lab_idx}_{gn}_lac", ""))),
            ""
        )
        _set(f"sis_cardio_lac_{sis_suf}", lac)

    # 10. Laboratoriais → Pele/Musculoesquelético (CPK — 5 slots)
    for sis_suf, _, lab_idx in _SLOTS:
        _set(f"sis_pele_cpk_{sis_suf}", _limpar(st.session_state.get(f"lab_{lab_idx}_cpk", "")))

    st.session_state["_agent_staging"] = staging
    if cnt[0]:
        st.toast(f"✅ {cnt[0]} campos preenchidos a partir dos Blocos Anteriores!", icon="📋")
    else:
        st.warning("⚠️ Nenhum valor encontrado nos blocos de origem. Preencha Controles, Lab, Antibióticos e Culturas primeiro.")
    st.rerun()
