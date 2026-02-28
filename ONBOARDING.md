# Guia de Onboarding — Intensiva Calculator

**Para:** Desenvolvedores, TI, ou qualquer pessoa/ferramenta que precise entender o projeto rapidamente.

---

## 1. O que é este projeto?

Aplicação web (Streamlit/Python) para **apoio à decisão clínica** em UTI. Principais funções:

- **Evolução Diária:** Gera evolução médica estruturada a partir de texto bruto, usando IA para extrair e preencher formulários.
- **Pacer:** Extrai exames e prescrições de laudos via IA.
- **Infusão, IOT, Conversor, Calculadoras:** Ferramentas clínicas auxiliares.

---

## 2. Como rodar (3 passos)

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar chaves de API (obrigatório para Evolução e Pacer)
# Copie .streamlit/secrets_example.toml para .streamlit/secrets.toml
# Ou crie .env com: OPENAI_API_KEY=... e GOOGLE_API_KEY=...

# 3. Executar
streamlit run app.py
# Windows: executar.bat ou scripts\iniciar.bat
```

---

## 3. Roteiro de leitura (em ordem)

| Ordem | Arquivo | Conteúdo |
|-------|---------|----------|
| 1 | `README.md` | Visão geral, módulos, instalação |
| 2 | `MDs Gerados/RESUMO_SITE.md` | Arquitetura, fluxo de dados, páginas, configuração |
| 3 | `MDs Gerados/ESTRUTURA_PROJETO.md` | Detalhes da estrutura de pastas |
| 4 | `RULE.md` | Regras do projeto (novos campos, etc.) |

---

## 4. Estrutura em uma frase

- **app.py** → Router (define páginas e autenticação)
- **views/** → Uma página por ferramenta (evolucao, infusao, pacer...)
- **modules/** → Lógica: `fichas` (formulários), `gerador` (texto), `agentes_secoes` (IA), `ia_extrator` (recorte)
- **utils.py** → Google Sheets, load/save de evoluções

---

## 5. Fluxo principal (Evolução Diária)

```
Texto colado → ia_extrator (recorta em 14 seções) → fluxo.atualizar_notas_ia
→ agentes_secoes (12 agentes preenchem campos) → gerador.gerar_texto_final
→ Prontuário completo
```

---

## 6. Configuração necessária

| Item | Onde | Obrigatório para |
|------|------|------------------|
| OPENAI_API_KEY | `.streamlit/secrets.toml` ou `.env` | Evolução, Pacer |
| GOOGLE_API_KEY | `.streamlit/secrets.toml` ou `.env` | Evolução, Pacer |
| Google Sheets | `utils.py` (SHEET_URL) | Infusão, salvar evoluções |

---

## 7. Onde está cada coisa?

- **Adicionar novo campo em uma seção:** `.cursor/rules/novos-campos.mdc` (regra obrigatória)
- **Documentação detalhada:** `MDs Gerados/` (30+ docs; comece por `RESUMO_SITE.md`)
- **Scripts auxiliares:** `scripts/` (gerar_exemplo, testar_gemini, sync_infusao)

---

*Este arquivo é o ponto de entrada para quem precisa entender o projeto do zero.*
