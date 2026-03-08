# ==============================================================================
# modules/pacer/tab_controles.py
# Renderiza a aba "💧 Controles & BH" da página Laboratoriais & Controles.
# ==============================================================================

import re
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.secoes import controles as _ctrl_sec
from modules.parsers import parse_controles_deterministico
from modules.parsers.controles import parse_controles_dia
from modules.agentes_secoes.controles import preencher_controles_dia
from modules.ia_config import get_ia_config

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


def render():
    """Renderiza a aba completa de Controles & Balanço Hídrico."""
    from utils import save_evolucao, load_evolucao
    from modules import fichas

    st.subheader("💧 Controles & Balanço Hídrico")

    # ── Prontuário ────────────────────────────────────────────────────────────
    _fragment_prontuario_ctrl()
    _confirmar_novo_prontuario_ctrl()

    st.write("")
    st.markdown(_CSS_DATAS, unsafe_allow_html=True)

    prontuario = st.session_state.get("prontuario", "").strip()

    # Placeholder para mensagens de save — aparece acima do formulário
    _msg_salvar = st.empty()

    # ── Form principal — sem rerender ao digitar ──────────────────────────────
    with st.form("form_controles_main"):
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            btn_evo = st.form_submit_button(
                "Evolução Hoje", use_container_width=True,
                help="Anteontem some; ontem→anteontem; hoje→ontem; hoje fica em branco.",
            )
        with c2:
            btn_ia = st.form_submit_button(
                "Extrair Controles", use_container_width=True,
                type="primary",
                help="Usa GPT-4o para extrair vitais, diurese e BH do texto de cada coluna "
                     "em qualquer formato, preenchendo os campos automaticamente.",
            )
        with c3:
            btn_parse = st.form_submit_button(
                "Parsing Controles", use_container_width=True,
                help="Preenche deterministicamente. Use: # Controles - 24h, > DD/MM/YYYY, PAS: min - max...",
            )
        with c4:
            btn_salvar = st.form_submit_button(
                "💾 Salvar no Prontuário", use_container_width=True,
                type="primary", disabled=not prontuario,
                help="Salva todos os campos no Google Sheets",
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

        # Dias extras (5º → 10º) em expander
        with st.expander("Demais dias (5º ao 10º)", expanded=False):
            _render_ctrl_block(_ctrl_sec._DIAS_EXP)

    # ── Handlers (fora do form, após submissão) ───────────────────────────────
    if btn_evo:
        _ctrl_sec._deslocar_dias()
        st.toast("Evolução Hoje: hoje está em branco para novos dados.", icon="📅")
        st.rerun()

    if btn_parse:
        dias_com_texto = [
            d for d in _ctrl_sec._DIAS
            if (st.session_state.get(f"ctrl_{d}_texto_entrada") or "").strip()
        ]
        if not dias_com_texto:
            st.warning("Cole o texto de controles nos campos de cada coluna antes de parsear.")
        else:
            # Concatena texto de todas as colunas para detecção de formato multi-bloco
            texto_total = "\n\n".join(
                st.session_state.get(f"ctrl_{d}_texto_entrada", "").strip()
                for d in dias_com_texto
            )

            _tem_bloco = bool(re.search(r"#\s*Controles", texto_total, re.IGNORECASE))

            n = 0
            if _tem_bloco:
                # Formato multi-bloco (# Controles - 24h + > data):
                # usa parse_controles_deterministico que auto-distribui por slot
                existing_dates = {
                    dia: st.session_state.get(f"ctrl_{dia}_data", "")
                    for dia in _ctrl_sec._DIAS
                }
                resultado = parse_controles_deterministico(
                    texto_total, existing_dates=existing_dates
                )
                for k, v in resultado.items():
                    if v:
                        _ctrl_sec._set_ss(k, v)
                        n += 1
            else:
                # Formato por-coluna: cada texto área → seu dia
                def _parse_dia(dia):
                    texto = st.session_state.get(f"ctrl_{dia}_texto_entrada", "").strip()
                    return dia, parse_controles_dia(texto, dia)

                resultados = {}
                with ThreadPoolExecutor(max_workers=len(dias_com_texto)) as ex:
                    futures = {ex.submit(_parse_dia, d): d for d in dias_com_texto}
                    for fut in as_completed(futures):
                        dia, dados = fut.result()
                        resultados[dia] = dados

                for dados in resultados.values():
                    for k, v in dados.items():
                        if v:
                            _ctrl_sec._set_ss(k, v)
                            n += 1

            if n:
                st.toast(f"✅ {n} campos preenchidos.", icon="📊")
                st.rerun()
            else:
                st.warning("⚠️ Nenhum valor reconhecido no formato esperado.")

    if btn_ia:
        dias_com_texto = [
            d for d in _ctrl_sec._DIAS
            if (st.session_state.get(f"ctrl_{d}_texto_entrada") or "").strip()
        ]
        if not dias_com_texto:
            st.warning("Cole o texto de controles nos campos de cada coluna antes de usar a IA.")
        else:
            google_key = st.session_state.get("google_api_key", "")
            openai_key = st.session_state.get("openai_api_key", "")
            api_key, provider, modelo = get_ia_config("controles", google_key, openai_key)

            if not api_key:
                st.error("⚠️ Configure uma chave de API (OpenAI ou Google) nas configurações.")
            else:
                def _ia_dia(dia):
                    texto = st.session_state.get(f"ctrl_{dia}_texto_entrada", "").strip()
                    return dia, preencher_controles_dia(texto, dia, api_key, provider, modelo)

                with st.spinner(
                    f"🤖 Extraindo {len(dias_com_texto)} coluna(s) via {provider} ({modelo})..."
                ):
                    with ThreadPoolExecutor(max_workers=len(dias_com_texto)) as ex:
                        futures = {ex.submit(_ia_dia, d): d for d in dias_com_texto}
                        resultados = {}
                        for fut in as_completed(futures):
                            dia, dados = fut.result(timeout=120)
                            resultados[dia] = dados

                erros = [f"{d}: {r['_erro']}" for d, r in resultados.items() if r.get("_erro")]
                if erros:
                    st.error("❌ Erros: " + " | ".join(erros))

                n = 0
                for dados in resultados.values():
                    for k, v in dados.items():
                        if k != "_erro" and v and v != "":
                            _ctrl_sec._set_ss(k, v)
                            n += 1
                if n:
                    st.toast(
                        f"✅ IA preencheu {n} campos em {len(dias_com_texto)} coluna(s).",
                        icon="🤖",
                    )
                    st.rerun()

    if btn_salvar:
        _msg_salvar.info("💾 Salvando...")
        with st.spinner("💾 Salvando..."):
            # Carrega última versão salva para preservar seções fora do escopo desta aba
            base = load_evolucao(prontuario) or {}
            base.pop("_data_hora", None)
            todas_chaves = fichas.get_todos_campos_keys()
            # Campos ctrl_* vêm do session_state atual; todo o resto vem do último save
            dados = {
                k: (st.session_state.get(k) if k.startswith("ctrl_")
                    else base.get(k, st.session_state.get(k)))
                for k in todas_chaves
            }
            ok = save_evolucao(prontuario, st.session_state.get("nome", "").strip(), dados)
        if ok:
            _msg_salvar.success(f"✅ Salvo com sucesso! Prontuário: {prontuario}")
        else:
            _msg_salvar.error("❌ Erro ao salvar. Verifique a conexão.")

