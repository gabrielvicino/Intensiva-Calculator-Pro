import streamlit as st
from PIL import Image
import os
from utils import mostrar_rodape

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
# [BLOQUEADO] Gerenciado pelo app.py para evitar conflito
# st.set_page_config(
#     page_title="Home - Intensiva Calculator",
#     page_icon="⚕️", 
#     layout="wide"
# )

# --- 2. CONTEÚDO PRINCIPAL ---
st.title("⚕️ Intensiva Calculator")

st.markdown("""
### Bem-vindo ao **Intensiva Calculator**

O **Intensiva Calculator** é uma solução modular desenvolvida para auxiliar a tomada de decisões clínicas em ambientes de **Terapia Intensiva e Medicina de Emergência**, com foco em **precisão, segurança e padronização assistencial**.

Sua arquitetura foi projetada para otimizar o **fluxo de trabalho** em cenários críticos. Ao fornecer informações essenciais para **suporte à decisão clínica-assistencial**, a ferramenta assegura maior assertividade à conduta médica, convertendo dados em **decisões ágeis e precisas**, visando à **segurança do paciente** e à melhor prática da **medicina baseada em evidências**.

O sistema opera com **redundância de dados** (Nuvem e Local), garantindo **alta disponibilidade**, e foi desenvolvido em Python, utilizando a estrutura Streamlit, o que permite alta performance, escalabilidade e integração de dados.

---

#### 🚀 Módulos Disponíveis

Selecione uma das ferramentas no menu lateral para iniciar:

* **💉 Infusão Contínua:** Calculadora de alta precisão para **drogas vasoativas, sedativos e analgésicos**. Permite ajustes personalizados de concentração, cálculo reverso de doses e definição de limites de segurança.
    
* **⚡ Intubação Orotraqueal (IOT):** Guia rápido para indução de **sequência rápida**, com sugestões de doses mínimas, usuais e máximas de agentes indutores e bloqueadores neuromusculares, **ajustadas ao peso corporal**.

* **🔄 Conversão Universal:** Ferramenta para **conversão instantânea** entre unidades farmacológicas (mcg, mg, g, UI) e taxas de infusão (ml/h ↔ dose/kg/min), facilitando a prática clínica diária.

* **📃 Pacer - Exames & Prescrição:** Processador especializado para **organização de resultados laboratoriais** e prescrições médicas. Extrai e formata dados de exames em texto estruturado para registro rápido.

* **🚧 [EM CONSTRUÇÃO] Evolução Diária:** Geração inteligente de evoluções médicas com auxílio de **Inteligência Artificial**. Extração automática de dados clínicos, exames e parâmetros vitais para otimização do registro em prontuário.

* **🚧 [EM CONSTRUÇÃO] Calculadoras Médicas:** Conjunto de calculadoras especializadas incluindo **scores prognósticos**, índices de gravidade e cálculos de função orgânica para avaliação clínica completa.

---
Ferramenta em desenvolvimento por *Dr. Gabriel Valladão Vicino – CRM-SP 223.216*

<br>

""", unsafe_allow_html=True)

# Rodapé com nota legal
mostrar_rodape()