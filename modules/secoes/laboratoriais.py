import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# COMO ADICIONAR UM NOVO CAMPO LABORATORIAL
# ─────────────────────────────────────────────────────────────────────────────
# 1. Adicione o sufixo em _LAB_SUFIXOS (para deslocamento automático).
# 2. Adicione o campo em get_campos() com valor padrão ''.
# 3. Adicione o widget em _render_labs_table() (use _row(label, sufixo)).
# 4. Para que o campo vá para Sistemas (bridge): adicione em bridge.py → _BRIDGE_LAB.
#    Exemplo: ("sis_metab_glic_{s}", "glic", _limpar)
# ─────────────────────────────────────────────────────────────────────────────

# Sufixos dos campos lab_{i}_{suf} para deslocamento (Evolução Hoje)
_LAB_SUFIXOS = [
    "data", "hb", "ht", "vcm", "hcm", "rdw", "leuco", "plaq",
    "cr", "ur", "na", "k", "mg", "pi", "cat", "cai",
    "tgp", "tgo", "fal", "ggt", "bt", "bd", "prot_tot", "alb", "amil", "lipas",
    "cpk", "cpk_mb", "bnp", "trop", "pcr", "vhs", "tp", "ttpa",
    "ur_dens", "ur_le", "ur_nit", "ur_leu", "ur_hm", "ur_prot", "ur_cet", "ur_glic",
    # Gasometria 1
    "gas_tipo", "gas_hora",
    "gas_ph", "gas_pco2", "gas_po2", "gas_hco3", "gas_be", "gas_sat",
    "gas_lac", "gas_ag", "gas_cl", "gas_na", "gas_k", "gas_cai",
    "gasv_pco2", "svo2",
    # Gasometria 2
    "gas2_tipo", "gas2_hora",
    "gas2_ph", "gas2_pco2", "gas2_po2", "gas2_hco3", "gas2_be", "gas2_sat",
    "gas2_lac", "gas2_ag", "gas2_cl", "gas2_na", "gas2_k", "gas2_cai",
    "gas2v_pco2", "gas2_svo2",
    # Gasometria 3
    "gas3_tipo", "gas3_hora",
    "gas3_ph", "gas3_pco2", "gas3_po2", "gas3_hco3", "gas3_be", "gas3_sat",
    "gas3_lac", "gas3_ag", "gas3_cl", "gas3_na", "gas3_k", "gas3_cai",
    "gas3v_pco2", "gas3_svo2",
    "outros", "conduta",
]

# Sufixos que armazenam o tipo de gasometria (precisam de tratamento especial no deslocamento)
_GAS_TIPO_SUFIXOS = {"gas_tipo", "gas2_tipo", "gas3_tipo"}


def _set_ss(key: str, value) -> None:
    """Define session_state liberando antes qualquer widget vinculado à chave."""
    if key in st.session_state:
        del st.session_state[key]
    st.session_state[key] = value


def _deslocar_laboratoriais():
    """
    Desloca os resultados por data: Hoje→vazio, Ontem→Hoje, Anteontem→Ontem, Anteontem→4 dias atrás.
    Slot 4 (Laboratoriais Admissão / Externo) é FIXO — nunca é deslocado.
    """
    def _copiar(orig: int, dest: int):
        for suf in _LAB_SUFIXOS:
            key_orig = f"lab_{orig}_{suf}"
            key_dest = f"lab_{dest}_{suf}"
            val = st.session_state.get(key_orig)
            if suf in _GAS_TIPO_SUFIXOS:
                _set_ss(key_dest, val if val in (None, "Arterial", "Venosa", "Pareada") else None)
            else:
                _set_ss(key_dest, val if val is not None else "")

    def _limpar(slot: int):
        for suf in _LAB_SUFIXOS:
            key = f"lab_{slot}_{suf}"
            if suf in _GAS_TIPO_SUFIXOS:
                _set_ss(key, None)
            else:
                _set_ss(key, "")

    # Ordem reversa para não sobrescrever antes de ler
    # 9→10, 8→9, 7→8, 6→7, 5→6 (demais exames)
    for i in range(9, 4, -1):
        _copiar(i, i + 1)
    # 3→5 (anteontem vira 4 dias atrás; pula slot 4)
    _copiar(3, 5)
    # 2→3, 1→2 (ontem→anteontem, hoje→ontem)
    _copiar(2, 3)
    _copiar(1, 2)
    # Slot 1 fica vazio; slot 4 permanece inalterado
    _limpar(1)


# 1. Definição das Variáveis (10 Slots de Data)
def get_campos():
    campos = {'laboratoriais_notas': ''}
    
    for i in range(1, 11):
        campos.update({
            f'lab_{i}_data': '',
            
            # Linha 1: Hemato
            f'lab_{i}_hb': '', f'lab_{i}_ht': '', f'lab_{i}_vcm': '', f'lab_{i}_hcm': '', 
            f'lab_{i}_rdw': '', f'lab_{i}_leuco': '', f'lab_{i}_plaq': '',
            
            # Linha 2: Renal/Eletrolitos
            f'lab_{i}_cr': '', f'lab_{i}_ur': '', f'lab_{i}_na': '', f'lab_{i}_k': '', 
            f'lab_{i}_mg': '', f'lab_{i}_pi': '', f'lab_{i}_cat': '', f'lab_{i}_cai': '',
            
            # Linha 3: Hepático/Panc
            f'lab_{i}_tgp': '', f'lab_{i}_tgo': '', f'lab_{i}_fal': '', f'lab_{i}_ggt': '',
            f'lab_{i}_bt': '', f'lab_{i}_bd': '', f'lab_{i}_prot_tot': '',
            f'lab_{i}_alb': '', f'lab_{i}_amil': '', f'lab_{i}_lipas': '',
            
            # Linha 4: Cardio/Coag/Inflam
            f'lab_{i}_cpk': '', f'lab_{i}_cpk_mb': '', f'lab_{i}_bnp': '',
            f'lab_{i}_trop': '', f'lab_{i}_pcr': '', f'lab_{i}_vhs': '',
            f'lab_{i}_tp': '', f'lab_{i}_ttpa': '',
            
            # Linha 5: Urina
            f'lab_{i}_ur_dens': '', f'lab_{i}_ur_le': '', f'lab_{i}_ur_nit': '', f'lab_{i}_ur_leu': '',
            f'lab_{i}_ur_hm': '', f'lab_{i}_ur_prot': '', f'lab_{i}_ur_cet': '', f'lab_{i}_ur_glic': '',
            
            # Gasometria 1
            f'lab_{i}_gas_tipo': None, f'lab_{i}_gas_hora': '',
            f'lab_{i}_gas_ph': '', f'lab_{i}_gas_pco2': '', f'lab_{i}_gas_po2': '', f'lab_{i}_gas_hco3': '',
            f'lab_{i}_gas_be': '', f'lab_{i}_gas_sat': '', f'lab_{i}_gas_lac': '', f'lab_{i}_gas_ag': '',
            f'lab_{i}_gas_cl': '', f'lab_{i}_gas_na': '', f'lab_{i}_gas_k': '', f'lab_{i}_gas_cai': '',
            f'lab_{i}_gasv_pco2': '', f'lab_{i}_svo2': '',

            # Gasometria 2
            f'lab_{i}_gas2_tipo': None, f'lab_{i}_gas2_hora': '',
            f'lab_{i}_gas2_ph': '', f'lab_{i}_gas2_pco2': '', f'lab_{i}_gas2_po2': '', f'lab_{i}_gas2_hco3': '',
            f'lab_{i}_gas2_be': '', f'lab_{i}_gas2_sat': '', f'lab_{i}_gas2_lac': '', f'lab_{i}_gas2_ag': '',
            f'lab_{i}_gas2_cl': '', f'lab_{i}_gas2_na': '', f'lab_{i}_gas2_k': '', f'lab_{i}_gas2_cai': '',
            f'lab_{i}_gas2v_pco2': '', f'lab_{i}_gas2_svo2': '',

            # Gasometria 3
            f'lab_{i}_gas3_tipo': None, f'lab_{i}_gas3_hora': '',
            f'lab_{i}_gas3_ph': '', f'lab_{i}_gas3_pco2': '', f'lab_{i}_gas3_po2': '', f'lab_{i}_gas3_hco3': '',
            f'lab_{i}_gas3_be': '', f'lab_{i}_gas3_sat': '', f'lab_{i}_gas3_lac': '', f'lab_{i}_gas3_ag': '',
            f'lab_{i}_gas3_cl': '', f'lab_{i}_gas3_na': '', f'lab_{i}_gas3_k': '', f'lab_{i}_gas3_cai': '',
            f'lab_{i}_gas3v_pco2': '', f'lab_{i}_gas3_svo2': '',

            # Linha 8: Outros
            f'lab_{i}_outros': '',
            
            # Linha 9: Conduta Específica desta data
            f'lab_{i}_conduta': ''
        })
    return campos

# Títulos dos slots
_SLOT_TITULOS = {
    1: "Hoje",
    2: "Ontem",
    3: "Anteontem",
    4: "Admissão / Externo",
}

_SEC_STYLE = (
    'font-size:0.73rem;font-weight:700;color:#1565c0;'
    'text-transform:uppercase;letter-spacing:.06em;'
    'border-top:1px solid #dee2e6;margin-top:4px;padding:4px 0 2px 0;'
    'line-height:1.2;height:1.6em;display:block;'
)


_COL_WIDTHS_FN = lambda slots: [1] * len(slots)


def _render_day_headers(slots: list):
    """Renderiza apenas a linha de cabeçalho (Hoje / Ontem / etc.)."""
    cols = st.columns(_COL_WIDTHS_FN(slots))
    for dc, slot in zip(cols, slots):
        titulo = _SLOT_TITULOS.get(slot, f"Exame #{slot}")
        with dc:
            st.markdown(
                f'<div style="text-align:center;font-size:0.82rem;font-weight:700;'
                f'color:#1a73e8;padding-bottom:2px;">{titulo}</div>',
                unsafe_allow_html=True,
            )


def _render_labs_table(slots: list, show_header: bool = True):
    """
    Layout vertical: linhas = parâmetros, colunas = dias.

    • A coluna do PRIMEIRO slot mostra labels visíveis (label_visibility="visible").
    • As demais usam label_visibility="hidden": o label fica invisível mas ocupa o
      mesmo espaço → alinhamento perfeito sem depender de alturas fixas em px.
    • Tab desce dentro de cada coluna (DOM order: col1 completa → col2 → ...).
    • show_header=False pula o cabeçalho (usado quando renderizado separadamente).
    """
    col_widths = _COL_WIDTHS_FN(slots)
    cols = st.columns(col_widths)
    day_cols = list(cols)
    first = slots[0]

    def _lv(slot):
        return "visible" if slot == first else "hidden"

    def _sec(title):
        for dc, slot in zip(day_cols, slots):
            text = title if slot == first else "&nbsp;"
            with dc:
                st.markdown(f'<div style="{_SEC_STYLE}">{text}</div>',
                            unsafe_allow_html=True)

    def _row(label, suf, placeholder=""):
        for dc, slot in zip(day_cols, slots):
            with dc:
                st.text_input(label, key=f"lab_{slot}_{suf}",
                              label_visibility=_lv(slot), placeholder=placeholder)

    def _row_pills(label, gprefix, gn):
        for dc, slot in zip(day_cols, slots):
            with dc:
                _tipo_key = f"lab_{slot}_{gprefix}_tipo"
                if st.session_state.get(_tipo_key) not in (None, "Arterial", "Venosa", "Pareada"):
                    st.session_state[_tipo_key] = None
                st.selectbox(label, ["Arterial", "Venosa", "Pareada"],
                             index=None, key=_tipo_key,
                             placeholder="Tipo...",
                             label_visibility=_lv(slot))

    # ── Cabeçalho de dia (opcional) ───────────────────────────────
    if show_header:
        for dc, slot in zip(day_cols, slots):
            titulo = _SLOT_TITULOS.get(slot, f"Exame #{slot}")
            with dc:
                st.markdown(
                    f'<div style="text-align:center;font-size:0.82rem;font-weight:700;'
                    f'color:#1a73e8;padding-bottom:2px;">{titulo}</div>',
                    unsafe_allow_html=True,
                )

    _row("Data", "data", "DD/MM/AAAA")

    # ── Hematologia ──────────────────────────────────────────────
    _sec("Hematologia")
    _row("Hb",   "hb")
    _row("Ht",   "ht")
    _row("VCM",  "vcm")
    _row("HCM",  "hcm")
    _row("RDW",  "rdw")
    for dc, slot in zip(day_cols, slots):
        with dc:
            st.text_input("Leuco (Dif)", key=f"lab_{slot}_leuco",
                          label_visibility=_lv(slot), placeholder="Total (Seg/Bast)")
    _row("Plaq", "plaq")

    # ── Renal / Eletrólitos ──────────────────────────────────────
    _sec("Renal / Eletrólitos")
    _row("Cr",  "cr")
    _row("Ur",  "ur")
    _row("Na",  "na")
    _row("K",   "k")
    _row("Mg",  "mg")
    _row("Pi",  "pi")
    _row("CaT", "cat")
    _row("CaI", "cai")

    # ── Hepático / Pancreático ────────────────────────────────────
    _sec("Hepático / Pancreático")
    _row("TGP",      "tgp")
    _row("TGO",      "tgo")
    _row("FAL",      "fal")
    _row("GGT",      "ggt")
    _row("BT",       "bt")
    _row("BD",       "bd")
    _row("Prot Tot", "prot_tot")
    _row("Alb",      "alb")
    _row("Amil",     "amil")
    _row("Lipas",    "lipas")

    # ── Cardiologia / Hematologia / Inflamatórios ─────────────────
    _sec("Cardiologia / Hematologia / Inflamatórios")
    _row("CPK",    "cpk")
    _row("CPK-MB", "cpk_mb")
    _row("BNP",    "bnp")
    _row("Trop",   "trop")
    _row("PCR",    "pcr")
    _row("VHS",    "vhs")
    _row("TP",     "tp")
    _row("TTPa",   "ttpa")

    # ── Gasometria 1 ─────────────────────────────────────────────
    _sec("Gasometria")
    _row("Hora",    "gas_hora",  "16h")
    _row_pills("Tipo", "gas", 1)
    _row("pH",      "gas_ph")
    _row("pCO2",    "gas_pco2")
    _row("pO2",     "gas_po2")
    _row("HCO3",    "gas_hco3")
    _row("BE",      "gas_be")
    _row("SatO2",   "gas_sat")
    _row("Lac",     "gas_lac")
    _row("AG",      "gas_ag")
    _row("Cl",      "gas_cl")
    _row("Na (g)",  "gas_na")
    _row("K (g)",   "gas_k")
    _row("CaI (g)", "gas_cai")
    _row("pCO2(v)", "gasv_pco2")
    _row("SvO2",    "svo2")

    # ── Urina (EAS) ──────────────────────────────────────────────
    _sec("Urina (EAS)")
    _row("Dens",      "ur_dens")
    _row("L.Est",     "ur_le")
    _row("Nit",       "ur_nit")
    _row("Leuco (U)", "ur_leu")
    _row("Hm",        "ur_hm")
    _row("Prot",      "ur_prot")
    _row("Cet",       "ur_cet")
    _row("Glic",      "ur_glic")

    # ── Outros & Conduta ─────────────────────────────────────────
    _sec("Outros")
    _row("Não Transcritos", "outros", "Culturas, níveis séricos...")
    for dc, slot in zip(day_cols, slots):
        with dc:
            st.text_input("Conduta", key=f"lab_{slot}_conduta",
                          label_visibility="collapsed",
                          placeholder="Escreva a conduta aqui...")


def _render_gas_extras(slots: list):
    """Gasometrias 2 e 3 — em expander abaixo da tabela principal."""
    with st.expander("Gasometrias adicionais (Gas 2 / Gas 3)", expanded=False):
        gas_cols = st.columns(len(slots))
        for gc, slot in zip(gas_cols, slots):
            titulo = _SLOT_TITULOS.get(slot, f"#{slot}")
            with gc:
                st.markdown(f"**{titulo}**")
                for gn, gp in [(2, "gas2"), (3, "gas3")]:
                    st.caption(f"Gas {gn}")
                    _tipo_key = f"lab_{slot}_{gp}_tipo"
                    if st.session_state.get(_tipo_key) not in (None, "Arterial", "Venosa", "Pareada"):
                        st.session_state[_tipo_key] = None
                    _c_hora, _c_tipo = st.columns([1, 2])
                    with _c_hora:
                        st.text_input("Hora", key=f"lab_{slot}_{gp}_hora",
                                      placeholder="16h", label_visibility="collapsed")
                    with _c_tipo:
                        st.selectbox("Tipo", ["Arterial", "Venosa", "Pareada"],
                                     index=None, key=_tipo_key,
                                     placeholder="Tipo...",
                                     label_visibility="collapsed")
                    kv = f"lab_{slot}_{gp}v_pco2"
                    ks = f"lab_{slot}_{gp}_svo2"
                    for lbl, suf in [
                        ("pH", f"{gp}_ph"), ("pCO2", f"{gp}_pco2"), ("pO2", f"{gp}_po2"),
                        ("HCO3", f"{gp}_hco3"), ("BE", f"{gp}_be"), ("SatO2", f"{gp}_sat"),
                        ("Lac", f"{gp}_lac"), ("AG", f"{gp}_ag"), ("Cl", f"{gp}_cl"),
                        ("Na", f"{gp}_na"), ("K", f"{gp}_k"), ("CaI", f"{gp}_cai"),
                    ]:
                        st.text_input(lbl, key=f"lab_{slot}_{suf}",
                                      label_visibility="visible")
                    st.text_input("pCO2(v)", key=kv)
                    st.text_input("SvO2",    key=ks)
                    if gn == 2:
                        st.divider()


# 2. Renderização Principal
def render(_agent_btn_callback=None):
    st.markdown('<span id="sec-12"></span>', unsafe_allow_html=True)
    st.markdown("##### 12. Exames Laboratoriais")

    st.text_area("Notas", key="laboratoriais_notas", height="content",
                 placeholder="Cole neste campo a evolução...", label_visibility="collapsed")
    st.write("")

    # Botões
    _bcol1, _bcol2, _bcol3, _bcol4, _bcol5 = st.columns([1, 1, 1, 1, 1])
    with _bcol1:
        if st.form_submit_button(
            "Evolução Hoje",
            key="btn_evolucao_hoje_lab",
            use_container_width=True,
            help="Último Resultado vira Anterior #2, Anterior #2 vira #3, etc. Slot 1 fica vazio para novos exames.",
        ):
            _deslocar_laboratoriais()
            st.toast("✅ Resultados deslocados.", icon="✅")
    with _bcol2:
        if st.form_submit_button(
            "Parsing Exames",
            key="_fsbtn_lab_deterministico",
            use_container_width=True,
            help="Preenche deterministicamente. Não perde dados já preenchidos.",
        ):
            st.session_state["_lab_deterministico_pendente"] = True
    with _bcol3:
        if _agent_btn_callback:
            _agent_btn_callback()
    with _bcol4:
        if st.form_submit_button(
            "Extrair Exames",
            key="_fsbtn_extrair_lab",
            use_container_width=True,
            help="Formata os exames com IA (PACER) e aplica o agente automaticamente",
        ):
            st.session_state["_lab_extrair_pendente"] = True
    with _bcol5:
        if st.form_submit_button(
            "Comparar",
            key="_fsbtn_comparar_lab",
            use_container_width=True,
            help="Abre tabela comparativa com todos os campos",
        ):
            st.session_state["_comparar_lab_pendente"] = True

    # ── Tabela principal: slots 1–4 ──────────────────────────────
    _render_labs_table([1, 2, 3, 4])
    _render_gas_extras([1, 2, 3, 4])

    # ── Demais exames: slots 5–10 ────────────────────────────────
    with st.expander("Demais exames", expanded=False):
        _render_labs_table([5, 6, 7, 8, 9, 10])
        _render_gas_extras([5, 6, 7, 8, 9, 10])