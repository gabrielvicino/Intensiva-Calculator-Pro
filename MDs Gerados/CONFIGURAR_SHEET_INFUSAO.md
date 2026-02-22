# Configurar Google Sheet para Infusão Contínua

## Objetivo

Ao selecionar uma medicação na página **Infusão Contínua**, os campos **Número de Ampolas** e **Volume de Diluente** são preenchidos automaticamente com os valores padrão definidos na planilha.

**Exemplo:** Ao escolher Adrenalina, já aparece 4 ampolas e 246 ml no diluente.

---

## Sincronizar dados (recomendado)

Na página **Infusão Contínua**, abra o expander **"Atualizar dados padrão no Sheet"** e clique em **Sincronizar DB_INFUSAO**. Ou execute:

```bash
streamlit run scripts/sync_infusao_sheet.py
```

---

## Estrutura da aba DB_INFUSAO

| Coluna | Descrição |
|--------|-----------|
| nome_formatado | Nome da medicação |
| mg_amp | mg por ampola |
| vol_amp | ml por ampola |
| dose_min, dose_max_hab, dose_max_tol | Limites de dose |
| unidade | mcg/kg/min, mg/h, etc. |
| **qtd_amp_padrao** | Número de ampolas padrão |
| **diluente_padrao** | Volume de diluente em ml |

---

## Valores de pré-carregamento (referência)

| Medicação | Ampolas | Diluente (ml) |
|-----------|---------|---------------|
| Adrenalina 1ml (1mg/ml) | 4 | 246 |
| Amiodarona 3ml (50mg/ml) | 2 | 244 |
| Atracúrio 2,5ml (10mg/ml) | 4 | 90 |
| Atracúrio 5ml (10mg/ml) | 2 | 90 |
| Cisatracúrio 5ml (2mg/ml) | 10 | 50 |
| Dexmedetomidina 2ml (100mcg/ml) | 1 | 48 |
| Dobutamina 20ml (12,5mg/ml) | 1 | 230 |
| Dopamina 10ml (5mg/ml) | 5 | 200 |
| Esmolol, Fentanil, Propofol | 1 | 0 (uso direto) |
| Lidocaína 20ml (20mg/ml) | 2 | 210 |
| Midazolam 3ml (5mg/ml) | 7 | 79 |
| Midazolam 5ml (1mg/ml) | 20 | 0 |
| Midazolam 10ml (5mg/ml) | 2 | 80 |
| Morfina 1ml (10mg/ml) | 10 | 90 |
| Nitroglicerina 5ml (5mg/ml) | 2 | 240 |
| Nitroprussiato 2ml (25mg/ml) | 1 | 248 |
| Norepinefrina 4ml (1mg/ml) | 4 | 234 |
| Norepinefrina 4ml (2mg/ml) | 2 | 242 |
| Remifentanil 2mg/5mg (Pó) | 1 | 50 |
| Rocurônio 5ml (10mg/ml) | 2 | 90 |
| Vasopressina 1ml (20UI/ml) | 1 | 99 |
| Cetamina 2ml (50mg/ml) | 5 | 40 |
| Terbutalina 1ml (0,5mg/ml) | 1 | 49 |
| Octreotida 1ml (0,1mg/ml) | 5 | 95 |

---

## ⚠️ IMPORTANTE: O app usa APENAS Google Sheets

Todos os dados de infusão vêm exclusivamente da aba **DB_INFUSAO**. Use o script de sincronização para manter a planilha atualizada.
