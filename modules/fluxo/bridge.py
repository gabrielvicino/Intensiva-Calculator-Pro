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

# ── Slots fixos para Controles → Sistemas ──────────────────────────────────────
_SLOTS_CTRL = [
    ("hoje",    "hoje"),
    ("ult",     "ontem"),
    ("antepen", "anteontem"),
    ("ant4",    "ant4"),
    ("ant5",    "ant5"),
]

# Sufixos de destino em ordem: mais recente → mais antigo
_SLOTS_SIS_ORDEM = ["hoje", "ult", "antepen", "ant4", "ant5"]

# Mapeamento completo (sis_suf, ctrl_dia, lab_idx) — usado pelo botão "Evolução Diária"
_SLOTS = [
    ("hoje",    "hoje",      1),
    ("ult",     "ontem",     2),
    ("antepen", "anteontem", 3),
    ("ant4",    "ant4",      4),
    ("ant5",    "ant5",      5),
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
        # Sempre sobrescreve quando a fonte tem valor — o usuário clicou
        # explicitamente em "Completar Blocos Anteriores" para sincronizar.
        if val:
            staging[sis_key] = val
            cnt[0] += 1

    # 1. Campos fixos de Controles → Renal (apenas slot "hoje")
    _set("sis_renal_diurese", _limpar(st.session_state.get("ctrl_hoje_diurese", "")))
    _set("sis_renal_balanco",  _limpar(st.session_state.get("ctrl_hoje_balanco", "")))

    # 1b. BH Acumulado por slot — soma cumulativa do mais antigo para hoje
    def _bh_num(slot_ctrl: str) -> float | None:
        """Retorna BH do slot como número ou None se vazio/não-numérico."""
        raw = _limpar(st.session_state.get(f"ctrl_{slot_ctrl}_balanco", ""))
        if not raw:
            return None
        try:
            return float(raw.replace(",", ".").replace("+", "").lower().replace("ml", "").strip())
        except ValueError:
            return None

    _bh_slots_ctrl = ["ant5", "ant4", "anteontem", "ontem", "hoje"]  # mais antigo → mais novo
    _bh_slots_sis  = ["ant5", "ant4",  "antepen",   "ult",  "hoje"]  # sufixos sis correspondentes
    _bh_acum: float = 0.0
    _bh_acum_por_slot: dict = {}
    for _ctrl_slot, _sis_slot in zip(_bh_slots_ctrl, _bh_slots_sis):
        _v = _bh_num(_ctrl_slot)
        if _v is not None:
            _bh_acum += _v
        _bh_acum_por_slot[_sis_slot] = _bh_acum if any(
            _bh_num(s) is not None for s in _bh_slots_ctrl[:_bh_slots_ctrl.index(_ctrl_slot) + 1]
        ) else None

    def _fmt_acum(val: float | None) -> str:
        if val is None:
            return ""
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:,.0f}".replace(",", ".")

    for _sis_slot, _acum_val in _bh_acum_por_slot.items():
        _formatted = _fmt_acum(_acum_val)
        if _formatted:
            staging[f"sis_renal_bacum_{_sis_slot}"] = _formatted
            cnt[0] += 1

    # Se tiver pelo menos 1 slot preenchido, ativa o checkbox
    if any(_bh_acum_por_slot.values()):
        staging["sis_renal_bacum_show"] = True
        cnt[0] += 1

    # 2. Mapeamento campo-a-campo: Lab → Sistemas
    #    Para cada campo (ex: "cr"), coleta os valores não-vazios dos lab_slots
    #    ordenados do mais recente ao mais antigo e distribui para hoje/ult/antepen/ant4/ant5.
    #    Isso evita "buracos" quando um slot recente tem dados parciais.
    from modules.secoes.laboratoriais import get_active_slots_sorted as _get_lab_slots
    lab_slots_recentes = list(reversed(_get_lab_slots()))  # [mais_novo, ..., mais_antigo]

    for dest_pat, suf_lab, fn in _BRIDGE_LAB:
        valores: list[str] = []
        for lab_idx in lab_slots_recentes:
            v = fn(st.session_state.get(f"lab_{lab_idx}_{suf_lab}", ""))
            if v:
                valores.append(v)
            if len(valores) >= 5:
                break
        for pos, val in enumerate(valores):
            if pos < len(_SLOTS_SIS_ORDEM):
                _set(dest_pat.format(s=_SLOTS_SIS_ORDEM[pos]), val)

    # Lactato: campo-a-campo (gas → gas2 → gas3 por slot)
    lac_valores: list[str] = []
    for lab_idx in lab_slots_recentes:
        v = _lac_do_dia(lab_idx)
        if v:
            lac_valores.append(v)
        if len(lac_valores) >= 5:
            break
    for pos, val in enumerate(lac_valores):
        if pos < len(_SLOTS_SIS_ORDEM):
            _set(f"sis_cardio_lac_{_SLOTS_SIS_ORDEM[pos]}", val)

    # 2b. Controles → Sistemas (mantém mapeamento fixo por dia)
    for i, (sis_suf, ctrl_dia) in enumerate(_SLOTS_CTRL):
        for dest_pat, suf_ctrl, fn in _BRIDGE_CTRL:
            _set(
                dest_pat.format(s=sis_suf),
                fn(st.session_state.get(f"ctrl_{ctrl_dia}_{suf_ctrl}", "")),
            )

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

    # Auto-ativa _show=True para todos os prefixos de evolução que foram preenchidos.
    # Isso garante que as linhas de evolução apareçam na saída sem precisar marcar
    # manualmente cada checkbox dentro do formulário.
    import re as _re_bridge
    _prefixos_evo: set = set()
    for _sk, _sv in list(staging.items()):
        if _sv:
            _m = _re_bridge.match(r"^(sis_\w+)_(hoje|ult|antepen|ant4|ant5)$", _sk)
            if _m:
                _prefixos_evo.add(_m.group(1))
    for _pref in _prefixos_evo:
        staging[f"{_pref}_show"] = True

    st.session_state["_agent_staging"] = staging
    if rerun:
        if cnt[0]:
            st.toast(f"{cnt[0]} campos preenchidos a partir dos Blocos Anteriores!", icon="📋")
        else:
            st.warning("Nenhum valor encontrado nos blocos de origem. Preencha Controles, Lab, Antibioticos e Culturas primeiro.")
        st.rerun()
