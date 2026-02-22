# Contexto — Página Evolução Diária

## O que é

Ferramenta de round de UTI digitalizado. O médico cola um prontuário bruto, a IA organiza os dados em campos estruturados, e o sistema gera um texto final padronizado pronto para o prontuário.

---

## Fluxo em 3 etapas

```
[1] ENTRADA BRUTA
    Médico cola prontuário no campo de texto

        ↓  botão "✨ Extrair Dados Selecionados"

[2] IA EXTRATORA  (modules/ia_extrator.py)
    GPT-4o / Gemini fatia o texto em 14 campos JSON
    → preenche os campos *_notas de cada seção (via fluxo.atualizar_notas_ia)

        ↓  botão "🚀 Aplicar Agentes Selecionados"

[3] AGENTES DE IA  (modules/agentes_secoes.py)
    13 agentes (um por seção) leem o *_notas e preenchem os campos estruturados
    Usuário controla quais agentes rodar via checklist
    Padrão marcado: laboratoriais, controles, evolucao, sistemas

        ↓  automático

[4] SAÍDA DETERMINÍSTICA  (modules/gerador.py)
    Lê session_state → monta texto formatado campo por campo
    Sem IA, sem inferência — só o que está preenchido aparece
```

---

## Estrutura do formulário (14 seções, ~450 campos)

| Expander | # | Seção | Módulo |
|---|---|---|---|
| **Dados do Paciente** | 1 | Identificação & Scores | `identificacao.py` |
| | 2 | Diagnósticos | `hd.py` |
| | 3 | Comorbidades | `comorbidades.py` |
| | 4 | Medicações de Uso Contínuo | `muc.py` |
| | 5 | HMPA | `hmpa.py` |
| **Evolução Horizontal** | 6 | Dispositivos Invasivos | `dispositivos.py` |
| | 7 | Culturas | `culturas.py` |
| | 8 | Antibióticos | `antibioticos.py` |
| | 9 | Exames Complementares | `complementares.py` |
| **Evolução Diária** | 10 | Laboratoriais (Curva) | `laboratoriais.py` |
| | 11 | Controles & Balanço Hídrico | `controles.py` |
| | 12 | Evolução Clínica (Texto Livre) | `evolucao_clinica.py` |
| | 13 | Evolução Detalhada por Sistemas | `sistemas.py` |
| | 14 | Plano Terapêutico & Condutas | `condutas.py` |

---

## Mapa de arquivos principais

```
views/
  evolucao.py          → View principal: UI dos 3 blocos, sidebar IA, botões

modules/
  fichas.py            → Inicializa session_state + renderiza formulário completo
  gerador.py           → Saída determinística (função gerar_texto_final)
  fluxo.py             → atualizar_notas_ia() + limpar_tudo()
  ia_extrator.py       → Chama GPT/Gemini para fatiar o prontuário (14 campos JSON)
  agentes_secoes.py    → 13 agentes de IA (um por seção)
  secoes/              → Um arquivo por seção: get_campos() + render()
```

---

## Convenções importantes

### Campos de sessão
- `*_notas` → campo livre que recebe o texto fatiado pela IA (ex: `sistemas_notas`)
- Campos estruturados → preenchidos pelos agentes (ex: `sis_neuro_ecg`, `ctrl_hoje_pas_min`)

### Regras de UI
- **Nenhum campo com valor pré-selecionado** — radios com `index=None`, selectbox com `""` como primeira opção
- **Condutas em verde** — usar `with st.success("Conduta"):` para destacar
- **O que não está escrito não aparece** — regra absoluta do gerador

### Seção HMPA (especial)
- Tem 2 campos: `hmpa_texto` (extrator fatia aqui) e `hmpa_reescrito` (agente reescreve)
- O agente HMPA retorna texto puro, não JSON — é o único que não usa `_chamar_ia()`

### Autenticação
- PIN: `7894` — implementado em `app.py` via `verificar_autenticacao()`

---

## Status do gerador (modules/gerador.py)

O gerador é construído seção por seção. Cada seção é uma função `_secao_*()` independente.

| Seção | Status |
|---|---|
| 1. Identificação & Scores | ✅ Implementado |
| 2. Diagnósticos | 🔲 Pendente |
| 3. Comorbidades | 🔲 Pendente |
| 4. MUC | 🔲 Pendente |
| 5. HMPA | 🔲 Pendente |
| 6. Dispositivos | 🔲 Pendente |
| 7. Culturas | 🔲 Pendente |
| 8. Antibióticos | 🔲 Pendente |
| 9. Complementares | 🔲 Pendente |
| 10. Laboratoriais | 🔲 Pendente |
| 11. Controles & Balanço | 🔲 Pendente |
| 12. Evolução Clínica | 🔲 Pendente |
| 13. Sistemas | 🔲 Pendente |
| 14. Condutas | 🔲 Pendente |

### Como adicionar uma nova seção ao gerador

1. Criar `def _secao_nome() -> list[str]:` em `gerador.py`
2. Seguir a regra: **campo vazio → linha não aparece** (exceto exceções explícitas)
3. Retornar `[]` se não houver nenhum conteúdo (cabeçalho condicional)
4. Adicionar `secoes.append(_secao_nome())` em `gerar_texto_final()`

---

## Como adicionar um novo agente de IA

1. Criar `_PROMPT_NOME` e `def preencher_nome(texto, api_key, provider, modelo)` em `agentes_secoes.py`
2. Adicionar em `_AGENTES`, `_NOTAS_MAP` e `NOMES_SECOES` (os três juntos, sempre)
3. Adicionar campo `*_notas` no `get_campos()` da seção correspondente
4. Adicionar `"nome": "nome_notas"` em `fluxo._MAPA_NOTAS`

---

## Chaves de API

- OpenAI e Google Gemini carregadas de `.streamlit/secrets.toml` (produção) ou `.env` (local)
- Arquivos ignorados pelo git — nunca commitar chaves
- Padrão selecionado: OpenAI GPT-4o
