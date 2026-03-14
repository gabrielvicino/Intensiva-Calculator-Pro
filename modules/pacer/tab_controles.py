# ==============================================================================
# modules/pacer/tab_controles.py
# Renderiza a aba "💧 Controles & BH" da página Laboratoriais & Controles.
# ==============================================================================

import re
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.secoes import controles as _ctrl_sec
from modules.parsers.controles import parse_controles_dia as _parse_det_dia
from modules.parsers.controles import parse_controles_deterministico as _parse_det_multi
from modules.agentes_secoes.controles import preencher_controles_dia, preencher_controles

_CSS_DATAS = """
<style>
    input[id*="ctrl_hoje_data"], input[id*="ctrl_ontem_data"],
    input[id*="ctrl_anteontem_data"], input[id*="ctrl_ant4_data"], input[id*="ctrl_ant5_data"],
    input[id*="ctrl_ant6_data"], input[id*="ctrl_ant7_data"], input[id*="ctrl_ant8_data"],
    input[id*="ctrl_ant9_data"], input[id*="ctrl_ant10_data"] {
        text-align: center;
    }
    input[id*="ctrl_hoje_data"]::placeholder, input[id*="ctrl_ontem_data"]::placeholder,
    input[id*="ctrl_anteontem_data"]::placeholder, input[id*="ctrl_ant4_data"]::placeholder,
    input[id*="ctrl_ant5_data"]::placeholder, input[id*="ctrl_ant6_data"]::placeholder,
    input[id*="ctrl_ant7_data"]::placeholder, input[id*="ctrl_ant8_data"]::placeholder,
    input[id*="ctrl_ant9_data"]::placeholder, input[id*="ctrl_ant10_data"]::placeholder {
        text-align: center;
        text-transform: uppercase;
    }
</style>
"""


# ==============================================================================
# Prontuário — busca e salvamento (espelho do tab Laboratoriais)
# ==============================================================================

@st.fragment
def _fragment_prontuario_ctrl() -> None:
    """Campo de prontuário + botão Buscar — compartilha estado com o tab Laboratoriais."""
    from utils import load_evolucao
    from modules import fichas

    # Sincroniza com o prontuário sempre que ele for atualizado externamente
    # (ex.: carregado pelo tab Laboratoriais). Usa rastreador para não sobrescrever
    # o que o usuário está digitando manualmente.
    _pront_atual = st.session_state.get("prontuario", "")
    _last_sync   = st.session_state.get("_ctrl_pront_last_sync", None)
    if _pront_atual != _last_sync:
        st.session_state["_ctrl_pront_input"] = _pront_atual
        st.session_state["_ctrl_pront_last_sync"] = _pront_atual

    with st.form(key="form_busca_ctrl"):
        c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
        with c_input:
            busca_input = st.text_input(
                "Número do Prontuário",
                placeholder="Ex.: 1234567",
                key="_ctrl_pront_input",
            )
        with c_btn:
            btn_buscar = st.form_submit_button(
                "Buscar", use_container_width=True, type="primary"
            )

        busca = busca_input.strip() if busca_input else ""
        if btn_buscar:
            if not busca:
                st.warning("Informe o número do prontuário.")
            else:
                with st.spinner("Consultando banco de dados..."):
                    dados = load_evolucao(busca)
                if dados is not None:
                    _aplicar_dados_prontuario_ctrl(dados, fichas)
                    st.rerun()
                else:
                    st.session_state["_ctrl_pront_pendente"] = busca
                    st.rerun()


def _aplicar_dados_prontuario_ctrl(dados: dict, fichas_mod) -> None:
    """Aplica dados carregados ao session_state preservando valores não-vazios existentes."""
    if not dados:
        return
    data_hora = dados.pop("_data_hora", "")
    dados = fichas_mod.migrar_schema_legado(dados)
    campos_validos = set(fichas_mod.get_todos_campos_keys())
    for k, v in dados.items():
        if k in campos_validos:
            # Só sobrescreve se o Sheets tiver valor, ou se o campo estiver vazio
            if v or not st.session_state.get(k):
                if k in st.session_state:
                    del st.session_state[k]
                st.session_state[k] = v
    st.session_state["_data_hora_carregado"] = data_hora
    st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")


def _confirmar_novo_prontuario_ctrl() -> None:
    """Exibe opção de criar novo prontuário quando não encontrado."""
    from utils import save_evolucao

    if "_ctrl_pront_pendente" not in st.session_state:
        return

    pend = st.session_state["_ctrl_pront_pendente"]
    with st.container(border=True):
        st.markdown(
            f"**Prontuário {pend} não localizado.**  \n"
            "Nenhum registro encontrado. Deseja iniciar um novo prontuário?",
        )
        c_sim, c_nao, *_ = st.columns([2, 2, 8])
        with c_sim:
            if st.button(
                "Criar prontuário", type="primary",
                use_container_width=True, key="_ctrl_btn_criar",
            ):
                st.session_state.pop("_ctrl_pront_pendente", None)
                st.session_state["prontuario"] = pend
                with st.spinner("Registrando novo prontuário..."):
                    save_evolucao(pend, "", {"prontuario": pend})
                st.toast(f"Prontuário {pend} registrado com sucesso.", icon="✅")
                st.rerun()
        with c_nao:
            if st.button(
                "Cancelar", use_container_width=True, key="_ctrl_btn_cancelar_criar",
            ):
                st.session_state.pop("_ctrl_pront_pendente", None)
                st.rerun()


def render(api_key: str = "", modelo: str = "gpt-4o"):
    """Renderiza a aba completa de Controles & Balanço Hídrico."""
    from utils import save_evolucao, load_evolucao
    from modules import fichas

    # ── Auto-load: recupera controles salvos ao iniciar nova sessão ──────────
    _pront_autoload = st.session_state.get("prontuario", "").strip()
    _ctrl_vazios = not any(
        st.session_state.get(f"ctrl_{dia}_diurese") or st.session_state.get(f"ctrl_{dia}_data")
        for dia in ("hoje", "ontem", "anteontem")
    )
    _ultimo_reload_ctrl = st.session_state.get("_ctrl_ultimo_reload", "")

    if _pront_autoload and _ctrl_vazios and _ultimo_reload_ctrl != _pront_autoload:
        with st.spinner("Carregando controles salvos..."):
            _dados_autoload = load_evolucao(_pront_autoload)
        if _dados_autoload:
            _dados_autoload.pop("_data_hora", None)
            _dados_autoload = fichas.migrar_schema_legado(_dados_autoload)
            campos_validos = set(fichas.get_todos_campos_keys())
            for k, v in _dados_autoload.items():
                if k in campos_validos and (v or not st.session_state.get(k)):
                    if k in st.session_state:
                        del st.session_state[k]
                    st.session_state[k] = v
            st.toast("Controles carregados do prontuário.", icon="💧")
        st.session_state["_ctrl_ultimo_reload"] = _pront_autoload

    st.subheader("💧 Controles & Balanço Hídrico")

    # ── Prontuário ────────────────────────────────────────────────────────────
    _fragment_prontuario_ctrl()
    _confirmar_novo_prontuario_ctrl()

    st.write("")
    st.markdown(_CSS_DATAS, unsafe_allow_html=True)

    prontuario = st.session_state.get("prontuario", "").strip()

    # Feedback no topo — antes de tudo
    _msg_salvar = st.empty()
    _msg_avisos = st.empty()
    if "_ctrl_avisos" in st.session_state:
        with _msg_avisos.container():
            for aviso in st.session_state.pop("_ctrl_avisos"):
                if aviso.startswith("✅"):
                    st.success(aviso)
                elif aviso.startswith("❌") or aviso.startswith("⚠️"):
                    st.warning(aviso)
                else:
                    st.info(aviso)

    # ── Form principal — sem rerender ao digitar ──────────────────────────────
    with st.form("form_controles_main"):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            btn_evo = st.form_submit_button(
                "Evolução Hoje", use_container_width=True,
                help="Anteontem some; ontem→anteontem; hoje→ontem; hoje fica em branco.",
            )
        with c2:
            btn_ia = st.form_submit_button(
                "Extrair Controles", use_container_width=True,
                type="primary",
                help="Usa IA para extrair vitais, diurese e BH do texto de cada coluna. "
                     "Cole múltiplos dias no mesmo campo — a IA distribui automaticamente.",
            )
        with c3:
            btn_salvar = st.form_submit_button(
                "💾 Salvar e ir para Prescrição →", use_container_width=True,
                type="primary", disabled=not prontuario,
                help="Salva os controles e avança para a aba de Prescrição",
            )

        def _render_ctrl_block(dias_list: list) -> None:
            """
            Renderiza a tabela de controles COLUNA POR COLUNA.

            O DOM fica: todos os parâmetros do dia1 → todos do dia2 → ...
            Isso faz o Tab descer para o próximo parâmetro (mesmo dia),
            em vez de ir para o próximo dia (mesmo parâmetro).
            Igual à técnica usada em laboratoriais._render_labs_table.
            """
            first = dias_list[0]

            def _lv(dia):
                return "visible" if dia == first else "hidden"

            _HDR_STYLE = (
                "text-align:center;font-size:0.82rem;font-weight:700;"
                "color:#1a73e8;padding-bottom:2px;"
            )
            day_cols = st.columns([1] * len(dias_list))

            # ── cabeçalho: nome do dia + text_area + data ────────────────────
            for dc, dia in zip(day_cols, dias_list):
                with dc:
                    st.markdown(
                        f'<div style="{_HDR_STYLE}">'
                        f'{_ctrl_sec._LABEL_DIA[dia]}</div>',
                        unsafe_allow_html=True,
                    )
                    st.text_area(
                        "Controles", key=f"ctrl_{dia}_texto_entrada",
                        placeholder="Cole os controles aqui...",
                        label_visibility="collapsed",
                        height=68,
                    )
                    st.text_input(
                        "Data", key=f"ctrl_{dia}_data",
                        placeholder="DD/MM/AAAA", label_visibility=_lv(dia),
                    )

            # ── parâmetros: renderiza TODOS para cada coluna ─────────────────
            for dc, dia in zip(day_cols, dias_list):
                with dc:
                    for chave, _label, min_max, *_ in _ctrl_sec._PARAMS:
                        lbl = _ctrl_sec._LABEL_CURTO.get(chave, chave)
                        if min_max:
                            cmin, cmax = st.columns(2)
                            with cmin:
                                st.text_input(
                                    lbl, key=f"ctrl_{dia}_{chave}_min",
                                    placeholder="Mín", label_visibility=_lv(dia),
                                )
                            with cmax:
                                st.text_input(
                                    lbl + " max", key=f"ctrl_{dia}_{chave}_max",
                                    placeholder="Máx", label_visibility="hidden",
                                )
                        else:
                            st.text_input(
                                lbl, key=f"ctrl_{dia}_{chave}",
                                placeholder="Valor", label_visibility=_lv(dia),
                            )

        # Dias principais (hoje → 4º dia)
        _render_ctrl_block(_ctrl_sec._DIAS_MAIN)

        # Botões de apagar dia — dias principais
        st.divider()
        _clr_cols_main = st.columns(len(_ctrl_sec._DIAS_MAIN))
        for _col, _dia in zip(_clr_cols_main, _ctrl_sec._DIAS_MAIN):
            with _col:
                _label = _ctrl_sec._LABEL_DIA.get(_dia, _dia)
                if st.form_submit_button(
                    f"Apagar controles {_label.lower()}", use_container_width=True,
                    help=f"Apaga todos os dados de controles de '{_label}'",
                ):
                    st.session_state[f"_ctrl_clear_{_dia}"] = True

        # Dias extras (5º → 10º) em expander
        with st.expander("Demais dias (5º ao 10º)", expanded=False):
            _render_ctrl_block(_ctrl_sec._DIAS_EXP)

            # Botões de apagar dia — dias extras
            st.divider()
            _clr_cols_exp = st.columns(len(_ctrl_sec._DIAS_EXP))
            for _col, _dia in zip(_clr_cols_exp, _ctrl_sec._DIAS_EXP):
                with _col:
                    _label = _ctrl_sec._LABEL_DIA.get(_dia, _dia)
                    if st.form_submit_button(
                        f"Apagar {_label.lower()}", use_container_width=True,
                        help=f"Apaga todos os dados de '{_label}'",
                    ):
                        st.session_state[f"_ctrl_clear_{_dia}"] = True

    # ── Handlers (fora do form, após submissão) ───────────────────────────────
    if btn_evo:
        _ctrl_sec._deslocar_dias()
        st.toast("Evolução Hoje: hoje está em branco para novos dados.", icon="📅")
        st.rerun()

    # Handlers de apagar dia
    for _dia in _ctrl_sec._DIAS:
        if st.session_state.pop(f"_ctrl_clear_{_dia}", False):
            _ctrl_sec._limpar_dia(_dia)
            _label = _ctrl_sec._LABEL_DIA.get(_dia, _dia)
            st.toast(f"🗑️ Controles {_label} apagados.", icon="🗑️")
            st.rerun()

    if btn_ia:
        dias_com_texto = [
            d for d in _ctrl_sec._DIAS
            if (st.session_state.get(f"ctrl_{d}_texto_entrada") or "").strip()
        ]
        if not dias_com_texto:
            st.session_state["_ctrl_avisos"] = ["⚠️ Cole o texto nos campos de cada coluna antes de extrair."]
            st.session_state["_tab_index"] = 1
            st.rerun()
        else:
            _provider = "OpenAI GPT"

            # Lê textos ANTES de spawnar threads (session_state não é thread-safe)
            textos_ctrl = {
                d: (st.session_state.get(f"ctrl_{d}_texto_entrada") or "").strip()
                for d in dias_com_texto
            }

            def _extrair_coluna(dia):
                texto = textos_ctrl[dia]
                tem_multiplos = (
                    len(re.findall(r"#\s*Controles", texto, re.IGNORECASE)) > 1
                )

                # ── 1ª tentativa: parser determinístico (sem API, instantâneo) ──
                if tem_multiplos:
                    dados = _parse_det_multi(texto)
                else:
                    dados = _parse_det_dia(texto, dia)

                n_det = len([v for v in dados.values() if v and str(v).strip()])

                # ── Fallback IA: só se regex extraiu 0 campos E há chave de API ──
                if n_det == 0 and api_key:
                    if tem_multiplos:
                        dados = preencher_controles(texto, api_key, _provider, modelo)
                    else:
                        dados = preencher_controles_dia(texto, dia, api_key, _provider, modelo)

                return dia, dados, tem_multiplos

            with _msg_avisos.container():
                st.info(f"⚡ Extraindo {len(dias_com_texto)} coluna(s)...")
            with ThreadPoolExecutor(max_workers=len(dias_com_texto)) as ex:
                futures = {ex.submit(_extrair_coluna, d): d for d in dias_com_texto}
                resultados = {}
                for fut in as_completed(futures):
                    dia, dados, multi = fut.result(timeout=120)
                    resultados[dia] = (dados, multi)
            _msg_avisos.empty()

            erros = [
                f"{d}: {r[0]['_erro']}"
                for d, r in resultados.items() if r[0].get("_erro")
            ]
            if erros:
                st.session_state["_ctrl_avisos"] = [f"❌ {' | '.join(erros)}"]

            n = 0
            for dia, (dados, multi) in resultados.items():
                if dados.get("_erro"):
                    continue
                for k, v in dados.items():
                    if v and str(v).strip():
                        _ctrl_sec._set_ss(k, v)
                        n += 1
                # Limpa campo de texto de entrada após extração bem-sucedida
                _ctrl_sec._set_ss(f"ctrl_{dia}_texto_entrada", "")

            if n:
                st.toast(f"✅ {n} campos preenchidos em {len(dias_com_texto)} coluna(s).", icon="⚡")
            st.session_state["_tab_index"] = 1
            st.rerun()

    if btn_salvar:
        _msg_salvar.info("💾 Salvando controles...")
        base = load_evolucao(prontuario) or {}
        base.pop("_data_hora", None)
        for k in list(st.session_state.keys()):
            if k.startswith("ctrl_"):
                base[k] = st.session_state[k]
        ok = save_evolucao(prontuario, st.session_state.get("nome", "").strip(), base)
        if ok:
            st.session_state["_tab_index"] = 2  # → aba Prescrição
            st.rerun()
        else:
            _msg_salvar.error("❌ Erro ao salvar. Verifique a conexão.")

