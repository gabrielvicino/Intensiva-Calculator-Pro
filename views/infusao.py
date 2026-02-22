import streamlit as st
import pandas as pd
from utils import load_data, mostrar_rodape

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL
# ==============================================================================
COLOR_PRIMARY = "#0F9D58"
COLOR_ACCENT = "#1a73e8"
COLOR_BG = "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_PRIMARY}; font-family: 'Roboto', sans-serif; }}
    
    /* ESTILO DOS CARTÕES */
    .result-box {{
        background-color: white; 
        padding: 15px; 
        border-radius: 8px;
        border: 1px solid #ddd; 
        border-left: 5px solid {COLOR_ACCENT}; 
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .result-title {{ font-size: 0.85em; color: #666; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; }}
    .result-value {{ font-size: 1.3em; color: #333; font-weight: bold; }}
    
    .stForm {{ background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #eee; }}
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
# 2. CARREGAMENTO DE DADOS
# ==============================================================================
st.header("💉 Calculadora de Infusão")

df_inf = load_data('DB_INFUSAO')

if df_inf.empty:
    st.error("Erro: Banco de dados não encontrado. Verifique a conexão com o Google Sheets e a aba DB_INFUSAO.")
    st.stop()

# ==============================================================================
# 3. INTERFACE DE ENTRADA
# ==============================================================================
col_input_1, col_input_2 = st.columns([1, 2.5])

with col_input_1:
    peso = st.number_input("Peso do Paciente (kg)", value=70.0, step=0.1, format="%.1f")

with col_input_2:
    col_nome = 'nome_formatado' if 'nome_formatado' in df_inf.columns else 'apresentacao'
    
    if col_nome in df_inf.columns:
        lista_drogas = sorted(df_inf[col_nome].unique())
        
        # --- LÓGICA PARA PADRÃO NOREPINEFRINA ---
        index_padrao = 0
        for i, droga in enumerate(lista_drogas):
            if "noradrenalina" in droga.lower() or "norepinefrina" in droga.lower():
                index_padrao = i
                break
        
        droga_nome = st.selectbox("Selecione a Medicação", lista_drogas, index=index_padrao)
    else:
        st.error("Erro de estrutura: Coluna de nome não encontrada.")
        st.stop()

# ==============================================================================
# 4. MOTOR DE CÁLCULO E LÓGICA
# ==============================================================================
if droga_nome:
    row = df_inf[df_inf[col_nome] == droga_nome].iloc[0]
    info = row.to_dict()
    
    # Normaliza chaves para compatibilidade Sheet/CSV (strip, lowercase)
    info_norm = {str(k).strip().lower().replace(" ", "_"): v for k, v in info.items()}

    st.markdown("### Preparo")
    c1, c2, c3 = st.columns(3)
    
    # --- VALORES PADRÃO: vêm do Sheet/CSV (qtd_amp_padrao, diluente_padrao) ---
    try:
        v = info_norm.get('qtd_amp_padrao') or info.get('qtd_amp_padrao')
        def_amp = float(v) if v is not None and pd.notna(v) and float(v) > 0 else 1.0
    except (ValueError, TypeError):
        def_amp = 1.0
    try:
        v = info_norm.get('diluente_padrao') or info.get('diluente_padrao')
        def_dil = int(float(v)) if v is not None and pd.notna(v) and float(v) >= 0 else 50
    except (ValueError, TypeError):
        def_dil = 50

    try:
        mg_amp = float(info.get('mg_amp', 0))
        vol_amp = float(info.get('vol_amp', 0))
    except:
        mg_amp = 0
        vol_amp = 0

    # Keys incluem a medicação para resetar os campos ao trocar de droga
    _key_safe = droga_nome.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")[:40]
    with c1:
        n_ampolas = st.number_input("Número de Ampolas", value=def_amp, step=1.0, format="%.1f", key=f"inf_amp_{_key_safe}")
    with c2:
        vol_diluente = st.number_input("Volume de Diluente (ml)", value=def_dil, step=1, format="%d", key=f"inf_dil_{_key_safe}")
        
    # --- CÁLCULOS MATEMÁTICOS ---
    qtd_total = n_ampolas * mg_amp
    vol_total = (n_ampolas * vol_amp) + vol_diluente
    if vol_total <= 0: vol_total = 1
    
    conc_principal = qtd_total / vol_total
    conc_secundaria = conc_principal * 1000
    
    # Tratamento de Strings e Unidades
    unidade_str = str(info.get('unidade', 'mg')).strip()
    
    # Definição Dinâmica de Rótulos
    if "UI" in unidade_str:
        label_conc_1, label_conc_2 = "UI/ml", "mUI/ml"
    elif "g" == unidade_str:
        label_conc_1, label_conc_2 = "g/ml", "mg/ml"
    else:
        label_conc_1, label_conc_2 = "mg/ml", "mcg/ml"

    # --- FUNÇÃO CONVERSORA (Universal & Blindada) ---
    def converte_dose(dose, unidade_droga):
        try: dose = float(dose)
        except: return 0.0
        if dose == 0: return 0.0
        
        u = unidade_droga # Já sanitizado acima
        
        # --- BLINDAGEM DE UNIDADES RARAS ---
        if u == "ng/kg/min":    return (dose * peso * 60) / (conc_secundaria * 1000) if conc_secundaria else 0
        elif u == "ng/kg/h":    return (dose * peso) / (conc_secundaria * 1000) if conc_secundaria else 0
        elif u == "mEq/h":      return dose / conc_principal if conc_principal else 0
        elif u == "mEq/kg/h":   return (dose * peso) / conc_principal if conc_principal else 0
        elif u == "mmol/h":     return dose / conc_principal if conc_principal else 0
        elif u == "mmol/kg/h":  return (dose * peso) / conc_principal if conc_principal else 0

        # --- PADRÕES COMUNS ---
        # Grupo A: Dependentes de Peso
        elif u == "mcg/kg/min": return (dose * peso * 60) / conc_secundaria if conc_secundaria else 0
        elif u == "mcg/kg/h":   return (dose * peso) / conc_secundaria if conc_secundaria else 0
        elif u == "mg/kg/h":    return (dose * peso) / conc_principal if conc_principal else 0
        elif u == "mg/kg/min":  return (dose * peso * 60) / conc_principal if conc_principal else 0
        elif u == "UI/kg/h":    return (dose * peso) / conc_principal if conc_principal else 0
        elif u == "UI/kg/min":  return (dose * peso * 60) / conc_principal if conc_principal else 0
        
        # Grupo B: Dose Absoluta
        elif u == "mcg/h":      return dose / conc_secundaria if conc_secundaria else 0
        elif u == "mcg/min":    return (dose * 60) / conc_secundaria if conc_secundaria else 0
        elif u == "mg/h":       return dose / conc_principal if conc_principal else 0
        elif u == "mg/min":     return (dose * 60) / conc_principal if conc_principal else 0
        elif u == "UI/h":       return dose / conc_principal if conc_principal else 0
        elif u == "UI/min":     return (dose * 60) / conc_principal if conc_principal else 0
        elif u == "g/h":        return dose / conc_principal if conc_principal else 0
        
        return 0.0

    # Limites
    dose_min = info.get('dose_min', 0)
    dose_max_hab = info.get('dose_max_hab', 0)
    dose_max_tol = info.get('dose_max_tol', 0)

    bomba_min = converte_dose(dose_min, unidade_str)
    bomba_max_hab = converte_dose(dose_max_hab, unidade_str)
    bomba_max_tol = converte_dose(dose_max_tol, unidade_str)

    # --- EXIBIÇÃO DE RESULTADOS ---
    st.markdown("### 1. Dados da Solução")
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.markdown(f"""<div class="result-box" style="border-left-color: #28a745;"><div class="result-title">VOLUME FINAL</div><div class="result-value">{int(vol_total)} ml</div></div>""", unsafe_allow_html=True)
    with col_res2:
        st.markdown(f"""<div class="result-box" style="border-left-color: #28a745;"><div class="result-title">CONCENTRAÇÃO ({label_conc_1})</div><div class="result-value">{format_br(conc_principal, 2)} {label_conc_1}</div></div>""", unsafe_allow_html=True)
    with col_res3:
        st.markdown(f"""<div class="result-box" style="border-left-color: #28a745;"><div class="result-title">CONCENTRAÇÃO ({label_conc_2})</div><div class="result-value">{format_br(conc_secundaria, 2)} {label_conc_2}</div></div>""", unsafe_allow_html=True)

    # --- SEÇÃO CORRIGIDA E ATUALIZADA (COM UNIDADES) ---
    st.markdown(f"### 2. Limites de Velocidade da Bomba")
    c_lim1, c_lim2, c_lim3 = st.columns(3)
    
    with c_lim1:
        st.markdown(f"""<div class="result-box" style="border-left-color: #1a73e8;"><div class="result-title">MÍNIMA<br>({format_br(dose_min, 2)} {unidade_str})</div><div class="result-value">{format_br(bomba_min)} ml/h</div></div>""", unsafe_allow_html=True)
    with c_lim2:
        st.markdown(f"""<div class="result-box" style="border-left-color: #ffc107;"><div class="result-title">MÁXIMA HABITUAL<br>({format_br(dose_max_hab, 2)} {unidade_str})</div><div class="result-value">{format_br(bomba_max_hab)} ml/h</div></div>""", unsafe_allow_html=True)
    with c_lim3:
        st.markdown(f"""<div class="result-box" style="border-left-color: #dc3545;"><div class="result-title">MÁXIMA ESTUDADA<br>({format_br(dose_max_tol, 2)} {unidade_str})</div><div class="result-value">{format_br(bomba_max_tol)} ml/h</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # --- SIMULADOR EM TEMPO REAL ---
    st.subheader("3. Simulador em Tempo Real")
    col_sim1, col_sim2 = st.columns(2)
    
    with col_sim1:
        val_inicial = float(bomba_min) if bomba_min > 0 else 0.0
        ml_h_atual = st.number_input("Velocidade Atual da Bomba (ml/h)", value=val_inicial, step=0.1, format="%.1f", key=f"inf_mlh_{_key_safe}")
        
        if ml_h_atual > 0:
            dose_real = 0.0
            u = unidade_str

            # Grupo A: Reverso Dependente de Peso
            if u == "mcg/kg/min":   dose_real = (ml_h_atual * conc_secundaria) / peso / 60
            elif u == "mcg/kg/h":   dose_real = (ml_h_atual * conc_secundaria) / peso
            elif u == "mg/kg/h":    dose_real = (ml_h_atual * conc_principal) / peso
            elif u == "mg/kg/min":  dose_real = (ml_h_atual * conc_principal) / peso / 60
            elif u == "UI/kg/h":    dose_real = (ml_h_atual * conc_principal) / peso
            elif u == "UI/kg/min":  dose_real = (ml_h_atual * conc_principal) / peso / 60
            
            # Grupo B: Reverso Absoluto
            elif u == "mcg/h":      dose_real = (ml_h_atual * conc_secundaria)
            elif u == "mcg/min":    dose_real = (ml_h_atual * conc_secundaria) / 60
            elif u == "mg/h":       dose_real = (ml_h_atual * conc_principal)
            elif u == "mg/min":     dose_real = (ml_h_atual * conc_principal) / 60
            elif u == "UI/h":       dose_real = (ml_h_atual * conc_principal)
            elif u == "UI/min":     dose_real = (ml_h_atual * conc_principal) / 60
            elif u == "g/h":        dose_real = (ml_h_atual * conc_principal)
            
            # Grupo C: Reverso Blindado (Raros)
            elif u == "ng/kg/min":  dose_real = (ml_h_atual * conc_secundaria * 1000) / peso / 60
            elif u == "ng/kg/h":    dose_real = (ml_h_atual * conc_secundaria * 1000) / peso
            elif u == "mEq/h":      dose_real = (ml_h_atual * conc_principal)
            elif u == "mEq/kg/h":   dose_real = (ml_h_atual * conc_principal) / peso
            elif u == "mmol/h":     dose_real = (ml_h_atual * conc_principal)
            elif u == "mmol/kg/h":  dose_real = (ml_h_atual * conc_principal) / peso

            st.metric(f"Dose Entregue ({unidade_str})", f"{format_br(dose_real, 2)}")
            
            try:
                max_tol = float(dose_max_tol)
                max_hab = float(dose_max_hab)
                if max_tol > 0 and dose_real > max_tol: 
                    st.error("🚨 PERIGO: Dose acima da MÁXIMA ESTUDADA!")
                elif max_hab > 0 and dose_real > max_hab: 
                    st.warning("⚠️ Atenção: Dose acima da máxima habitual.")
                else: 
                    st.success("✅ Dentro da faixa segura.")
            except: pass
# Rodapé com nota legal
mostrar_rodape()
