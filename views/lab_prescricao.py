"""Laboratoriais & Prescrição — extração rápida de exames e prescrição via IA."""
import streamlit as st
import json
import streamlit.components.v1 as components
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules import ui
from modules.extrator_exames import extrair_exames, extrair_prescricao
from utils import mostrar_rodape, carregar_chave_api, verificar_rate_limit

# ── Setup ─────────────────────────────────────────────────────────────────────
ui.carregar_css()
GOOGLE_API_KEY = carregar_chave_api("GOOGLE_API_KEY", "GOOGLE_API_KEY")

_PROVIDER = "google"
_MODELO = "gemini-2.5-pro"

st.title("🔬 Laboratoriais & Prescrição")
st.caption("Cole os textos brutos e clique em **Extrair** — a IA formata tudo automaticamente.")

# ── 1. Entrada ────────────────────────────────────────────────────────────────
ui.render_header_secao("Dados de Entrada", "📄", ui.COLOR_BLUE)

col_in_lab, col_in_presc = st.columns(2, gap="medium")

with col_in_lab:
    with st.container(border=True):
        st.markdown("**🧪 Exames Laboratoriais**")
        texto_lab = st.text_area(
            "Exames",
            height=220,
            label_visibility="collapsed",
            placeholder="Cole aqui o texto bruto dos exames laboratoriais (PDF / laudo)...",
            key="lp_input_lab",
        )

with col_in_presc:
    with st.container(border=True):
        st.markdown("**💊 Prescrição Médica**")
        texto_presc = st.text_area(
            "Prescrição",
            height=220,
            label_visibility="collapsed",
            placeholder="Cole aqui o texto bruto da prescrição médica...",
            key="lp_input_presc",
        )

# ── Botões de ação ────────────────────────────────────────────────────────────
col_extrair, col_limpar, _ = st.columns([2, 1, 5])

with col_extrair:
    extrair_btn = st.button(
        "⚡ Extrair", type="primary", use_container_width=True,
    )
with col_limpar:
    limpar_btn = st.button(
        "🗑️ Limpar Tudo", use_container_width=True,
    )

# ── Handler: Limpar ──────────────────────────────────────────────────────────
if limpar_btn:
    for k in ["lp_input_lab", "lp_input_presc", "lp_output_lab", "lp_output_presc"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# ── Handler: Extrair ─────────────────────────────────────────────────────────
if extrair_btn:
    has_lab = bool(texto_lab and texto_lab.strip())
    has_presc = bool(texto_presc and texto_presc.strip())

    if not has_lab and not has_presc:
        st.warning("Cole pelo menos um texto (exames ou prescrição) para extrair.")
    elif not GOOGLE_API_KEY:
        st.error("🔑 Chave Google API não configurada. Verifique `.env` ou `secrets.toml`.")
    else:
        ok, msg = verificar_rate_limit()
        if not ok:
            st.error(f"🚫 {msg}")
        else:
            with st.status("⚡ Extraindo com IA...", expanded=True) as status:
                tarefas: dict[str, any] = {}
                resultados: dict[str, str] = {}

                def _run_lab():
                    return extrair_exames(
                        texto_lab, GOOGLE_API_KEY, _PROVIDER, _MODELO,
                    )

                def _run_presc():
                    return extrair_prescricao(
                        texto_presc, GOOGLE_API_KEY, _PROVIDER, _MODELO,
                    )

                with ThreadPoolExecutor(max_workers=2) as executor:
                    if has_lab:
                        st.write("🧪 Processando exames laboratoriais (7 agentes)...")
                        tarefas["lab"] = executor.submit(_run_lab)
                    if has_presc:
                        st.write("💊 Processando prescrição (3 agentes)...")
                        tarefas["presc"] = executor.submit(_run_presc)

                    for future in as_completed(tarefas.values()):
                        key = next(k for k, f in tarefas.items() if f is future)
                        try:
                            resultados[key] = future.result(timeout=120)
                        except Exception as e:
                            resultados[key] = f"❌ Erro: {e}"

                if "lab" in resultados:
                    if "lp_output_lab" in st.session_state:
                        del st.session_state["lp_output_lab"]
                    st.session_state["lp_output_lab"] = resultados["lab"]

                if "presc" in resultados:
                    if "lp_output_presc" in st.session_state:
                        del st.session_state["lp_output_presc"]
                    st.session_state["lp_output_presc"] = resultados["presc"]

                n = len(resultados)
                lbl = "extração concluída" if n == 1 else "extrações concluídas"
                status.update(label=f"✅ {n} {lbl}", state="complete", expanded=False)

            st.rerun()

# ── 2. Saída ──────────────────────────────────────────────────────────────────
ui.render_header_secao("Resultado", "✅", ui.COLOR_GREEN)

col_out_lab, col_out_presc = st.columns(2, gap="medium")


def _copiar(texto: str, rotulo: str):
    """Copia texto para a área de transferência via JS."""
    if texto:
        components.html(
            f"<script>navigator.clipboard.writeText({json.dumps(texto)}).then(()=>{{}});</script>",
            height=0,
        )
        st.toast(f"✅ {rotulo} copiado!", icon="📋")
    else:
        st.warning(f"Nenhum resultado de {rotulo.lower()} para copiar.")


with col_out_lab:
    with st.container(border=True):
        st.markdown("**🧪 Exames Laboratoriais**")
        st.text_area(
            "Saída Lab",
            height=300,
            label_visibility="collapsed",
            placeholder="Os exames formatados aparecerão aqui após clicar em Extrair...",
            key="lp_output_lab",
        )
    if st.button("📋 Copiar Exames", use_container_width=True, key="btn_cp_lab"):
        _copiar(st.session_state.get("lp_output_lab", ""), "Exames")

with col_out_presc:
    with st.container(border=True):
        st.markdown("**💊 Prescrição Médica**")
        st.text_area(
            "Saída Prescrição",
            height=300,
            label_visibility="collapsed",
            placeholder="A prescrição formatada aparecerá aqui após clicar em Extrair...",
            key="lp_output_presc",
        )
    if st.button("📋 Copiar Prescrição", use_container_width=True, key="btn_cp_presc"):
        _copiar(st.session_state.get("lp_output_presc", ""), "Prescrição")

# ── Rodapé ────────────────────────────────────────────────────────────────────
mostrar_rodape()
