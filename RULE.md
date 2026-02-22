# Regras do Projeto — Intensiva Calculator

## Workflow de Novos Campos

> **LEMBRE-SE SEMPRE:** ao criar um campo novo, atualize o **agente** (agentes_secoes.py) e a **saída determinística** (gerador.py). Nunca omitir.

**Ao criar ou alterar um campo em qualquer seção do prontuário, atualize obrigatoriamente os 3 locais:**

| # | Local | Arquivo | O que fazer |
|---|-------|---------|-------------|
| 1 | **Formulário** | `modules/secoes/<secao>.py` | Adicionar em `get_campos()` e na UI |
| 2 | **Gerador** | `modules/gerador.py` | Incluir na função `_secao_*` correspondente |
| 3 | **Agente** | `modules/agentes_secoes.py` | Atualizar prompt, schema JSON e `preencher_<secao>` |

### Compatibilidade JSON

- As chaves retornadas por `preencher_*` devem corresponder **exatamente** às chaves em `get_campos()`.
- Campos `*_conduta`: o agente **não preenche** (sempre `""`). O usuário preenche manualmente.
- Condutas são agregadas em `modules/secoes/condutas.py` → `coletar_condutas_agregadas()`.

### Exemplo

Novo campo `comp_{i}_exame` em Exames Complementares:

1. **Formulário**: `f'comp_{i}_exame': ''` em `get_campos()` + `st.text_input(..., key=f"comp_{id_real}_exame")`
2. **Gerador**: `exame = _get(f"comp_{i}_exame")` e incluir na linha gerada
3. **Agente**: schema com `comp_{i}_exame`, instruções no prompt, e `resultado[f"comp_{i}_exame"] = _v("exame")` em `preencher_complementares`

---

## Regra Persistente

Uma regra detalhada está em `.cursor/rules/novos-campos.mdc` para orientar a IA ao editar seções, gerador ou agentes.
