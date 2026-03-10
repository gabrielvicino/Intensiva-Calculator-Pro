import re
import streamlit as st
from modules import ui

# ---------------------------------------------------------------------------
# Formatação automática de datas
# ---------------------------------------------------------------------------
_PAT_CHAVE_DATA = re.compile(
    r"(_data|_ultima|_proxima|_ini$|_fim$|di_hosp$|di_uti$|di_enf$)",
    re.IGNORECASE,
)

_PAT_CHAVE_HORA = re.compile(r"_dt$", re.IGNORECASE)


def _fmt_hora(val: str) -> str:
    """
    Formata campo de hora para os campos _dt (ex: lactato).
    - "18"        → "18h"
    - "04/03 18"  → "04/03 18h"
    - "18h"       → sem alteração
    """
    if not isinstance(val, str):
        return val
    stripped = val.strip()
    if not stripped or stripped.endswith("h"):
        return val
    # Apenas dígitos (ex: "18") → hora pura
    if re.fullmatch(r"\d{1,2}", stripped):
        return f"{stripped}h"
    # Data + espaço + dígitos no final (ex: "04/03 18")
    m = re.match(r"^(.+\s)(\d{1,2})$", stripped)
    if m:
        return f"{m.group(1)}{m.group(2)}h"
    return val


def _fmt_data(val: str) -> str:
    """
    Converte dígitos para formato de data com barras.
    Formatação fluida: 01 → 01/, 0101 → 01/01/, 01012026 → 01/01/2026
    Aceita valores com ou sem barras. Só formata se o valor contiver apenas dígitos e barras.
    """
    if not isinstance(val, str):
        return val
    stripped = val.strip()
    if not stripped:
        return val
    # Só formata se contiver apenas dígitos e barras (evita sobrescrever texto extra)
    if not all(c.isdigit() or c == "/" for c in stripped):
        return val
    digitos = "".join(c for c in stripped if c.isdigit())
    if not digitos:
        return val
    n = len(digitos)
    if n <= 2:
        return f"{digitos}/"
    if n <= 4:
        return f"{digitos[0:2]}/{digitos[2:4]}/"
    if n == 6:
        # DD/MM/AA → DD/MM/20AA (ex: 040326 → 04/03/2026)
        return f"{digitos[0:2]}/{digitos[2:4]}/20{digitos[4:6]}"
    if n <= 8:
        return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"
    # Mais de 8 dígitos: formata só os 8 primeiros
    return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"


def _normalizar_datas():
    """
    Reformata automaticamente apenas as chaves conhecidas de data/_dt.
    Usa sets pré-computados — não faz regex sobre todo o session_state a cada render.
    """
    data_keys, hora_keys = _get_campos_data_hora_cached()
    ss = st.session_state
    for k in data_keys:
        v = ss.get(k)
        if isinstance(v, str) and v:
            novo = _fmt_data(v)
            if novo != v:
                ss[k] = novo
    for k in hora_keys:
        v = ss.get(k)
        if isinstance(v, str) and v:
            novo = _fmt_hora(v)
            if novo != v:
                ss[k] = novo

# ---------------------------------------------------------------------------
# Normalização de campos st.pills (matching case-insensitivo)
# ---------------------------------------------------------------------------

# Mapa completo: chave → opções válidas (exatamente como declaradas nos widgets)
_PILLS_MAPA: dict[str, list] = {
    # Hemato
    "sis_hemato_anticoag":           ["Sim", "Não"],
    "sis_hemato_anticoag_tipo":      ["Profilática", "Plena"],
    "sis_hemato_sangramento":        ["Sim", "Não"],
    # Pele
    "sis_pele_edema":               ["Presente", "Ausente"],
    "sis_pele_lpp":                 ["Sim", "Não"],
    "sis_pele_polineuropatia":      ["Sim", "Não"],
    # Renal
    "sis_renal_volemia":            ["Hipovolêmico", "Euvolêmico", "Hipervolêmico"],
    "sis_renal_trs":                ["Sim", "Não"],
    # Infeccioso
    "sis_infec_febre":              ["Sim", "Não"],
    "sis_infec_atb":                ["Sim", "Não"],
    "sis_infec_atb_guiado":         ["Sim", "Não"],
    "sis_infec_culturas_and":       ["Sim", "Não"],
    "sis_infec_isolamento":         ["Sim", "Não"],
    # Gastrointestinal
    "sis_gastro_ictericia_presente": ["Presente", "Ausente"],
    "sis_gastro_na_meta":           ["Sim", "Não"],
    "sis_gastro_escape_glicemico":  ["Sim", "Não"],
    "sis_gastro_insulino":          ["Sim", "Não"],
    "sis_gastro_evacuacao":         ["Sim", "Não"],
    # Cardiovascular
    "sis_cardio_perfusao":          ["Normal", "Lentificada", "Flush"],
    "sis_cardio_fluido_responsivo": ["Sim", "Não"],
    "sis_cardio_fluido_tolerante":  ["Sim", "Não"],
    # Respiratório
    "sis_resp_modo":                ["Ar Ambiente", "Oxigenoterapia", "VNI", "Cateter de Alto Fluxo", "Ventilação Mecânica"],
    "sis_resp_modo_vent":           ["VCV", "PCV", "PSV"],
    "sis_resp_vent_protetora":      ["Sim", "Não"],
    "sis_resp_sincronico":          ["Sim", "Não"],
    # Neurológico
    "sis_neuro_delirium":            ["Sim", "Não"],
    "sis_neuro_delirium_tipo":       ["Hiperativo", "Hipoativo"],
    "sis_neuro_cam_icu":             ["Positivo", "Negativo"],
    "sis_neuro_pupilas_tam":         ["Miótica", "Normal", "Midríase"],
    "sis_neuro_pupilas_simetria":    ["Simétricas", "Anisocoria"],
    "sis_neuro_pupilas_foto":        ["Fotoreagente", "Não fotoreagente"],
    "sis_neuro_deficits_ausente":    ["Ausente"],
    "sis_neuro_analgesico_adequado": ["Sim", "Não"],
    **{f"sis_neuro_analgesia_{i}_tipo": ["Fixa", "Se necessário"] for i in range(1, 4)},
}


def _normalizar_pills_dict(dados: dict) -> dict:
    """Normaliza valores de campos st.pills num dicionário para correspondência
    exata com as opções (matching case-insensitivo).

    'profilática' → 'Profilática' | valor inválido → None (evita crash).
    """
    for chave, opcoes in _PILLS_MAPA.items():
        valor = dados.get(chave)
        if not valor:
            continue
        if valor in opcoes:
            continue
        opcoes_lower = {o.lower(): o for o in opcoes}
        match = opcoes_lower.get(str(valor).lower())
        dados[chave] = match  # None se não reconhecido (widget aceita None)
    return dados


def _normalizar_pills_state() -> None:
    """Normaliza os campos st.pills diretamente no session_state."""
    ss = st.session_state
    for chave, opcoes in _PILLS_MAPA.items():
        valor = ss.get(chave)
        if not valor:
            continue
        if valor in opcoes:
            continue
        opcoes_lower = {o.lower(): o for o in opcoes}
        ss[chave] = opcoes_lower.get(str(valor).lower())  # None se inválido


# --- IMPORTAÇÃO DAS SEÇÕES ---
from modules.secoes import identificacao      # 1
from modules.secoes import scores             # 2
from modules.secoes import hd                 # 3
from modules.secoes import comorbidades       # 3
from modules.secoes import muc                # 4
from modules.secoes import hmpa
from modules.secoes import intraoperatorio               # 5
from modules.secoes import dispositivos       # 6
from modules.secoes import culturas           # 7
from modules.secoes import antibioticos       # 8
from modules.secoes import complementares     # 9
from modules.secoes import laboratoriais      # 10
from modules.secoes import evolucao_clinica   # 11
from modules.secoes import sistemas           # 12
from modules.secoes import controles          # 13
from modules.secoes import prescricao         # 14
from modules.secoes import condutas           # 15

# Mapa secao_key → módulo (usado para limpar campos individualmente)
_SECOES_MODULOS: dict = {}  # preenchido lazily para evitar imports circulares

def _get_secoes_modulos() -> dict:
    global _SECOES_MODULOS
    if not _SECOES_MODULOS:
        _SECOES_MODULOS = {
            "identificacao":  identificacao,
            "scores":         scores,
            "hd":             hd,
            "comorbidades":   comorbidades,
            "muc":            muc,
            "hmpa":           hmpa,
            "intraoperatorio": intraoperatorio,
            "dispositivos":   dispositivos,
            "culturas":       culturas,
            "antibioticos":   antibioticos,
            "complementares": complementares,
            "laboratoriais":  laboratoriais,
            "evolucao":       evolucao_clinica,
            "sistemas":       sistemas,
            "controles":      controles,
            "prescricao":     prescricao,
            "condutas":       condutas,
        }
    return _SECOES_MODULOS


def limpar_campos_secao(secao_key: str) -> int:
    """Restaura os campos de uma seção para os valores padrão.

    Retorna a quantidade de campos resetados.
    """
    mod = _get_secoes_modulos().get(secao_key)
    if mod is None:
        return 0
    defaults = mod.get_campos()
    ss = st.session_state
    for k, v in defaults.items():
        if k in ss:
            del ss[k]
        ss[k] = v
    return len(defaults)

def _campos_base() -> dict:
    """Retorna o dicionário com TODOS os campos do formulário e seus valores padrão."""
    campos = {}
    campos.update(identificacao.get_campos())
    campos.update(scores.get_campos())
    campos.update(hd.get_campos())
    campos.update(comorbidades.get_campos())
    campos.update(muc.get_campos())
    campos.update(hmpa.get_campos())
    campos.update(intraoperatorio.get_campos())
    campos.update(dispositivos.get_campos())
    campos.update(culturas.get_campos())
    campos.update(antibioticos.get_campos())
    campos.update(complementares.get_campos())
    campos.update(laboratoriais.get_campos())
    campos.update(evolucao_clinica.get_campos())
    campos.update(sistemas.get_campos())
    campos.update(controles.get_campos())
    campos.update(prescricao.get_campos())
    campos.update(condutas.get_campos())
    campos.update({
        'texto_bruto_original': '',  # Bloco 1: texto colado antes do processamento
        'texto_final_gerado': '',    # Bloco 3: prontuário gerado pelo modelo
        # campos _notas preenchidos pelo ia_extrator
        'identificacao_notas': '', 'scores_notas': '', 'hd_notas': '', 'comorbidades_notas': '',
        'muc_notas': '', 'hmpa_texto': '', 'dispositivos_notas': '',
        'culturas_notas': '', 'antibioticos_notas': '', 'complementares_notas': '',
        'laboratoriais_notas': '', 'controles_notas': '', 'evolucao_notas': '',
        'sistemas_notas': '',
        # flags de inclusão na saída deterministíca (True = incluir, padrão)
        'inc_identificacao':   True,
        'inc_scores':          True,
        'inc_hd':              True,
        'inc_comorbidades':    True,
        'inc_muc':             True,
        'inc_hmpa':            True,
        'inc_intraoperatorio': True,
        'inc_dispositivos':    True,
        'inc_culturas':        True,
        'inc_antibioticos':    True,
        'inc_complementares':  True,
        'inc_laboratoriais':   True,
        'inc_controles':       True,
        'inc_evolucao':        True,
        'inc_sistemas':        True,
        'inc_prescricao':      True,
        'inc_condutas':        True,
    })
    return campos


# ===========================================================================
# CACHES DE MÓDULO — calculados uma única vez por processo, não por render
# ===========================================================================
_CAMPOS_BASE_CACHE: dict | None = None
_CAMPOS_KEYS_CACHE: list | None = None
_CAMPOS_NONE_CACHE: set | None = None   # chaves cujo default é None (radio/pills)
_CAMPOS_DATA_CACHE: frozenset | None = None   # chaves de data
_CAMPOS_HORA_CACHE: frozenset | None = None   # chaves de hora (_dt)


def _get_campos_base_cached() -> dict:
    global _CAMPOS_BASE_CACHE
    if _CAMPOS_BASE_CACHE is None:
        _CAMPOS_BASE_CACHE = _campos_base()
    return _CAMPOS_BASE_CACHE


def _get_campos_keys_cached() -> list:
    global _CAMPOS_KEYS_CACHE
    if _CAMPOS_KEYS_CACHE is None:
        _CAMPOS_KEYS_CACHE = list(_get_campos_base_cached().keys())
    return _CAMPOS_KEYS_CACHE


def _get_campos_none_cached() -> set:
    """Retorna set de chaves cujo valor padrão é None (radios/pills)."""
    global _CAMPOS_NONE_CACHE
    if _CAMPOS_NONE_CACHE is None:
        _CAMPOS_NONE_CACHE = {k for k, v in _get_campos_base_cached().items() if v is None}
    return _CAMPOS_NONE_CACHE


def _get_campos_data_hora_cached() -> tuple[frozenset, frozenset]:
    """Retorna (data_keys, hora_keys) precomputados a partir dos campos conhecidos."""
    global _CAMPOS_DATA_CACHE, _CAMPOS_HORA_CACHE
    if _CAMPOS_DATA_CACHE is None:
        campos = _get_campos_base_cached()
        _CAMPOS_DATA_CACHE = frozenset(k for k in campos if _PAT_CHAVE_DATA.search(k))
        _CAMPOS_HORA_CACHE = frozenset(k for k in campos if _PAT_CHAVE_HORA.search(k))
    return _CAMPOS_DATA_CACHE, _CAMPOS_HORA_CACHE


def get_todos_campos_keys() -> list:
    """
    Retorna a lista de chaves de todos os campos do formulário.
    Usada para salvar/carregar dados no Google Sheets.
    """
    return _get_campos_keys_cached()


def inicializar_estado():
    """Garante que todos os campos estão no session_state com seu valor padrão."""
    defaults = _get_campos_base_cached()
    ss = st.session_state
    for k, v in defaults.items():
        if k not in ss:
            ss[k] = v


def _sanitizar_radios():
    """
    Corrige campos de radio/pills com default None que receberam '' (string vazia)
    vinda de agentes de IA ou do carregamento do Google Sheets.
    Usa set pré-computado — não itera o dict completo.
    """
    ss = st.session_state
    for k in _get_campos_none_cached():
        if ss.get(k) == "":
            ss[k] = None

def _btn_gerar_bloco(secao_key: str):
    """Renderiza o botão 'Comparar' para uma seção específica (dentro de um form).
    Gera deterministicamente a saída da seção e abre modal lado a lado com as notas."""
    from modules import agentes_secoes
    nome = agentes_secoes.NOMES_SECOES.get(secao_key, secao_key.capitalize())
    if st.form_submit_button(
        f"🔍 Comparar {nome}",
        key=f"_fsbtn_gerar_{secao_key}",
        help="Compara as notas coladas com a saída determinística gerada para esta seção",
        use_container_width=True,
    ):
        st.session_state["_gerar_bloco_pendente"] = secao_key


def _btn_agente(secao_key: str):
    """
    Retorna uma função que, quando chamada, renderiza o botão
    'Completar Campos' para a seção indicada.
    O botão roda apenas o agente daquela seção sem afetar o restante.
    """
    def _render():
        from modules import agentes_secoes
        nome_secao = agentes_secoes.NOMES_SECOES.get(secao_key, secao_key)

        clicked = st.form_submit_button(
            "Completar Campos",
            key=f"_fsbtn_ag_{secao_key}",
            help=f"Preenche apenas '{nome_secao}' com IA",
            use_container_width=True,
        )
        if clicked:
            st.session_state["_agente_pendente"] = secao_key
    return _render


def _btn_limpar_secao(secao_key: str, nome_display: str | None = None):
    """Renderiza o botão 'Limpar Seção' dentro de um form.
    Define a flag _limpar_secao_pendente que é processada fora do form.
    """
    from modules import agentes_secoes
    nome = nome_display or agentes_secoes.NOMES_SECOES.get(secao_key, secao_key.capitalize())
    if st.form_submit_button(
        "Limpar",
        key=f"_fsbtn_limpar_{secao_key}",
        help=f"Apaga apenas os campos de '{nome}' (demais seções e prontuário não são afetados)",
        use_container_width=True,
    ):
        st.session_state["_limpar_secao_pendente"] = secao_key


def _btn_salvar_secao(secao_key: str, nome_display: str | None = None):
    """
    Renderiza o botão 'Salvar Seção' dentro de um form.
    Salva todo o session_state (garante consistência) mas indica qual seção foi salva.
    """
    from modules import agentes_secoes
    nome = nome_display or agentes_secoes.NOMES_SECOES.get(secao_key, secao_key.capitalize())
    if st.form_submit_button(
        "💾 Salvar",
        key=f"_fsbtn_save_{secao_key}",
        help=f"Salva os dados de '{nome}' no prontuário",
        use_container_width=True,
    ):
        st.session_state["_salvar_secao_pendente"] = nome


def _btn_gerar_bloco_com_inc(secao_key: str):
    """Renderiza checkbox 'Incluir na saída' + botão 'Comparar' na mesma linha."""
    col_inc, col_btn = st.columns([1, 2])
    with col_inc:
        st.markdown('<div style="padding-top:6px"></div>', unsafe_allow_html=True)
        st.checkbox(
            "Incluir na saída",
            key=f"inc_{secao_key}",
            help="Quando desmarcado, esta seção não aparece no Prontuário Completo (dados preservados)",
        )
    with col_btn:
        _btn_gerar_bloco(secao_key)


def _rodape_secao(secao_key: str, nome_display: str | None = None):
    """Renderiza a barra de ações de uma seção: [Output | 🔍 Comparar | 💾 Salvar | Limpar]."""
    from modules import agentes_secoes
    nome = nome_display or agentes_secoes.NOMES_SECOES.get(secao_key, secao_key.capitalize())
    col_inc, col_cmp, col_salvar, col_limpar = st.columns([1, 2, 1, 1])
    with col_inc:
        st.checkbox(
            "Output",
            key=f"inc_{secao_key}",
        )
    with col_cmp:
        _btn_gerar_bloco(secao_key)
    with col_salvar:
        _btn_salvar_secao(secao_key, nome)
    with col_limpar:
        _btn_limpar_secao(secao_key, nome)


def render_formulario_completo():
    # ── Handler: registrar novo SOFA na janela deslizante ───────────────────
    if st.session_state.pop("_sofa_registrar_pendente", False):
        scores._shift_sofa()

    # Aplica valores capturados pela Evolução Diária (bridge Bloco 10/11 → Bloco 13)
    # Usa del+set para evitar StreamlitAPIException em chaves de widget já instanciadas
    if "_evo_bridge_hoje" in st.session_state:
        _bridge_vals = st.session_state.pop("_evo_bridge_hoje")
        for _k, _v in _bridge_vals.items():
            if _v:
                if _k in st.session_state:
                    del st.session_state[_k]
                st.session_state[_k] = _v

    # ── Reload silencioso de lab_*/ctrl_* ──────────────────────────────────────
    # DEVE ficar aqui, antes de qualquer widget ser criado.
    # Se ficar depois do Bloco 10/11, os widgets lab_*/ctrl_* já existem e a
    # atribuição levanta StreamlitAPIException (engolida pelo try/except antigo),
    # fazendo o session_state ficar vazio e o bridge não encontrar nenhum valor.
    _pront_rl = st.session_state.get("prontuario", "").strip()
    _labs_vazios_rl = not any(
        (st.session_state.get(f"lab_{s}_hb") or "").strip()
        or (st.session_state.get(f"lab_{s}_data") or "").strip()
        or (st.session_state.get(f"lab_{s}_cr") or "").strip()
        for s in range(1, 31)
    )
    if _labs_vazios_rl and _pront_rl and st.session_state.get("_ac_pront_reloaded", "") != _pront_rl:
        st.session_state["_ac_pront_reloaded"] = _pront_rl
        try:
            from utils import load_evolucao as _load_ev
            _dados_rl = _load_ev(_pront_rl)
            if _dados_rl:
                _dados_rl.pop("_data_hora", None)
                for _k, _v in _dados_rl.items():
                    if (_k.startswith("lab_") or _k.startswith("ctrl_")) and _v:
                        if _k in st.session_state:
                            del st.session_state[_k]
                        st.session_state[_k] = _v
        except Exception:
            pass

    # Aplica resultados de agentes pendentes ANTES de instanciar qualquer widget.
    # Usa del+set (igual ao _evo_bridge_hoje) para garantir que widgets já
    # existentes no session_state recebam o novo valor sem StreamlitAPIException.
    if "_agent_staging" in st.session_state:
        staging = st.session_state.pop("_agent_staging")
        _normalizar_pills_dict(staging)  # normaliza antes de aplicar ao state
        for k, v in staging.items():
            if k in st.session_state:
                del st.session_state[k]
            st.session_state[k] = v

    # Corrige campos de radio que receberam "" em vez de None
    _sanitizar_radios()
    # Normaliza valores de st.pills carregados da planilha ou por agentes
    _normalizar_pills_state()
    # Reformata campos de data digitados sem barras (ex.: 10022026 → 10/02/2026)
    _normalizar_datas()

    # ==========================================
    # 1. DADOS DO PACIENTE
    # ==========================================
    with st.expander("Dados do Paciente", expanded=False):
        identificacao.render(_agent_btn_callback=_btn_agente("identificacao"))
        _rodape_secao("identificacao", "Identificação")
        st.divider()
        scores.render(_agent_btn_callback=_btn_agente("scores"))
        _rodape_secao("scores", "Scores")
        st.divider()
        hd.render(_agent_btn_callback=_btn_agente("hd"))
        _rodape_secao("hd", "Diagnósticos")
        st.divider()
        comorbidades.render(_agent_btn_callback=_btn_agente("comorbidades"))
        _rodape_secao("comorbidades", "Comorbidades")
        st.divider()
        muc.render(_agent_btn_callback=_btn_agente("muc"))
        _rodape_secao("muc", "Medicações")
        st.divider()
        hmpa.render(_agent_btn_callback=_btn_agente("hmpa"))
        _rodape_secao("hmpa", "HMPA")
        st.divider()
        intraoperatorio.render()
        _rodape_secao("intraoperatorio", "Intraoperatório")

    st.write("")

    # ==========================================
    # 2. DADOS CLÍNICOS
    # ==========================================
    with st.expander("Evolução Horizontal", expanded=False):
        dispositivos.render(_agent_btn_callback=_btn_agente("dispositivos"))
        _rodape_secao("dispositivos", "Dispositivos")
        st.divider()
        culturas.render(_agent_btn_callback=_btn_agente("culturas"))
        _rodape_secao("culturas", "Culturas")
        st.divider()
        antibioticos.render(_agent_btn_callback=_btn_agente("antibioticos"))
        _rodape_secao("antibioticos", "Antibióticos")
        st.divider()
        complementares.render(_agent_btn_callback=_btn_agente("complementares"))
        _rodape_secao("complementares", "Complementares")

    st.write("")

    # ==========================================
    # 3. EVOLUÇÃO DIÁRIA
    # ==========================================
    with st.expander("Evolução Diária", expanded=True):
        # ── Botão global: Evolução Hoje para todos os blocos diários ──────────
        if st.form_submit_button(
            "📅 Evolução Diária",
            key="_fsbtn_evo_hoje_global",
            use_container_width=True,
            type="primary",
            help="Desloca Labs, Controles e Sistemas (hoje→ontem→…). "
                 "Os dados de hoje são carregados automaticamente no Bloco 13.",
        ):
            from modules.fluxo.bridge import _SLOTS, _BRIDGE_LAB, _BRIDGE_CTRL, _lac_do_dia
            from modules.fluxo.state import _limpar

            # ── Captura valores de HOJE antes de qualquer deslocamento ──────────
            # (lab_1/* e ctrl_hoje/* ainda têm os dados do dia atual)
            _captura: dict = {}
            for sis_suf, ctrl_dia, lab_idx in _SLOTS:
                if sis_suf != "hoje":
                    continue
                for dest_pat, suf_lab, fn in _BRIDGE_LAB:
                    val = fn(st.session_state.get(f"lab_{lab_idx}_{suf_lab}", ""))
                    if val:
                        _captura[dest_pat.format(s=sis_suf)] = val
                for dest_pat, suf_ctrl, fn in _BRIDGE_CTRL:
                    val = fn(st.session_state.get(f"ctrl_{ctrl_dia}_{suf_ctrl}", ""))
                    if val:
                        _captura[dest_pat.format(s=sis_suf)] = val
                lac = _lac_do_dia(lab_idx)
                if lac:
                    _captura[f"sis_cardio_lac_{sis_suf}"] = lac
                # Campos fixos (diurese e balanço do dia)
                for sis_key, ctrl_key in [
                    ("sis_renal_diurese", "ctrl_hoje_diurese"),
                    ("sis_renal_balanco",  "ctrl_hoje_balanco"),
                ]:
                    v = _limpar(st.session_state.get(ctrl_key, ""))
                    if v:
                        _captura[sis_key] = v

            if _captura:
                st.session_state["_evo_bridge_hoje"] = _captura

            # ── Deslocamentos (ordem: sistemas → labs → controles) ──────────────
            sistemas._deslocar_sistemas()
            laboratoriais._deslocar_laboratoriais()
            controles._deslocar_dias()
            st.toast("✅ Evolução Diária aplicada — Sistemas serão preenchidos.", icon="📅")

        st.divider()

        # ── 12. Análise Clínica ─────────────────────────────────────────────
        from modules.gerador.html import gerar_html_comparativo as _gerar_html_cmp

        # ── Gera tabela e armazena cache ──────────────────────────────────
        # O cache garante que a tabela NUNCA suma: se a geração atual retornar
        # vazia (por qualquer motivo), usa o último HTML gerado com dados reais.
        _html_labs, _html_ctrl = _gerar_html_cmp()
        if _html_labs:
            st.session_state["_html_labs_cache"] = _html_labs
        if _html_ctrl:
            st.session_state["_html_ctrl_cache"] = _html_ctrl
        _html_labs = _html_labs or st.session_state.get("_html_labs_cache", "")
        _html_ctrl = _html_ctrl or st.session_state.get("_html_ctrl_cache", "")

        st.markdown("##### 📊 12. Análise Clínica")
        st.markdown(
            "<style>"
            ".ac-sec{background:#fff;border:1px solid #e0e0e0;border-radius:10px;"
            "padding:14px 18px 8px;margin-bottom:10px;"
            "box-shadow:0 1px 4px rgba(60,64,67,.12)}"
            ".ac-tit{font-size:.88rem;font-weight:600;color:#1a73e8;"
            "display:block;margin-bottom:8px}"
            ".ac-empty{color:#888;font-size:.84rem;padding:4px 0}"
            "</style>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='ac-sec'><span class='ac-tit'>🧪 Exames Laboratoriais</span>"
            + (_html_labs if _html_labs else "<p class='ac-empty'>Nenhum exame preenchido. Acesse a aba Laboratoriais.</p>")
            + "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='ac-sec'><span class='ac-tit'>💧 Controles & Balanço Hídrico</span>"
            + (_html_ctrl if _html_ctrl else "<p class='ac-empty'>Nenhum controle preenchido. Acesse a aba Controles & BH.</p>")
            + "</div>",
            unsafe_allow_html=True,
        )

        # ── Incluir Laboratoriais e Controles na saída ──────────────────────
        _c_inc_l, _c_inc_c = st.columns(2)
        with _c_inc_l:
            st.checkbox(
                "Incluir Laboratoriais na saída",
                key="inc_laboratoriais",
                help="Quando desmarcado, a seção Laboratoriais não aparece no Prontuário Completo",
            )
        with _c_inc_c:
            st.checkbox(
                "Incluir Controles & BH na saída",
                key="inc_controles",
                help="Quando desmarcado, a seção Controles & BH não aparece no Prontuário Completo",
            )

        st.divider()
        # ── 13. Evolução Clínica ────────────────────────────────────────────
        evolucao_clinica.render()
        _rodape_secao("evolucao", "Evolução Clínica")
        st.divider()
        # ── 14. Evolução por Sistemas ───────────────────────────────────────
        sistemas.render(_agent_btn_callback=_btn_agente("sistemas"))
        _rodape_secao("sistemas", "Sistemas")
        st.divider()
        prescricao.render()
        _rodape_secao("prescricao", "Prescrição")
        st.divider()
        condutas.render()
        _rodape_secao("condutas", "Condutas")

    # ── Botão principal — fora dos expanders, dentro do form ────────────────
    st.write("")
    if st.form_submit_button(
        "💾 Salvar + Gerar Prontuário",
        type="primary",
        use_container_width=True,
        help="Salva todos os dados no banco e atualiza o prontuário completo",
    ):
        st.session_state["_salvar_gerar_pendente"] = True


def migrar_schema_legado(dados: dict) -> dict:
    """Migra prontuários com schema antigo (hd_atual_*/hd_prev_*) para o schema atual (hd_*).
    Também normaliza valores de st.pills para garantir correspondência exata com as opções.
    Seguro chamar sempre: retorna o dict intacto se não há campos legados.
    """
    if "hd_atual_1_nome" in dados:
        for i in range(1, 5):
            dados[f"hd_{i}_nome"]           = dados.get(f"hd_atual_{i}_nome", "")
            dados[f"hd_{i}_class"]          = dados.get(f"hd_atual_{i}_class", "")
            dados[f"hd_{i}_data_inicio"]    = dados.get(f"hd_atual_{i}_data", "")
            dados[f"hd_{i}_data_resolvido"] = ""
            dados[f"hd_{i}_status"]         = "Atual"
            dados[f"hd_{i}_obs"]            = dados.get(f"hd_atual_{i}_obs", "")
            dados[f"hd_{i}_conduta"]        = dados.get(f"hd_atual_{i}_conduta", "")
        for i in range(1, 5):
            j = i + 4
            dados[f"hd_{j}_nome"]           = dados.get(f"hd_prev_{i}_nome", "")
            dados[f"hd_{j}_class"]          = dados.get(f"hd_prev_{i}_class", "")
            dados[f"hd_{j}_data_inicio"]    = dados.get(f"hd_prev_{i}_data_ini", "")
            dados[f"hd_{j}_data_resolvido"] = dados.get(f"hd_prev_{i}_data_fim", "")
            dados[f"hd_{j}_status"]         = "Resolvida"
            dados[f"hd_{j}_obs"]            = dados.get(f"hd_prev_{i}_obs", "")
            dados[f"hd_{j}_conduta"]        = dados.get(f"hd_prev_{i}_conduta", "")
        dados["hd_ordem"] = list(range(1, 9))
    return _normalizar_pills_dict(dados)
