import streamlit as st
import pandas as pd
from utils import load_data, mostrar_rodape

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E ESTILO
# ==============================================================================
COLOR_PRIMARY = "#0F9D58"
COLOR_BG = "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
    
    /* Aumentar um pouco a fonte da tabela para ficar mais legível */
    .stDataFrame {{ font-size: 1.1rem; }}
    
    /* Remover padding excessivo do topo */
    .block-container {{ padding-top: 2rem; }}
    </style>
""", unsafe_allow_html=True)

# Função auxiliar de formatação
def format_br(valor, casas=1):
    if valor is None: return ""
    if isinstance(valor, (int, float)):
        fmt = f"{{:,.{casas}f}}"
        return fmt.format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)

# ==============================================================================
# 2. LÓGICA DA PÁGINA
# ==============================================================================
st.header("⚡ Intubação Orotraqueal")

# --- CARREGAMENTO DO GOOGLE SHEETS ---
df_iot = load_data('DB_IOT')

if df_iot.empty:
    st.error("Erro: Banco de dados não encontrado. Verifique a conexão com o Google Sheets e a aba DB_IOT.")
    st.stop()

# --- INPUT DE DADOS ---
col_p, col_idade, col_sexo = st.columns([1, 1, 1])
with col_p:
    peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.5, format="%.1f")
with col_idade:
    idade = st.number_input("Idade (anos)", min_value=0, max_value=120, value=50, step=1)
with col_sexo:
    sexo = st.radio("Sexo", ["Masculino", "Feminino"], horizontal=True)

# --- CÁLCULO DO TUBO SUGERIDO ---
def calcular_tubo_sugerido(sexo, idade, peso):
    """
    Calcula o tamanho do tubo orotraqueal (DI em mm) baseado em sexo, idade e peso.
    
    Lógica:
    - Adultos (idade >= 14): baseado em sexo
    - Pediatria (idade < 14): baseado em idade e peso
    """
    # ADULTOS (crescimento ósseo finalizado)
    if idade >= 14:
        if sexo == "Feminino":
            # Mulheres: 7.0-7.5mm (6.5mm se muito pequena)
            if peso < 45:
                return "6.5 mm", f"Mulher, {idade} anos"
            else:
                return "7.0 - 7.5 mm", f"Mulher, {idade} anos"
        else:
            # Homens: 7.5-8.5mm (8.0mm padrão)
            return "7.5 - 8.0 mm", f"Homem, {idade} anos"
    
    # PEDIATRIA
    else:
        # NEONATOS E LACTENTES (< 1 ano ou < 10kg)
        if idade < 1 or peso < 10:
            anos_texto = "ano" if idade == 1 else "anos"
            if peso < 1:
                return "2.5 mm (sem cuff)", f"Criança, {idade} {anos_texto}"
            elif peso < 2:
                return "3.0 mm (sem cuff)", f"Criança, {idade} {anos_texto}"
            elif idade < 0.5:  # < 6 meses
                return "3.0 - 3.5 mm", f"Criança, {idade} {anos_texto}"
            else:
                return "3.5 - 4.0 mm", f"Criança, {idade} {anos_texto}"
        
        # CRIANÇAS (>= 1 ano)
        else:
            # Fórmula de Cole
            tubo_sem_cuff = round((idade / 4) + 4, 1)
            tubo_com_cuff = round((idade / 4) + 3.5, 1)
            anos_texto = "ano" if idade == 1 else "anos"
            return f"{tubo_com_cuff} mm (c/ cuff) ou {tubo_sem_cuff} mm (s/ cuff)", f"Criança, {idade} {anos_texto}"

tubo_sugerido, categoria = calcular_tubo_sugerido(sexo, idade, peso)

# --- EXIBIÇÃO DO TUBO SUGERIDO (COMPACTA) ---
st.markdown(
    f"<p style='margin-top: 1rem; margin-bottom: 0.2rem; font-size: 0.95rem;'>"
    f"<strong>Tubo sugerido: {tubo_sugerido} ({categoria})</strong> - Variação padrão do tubo: ±0.5 mm"
    f"</p>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='font-size: 0.8rem; color: #808495; margin-bottom: 0.5rem;'>"
    "A avaliação individual é imprescindível e deve contemplar a estratificação dos preditores de via aérea difícil e a análise das variáveis clínicas e anatômicas específicas de cada paciente."
    "</p>",
    unsafe_allow_html=True
)
st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 0.5rem;'>", unsafe_allow_html=True)

# --- PROCESSAMENTO DA TABELA ---
dados_tabela = []

# Identifica coluna de nome
col_nome = None
possiveis_nomes = ['nome_formatado', 'medicacao', 'apresentacao', 'droga']
for c in possiveis_nomes:
    if c in df_iot.columns:
        col_nome = c
        break

if col_nome:
    for index, row in df_iot.iterrows():
        try:
            nome = row[col_nome]
            
            # Garante float
            conc = float(row.get('conc', 0))
            dose_min = float(row.get('dose_min', 0))
            # Tratamento para coluna habitual/média
            dose_hab = float(row.get('dose_hab', 0)) if 'dose_hab' in row else float(row.get('dose_media', 0))
            dose_max = float(row.get('dose_max', 0))
            
            if conc > 0:
                # Cálculo (Dose * Peso) / Conc
                vol_min = (dose_min * peso) / conc
                vol_hab = (dose_hab * peso) / conc
                vol_max = (dose_max * peso) / conc
                
                # Monta dicionário
                dados_tabela.append({
                    "Medicação": nome,
                    "Vol. Mínimo": f"{format_br(vol_min)} ml",
                    "Vol. Habitual": f"{format_br(vol_hab)} ml",
                    "Vol. Máximo": f"{format_br(vol_max)} ml"
                })
        except Exception:
            continue

    # --- EXIBIÇÃO ---
    if dados_tabela:
        df_display = pd.DataFrame(dados_tabela)
        
        # --- ESTILIZAÇÃO DA TABELA (Pandas Styler) ---
        def highlight_cols(x):
            df_styler = x.copy()
            df_styler.loc[:, :] = '' 
            return df_styler

        # Criação do Styler object
        styler = df_display.style\
            .map(lambda v: 'color: #1565C0; font-weight: bold;', subset=['Vol. Mínimo'])\
            .map(lambda v: 'color: #2E7D32; font-weight: bold;', subset=['Vol. Habitual'])\
            .map(lambda v: 'color: #C62828; font-weight: bold;', subset=['Vol. Máximo'])\
            .map(lambda v: 'font-weight: 600; color: #333;', subset=['Medicação'])

        st.dataframe(
            styler, 
            use_container_width=True, 
            hide_index=True,
            height=(len(df_display) + 1) * 35 + 3
        )
    else:
        st.warning("Não foi possível calcular as doses.")

else:
    st.error("Erro de Estrutura: Coluna de nome da medicação não encontrada.")

# Rodapé com nota legal
mostrar_rodape()