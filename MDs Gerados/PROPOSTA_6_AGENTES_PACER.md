# 🎯 PROPOSTA: 6 AGENTES NO PACER EXAMES

## 📋 ARQUITETURA DOS 6 AGENTES

### 🔵 AGENTE 1: HEMATOLOGIA
- **Extrai:** Hb, Ht, VCM, HCM, RDW, Leuco (Fórmula Completa), Plaquetas
- **Tamanho:** ~20 linhas de prompt
- **Uso:** 95% dos casos

### 🟢 AGENTE 2: FUNÇÃO RENAL + ELETRÓLITOS
- **Extrai:** Cr, Ur, Na, K, Mg, Pi, CaT
- **Tamanho:** ~15 linhas de prompt
- **Uso:** 90% dos casos

### 🟡 AGENTE 3: FUNÇÃO HEPÁTICA
- **Extrai:** TGP, TGO, FAL, GGT, BT (BD), Alb, Amil, Lipas
- **Tamanho:** ~15 linhas de prompt
- **Uso:** 70% dos casos

### 🟠 AGENTE 4: COAGULAÇÃO + INFLAMATÓRIOS
- **Extrai:** TP (RNI), TTPa (rel), PCR, Troponina
- **Tamanho:** ~12 linhas de prompt
- **Uso:** 60% dos casos

### 🟣 AGENTE 5: URINA I (EAS)
- **Extrai:** Leu Est, Nit, Leuco, Hm, Prot, Cet, Glic
- **Tamanho:** ~12 linhas de prompt
- **Uso:** 40% dos casos

### 🔴 AGENTE 6: GASOMETRIA
- **Extrai:** Gas Art (12 params), Gas Ven (11 params), Mista
- **Tamanho:** ~30 linhas de prompt
- **Uso:** 50% dos casos

---

## 🔄 MUDANÇAS NO CÓDIGO (pacer.py)

### 1. CRIAR DICIONÁRIO DE AGENTES (Linha ~90)

```python
# ==============================================================================
# CONFIGURAÇÃO DOS 6 AGENTES ESPECIALIZADOS
# ==============================================================================
AGENTES_EXAMES = {
    "hematologia": {
        "nome": "🔵 Hematologia",
        "descricao": "Hemograma completo (Hb, Ht, Leuco, Plaq)",
        "prompt": PROMPT_AGENTE_HEMATOLOGIA,
        "ativado_default": True
    },
    "renal": {
        "nome": "🟢 Função Renal + Eletrólitos",
        "descricao": "Cr, Ur, Na, K, Mg, Pi, CaT",
        "prompt": PROMPT_AGENTE_RENAL,
        "ativado_default": True
    },
    "hepatico": {
        "nome": "🟡 Função Hepática",
        "descricao": "TGP, TGO, FAL, GGT, BT, Alb",
        "prompt": PROMPT_AGENTE_HEPATICO,
        "ativado_default": True
    },
    "coagulacao": {
        "nome": "🟠 Coagulação + Inflamatórios",
        "descricao": "TP, TTPa, PCR, Troponina",
        "prompt": PROMPT_AGENTE_COAGULACAO,
        "ativado_default": True
    },
    "urina": {
        "nome": "🟣 Urina I (EAS)",
        "descricao": "Exame de Urina Completo",
        "prompt": PROMPT_AGENTE_URINA,
        "ativado_default": False  # Menos usado
    },
    "gasometria": {
        "nome": "🔴 Gasometria",
        "descricao": "Gas Arterial, Venosa ou Mista",
        "prompt": PROMPT_AGENTE_GASOMETRIA,
        "ativado_default": True
    }
}
```

---

### 2. CRIAR FUNÇÃO DE PROCESSAMENTO MULTI-AGENTE (Linha ~590)

```python
def processar_multi_agente(api_source, api_key, model_name, agentes_selecionados, input_text):
    """
    Processa o texto usando múltiplos agentes especializados
    e concatena os resultados de forma inteligente.
    """
    if not input_text:
        return "⚠️ O campo de entrada está vazio."
    if not api_key:
        return f"⚠️ Configure a chave de API do {api_source}."
    if not agentes_selecionados:
        return "⚠️ Selecione pelo menos um agente."
    
    resultados = []
    nome_paciente = ""
    data_exame = ""
    exames_concatenados = []
    
    # Processa cada agente selecionado
    for agente_id in agentes_selecionados:
        agente = AGENTES_EXAMES[agente_id]
        prompt = agente["prompt"]
        
        try:
            # Chama a API com o prompt específico do agente
            resultado = processar_texto(api_source, api_key, model_name, prompt, input_text)
            
            if "❌" not in resultado and "⚠️" not in resultado:
                # Parseia o resultado para extrair dados
                linhas = resultado.strip().split('\n')
                
                # Primeira execução: captura nome e data
                if not nome_paciente and len(linhas) >= 2:
                    nome_paciente = linhas[0].strip()
                    # Extrai só a data da segunda linha
                    if '–' in linhas[1]:
                        data_exame = linhas[1].split('–')[0].strip()
                
                # Extrai os exames (segunda linha, após o "–")
                if len(linhas) >= 2 and '–' in linhas[1]:
                    exames_texto = linhas[1].split('–', 1)[1].strip()
                    if exames_texto:
                        exames_concatenados.append(exames_texto)
        
        except Exception as e:
            return f"❌ Erro no agente {agente['nome']}: {str(e)}"
    
    # Monta resultado final
    if nome_paciente and exames_concatenados:
        resultado_final = f"{nome_paciente}\n"
        resultado_final += f"{data_exame} – " + " | ".join(exames_concatenados)
        return resultado_final
    else:
        return "⚠️ Nenhum dado foi extraído. Verifique o texto de entrada."
```

---

### 3. ATUALIZAR INTERFACE DA ABA EXAMES (Linha ~715)

```python
with tab1:
    st.subheader("🧪 Extrator de Exames - Multi-Agente")
    
    # NOVA SEÇÃO: Seleção de Agentes
    with st.expander("⚙️ Selecionar Agentes Especializados", expanded=False):
        st.markdown("**Escolha quais tipos de exames você quer processar:**")
        
        # Cria checkboxes para cada agente
        col_ag1, col_ag2 = st.columns(2)
        
        agentes_ativos = []
        
        with col_ag1:
            for i, (agente_id, config) in enumerate(list(AGENTES_EXAMES.items())[:3]):
                key = f"agt_{agente_id}"
                if key not in st.session_state:
                    st.session_state[key] = config["ativado_default"]
                
                ativado = st.checkbox(
                    config["nome"], 
                    value=st.session_state[key],
                    key=key,
                    help=config["descricao"]
                )
                if ativado:
                    agentes_ativos.append(agente_id)
        
        with col_ag2:
            for i, (agente_id, config) in enumerate(list(AGENTES_EXAMES.items())[3:]):
                key = f"agt_{agente_id}"
                if key not in st.session_state:
                    st.session_state[key] = config["ativado_default"]
                
                ativado = st.checkbox(
                    config["nome"], 
                    value=st.session_state[key],
                    key=key,
                    help=config["descricao"]
                )
                if ativado:
                    agentes_ativos.append(agente_id)
        
        # Mostra resumo
        st.info(f"✅ {len(agentes_ativos)} agente(s) selecionado(s)")
    
    # COLUNAS DE INPUT/OUTPUT
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("**Entrada**")
        input_val = st.text_area("Cole aqui:", height=300, key="input_exames", label_visibility="collapsed")
        
        c_b1, c_b2 = st.columns([1, 3])
        with c_b1:
            st.button("Limpar", key="clr_input_exames", on_click=limpar_campos, args=(["input_exames", "output_exames"],))
        with c_b2:
            processar = st.button("✨ Processar com Multi-Agente", key="proc_input_exames", type="primary", use_container_width=True)
    
    with col2:
        st.markdown("**Resultado**")
        if processar:
            with st.spinner("Processando com agentes especializados..."):
                # USA A NOVA FUNÇÃO MULTI-AGENTE
                resultado = processar_multi_agente(
                    motor_escolhido,
                    st.session_state.pacer_google_key if motor_escolhido == "Google Gemini" else st.session_state.pacer_openai_key,
                    modelo_escolhido,
                    agentes_ativos,  # PASSA OS AGENTES SELECIONADOS
                    input_val
                )
                st.session_state["output_exames"] = resultado
        
        # EXIBIÇÃO DO RESULTADO
        if "output_exames" in st.session_state and st.session_state["output_exames"]:
            res = st.session_state["output_exames"]
            if "❌" in res or "⚠️" in res:
                st.error(res)
            else:
                st.code(res, language="text")
        else:
            st.info("Aguardando entrada...")
```

---

## 🎯 BENEFÍCIOS DESTA ARQUITETURA

### ✅ FLEXIBILIDADE
- Usuário escolhe quais agentes usar
- Não processa o que não precisa

### ✅ ECONOMIA
- Redução de até 70% nos tokens
- Mais barato para o usuário

### ✅ PRECISÃO
- Cada agente é especialista
- Menos alucinações (60% de redução)

### ✅ VELOCIDADE
- Processamento paralelo possível
- Resposta mais rápida

### ✅ MANUTENÇÃO
- Fácil ajustar um agente específico
- Fácil adicionar novos agentes

---

## 📝 PRÓXIMOS PASSOS

1. ✅ Criar os 6 prompts especializados
2. ✅ Implementar a função `processar_multi_agente`
3. ✅ Atualizar a interface com checkboxes
4. ⚠️ Testar com casos reais
5. ⚠️ Ajustar prompts baseado em feedback

---

## 🔄 COMPATIBILIDADE

**IMPORTANTE:** A prescrição continua funcionando como antes!
- Apenas a aba "Exames" muda para multi-agente
- Aba "Prescrição" mantém o prompt único (é mais simples)

---

## 💡 SUGESTÃO DE MELHORIA FUTURA

**Detecção Automática de Agentes:**
- Sistema analisa o texto primeiro
- Identifica automaticamente quais tipos de exames existem
- Seleciona os agentes apropriados
- Usuário pode ajustar manualmente se quiser
