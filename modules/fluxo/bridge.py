"""
bridge.py — copia de dados entre blocos: Lab/Ctrl/ATB/Culturas → Sistemas (bloco 13).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  COMO ADICIONAR UM NOVO CAMPO AO BRIDGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ► Para Controles → Sistemas:
      Edite APENAS modules/secoes/controles.py → _PARAMS
      Coloque o padrão destino no campo bridge_sis da linha correspondente.
      Exemplo: ("glic", "Glicemia", True, "Glic", "sis_metab_glic_{s}")
      Nenhuma alteração é necessária aqui em bridge.py.

  ► Para Laboratoriais → Sistemas:
      Acrescente UMA linha em _BRIDGE_LAB abaixo:
      ("sis_SISTEMA_CAMPO_{s}", "sufixo_lab", fn_transform)
      Onde {s} = hoje | ult | antepen | ant4 | ant5
            lab_{i}_{sufixo} com i = 1 (hoje) … 5 (ant5)

  ► Disponíveis: _limpar, _limpar_leuco, _extrair_parenteses

  ► Campos de Sistemas existentes: veja modules/secoes/sistemas/__init__.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import streamlit as st
from .state import _limpar, _limpar_leuco, _extrair_parenteses
from modules.secoes.controles import _PARAMS as _CTRL_PARAMS


# ── Mapeamento Lab → Sistemas ──────────────────────────────────────────────────
# Cada linha: (padrão destino c/ {s},  sufixo lab_{i}_{aqui},  fn_transform)
# Para adicionar: acrescente UMA linha aqui (veja cabeçalho do arquivo)
_BRIDGE_LAB = [
    # Renal
    ("sis_renal_cr_{s}",    "cr",    _limpar),
    ("sis_renal_ur_{s}",    "ur",    _limpar),
    ("sis_renal_na_{s}",    "na",    _limpar),
    ("sis_renal_k_{s}",     "k",     _limpar),
    ("sis_renal_mg_{s}",    "mg",    _limpar),
    ("sis_renal_fos_{s}",   "pi",    _limpar),
    ("sis_renal_cai_{s}",   "cai",   _limpar),
    # Infeccioso
    ("sis_infec_pcr_{s}",   "pcr",   _limpar),
    ("sis_infec_leuc_{s}",  "leuco", _limpar_leuco),
    ("sis_infec_vhs_{s}",   "vhs",   _limpar),
    # Hematológico
    ("sis_hemato_hb_{s}",   "hb",    _limpar),
    ("sis_hemato_plaq_{s}", "plaq",  _limpar),
    ("sis_hemato_inr_{s}",  "tp",    _extrair_parenteses),
    ("sis_hemato_ttpa_{s}", "ttpa",  _extrair_parenteses),
    # Gastro / TGI
    ("sis_gastro_tgo_{s}",  "tgo",   _limpar),
    ("sis_gastro_tgp_{s}",  "tgp",   _limpar),
    ("sis_gastro_fal_{s}",  "fal",   _limpar),
    ("sis_gastro_ggt_{s}",  "ggt",   _limpar),
    ("sis_gastro_bt_{s}",   "bt",    _limpar),
    # Cardiovascular
    ("sis_cardio_trop_{s}", "trop",  _limpar),
    # Pele / Musculoesquelético
    ("sis_pele_cpk_{s}",    "cpk",   _limpar),
    # ── Adicione novos campos Lab → Sistemas aqui ─────────────────────────────
    # Exemplo (descomentar quando campo sis_metab_glic_* existir no Bloco 13):
    # ("sis_metab_glic_{s}", "glic", _limpar),
]

# ── Mapeamento Ctrl → Sistemas (auto-derivado de controles._PARAMS) ────────────
# NÃO edite aqui. Edite controles._PARAMS campo bridge_sis.
_BRIDGE_CTRL = [
    (bridge_sis, chave, _limpar)
    for chave, _, __, ___, bridge_sis in _CTRL_PARAMS
    if bridge_sis is not None
]

# ── Slots: (sufixo_sis, dia_ctrl, idx_lab) ─────────────────────────────────────
# lab_4 = "Admissão/Externo" (fixo, não participa da cadeia temporal).
# ant4 em Sistemas ← lab_5 (real 4º dia); ant5 ← lab_6 (real 5º dia).
_SLOTS = [
    ("hoje",    "hoje",      1),
    ("ult",     "ontem",     2),
    ("antepen", "anteontem", 3),
    ("ant4",    "ant4",      5),   # lab_5 = 4º dia real (pula lab_4 = Admissão)
    ("ant5",    "ant5",      6),   # lab_6 = 5º dia real
]


def _lac_do_dia(lab_idx: int) -> str:
    """Retorna lactato da primeira gasometria disponível do dia (gas → gas2 → gas3)."""
    return next(
        (
            _limpar(st.session_state.get(f"lab_{lab_idx}_{gn}_lac", ""))
            for gn in ("gas", "gas2", "gas3")
            if _limpar(st.session_state.get(f"lab_{lab_idx}_{gn}_lac", ""))
        ),
        "",
    )


def completar_sistemas_de_outros_blocos(rerun: bool = True) -> None:
    """
    Copia dados de Laboratoriais, Controles, Antibioticos e Culturas
    para os campos sis_* do Bloco 13 (Sistemas).

    Regra: só preenche se o campo de destino estiver vazio — preserva dados manuais.

    Para adicionar um novo mapeamento:
      • Lab  → acrescente uma linha em _BRIDGE_LAB no topo deste arquivo
      • Ctrl → acrescente uma linha em _BRIDGE_CTRL no topo deste arquivo

    rerun=False: apenas preenche o staging sem chamar st.rerun() — usado quando o
    chamador já gerencia o rerun (ex: handler do botão Evolução Diária em fichas.py).
    """
    staging = st.session_state.get("_agent_staging", {})
    cnt = [0]

    def _set(sis_key: str, val: str) -> None:
        dest = st.session_state.get(sis_key, "") or ""
        if val and not str(dest).strip():
            staging[sis_key] = val
            cnt[0] += 1

    # 1. Campos fixos de Controles → Renal (apenas slot "hoje")
    _set("sis_renal_diurese", _limpar(st.session_state.get("ctrl_hoje_diurese", "")))
    _set("sis_renal_balanco",  _limpar(st.session_state.get("ctrl_hoje_balanco", "")))

    # 2. Mapeamento por slots: Lab + Ctrl → Sistemas
    for sis_suf, ctrl_dia, lab_idx in _SLOTS:
        for dest_pat, suf_lab, fn in _BRIDGE_LAB:
            _set(
                dest_pat.format(s=sis_suf),
                fn(st.session_state.get(f"lab_{lab_idx}_{suf_lab}", "")),
            )
        for dest_pat, suf_ctrl, fn in _BRIDGE_CTRL:
            _set(
                dest_pat.format(s=sis_suf),
                fn(st.session_state.get(f"ctrl_{ctrl_dia}_{suf_ctrl}", "")),
            )
        # Lactato: caso especial — tenta gas, gas2, gas3 em ordem
        _set(f"sis_cardio_lac_{sis_suf}", _lac_do_dia(lab_idx))

    # 3. Antibióticos atuais → Infeccioso (até 3 ATBs com status "Atual")
    ordem_atb = st.session_state.get("atb_ordem", list(range(1, 9)))
    atuais = [
        st.session_state.get(f"atb_{idx}_nome", "")
        for idx in ordem_atb
        if st.session_state.get(f"atb_{idx}_status") == "Atual"
    ]
    for i in range(1, 4):
        _set(f"sis_infec_atb_{i}", _limpar(atuais[i - 1] if i <= len(atuais) else ""))

    # 4. Culturas → Infeccioso (sítio e data de coleta, slots 1-4)
    for i in range(1, 5):
        _set(f"sis_infec_cult_{i}_sitio", _limpar(st.session_state.get(f"cult_{i}_sitio",       "")))
        _set(f"sis_infec_cult_{i}_data",  _limpar(st.session_state.get(f"cult_{i}_data_coleta", "")))

    st.session_state["_agent_staging"] = staging
    if rerun:
        if cnt[0]:
            st.toast(f"{cnt[0]} campos preenchidos a partir dos Blocos Anteriores!", icon="📋")
        else:
            st.warning("Nenhum valor encontrado nos blocos de origem. Preencha Controles, Lab, Antibioticos e Culturas primeiro.")
        st.rerun()
