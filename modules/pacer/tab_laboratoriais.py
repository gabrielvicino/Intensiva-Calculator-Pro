# ==============================================================================
# modules/pacer/tab_laboratoriais.py
# Aba "🧪 Laboratoriais" — refatorada para coletas cronológicas (max 30).
#
# Fluxo híbrido de extração:
#   1. Parser determinístico HC Unicamp
#   2. (Futuros parsers)
#   3. LLM fallback (7 agentes em paralelo)
#
# Colunas ordenadas por (data, hora_cheia).
# Sem regra de Admissão — todas as colunas são iguais.
# ==============================================================================

import re
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.secoes import laboratoriais as _lab_sec
from modules.secoes.laboratoriais import (
    MAX_SLOTS,
    get_active_slots_sorted,
    adicionar_coleta,
    render_chrono_headers,
    limpar_slot,
)
from modules.pacer.pdf_extractor import _chamar_agente, _AGENTES

_COLS_VISIVEL = 6


# ==============================================================================
# Prontuário — busca e salvamento (espelho da Evolução Diária)
# ==============================================================================

@st.fragment
def _fragment_prontuario() -> None:
    from utils import load_evolucao
    from modules import fichas

    _pront_atual = st.session_state.get("prontuario", "")
    _last_sync = st.session_state.get("_lab_pront_last_sync", None)
    if _pront_atual != _last_sync:
        st.session_state["_lab_pront_input"] = _pront_atual
        st.session_state["_lab_pront_last_sync"] = _pront_atual

    with st.form(key="form_busca_lab"):
        c_input, c_btn = st.columns([5, 1], vertical_alignment="bottom")
        with c_input:
            busca_input = st.text_input(
                "Número do Prontuário",
                placeholder="Ex.: 1234567",
                key="_lab_pront_input",
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
                    _aplicar_dados_prontuario(dados, fichas)
                    st.rerun()
                else:
                    st.session_state["_lab_pront_pendente"] = busca
                    st.rerun()


def _aplicar_dados_prontuario(dados: dict, fichas_mod) -> None:
    if not dados:
        return
    data_hora = dados.pop("_data_hora", "")
    dados = fichas_mod.migrar_schema_legado(dados)
    campos_validos = set(fichas_mod.get_todos_campos_keys())
    for k, v in dados.items():
        if k in campos_validos:
            if v or not st.session_state.get(k):
                st.session_state[k] = v
    st.session_state["_data_hora_carregado"] = data_hora
    st.toast(f"Prontuário carregado — última evolução: {data_hora}", icon="✅")


def _confirmar_novo_prontuario() -> None:
    from utils import save_evolucao

    if "_lab_pront_pendente" not in st.session_state:
        return

    pend = st.session_state["_lab_pront_pendente"]
    with st.container(border=True):
        st.markdown(
            f"**Prontuário {pend} não localizado.**  \n"
            "Nenhum registro encontrado. Deseja iniciar um novo prontuário?",
        )
        c_sim, c_nao, *_ = st.columns([2, 2, 8])
        with c_sim:
            if st.button(
                "Criar prontuário", type="primary",
                use_container_width=True, key="_lab_btn_criar",
            ):
                st.session_state.pop("_lab_pront_pendente", None)
                st.session_state["prontuario"] = pend
                with st.spinner("Registrando novo prontuário..."):
                    save_evolucao(pend, "", {"prontuario": pend})
                st.toast(f"Prontuário {pend} registrado com sucesso.", icon="✅")
                st.rerun()
        with c_nao:
            if st.button(
                "Cancelar", use_container_width=True, key="_lab_btn_cancelar_criar",
            ):
                st.session_state.pop("_lab_pront_pendente", None)
                st.rerun()


# ==============================================================================
# Agente complementar — Não Transcritos (OpenAI, chamada única)
# ==============================================================================

_PROMPT_NAO_TRANSCRITOS_OPENAI = """\
Você é um especialista em auditoria de laudos laboratoriais brasileiros.

TAREFA
Leia o laudo e identifique TODOS os exames/testes laboratoriais presentes.
Em seguida, liste APENAS os que NÃO pertencem às categorias abaixo (já extraídas por outro sistema):

CATEGORIAS JÁ COBERTAS — IGNORE:
- Hemograma: Hb, Ht, VCM, HCM, RDW, Leucócitos e diferencial, Plaquetas
- Renal/Eletrólitos: Creatinina, Ureia, Sódio, Potássio, Magnésio, Fósforo, Cálcio Total, Cálcio Iônico
- Hepático/Pancreático: TGP, TGO, FAL, GGT, Bilirrubinas (BT, BD, BI), Proteínas Totais, Albumina, Amilase, Lipase
- Cardio/Coag/Inflamação: CPK, CK-MB, BNP, Troponina, PCR, VHS, TP, RNI, TTPa, Lactato
- Urina (EAS): Densidade, Leucócitos, Hemácias, Proteína, Nitrito, Corpos Cetônicos, Glicose, Esterase
- Gasometria: pH, pCO2, pO2, HCO3, BE, SatO2, SvO2, Anion Gap, Cloreto

REGRAS:
1. Liste APENAS exames fora das categorias acima.
2. Use o nome comum em português, capitalizado (ex: TSH, T4 Livre, Ferritina, PTH, Insulina, Vancomicina sérica).
3. Separe por vírgula e espaço: TSH, T4 Livre, Ferritina
4. Se não houver nenhum exame extra: responda exatamente VAZIO
5. Sem explicações, sem markdown.

LAUDO:
{{TEXTO_INPUT}}"""


def _extrair_nao_transcritos(texto: str, openai_api_key: str) -> str:
    """
    Chama GPT-4o-mini para extrair nomes de exames não capturados pelo parser.
    Retorna string "TSH, Glicose, PTH" ou "" se vazio/erro.
    """
    if not openai_api_key or not texto:
        return ""
    try:
        from openai import OpenAI as _OpenAI
        client = _OpenAI(api_key=openai_api_key)
        prompt = _PROMPT_NAO_TRANSCRITOS_OPENAI.replace("{{TEXTO_INPUT}}", texto)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            seed=42,
        )
        resultado = (resp.choices[0].message.content or "").strip()
        if not resultado or resultado.upper() == "VAZIO":
            return ""
        return resultado
    except Exception as e:
        print(f"[NÃO TRANSCRITOS] Erro OpenAI: {e}")
        return ""


# ==============================================================================
# Extração híbrida — parser determinístico → LLM fallback
# ==============================================================================

def _extrair_data_hora_texto(texto: str) -> tuple[str, str]:
    """Extrai (data, hora) via regex no texto bruto."""
    m = re.search(
        r'Recebimento material:\s*(\d{2}/\d{2}/\d{2,4})\s+(\d{2}:\d{2})', texto
    )
    if m:
        partes = m.group(1).split("/")
        if len(partes) == 3 and len(partes[2]) == 2:
            partes[2] = "20" + partes[2]
        return "/".join(partes), m.group(2)
    m2 = re.search(r'(\d{2}/\d{2}/\d{2,4})', texto)
    if m2:
        partes = m2.group(1).split("/")
        if len(partes) == 3 and len(partes[2]) == 2:
            partes[2] = "20" + partes[2]
        return "/".join(partes), ""
    return "", ""


def _processar_texto_hibrido(
    texto: str, api_key: str, modelo: str, provider: str = "",
) -> tuple[list[dict], str]:
    """
    Processa texto de laudo com fluxo híbrido:
      1. Parser HC Unicamp (determinístico, instantâneo)
      2. LLM fallback (7 agentes em paralelo)
    Retorna (lista de coletas, caminho usado: "regex" | "ia").
    NÃO chama GPT para não-transcritos — isso é feito depois, desacoplado.
    """
    from modules.parsers.hc_unicamp import parsear as _parsear_unicamp

    coletas = _parsear_unicamp(texto)
    if coletas:
        return coletas, "regex"

    from modules.parsers.lab import parse_agentes_bare

    resultados: dict[str, str | None] = {}

    def _worker(nome: str, prompt: str):
        return nome, _chamar_agente(prompt, texto, api_key, modelo, provider)

    with ThreadPoolExecutor(max_workers=7) as ex:
        futures = {ex.submit(_worker, n, p): n for n, p in _AGENTES.items()}
        for f in as_completed(futures):
            nome, saida = f.result(timeout=90)
            resultados[nome] = saida

    if not any(v for v in resultados.values()):
        return [], "ia"

    coleta = parse_agentes_bare(resultados)

    data, hora = _extrair_data_hora_texto(texto)
    if not data:
        data_agent = (resultados.get("data_coleta") or "").strip()
        if data_agent and data_agent.upper() != "VAZIO":
            data = data_agent
    coleta["data"] = data
    coleta["hora"] = hora
    try:
        coleta["hora_cheia"] = int(hora.split(":")[0]) if ":" in hora else 0
    except (ValueError, IndexError):
        coleta["hora_cheia"] = 0

    result = [coleta] if any(v for k, v in coleta.items() if k not in ("data", "hora", "hora_cheia")) else []
    return result, "ia"


def _extrair_com_ia(
    api_key: str, modelo: str, provider: str = "",
    openai_api_key: str = "", placeholder=None,
) -> None:
    """Extrai dos 4 campos de input em paralelo, adiciona como coletas.

    Fluxo otimizado:
      1. Parser regex (instantâneo) — adiciona coletas imediatamente
      2. GPT-4o-mini para não-transcritos — roda depois, só para textos regex
    """
    textos = []
    for i in range(4):
        txt = (st.session_state.get(f"_lab_input_{i}") or "").strip()
        if txt:
            textos.append((i, txt))

    if not textos:
        st.session_state["_lab_avisos"] = [
            "⚠️ Cole o texto do laudo nos campos acima antes de extrair."
        ]
        return

    if placeholder is not None:
        with placeholder.container():
            st.info(f"🔬 Processando {len(textos)} laudo(s)...")

    # Fase 1: parser regex/IA (sem GPT não-transcritos)
    def _processar_um(idx_texto):
        idx, texto = idx_texto
        coletas, caminho = _processar_texto_hibrido(
            texto, api_key, modelo, provider,
        )
        return idx, coletas, caminho

    resultados_paralelos = {}
    with ThreadPoolExecutor(max_workers=max(len(textos), 1)) as ex:
        futures = {ex.submit(_processar_um, t): t[0] for t in textos}
        for f in as_completed(futures):
            idx, coletas, caminho = f.result()
            resultados_paralelos[idx] = (coletas, caminho)

    n_total = 0
    erros = []
    logs = []
    regex_textos_para_gpt: list[tuple[int, str, int]] = []

    for idx, texto in textos:
        coletas, caminho = resultados_paralelos.get(idx, ([], "?"))
        icone = "⚡" if caminho == "regex" else "🤖"
        if coletas:
            n_coletas = 0
            primeiro_slot = None
            for coleta in coletas:
                slot = adicionar_coleta(coleta)
                if slot is not None:
                    if primeiro_slot is None:
                        primeiro_slot = slot
                    n_campos = len([v for k, v in coleta.items()
                                    if v and k not in ("data", "hora", "hora_cheia")])
                    n_total += n_campos
                    n_coletas += 1
                else:
                    erros.append(f"Laudo {idx + 1}: limite de {MAX_SLOTS} coletas atingido.")
            via = "Parser regex (HC Unicamp)" if caminho == "regex" else f"IA ({modelo})"
            logs.append(f"{icone} Laudo {idx + 1}: {n_coletas} coleta(s) via {via}")
            st.session_state.pop(f"_lab_input_{idx}", None)
            st.session_state[f"_lab_input_{idx}"] = ""
            if caminho == "regex" and primeiro_slot is not None:
                regex_textos_para_gpt.append((idx, texto, primeiro_slot))
        else:
            erros.append(f"Laudo {idx + 1}: nenhum campo extraído.")

    # Fase 2: GPT não-transcritos (só para textos parseados por regex)
    if regex_textos_para_gpt and openai_api_key:
        if placeholder is not None:
            with placeholder.container():
                st.info("🤖 Buscando exames não transcritos (GPT)...")
        with ThreadPoolExecutor(max_workers=max(len(regex_textos_para_gpt), 1)) as ex:
            futs = {
                ex.submit(_extrair_nao_transcritos, txt, openai_api_key): slot
                for _, txt, slot in regex_textos_para_gpt
            }
            for f in as_completed(futs):
                slot = futs[f]
                try:
                    nao_trans = f.result()
                    if nao_trans:
                        st.session_state[f"lab_{slot}_outros"] = nao_trans
                except Exception:
                    pass

    if placeholder is not None:
        placeholder.empty()

    avisos = []
    if n_total > 0:
        avisos.append(f"✅ {n_total} campos extraídos com sucesso!")
    avisos += [f"ℹ️ {lg}" for lg in logs]
    if erros:
        avisos += [f"⚠️ {e}" for e in erros]
    if avisos:
        st.session_state["_lab_avisos"] = avisos


# ==============================================================================
# Campos de texto para input (4 áreas para colar laudos)
# ==============================================================================

def _render_input_areas() -> None:
    cols = st.columns(4)
    for i, col in enumerate(cols):
        with col:
            st.text_area(
                f"Laudo {i + 1}",
                key=f"_lab_input_{i}",
                placeholder="Cole o laudo aqui...",
                label_visibility="collapsed",
                height=68,
            )


# ==============================================================================
# render() — ponto de entrada da aba
# ==============================================================================

def render(api_key: str = "", modelo: str = "gpt-4o", openai_api_key: str = "") -> None:
    from utils import save_evolucao, load_evolucao
    from modules import fichas

    # ── Auto-load ──────────────────────────────────────────────────────────
    _pront_autoload = st.session_state.get("prontuario", "").strip()
    _labs_vazios = not any(
        st.session_state.get(f"lab_{i}_hb") or st.session_state.get(f"lab_{i}_data")
        for i in range(1, 5)
    )
    _ultimo_reload_lab = st.session_state.get("_lab_ultimo_reload", "")

    if _pront_autoload and _labs_vazios and _ultimo_reload_lab != _pront_autoload:
        with st.spinner("Carregando exames salvos..."):
            _dados_autoload = load_evolucao(_pront_autoload)
        if _dados_autoload:
            _aplicar_dados_prontuario(_dados_autoload, fichas)
            st.toast("Exames carregados do prontuário.", icon="🧪")
        st.session_state["_lab_ultimo_reload"] = _pront_autoload

    # Aplica resultados pendentes
    if "_lab_pending_update" in st.session_state:
        pending_update = st.session_state.pop("_lab_pending_update")
        for k, v in pending_update.items():
            if v is not None and str(v).strip() != "":
                st.session_state[k] = v

    st.subheader("🧪 Exames Laboratoriais")

    # ── Feedback no topo (antes de tudo) ───────────────────────────────────
    _msg_topo = st.empty()
    _msg_avisos = st.empty()
    if "_lab_avisos" in st.session_state:
        with _msg_avisos.container():
            for aviso in st.session_state.pop("_lab_avisos"):
                if aviso.startswith("✅"):
                    st.success(aviso)
                elif aviso.startswith("⚠️"):
                    st.warning(aviso)
                else:
                    st.info(aviso)

    # ── Prontuário ─────────────────────────────────────────────────────────
    _fragment_prontuario()
    _confirmar_novo_prontuario()
    st.write("")

    prontuario = st.session_state.get("prontuario", "").strip()

    # ── Form principal ─────────────────────────────────────────────────────
    with st.form("form_laboratoriais_main"):
        # Input areas
        st.markdown(
            '<div style="font-size:0.8rem;font-weight:600;color:#5f6368;'
            'margin-bottom:4px">Cole os laudos abaixo:</div>',
            unsafe_allow_html=True,
        )
        _render_input_areas()

        # Botões
        b1, b2, b3 = st.columns(3)
        with b1:
            btn_extrair = st.form_submit_button(
                "🔬 Parsear e Adicionar",
                use_container_width=True,
                type="primary",
                help="HC Unicamp: parser determinístico + ChatGPT para não-transcritos. Outros labs: IA completa.",
            )
        with b2:
            btn_nova = st.form_submit_button(
                "➕ Nova Coleta Vazia",
                use_container_width=True,
                help="Cria uma coleta vazia para preenchimento manual.",
            )
        with b3:
            btn_salvar = st.form_submit_button(
                "💾 Salvar no Prontuário",
                use_container_width=True,
                type="primary",
                disabled=not prontuario,
            )

        # ── Tabela cronológica (mais recente primeiro) ────────────────────
        active_slots = list(reversed(get_active_slots_sorted()))

        if active_slots:
            main_slots = active_slots[:_COLS_VISIVEL]
            rest_slots = active_slots[_COLS_VISIVEL:]

            render_chrono_headers(main_slots)
            _lab_sec._render_labs_table(
                main_slots, show_header=False, show_conduta=False
            )
            _lab_sec._render_gas_extras(main_slots)

            # Botões de apagar — colunas principais
            st.divider()
            del_cols = st.columns(len(main_slots))
            for col, slot in zip(del_cols, main_slots):
                data = st.session_state.get(f"lab_{slot}_data", "") or f"#{slot}"
                hora_raw = st.session_state.get(f"lab_{slot}_hora", "") or ""
                try:
                    h = int(hora_raw.split(":")[0])
                    label = f"Apagar {data} {h:02d}h"
                except (ValueError, IndexError):
                    label = f"Apagar {data}"
                with col:
                    if st.form_submit_button(
                        label, use_container_width=True,
                        key=f"_btn_del_main_{slot}",
                        help=f"Apaga todos os dados desta coleta",
                    ):
                        st.session_state[f"_lab_clear_slot_{slot}"] = True

            # Demais coletas em expander
            if rest_slots:
                with st.expander(
                    f"Mais coletas ({len(rest_slots)})", expanded=False
                ):
                    render_chrono_headers(rest_slots)
                    _lab_sec._render_labs_table(
                        rest_slots, show_header=False, show_conduta=False
                    )
                    _lab_sec._render_gas_extras(rest_slots)

                    st.divider()
                    del_cols2 = st.columns(min(len(rest_slots), 6))
                    for col, slot in zip(del_cols2, rest_slots[:6]):
                        data = st.session_state.get(f"lab_{slot}_data", "")
                        with col:
                            if st.form_submit_button(
                                f"Apagar {data or f'#{slot}'}",
                                use_container_width=True,
                                key=f"_btn_del_rest_{slot}",
                            ):
                                st.session_state[f"_lab_clear_slot_{slot}"] = True
        else:
            st.info("Nenhuma coleta registrada. Cole um laudo acima e clique em **Parsear e Adicionar**.")

    # ── Handlers (fora do form) ────────────────────────────────────────────
    for _slot in range(1, MAX_SLOTS + 1):
        if st.session_state.pop(f"_lab_clear_slot_{_slot}", False):
            limpar_slot(_slot)
            st.toast(f"🗑️ Coleta apagada.", icon="🗑️")
            st.rerun()

    if btn_extrair:
        _extrair_com_ia(
            api_key, modelo, openai_api_key=openai_api_key, placeholder=_msg_topo
        )
        st.rerun()

    if btn_nova:
        from datetime import date as _date
        hoje = _date.today().strftime("%d/%m/%Y")
        from datetime import datetime as _dt
        hora_atual = _dt.now().strftime("%H:%M")
        hc = int(hora_atual.split(":")[0])
        coleta = {"data": hoje, "hora": hora_atual, "hora_cheia": hc}
        slot = adicionar_coleta(coleta)
        if slot:
            st.toast(f"Nova coleta criada: {hoje} {hc:02d}h", icon="➕")
        else:
            st.warning(f"Limite de {MAX_SLOTS} coletas atingido.")
        st.rerun()

    if btn_salvar:
        _msg_topo.info("💾 Salvando exames...")
        base = load_evolucao(prontuario) or {}
        base.pop("_data_hora", None)
        for k in list(st.session_state.keys()):
            if k.startswith("lab_"):
                base[k] = st.session_state[k]
        ok = save_evolucao(
            prontuario,
            st.session_state.get("nome", "").strip(),
            base,
        )
        if ok:
            _msg_topo.success(f"✅ Exames salvos! Prontuário: {prontuario}")
        else:
            _msg_topo.error("❌ Erro ao salvar. Verifique a conexão.")
