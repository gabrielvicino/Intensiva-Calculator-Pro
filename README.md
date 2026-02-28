# Intensiva Calculator Pro ⚕️

O **Intensiva Calculator Pro** é uma solução modular desenvolvida para **auxiliar na tomada de decisões críticas** em Terapia Intensiva e Medicina de Emergência.

> **Para desenvolvedores/TI:** Leia `ONBOARDING.md` para entender o projeto rapidamente.

Com foco em **segurança e praticidade**, a ferramenta automatiza cálculos complexos de farmacologia e padroniza protocolos de atendimento. O sistema opera com redundância de dados (Nuvem/Local) para garantir disponibilidade total e foi projetado em linguagem **Python**, utilizando a estrutura **Streamlit** para alta performance e integração de dados.

---

## 🚀 Módulos Disponíveis

Selecione uma das ferramentas no menu lateral para iniciar:

### 📋 **Evolução Diária**
Geração inteligente de evoluções médicas com auxílio de IA. Extração automática de dados clínicos, exames e parâmetros vitais. Suporte aos modelos Google Gemini e OpenAI GPT para processamento de linguagem natural.

### 📃 **Pacer - Exames & Prescrição**
Processador especializado para organização de resultados laboratoriais e prescrições médicas. Extrai e formata dados de exames em texto estruturado para registro rápido em prontuários.

### 💉 **Infusão Contínua**
Calculadora de precisão para drogas vasoativas e sedação. Permite ajustes de concentração, cálculo reverso de doses e alertas de segurança.

### ⚡ **Intubação Orotraqueal (IOT)**
Guia rápido de indução de sequência rápida. Fornece doses mínimas, médias e máximas de indutores e bloqueadores neuromusculares ajustadas pelo peso.

### 🔄 **Conversão Universal**
Ferramenta versátil para conversão instantânea entre unidades farmacológicas (mcg, mg, g, UI) e taxas de infusão (ml/h ↔ dose/kg/min).

### 🧮 **Calculadoras Médicas**
Conjunto de calculadoras especializadas incluindo scores prognósticos, índices de gravidade e cálculos de função orgânica para avaliação clínica completa.

---

## 🛠️ Tecnologias

- **Python 3.8+** - Linguagem principal
- **Streamlit** - Framework web interativo
- **Google Gemini AI** - Processamento de linguagem natural
- **OpenAI GPT** - Modelos de IA alternativos
- **Pandas** - Manipulação de dados
- **Google Sheets API** - Sincronização de dados em nuvem

---

## 🚀 Como Usar

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/intensiva-calculator.git

# Instale as dependências
pip install -r requirements.txt

# Execute o aplicativo
streamlit run app.py

# Windows: duplo clique em executar.bat ou scripts\iniciar.bat
```

### Configuração

1. Configure suas credenciais em `.streamlit/secrets.toml`
2. Adicione sua API Key do Google Gemini ou OpenAI
3. Configure o acesso ao Google Sheets (opcional)

---

## 📁 Estrutura do Projeto

```
Intensiva Calculator/
├── ONBOARDING.md       ← Leia primeiro (dev/TI)
├── app.py              ← Ponto de entrada
├── utils.py            ← Google Sheets, load/save
├── executar.bat        ← Inicia o app (Windows)
├── fazer_commit.bat    ← Commit e push
├── modules/            ← Lógica (fichas, gerador, agentes, parsers)
├── views/              ← Páginas (home, evolucao, infusao, pacer...)
├── calculos/           ← Cálculos especializados (renal)
├── scripts/            ← Scripts auxiliares (gerar_exemplo, testar_gemini)
└── MDs Gerados/        ← Documentação detalhada
```

- **Entender o projeto:** `ONBOARDING.md` (roteiro completo)
- **Arquitetura detalhada:** `MDs Gerados/RESUMO_SITE.md`

---

**Ferramenta atualmente em desenvolvimento**  
*Dr. Gabriel Valladão Vicino - CRM-SP 223.216*

---

**Nota Legal:** Conforme os Termos de Uso, esta aplicação destina-se a servir estritamente como uma ferramenta de auxílio e suporte à decisão clínica-assistencial. Ela não substitui o julgamento clínico individualizado. A responsabilidade final pela decisão terapêutica e pela assistência ao paciente compete exclusivamente ao profissional devidamente habilitado.

Nota Legal: Conforme os Termos de Uso, esta aplicação destina-se a servir estritamente como uma ferramenta de auxílio e suporte à decisão clínica-assistencial. Ela não substitui o julgamento clínico individualizado. A responsabilidade final pela decisão terapêutica e pela assistência ao paciente compete exclusivamente ao profissional devidamente habilitado.
