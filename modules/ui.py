import streamlit as st

# --- CONSTANTES DE CORES ---
COLOR_BLUE = "#1a73e8"
COLOR_GREEN = "#0F9D58"
COLOR_NEUTRAL = "#666666"
COLOR_YELLOW = "#f59e0b" 

# --- 1. FUNÇÕES DE ESTILO E CSS ---
def carregar_css():
    """Carrega o CSS global da aplicação."""
    st.markdown(f"""
    <style>
        .stApp {{ background-color: #ffffff; }}
        h1, h2, h3 {{ font-family: 'Roboto', sans-serif; }}
        .block-container {{ padding-top: 2rem; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. COMPONENTES DE INTERFACE ---

def render_header_secao(titulo, icone, cor):
    """Renderiza o cabeçalho colorido de cada seção."""
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 15px; margin-top: 20px; border-bottom: 2px solid {cor}; padding-bottom: 8px;">
        <span style="font-size: 1.6rem; margin-right: 12px;">{icone}</span>
        <h3 style="margin: 0; color: {cor}; font-size: 1.3rem; font-weight: 700;">{titulo}</h3>
    </div>
    """, unsafe_allow_html=True)

def card_paciente(nome, leito, idade):
    pass 

# --- 3. NOVA FUNÇÃO: CABEÇALHO DETALHADO ---
def render_barra_paciente():
    """
    Renderiza uma barra fixa com os dados principais do paciente.
    """
    nome = st.session_state.get('nome')
    idade = st.session_state.get('idade') or "-"
    prontuario = st.session_state.get('prontuario') or "-"
    leito = st.session_state.get('leito') or "-"
    origem = st.session_state.get('origem') or "-"
    dias_hosp = st.session_state.get('di_hosp') or "-" 
    dias_uti = st.session_state.get('di_uti') or "-"

    if not nome:
        return

    # Mudei a cor dos headers (Prontuário, Leito, etc) para #1a73e8 (Azul Forte) 
    # e aumentei a fonte para 0.85rem com peso 800 para destacar bem.
    st.markdown(f"""
    <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.04);">
        <div style="color: #2c3e50; font-size: 1.6rem; font-weight: 700; font-family: 'Roboto', sans-serif; margin-bottom: 20px; letter-spacing: -0.5px;">
            {nome}, {idade} anos
        </div>
        <div style="height: 1px; background-color: #dee2e6; margin-bottom: 20px;"></div>
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 20px;">
            <div style="flex: 1; min-width: 100px;">
                <div style="font-size: 0.85rem; color: #1a73e8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Prontuário</div>
                <div style="font-size: 1.15rem; color: #343a40; font-weight: 600;">{prontuario}</div>
            </div>
            <div style="flex: 1; min-width: 100px;">
                <div style="font-size: 0.85rem; color: #1a73e8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Leito</div>
                <div style="font-size: 1.15rem; color: #343a40; font-weight: 600;">{leito}</div>
            </div>
            <div style="flex: 1; min-width: 100px;">
                <div style="font-size: 0.85rem; color: #1a73e8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Origem</div>
                <div style="font-size: 1.15rem; color: #343a40; font-weight: 600;">{origem}</div>
            </div>
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.85rem; color: #1a73e8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Internação</div>
                <div style="font-size: 1.15rem; color: #343a40; font-weight: 600;"> {dias_hosp}</div>
            </div>
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.85rem; color: #1a73e8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Tempo UTI</div>
                <div style="font-size: 1.15rem; color: #343a40; font-weight: 600;"> {dias_uti}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)