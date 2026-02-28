# 📁 ESTRUTURA DO PROJETO - Intensiva Calculator

**Última atualização:** Janeiro 2026

---

## 🎯 ESTRUTURA ORGANIZADA

```
Intensiva Calculator/
├── 📄 app.py                       ← Aplicativo principal Streamlit
├── 📄 utils.py                     ← Funções utilitárias (load_data, etc.)
├── 📄 requirements.txt             ← Dependências do projeto
├── 📄 README.md                    ← Documentação principal
├── 📄 LICENSE                      ← Licença do projeto
├── 📄 .gitignore                   ← Arquivos ignorados pelo Git
├── 📄 .cursorrules                 ← Regras do Cursor IDE
├── 📄 REGRA_ORGANIZACAO_MDS.txt   ← Regra de organização (nesta pasta)
│
├── 📁 scripts/                     ← SCRIPTS (executáveis e automação)
│   └── iniciar.bat
│
├── 📁 modules/                     ← MÓDULOS PYTHON (lógica do negócio)
│   ├── __init__.py
│   ├── agentes_secoes.py           ← Integração com IA (Gemini/OpenAI) por seção
│   ├── fichas.py                   ← Gerenciamento de fichas
│   ├── fluxo.py                    ← Fluxo de dados
│   └── gerador.py                  ← Geração de conteúdo
│
├── 📁 calculos/                    ← CÁLCULOS ESPECIALIZADOS
│   ├── __init__.py
│   └── renal.py                    ← Cálculos renais
│
├── 📁 views/                       ← PÁGINAS DO APLICATIVO
│   ├── home.py                     ← Página inicial
│   ├── evolucao.py                 ← Evolução Diária (com IA)
│   ├── pacer.py                    ← Pacer (Exames & Prescrição)
│   ├── infusao.py                  ← Calculadora de Infusão
│   ├── intubacao.py                ← IOT Calculator
│   ├── conversao.py                ← Conversões médicas
│   └── calculadoras.py             ← Outras calculadoras
│
├── 📁 MDs Gerados/                 ← DOCUMENTAÇÃO (todos os .md aqui!)
│   ├── .INSTRUCOES.md              ← Regras de organização
│   ├── README.md                   ← Índice dos documentos
│   ├── TODOS_MODELOS_GEMINI.md
│   ├── FUNCAO_ATUALIZAR_MODELOS.md
│   └── [outros 10+ documentos...]
│
├── 📁 .streamlit/                  ← CONFIGURAÇÃO STREAMLIT
│   ├── config.toml                 ← Configurações do app
│   ├── secrets.toml                ← Credenciais (NÃO versionar!)
│   └── atualizar.py
│
├── 📁 .github/                     ← CONFIGURAÇÃO GITHUB
│   └── CONTRIBUTING.md             ← Guia de contribuição
│
├── 📁 .devcontainer/               ← DESENVOLVIMENTO (Docker)
├── 📁 .vscode/                     ← CONFIGURAÇÃO VS CODE
├── 📁 .venv/                       ← AMBIENTE VIRTUAL PYTHON
└── 📁 __pycache__/                 ← CACHE PYTHON (auto-gerado)
```

---

## 📋 DESCRIÇÃO DAS PASTAS

### **📁 scripts/** - Scripts de Automação
**Propósito:** Centralizar scripts executáveis e de automação

**Conteúdo:**
- `iniciar.bat` - Script para iniciar o aplicativo no Windows

**Motivo:** Organizar ferramentas de linha de comando

---

### **📁 modules/** - Módulos Python
**Propósito:** Lógica de negócio reutilizável

**Conteúdo:**
- `agentes_secoes.py` - Integração com IA (Google Gemini, OpenAI GPT) por seção
- `fichas.py` - Gerenciamento de fichas médicas
- `fluxo.py` - Fluxo de dados entre componentes
- `gerador.py` - Geração de textos e conteúdo

**Motivo:** Separar lógica da apresentação

---

### **📁 calculos/** - Cálculos Especializados
**Propósito:** Módulos de cálculos médicos específicos

**Conteúdo:**
- `renal.py` - Cálculos de função renal

**Motivo:** Organizar cálculos complexos por especialidade

---

### **📁 views/** - Páginas do Aplicativo
**Propósito:** Interface do usuário (UI) - páginas Streamlit

**Conteúdo:**
- `home.py` - Página inicial
- `evolucao.py` - Evolução Diária com IA
- `pacer.py` - Pacer (Exames & Prescrição)
- `infusao.py` - Calculadora de Infusão
- `intubacao.py` - IOT Calculator
- `conversao.py` - Conversões médicas
- `calculadoras.py` - Hub de calculadoras

**Motivo:** Separar cada página/funcionalidade do app

---

### **📁 MDs Gerados/** - Documentação
**Propósito:** Toda a documentação do projeto em Markdown

**Conteúdo:**
- 15+ documentos .md organizados
- Instruções, guias, referências técnicas
- Documentação de funcionalidades

**⚠️ REGRA:** Todos os novos .md devem ser criados aqui!

**Motivo:** Centralizar documentação, manter raiz limpa

---

### **📁 .streamlit/** - Configuração Streamlit
**Propósito:** Configurações do Streamlit e credenciais

**Conteúdo:**
- `config.toml` - Tema, configurações do app
- `secrets.toml` - Credenciais sensíveis (Google Sheets, APIs)

**⚠️ IMPORTANTE:** `secrets.toml` NÃO deve ser versionado!

---

### **📁 .github/** - Configuração GitHub
**Propósito:** Arquivos relacionados ao GitHub

**Conteúdo:**
- `CONTRIBUTING.md` - Guia para contribuidores

---

## 🔄 MUDANÇAS RECENTES (Janeiro 2026)

### **✅ Organização Implementada:**

1. **Criada pasta `scripts/`**
   - Movido: `iniciar.bat`

2. **Removida pasta `pages/`**
   - Estava vazia e não era utilizada

3. **Criada pasta `MDs Gerados/`**
   - Organizados 15 documentos de documentação
   - Adicionado `.INSTRUCOES.md` com regras

4. **Dados:** O app usa exclusivamente Google Sheets (DB_INFUSAO, DB_IOT). Sem CSV.

---

## 📝 CONVENÇÕES E REGRAS

### **1. Arquivos .md (Markdown)**
- ✅ `README.md` na raiz (único permitido)
- ✅ Todos os outros .md em `MDs Gerados/`
- ❌ Nunca criar .md na raiz ou outras pastas

### **2. Dados**
- ✅ Todos os dados no Google Sheets (DB_INFUSAO, DB_IOT)
- ❌ Não usar CSV ou arquivos locais de dados

### **3. Scripts**
- ✅ Scripts executáveis em `scripts/`
- ✅ Pode incluir: `.bat`, `.sh`, `.ps1`
- ❌ Não deixar scripts na raiz

### **4. Módulos Python**
- ✅ Lógica de negócio em `modules/`
- ✅ Páginas UI em `views/`
- ✅ Cálculos especializados em `calculos/`
- ❌ Não misturar lógica com apresentação

---

## 🎯 COMO NAVEGAR NO PROJETO

### **Para adicionar nova funcionalidade:**
1. **Página UI:** Criar em `views/nova_pagina.py`
2. **Lógica:** Criar em `modules/nova_logica.py`
3. **Dados:** Editar no Google Sheets (aba DB_INFUSAO ou DB_IOT)
4. **Documentação:** Criar em `MDs Gerados/NOVA_DOC.md`

### **Para encontrar código:**
- **UI/Interface:** Procure em `views/`
- **Lógica/Funções:** Procure em `modules/`
- **Cálculos:** Procure em `calculos/`
- **Dados:** Google Sheets (utils.py → load_data)
- **Docs:** Procure em `MDs Gerados/`

---

## 📊 ESTATÍSTICAS DO PROJETO

```
Arquivos Python: ~15 arquivos
Páginas UI: 7 páginas
Módulos: 4 módulos + 1 calculadora
Documentos .md: 15+ documentos
Dados: Google Sheets (DB_INFUSAO, DB_IOT)
Scripts: 1 bat
```

---

## 🔍 ARQUIVOS PRINCIPAIS

| Arquivo | Propósito | Localização |
|---------|-----------|-------------|
| `app.py` | Entry point do app | Raiz |
| `utils.py` | Funções utilitárias | Raiz |
| `requirements.txt` | Dependências | Raiz |
| `evolucao.py` | Página Evolução | views/ |
| `pacer.py` | Página Pacer | views/ |
| `infusao.py` | Calculadora Infusão | views/ |
| `agentes_secoes.py` | Integração IA | modules/ |

---

## 💡 DICAS

### **Para novos desenvolvedores:**
1. Leia `README.md` primeiro
2. Explore `ESTRUTURA_PROJETO.md` (este arquivo)
3. Veja `MDs Gerados/README.md` para documentação
4. Siga as convenções estabelecidas

### **Para contribuir:**
1. Leia `.github/CONTRIBUTING.md`
2. Siga a estrutura de pastas
3. Documente em `MDs Gerados/`
4. Atualize este arquivo se mudar estrutura

---

## ✅ BENEFÍCIOS DESTA ORGANIZAÇÃO

✅ **Navegabilidade:** Fácil encontrar arquivos por função
✅ **Manutenibilidade:** Código organizado é mais fácil de manter
✅ **Escalabilidade:** Fácil adicionar novas funcionalidades
✅ **Clareza:** Estrutura clara para novos desenvolvedores
✅ **Profissionalismo:** Projeto bem organizado
✅ **Documentação:** Tudo em um só lugar

---

## 🚀 PRÓXIMOS PASSOS

Para continuar melhorando a organização:

1. ✅ Considerar criar `tests/` para testes
2. ✅ Considerar criar `assets/` para imagens/ícones
3. ✅ Considerar criar `config/` para configurações
4. ✅ Revisar e atualizar documentação regularmente

---

**📁 Estrutura organizada e documentada!**

**Criado:** Janeiro 2026  
**Propósito:** Guia de navegação e organização do projeto  
**Mantenha:** Atualize este arquivo ao mudar a estrutura
