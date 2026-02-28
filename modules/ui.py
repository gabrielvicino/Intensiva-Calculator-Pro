"""
Módulo de componentes de UI reutilizáveis para o Intensiva Calculator.
"""
from datetime import datetime
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


def _dias_internados_valor(di_hosp: str) -> str:
    """Retorna 'X dias' a partir de di_hosp (data DD/MM/AAAA ou já 'X dias')."""
    if not di_hosp or not isinstance(di_hosp, str):
        return ""
    s = di_hosp.strip()
    if "dias" in s.lower():
        return s  # já está no formato "12 dias"
    try:
        d1 = datetime.strptime(s, "%d/%m/%Y")
        d2 = datetime.now()
        dias = (d2 - d1).days
        if dias >= 0:
            return f"{dias} dias"
    except ValueError:
        pass
    return ""


def render_barra_paciente():
    """Renderiza o card com dados do paciente (nome, prontuário, leito, dias internados)."""
    nome = st.session_state.get("nome", "") or ""
    pront = st.session_state.get("prontuario", "") or ""
    leito = st.session_state.get("leito", "") or ""
    di_hosp = st.session_state.get("di_hosp", "") or ""
    dias_val = _dias_internados_valor(di_hosp)

    if nome or pront or leito or dias_val:
        itens = []
        if nome:
            itens.append(('Paciente', nome, '👤'))
        if pront:
            itens.append(('Prontuário', pront, '📋'))
        if leito:
            leito_val = leito.replace("Leito ", "", 1) if leito.lower().startswith("leito ") else leito
            itens.append(('Leito', leito_val, '🛏️'))
        if dias_val:
            itens.append(('Dias internados', dias_val, '📅'))

        badges = "".join(
            f'<span class="paciente-badge"><span class="paciente-icone">{icon}</span>'
            f'<span class="paciente-label">{label}:</span> <span class="paciente-valor">{valor}</span></span>'
            for label, valor, icon in itens
        )
        st.markdown(
            f"""
            <div class="paciente-card">
                {badges}
            </div>
            <style>
                .paciente-card {{
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 0.75rem 1.25rem;
                    margin-bottom: 1rem;
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: 1rem 1.5rem;
                }}
                .paciente-badge {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.35rem;
                    font-size: 0.95rem;
                    color: #334155;
                }}
                .paciente-icone {{
                    font-size: 1rem;
                    opacity: 0.9;
                }}
                .paciente-label {{
                    color: #64748b;
                    font-weight: 500;
                }}
                .paciente-valor {{
                    color: #1e293b;
                    font-weight: 600;
                }}
                .paciente-badge:first-child .paciente-valor {{
                    font-size: 1.05rem;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )


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
