"""
Módulo de componentes de UI reutilizáveis para o Intensiva Calculator.
"""
import streamlit as st
import streamlit.components.v1 as components

# Cores padrão para cabeçalhos de seção
COLOR_BLUE = "#2563eb"
COLOR_GREEN = "#16a34a"


def carregar_css():
    """Carrega estilos CSS globais da aplicação."""
    st.markdown("""
    <style>
        /* Estilos gerais para a aplicação */
        [data-testid="stExpander"] { 
            border: none !important; 
            box-shadow: none !important; 
            background: transparent !important;
        }
        [data-testid="stExpander"] details {
            border-radius: 4px !important;
            border: 1px solid #f0f0f0 !important;
            background-color: #fafafa;
            margin-bottom: 8px !important; 
        }
        [data-testid="stExpander"] details summary {
            background-color: transparent !important;
            padding: 0.6rem 0.8rem !important;
        }
        div[data-testid="stTextInput"]:has(input[placeholder="Escreva a conduta aqui..."]) {
            border-left: 3px solid #43a047;
            padding-left: 8px;
        }
        /* Remove spinners do number_input para Tab ir ao próximo campo */
        input[type="number"]::-webkit-inner-spin-button,
        input[type="number"]::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type="number"] {
            -moz-appearance: textfield;
        }
    </style>
    """, unsafe_allow_html=True)
    # Script: remove botões (x) e (+/-) do tab order para Tab ir ao próximo campo
    components.html("""
    <script>
    (function() {
        try {
            const doc = window.parent.document;
            const run = () => {
                doc.querySelectorAll('[data-testid="stNumberInput"] button').forEach(b => b.setAttribute('tabindex', '-1'));
                doc.querySelectorAll('[data-testid="stTextInput"] button').forEach(b => b.setAttribute('tabindex', '-1'));
            };
            if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', run);
            else run();
            setTimeout(run, 500);
        } catch(e) {}
    })();
    </script>
    """, height=0)


def render_barra_paciente():
    """Renderiza a barra com dados do paciente (nome, prontuário, leito)."""
    nome = st.session_state.get("nome", "") or ""
    pront = st.session_state.get("prontuario", "") or ""
    leito = st.session_state.get("leito", "") or ""
    origem = st.session_state.get("origem", "") or ""

    if nome or pront or leito:
        partes = []
        if nome:
            partes.append(f"**{nome}**")
        if pront:
            partes.append(f"Pront. {pront}")
        if leito:
            partes.append(f"Leito {leito}")
        if origem:
            partes.append(f"Origem: {origem}")

        st.markdown(" | ".join(partes))
        st.markdown("---")


def render_header_secao(titulo: str, emoji: str, cor: str):
    """Renderiza o cabeçalho de uma seção com emoji e cor."""
    st.markdown(
        f'<h5 style="background: linear-gradient(90deg, {cor}15 0%, #ffffff 100%); '
        f'padding: 0.6rem 1rem; border-left: 4px solid {cor}; '
        f'border-radius: 4px; margin-bottom: 1rem;">{emoji} {titulo}</h5>',
        unsafe_allow_html=True,
    )


# Mapa seção → (âncora, título completo) para o guia de navegação
_GUIA_SECOES = [
    (1, "Identificação & Scores"),
    (2, "Diagnósticos Atuais & Prévios"),
    (3, "Comorbidades"),
    (4, "Medicações de Uso Contínuo"),
    (5, "História da Moléstia Pregressa Atual"),
    (6, "Dispositivos Invasivos"),
    (7, "Culturas"),
    (8, "Antibióticos"),
    (9, "Exames Complementares"),
    (10, "Exames Laboratoriais"),
    (11, "Controles & Balanço Hídrico"),
    (12, "Evolução Clínica"),
    (13, "Evolução por Sistemas"),
    (14, "Prescrição"),
    (15, "Plano Terapêutico & Condutas"),
]


def render_guia_navegacao():
    """
    Renderiza o guia de navegação com links para as seções 1–15.
    Ao clicar, a página rola até a seção correspondente.
    Estilo alinhado ao bloco "2. Dados Clínicos" (âmbar #f59e0b).
    """
    cor = "#f59e0b"
    links = "".join(
        f'<a href="#sec-{n}" class="guia-link" title="{label}" '
        f'onclick="document.getElementById(\'sec-{n}\').scrollIntoView({{behavior:\'smooth\'}}); return false;">{n}. {label}</a>'
        for n, label in _GUIA_SECOES
    )
    st.markdown(
        f"""
        <div class="guia-navegacao" style="
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-left: 4px solid {cor};
            border-radius: 4px;
            padding: 0.5rem 1rem;
            margin-bottom: 1rem;
        ">
            <span style="font-size: 1.05rem; font-weight: bold; color: #444; margin-right: 0.6rem;">Buscar sessão:</span>
            <span class="guia-links">{links}</span>
        </div>
        <style>
            .guia-navegacao .guia-links {{ display: flex; flex-wrap: wrap; gap: 0.25rem; align-items: center; }}
            .guia-navegacao .guia-link {{
                display: inline-flex; align-items: center; justify-content: center;
                padding: 0.25rem 0.5rem; min-height: 1.6rem;
                background: #f8f9fa; color: #444;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 0.8rem; font-weight: 500;
                text-decoration: none;
                transition: all 0.15s ease;
            }}
            .guia-navegacao .guia-link:hover {{
                background: #f0f0f0; color: #2c3e50;
                border-color: #d0d0d0;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
