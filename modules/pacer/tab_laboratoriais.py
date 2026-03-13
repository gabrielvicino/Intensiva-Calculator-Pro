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
    # Cache do DB antes de modificar: evita load_evolucao redundante no save
    st.session_state["_lab_db_cache"] = {k: v for k, v in dados.items() if k != "_data_hora"}
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
# Auditoria de extração — GPT-4o-mini (Opção 2) + Determinística (Opção 3)
# ==============================================================================

_PROMPT_AUDITORIA_COMPLETA = """\
Você é um auditor de laudos laboratoriais brasileiros. Responda em EXATAMENTE 2 linhas.

CAMPOS JÁ EXTRAÍDOS PELO SISTEMA: {campos_extraidos}

CATEGORIAS COBERTAS (já processadas por outro sistema):
Hemograma: Hb, Ht, VCM, HCM, RDW, Leucócitos, diferencial, Plaquetas
Renal/Eletról: Creatinina, Ureia, Sódio, Potássio, Magnésio, Fósforo, CaT, CaI
Hepático: TGP, TGO, FAL, GGT, Bilirrubinas, Proteínas Totais, Albumina, Amilase, Lipase
Cardio/Coag: CPK, CK-MB, BNP, NT-proBNP, Troponina, PCR, VHS, TP, TTPa, Fibrinogênio, Lactato sérico
Urina: Urina Tipo I, EAS, Densidade, Leucócitos/Hemácias urinárias, Proteína, Glicose, Nitrito
Gasometria: pH, pCO2, pO2, HCO3, BE, SatO2, SvO2, Lactato da gasometria, Anion Gap
IGNORE: qualquer exame cujo título contenha "HEMODIÁLISE"

TAREFA 1 — FORA: exames no laudo que NÃO pertencem a nenhuma categoria coberta acima.
TAREFA 2 — COBERTOS: exames cobertos que têm valor numérico EXPLÍCITO no laudo mas NÃO estão em CAMPOS JÁ EXTRAÍDOS. Máximo 5. Só inclua se certeza absoluta (nome + número visíveis no laudo).

FORMATO OBRIGATÓRIO — exatamente 2 linhas, sem mais nada:
FORA: [nomes pt-BR separados por vírgula, ou VAZIO]
COBERTOS: [nomes separados por vírgula, ou VAZIO]

LAUDO:
{texto_input}"""

# Mapeamento de campo do coleta dict → nome legível para o resumo do prompt
_CAMPO_NOME_RESUMO: dict[str, str] = {
    "hb": "Hb", "ht": "Ht", "vcm": "VCM", "hcm": "HCM", "rdw": "RDW",
    "leuco": "Leuco", "plaq": "Plaq", "cr": "Cr", "ur": "Ur",
    "na": "Na", "k": "K", "mg": "Mg", "pi": "Pi", "cat": "CaT", "cai": "CaI",
    "tgp": "TGP", "tgo": "TGO", "fal": "FAL", "ggt": "GGT",
    "bt": "BT", "bd": "BD", "alb": "Albumina", "amil": "Amilase", "lipas": "Lipase",
    "cpk": "CPK", "bnp": "BNP", "trop": "Troponina", "pcr": "PCR",
    "vhs": "VHS", "tp": "TP", "ttpa": "TTPa",
    "gas_ph": "Gasometria", "ur_dens": "EAS",
}


def _resumo_campos_extraidos(coletas: list[dict]) -> str:
    """Converte lista de coletas para string de campos extraídos (usada no prompt GPT)."""
    extraidos: set[str] = set()
    for coleta in coletas:
        for k, v in coleta.items():
            if v and str(v).strip() and k in _CAMPO_NOME_RESUMO:
                extraidos.add(_CAMPO_NOME_RESUMO[k])
    return ", ".join(sorted(extraidos)) if extraidos else "nenhum"


def _auditar_laudo_gpt(
    texto: str, coletas: list[dict], openai_api_key: str
) -> tuple[str, list[str]]:
    """
    Auditoria GPT-4o-mini: detecta exames não transcritos E cobertos possivelmente ausentes.
    Retorna (nao_transcritos_str, cobertos_suspeitos_list).
    """
    if not openai_api_key or not texto:
        return "", []
    try:
        from openai import OpenAI as _OpenAI
        campos_resumo = _resumo_campos_extraidos(coletas)
        prompt = (
            _PROMPT_AUDITORIA_COMPLETA
            .replace("{campos_extraidos}", campos_resumo)
            .replace("{texto_input}", texto[:6000])
        )
        client = _OpenAI(api_key=openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300,
            seed=42,
        )
        resposta = (resp.choices[0].message.content or "").strip()
        nao_trans = ""
        cobertos: list[str] = []
        for linha in resposta.splitlines():
            if linha.startswith("FORA:"):
                val = linha[5:].strip()
                if val and val.upper() != "VAZIO":
                    nao_trans = val
            elif linha.startswith("COBERTOS:"):
                val = linha[9:].strip()
                if val and val.upper() != "VAZIO":
                    cobertos = [v.strip() for v in val.split(",") if v.strip()]
        return nao_trans, cobertos
    except Exception as e:
        print(f"[AUDITORIA GPT] Erro: {e}")
        return "", []


# Mapeamento determinístico: (termos_no_texto, campos_coleta, nome_display)
# Termos específicos para minimizar falsos positivos
_AUDIT_TERMS: list[tuple[list[str], list[str], str]] = [
    (["hemoglobina:"], ["hb"], "Hb"),
    (["creatinina:"], ["cr"], "Cr"),
    (["leucocitometria", "contagem de leucócitos", "leucócitos:"], ["leuco"], "Leuco"),
    (["contagem de plaquetas", "plaquetas:"], ["plaq"], "Plaq"),
    (["troponina:"], ["trop"], "Trop"),
    (["gasometria arterial", "gasometria venosa"], ["gas_ph"], "Gasometria"),
    (["urina tipo i", "elementos anormais e sedimento"], ["ur_dens"], "EAS"),
    (["alanina aminotransferase:"], ["tgp"], "TGP"),
    (["aspartato aminotransferase:"], ["tgo"], "TGO"),
    (["proteína c reativa:"], ["pcr"], "PCR"),
    (["bilirrubinas totais:"], ["bt"], "BT"),
    (["albumina:"], ["alb"], "Albumina"),
]


def _auditar_deterministico(texto: str, coletas: list[dict]) -> list[str]:
    """
    Verifica se termos-chave do laudo aparecem no texto mas não foram extraídos.
    Retorna lista de nomes de exames possivelmente omitidos (alerta discreto).
    """
    if not texto or not coletas:
        return []
    texto_lower = texto.lower()
    campos_extraidos: dict[str, str] = {}
    for coleta in coletas:
        for k, v in coleta.items():
            if v and str(v).strip():
                campos_extraidos[k] = str(v)
    suspeitos = []
    for termos, campos, nome in _AUDIT_TERMS:
        if not any(t in texto_lower for t in termos):
            continue
        if any(campos_extraidos.get(c, "").strip() for c in campos):
            continue
        suspeitos.append(nome)
    return suspeitos


# ==============================================================================
# Fragment assíncrono — auditoria GPT (não bloqueia a tabela principal)
# ==============================================================================

@st.fragment
def _fragment_auditoria_gpt(openai_api_key: str) -> None:
    """Executa auditoria GPT-4o-mini de forma independente da tabela principal.

    Fase A (1º render do fragment): mostra indicador visual e dispara re-run do fragment.
    Fase B (2º render do fragment): executa GPT, atualiza session_state, re-roda a app.
    O resultado: tabela aparece imediatamente após o parser; auditoria atualiza
    apenas a área do fragment, sem bloquear o render principal.
    """
    if "_lab_auditoria_pendente" not in st.session_state:
        return

    if not st.session_state.get("_lab_auditoria_fase2"):
        st.session_state["_lab_auditoria_fase2"] = True
        st.caption("🤖 Auditando laudos (GPT-4o-mini)...")
        st.rerun(scope="fragment")
        return

    # Fase B — executa GPT audit
    pending = st.session_state["_lab_auditoria_pendente"]
    logs_gpt: list[str] = []

    with st.spinner("🤖 Auditando laudos (GPT-4o-mini)..."):
        with ThreadPoolExecutor(max_workers=max(len(pending), 1)) as ex:
            futs = {
                ex.submit(_auditar_laudo_gpt, txt, colts, openai_api_key): (slot, idx)
                for idx, txt, slot, colts in pending
            }
            for f in as_completed(futs):
                slot, idx_text = futs[f]
                try:
                    nao_trans, cobertos = f.result()
                    if nao_trans:
                        st.session_state[f"lab_{slot}_outros"] = nao_trans
                    if cobertos:
                        logs_gpt.append(
                            f"🔍 Laudo {idx_text + 1}: GPT — verificar: {', '.join(cobertos)}"
                        )
                except Exception:
                    pass

    st.session_state.pop("_lab_auditoria_pendente", None)
    st.session_state.pop("_lab_auditoria_fase2", None)

    if logs_gpt:
        existing = st.session_state.get("_lab_avisos", [])
        st.session_state["_lab_avisos"] = existing + [f"ℹ️ {lg}" for lg in logs_gpt]

    st.rerun(scope="app")


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
    # Rastreia todos os textos com coletas extraídas (regex e IA)
    todos_textos_para_gpt: list[tuple[int, str, int, list[dict]]] = []

    for idx, texto in textos:
        coletas, caminho = resultados_paralelos.get(idx, ([], "?"))
        icone = "⚡" if caminho == "regex" else "🤖"
        if coletas:
            n_coletas = 0
            primeiro_slot = None
            coletas_adicionadas: list[dict] = []
            for coleta in coletas:
                slot = adicionar_coleta(coleta)
                if slot is not None:
                    if primeiro_slot is None:
                        primeiro_slot = slot
                    coletas_adicionadas.append(coleta)
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
            # Opção 3 — auditoria determinística (sem custo de API)
            suspeitos = _auditar_deterministico(texto, coletas_adicionadas)
            if suspeitos:
                logs.append(f"🔍 Laudo {idx + 1}: verificar — {', '.join(suspeitos)}")
            if primeiro_slot is not None:
                todos_textos_para_gpt.append((idx, texto, primeiro_slot, coletas_adicionadas))
        else:
            erros.append(f"Laudo {idx + 1}: nenhum campo extraído.")

    # Fase 2 — Auditoria GPT desacoplada: armazena dados para _fragment_auditoria_gpt
    if todos_textos_para_gpt and openai_api_key:
        st.session_state["_lab_auditoria_pendente"] = todos_textos_para_gpt

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
                elif aviso.startswith("🔍"):
                    st.caption(aviso)
                else:
                    st.info(aviso)

    # ── Prontuário ─────────────────────────────────────────────────────────
    _fragment_prontuario()
    _confirmar_novo_prontuario()

    # ── Auditoria GPT assíncrona (roda independentemente da tabela) ─────────
    _fragment_auditoria_gpt(openai_api_key=openai_api_key)

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
        # Usa cache do último load (evita round-trip ao Google Sheets).
        # Fallback para load_evolucao apenas se o cache não existir
        # (ex.: sessão nova sem auto-load).
        base = st.session_state.get("_lab_db_cache")
        if base is None:
            base = load_evolucao(prontuario) or {}
            base.pop("_data_hora", None)
        else:
            base = dict(base)  # cópia para não mutar o cache
        for k in list(st.session_state.keys()):
            if k.startswith("lab_"):
                base[k] = st.session_state[k]
        ok = save_evolucao(
            prontuario,
            st.session_state.get("nome", "").strip(),
            base,
        )
        if ok:
            # Atualiza cache com os dados recém-salvos
            st.session_state["_lab_db_cache"] = {k: v for k, v in base.items()}
            _msg_topo.success(f"✅ Exames salvos! Prontuário: {prontuario}")
        else:
            _msg_topo.error("❌ Erro ao salvar. Verifique a conexão.")
