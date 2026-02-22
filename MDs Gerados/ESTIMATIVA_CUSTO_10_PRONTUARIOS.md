# Estimativa de Custo — 10 Prontuários (Evolução Diária)

## Chamadas de IA por prontuário completo

| # | Chamada | Quantidade | Tokens (est.) |
|---|---------|------------|---------------|
| 1 | **Recortador** (Extrair Seções) | 1 | ~3.500 |
| 2 | **Agentes de seções** (Completar Todos) | 13 | ~14.000 |
| 3 | **Extrair Exames** (Bloco 10) | 6 (1 id + 5 paralelos) | ~1.800 |
| 4 | **Extrair Prescrição** (Bloco 14) | 3 (sequenciais) | ~2.200 |
| | **TOTAL por prontuário** | **23 chamadas** | **~21.500 tokens** |

> Proporção aproximada: ~65% input / ~35% output  
> **Por 10 prontuários:** ~140.000 input + ~75.000 output ≈ **215.000 tokens**

---

## Custo por 10 prontuários (preços fev/2026)

| Modelo | Input/1M | Output/1M | **Custo 10 pront.** | Em R$ |
|--------|----------|-----------|---------------------|-------|
| **GPT-4o** | $2,50 | $10,00 | **~$1,10** | ~R$6,50 |
| **GPT-4o-mini** | $0,15 | $0,60 | **~$0,07** | ~R$0,40 |
| **Gemini 2.5 Flash** | $0,075 | $0,30 | **~$0,02** | ~R$0,12 |
| **Gemini 2.5 Pro** | $1,25 | $10,00 | **~$0,93** | ~R$5,50 |

---

## Projeção mensal (20 dias úteis)

| Volume/dia | GPT-4o | Gemini 2.5 Flash |
|------------|--------|-------------------|
| 10 pront./dia | ~R$130/mês | ~R$2,40/mês |
| 5 pront./dia | ~R$65/mês | ~R$1,20/mês |
| 20 pront./dia | ~R$260/mês | ~R$4,80/mês |

---

## Recomendação

- **Gemini 2.5 Flash** → custo muito baixo (~R$0,01 por prontuário)
- **GPT-4o-mini** → custo moderado, boa qualidade
- **GPT-4o** → maior custo, melhor para casos complexos

> Valores baseados em evolução típica (~600 tokens). Evoluções longas ou prescrições extensas podem aumentar o custo em até 2×.
