"""Evolução por Sistemas — página rápida para gerar apenas o bloco de sistemas."""
import streamlit as st
import json
import streamlit.components.v1 as components
from modules import ui
from modules.secoes import sistemas
from modules.gerador.sistemas import _secao_sistemas
from utils import mostrar_rodape

ui.carregar_css()

# Inicializa campos do bloco 14 com presets
for k, v in sistemas.get_campos().items():
    if k not in st.session_state:
        st.session_state[k] = v
    elif v and v is not True and v is not False and st.session_state.get(k) in ("", None):
        st.session_state[k] = v

st.title("📝 Evolução por Sistemas")
st.write("")

# ── Formulário ────────────────────────────────────────────────────────────────
with st.form("form_sistemas_rapido"):
    sistemas.render(show_toolbar=False)

    st.markdown("---")
    col_gerar, col_limpar, _ = st.columns([2, 1, 5])
    with col_gerar:
        gerar_btn = st.form_submit_button(
            "📄 Gerar Prontuário",
            type="primary",
            use_container_width=True,
        )
    with col_limpar:
        limpar_btn = st.form_submit_button(
            "🗑️ Limpar",
            use_container_width=True,
        )

# ── Handlers ──────────────────────────────────────────────────────────────────
if gerar_btn:
    linhas = _secao_sistemas()
    texto = "\n".join(linhas) if linhas else ""
    if "texto_sistemas_gerado" in st.session_state:
        del st.session_state["texto_sistemas_gerado"]
    st.session_state["texto_sistemas_gerado"] = texto
    if not texto:
        st.warning("Nenhum campo preenchido — preencha pelo menos uma seção.")
    st.rerun()

if limpar_btn:
    for k, v in sistemas.get_campos().items():
        if k in st.session_state:
            del st.session_state[k]
        st.session_state[k] = v
    if "texto_sistemas_gerado" in st.session_state:
        del st.session_state["texto_sistemas_gerado"]
    st.rerun()

# ── Saída ─────────────────────────────────────────────────────────────────────
ui.render_header_secao("Resultado", "✅", ui.COLOR_GREEN)

with st.container(border=True):
    st.text_area(
        "Resultado", height=250,
        label_visibility="collapsed",
        placeholder="Preencha os campos acima e clique em Gerar Prontuário.",
        key="texto_sistemas_gerado",
    )

_c_esp, _c_btn = st.columns([4, 1])
with _c_btn:
    if st.button("📋 Copiar", use_container_width=True):
        texto = st.session_state.get("texto_sistemas_gerado", "")
        if texto:
            components.html(
                f"""<script>
                const text = {json.dumps(texto)};
                navigator.clipboard.writeText(text).then(() => {{}});
                </script>""",
                height=0,
            )
            st.toast("✅ Copiado!", icon="📋")
        else:
            st.warning("Gere o prontuário primeiro.")

mostrar_rodape()
