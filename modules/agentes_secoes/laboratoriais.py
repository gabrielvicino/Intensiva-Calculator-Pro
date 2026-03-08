from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 10: LABORATORIAIS
# ==============================================================================
_PROMPT_LABORATORIAIS = """# CONTEXTO
Você é um extrator estruturado de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o texto fornecido na tag <TEXTO_ALVO> e extrair os valores laboratoriais e gasométricos. Você deve preencher EXCLUSIVAMENTE três blocos:
- lab_1: conjunto de exames mais recente (pela data).
- lab_2: conjunto de exames imediatamente anterior (se disponível).
- lab_3: conjunto de exames terceiro mais recente (se disponível).

# REGRAS DE EXTRAÇÃO E PASSO A PASSO
1. ESTRUTURA PLANA: Preencha o JSON sequencialmente. Não utilize arrays ou listas aninhadas.
2. PREENCHIMENTO VAZIO: Se não houver exames suficientes para preencher os 3 blocos, retorne estritamente `""` (string vazia) para todos os campos dos blocos não utilizados. Não use `null` em hipótese alguma.
3. FIDELIDADE DOS DADOS: Mantenha o formato original das datas (DD/MM/AAAA ou DD/MM). Não calcule médias, não interprete valores, não infira unidades e não reorganize valores entre datas diferentes.
4. CONDUTAS E NOTAS: Os campos de conduta e notas laboratoriais são de entrada manual do médico. A IA deve preenchê-los SEMPRE com `""`.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem blocos de código markdown ao redor.

# REGRAS DE MAPEAMENTO CLÍNICO
- HEMOGRAMA: `lab_X_leuco` recebe APENAS o total de leucócitos (Ex: "12500" ou "12.500"). O diferencial leucocitário vai em campos separados com "%" no valor: `leuco_bla` (Blastos), `leuco_mie` (Mielócitos), `leuco_meta` (Metamielócitos), `leuco_bast` (Bastões/Bastonetes), `leuco_seg` (Segmentados/Neutrófilos), `leuco_linf` (Linfócitos), `leuco_mon` (Monócitos), `leuco_eos` (Eosinófilos), `leuco_bas` (Basófilos). Se algum componente não constar no laudo, deixe "". Ex: leuco_bast="6%", leuco_seg="84%", leuco_linf="8%".
- LACTATO: Se o lactato aparecer DENTRO de uma gasometria (gás), coloque em `lab_X_gas_lac`. Se aparecer como exame sérico isolado (pedido separado, "Lactato sérico", "Lac", "Lac venoso/arterial" fora do bloco de gasometria), coloque em `lab_X_lac`. Se aparecer nas duas fontes, preencha ambos os campos.
- RENAL E ELETRÓLITOS:
  - CaT (Cálcio Total) e CaI (Cálcio Iônico) são campos distintos.
  - O Cálcio Iônico extraído da gasometria deve ir OBRIGATORIAMENTE para a chave `cai` ou `gas_cai`, NUNCA para `cat`.
- HEPÁTICO:
  - Se o texto mostrar "BT 1,0 (0,3)", separe: `bt` = "1,0" e `bd` = "0,3".
- COAGULAÇÃO: Manter strings literais. Ex: `tp` = "14,2s (1,10)" ou "Ativ 60% (RNI 1,5)"; `ttpa` = "30,0s (1,00)".
- GASOMETRIA (até 3 entradas, da mais recente para a mais antiga → gas_, gas2_, gas3_):
  PASSO A — Identifique TODAS as gasometrias do mesmo dia com seus horários.
  PASSO B — Regra de agrupamento por par Arterial + Venosa:
    · Diferença de horário < 2h  → PAREADA: uma entrada. `gas_tipo`="Pareada". Campos arteriais + `gasv_pco2` e `svo2` da venosa.
    · Diferença de horário ≥ 2h  → SEPARADAS: cada uma é entrada independente. Venosa completa (sem pO2; SatO2 → svo2).
    · Mesmo tipo (ex: 2 arteriais) → sempre entradas independentes.
  PASSO C — Ordene da mais recente para a mais antiga e distribua:
    · 1ª (mais recente) → `gas_*` / `gasv_pco2` / `svo2`
    · 2ª               → `gas2_*` / `gas2v_pco2` / `gas2_svo2`
    · 3ª (mais antiga)  → `gas3_*` / `gas3v_pco2` / `gas3_svo2`
    · Se houver apenas 1: preencha só `gas_*`. Se houver 2: `gas_*` e `gas2_*`. Se houver 3: todas.
  REGRAS DE TIPO:
    · Explicitamente "arterial" → "Arterial"; explicitamente "venosa" → "Venosa".
    · Se houver pO2 (paO2) → "Arterial".
    · SatO2 > 82% → "Arterial" (em `gas_sat`); SatO2 ≤ 82% → "Venosa" (valor para `svo2`/`gas2_svo2`/`gas3_svo2`, `sat` vazio).
    · `gas_tipo` / `gas2_tipo` / `gas3_tipo` aceita: "Arterial", "Venosa" ou "Pareada".
  HORA: `gas_hora` / `gas2_hora` / `gas3_hora`: horas cheias, formato "HHh" (ex: "16h", "06h").
    · Busque em "Recebimento material:", "Data da coleta" ou similar. Se pareada, use a hora da arterial.
- OUTROS / NÃO TRANSCRITOS: Identifique TODOS os exames/testes laboratoriais presentes no texto. Liste em `lab_1_outros` os que NÃO pertencem a nenhuma dessas categorias já cobertas: Hemograma (Hb, Ht, VCM, HCM, RDW, Leucócitos, Plaquetas), Renal/Eletrólitos (Cr, Ur, Na, K, Mg, Pi, CaT, CaI), Hepático/Pancreático (TGP, TGO, FAL, GGT, BT, BD, ProtTot, Alb, LDH, Amil, Lipas), Cardio/Coag/Inflamação (CPK, CK-MB, BNP, Trop, PCR, VHS, TP, TTPa, Fibrin), Urina EAS (Densidade, Leucocitária, Nitrito, Leucócitos, Hemácias, Proteína, Cetona, Glicose), Gasometria (pH, pCO2, pO2, HCO3, BE, SatO2, SvO2, Lactato, AG, Cl). Exemplos de exames que vão para `outros`: TSH, T4 Livre, T4 Total, Ferritina, Ferro Sérico, TIBC, Cortisol, PTH, Vitamina B12, Folato, HbA1c, Ácido Úrico, Vancomicina (nível), Tacrolimus, Amicacina (nível), Procalcitonina, Galactomanana, Beta-D-Glucana, HIV, HTLV, sorologias, PCR quantitativo, tipagem sanguínea, etc. Formato de saída: "Nome Valor | Nome Valor". Se não houver nenhum exame fora das categorias acima, deixe `lab_1_outros` vazio.

# ENTRADAS
<TEXTO_ALVO>
[O texto com os exames laboratoriais será fornecido pelo usuário aqui]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON, gerando-as nesta exata ordem:

# --- NOTAS GERAIS ---
- laboratoriais_notas (string): "".

# --- BLOCO LAB 1 (EXAMES MAIS RECENTES) ---
- lab_1_data (string): Data do conjunto mais recente.
- lab_1_hb (string): Hemoglobina.
- lab_1_ht (string): Hematócrito.
- lab_1_vcm (string): VCM.
- lab_1_hcm (string): HCM.
- lab_1_rdw (string): RDW.
- lab_1_leuco (string): Leucócitos — APENAS o total (Ex: "12500"). NÃO inclua o diferencial aqui.
- lab_1_leuco_bla (string): Diferencial — Blastos (Ex: "2%"). Vazio se ausente.
- lab_1_leuco_mie (string): Diferencial — Mielócitos (Ex: "1%"). Vazio se ausente.
- lab_1_leuco_meta (string): Diferencial — Metamielócitos (Ex: "1%"). Vazio se ausente.
- lab_1_leuco_bast (string): Diferencial — Bastões/Bastonetes (Ex: "8%"). Vazio se ausente.
- lab_1_leuco_seg (string): Diferencial — Segmentados/Neutrófilos (Ex: "68%"). Vazio se ausente.
- lab_1_leuco_linf (string): Diferencial — Linfócitos (Ex: "15%"). Vazio se ausente.
- lab_1_leuco_mon (string): Diferencial — Monócitos (Ex: "5%"). Vazio se ausente.
- lab_1_leuco_eos (string): Diferencial — Eosinófilos (Ex: "1%"). Vazio se ausente.
- lab_1_leuco_bas (string): Diferencial — Basófilos (Ex: "0%"). Vazio se ausente.
- lab_1_plaq (string): Plaquetas.
- lab_1_cr (string): Creatinina.
- lab_1_ur (string): Ureia.
- lab_1_na (string): Sódio.
- lab_1_k (string): Potássio.
- lab_1_mg (string): Magnésio.
- lab_1_pi (string): Fósforo.
- lab_1_cat (string): Cálcio Total.
- lab_1_cai (string): Cálcio Iônico (sérico).
- lab_1_tgp (string): TGP / ALT.
- lab_1_tgo (string): TGO / AST.
- lab_1_fal (string): Fosfatase Alcalina.
- lab_1_ggt (string): GGT.
- lab_1_bt (string): Bilirrubina Total.
- lab_1_bd (string): Bilirrubina Direta.
- lab_1_prot_tot (string): Proteínas Totais.
- lab_1_alb (string): Albumina.
- lab_1_ldh (string): LDH (Lactato Desidrogenase).
- lab_1_amil (string): Amilase.
- lab_1_lipas (string): Lipase.
- lab_1_cpk (string): CPK.
- lab_1_cpk_mb (string): CK-MB.
- lab_1_bnp (string): BNP / NT-proBNP.
- lab_1_trop (string): Troponina.
- lab_1_pcr (string): PCR.
- lab_1_vhs (string): VHS.
- lab_1_lac (string): Lactato SÉRICO isolado (coleta venosa/arterial fora da gasometria). Se o lactato vier da gasometria, use lab_1_gas_lac (não preencha aqui). Se vier de ambas as fontes, preencha as duas.
- lab_1_tp (string): Tempo de Protrombina (TAP / RNI).
- lab_1_ttpa (string): Tempo de Tromboplastina Parcial ativada.
- lab_1_fbrn (string): Fibrinogênio.
- lab_1_gas_tipo (string): "Arterial", "Venosa", "Pareada" ou "".
- lab_1_gas_hora (string): Hora da coleta da gasometria (horas cheias, formato "HHh", ex: "16h").
- lab_1_gas_ph (string): pH da gasometria principal.
- lab_1_gas_pco2 (string): pCO2 da gasometria principal.
- lab_1_gas_po2 (string): pO2.
- lab_1_gas_hco3 (string): HCO3.
- lab_1_gas_be (string): Base Excess.
- lab_1_gas_sat (string): SatO2.
- lab_1_gas_lac (string): Lactato.
- lab_1_gas_ag (string): Anion Gap.
- lab_1_gas_cl (string): Cloreto da gasometria.
- lab_1_gas_na (string): Sódio da gasometria.
- lab_1_gas_k (string): Potássio da gasometria.
- lab_1_gas_cai (string): Cálcio Iônico da gasometria.
- lab_1_gasv_pco2 (string): pCO2 venoso (se gasometria pareada).
- lab_1_svo2 (string): SvO2 (se gasometria pareada).
- lab_1_gas2_tipo (string): "Arterial", "Venosa", "Pareada" ou "" (2ª gasometria mais recente do mesmo dia).
- lab_1_gas2_hora (string): Hora da 2ª gasometria (HHh).
- lab_1_gas2_ph (string): pH.
- lab_1_gas2_pco2 (string): pCO2.
- lab_1_gas2_po2 (string): pO2.
- lab_1_gas2_hco3 (string): HCO3.
- lab_1_gas2_be (string): Base Excess.
- lab_1_gas2_sat (string): SatO2.
- lab_1_gas2_lac (string): Lactato.
- lab_1_gas2_ag (string): Anion Gap.
- lab_1_gas2_cl (string): Cloreto.
- lab_1_gas2_na (string): Sódio.
- lab_1_gas2_k (string): Potássio.
- lab_1_gas2_cai (string): Cálcio Iônico.
- lab_1_gas2v_pco2 (string): pCO2 venoso (se 2ª gasometria for pareada).
- lab_1_gas2_svo2 (string): SvO2 (se 2ª gasometria for pareada ou venosa).
- lab_1_gas3_tipo (string): "Arterial", "Venosa", "Pareada" ou "" (3ª gasometria mais recente do mesmo dia).
- lab_1_gas3_hora (string): Hora da 3ª gasometria (HHh).
- lab_1_gas3_ph (string): pH.
- lab_1_gas3_pco2 (string): pCO2.
- lab_1_gas3_po2 (string): pO2.
- lab_1_gas3_hco3 (string): HCO3.
- lab_1_gas3_be (string): Base Excess.
- lab_1_gas3_sat (string): SatO2.
- lab_1_gas3_lac (string): Lactato.
- lab_1_gas3_ag (string): Anion Gap.
- lab_1_gas3_cl (string): Cloreto.
- lab_1_gas3_na (string): Sódio.
- lab_1_gas3_k (string): Potássio.
- lab_1_gas3_cai (string): Cálcio Iônico.
- lab_1_gas3v_pco2 (string): pCO2 venoso (se 3ª gasometria for pareada).
- lab_1_gas3_svo2 (string): SvO2 (se 3ª gasometria for pareada ou venosa).
- lab_1_ur_dens (string): Urina - Densidade.
- lab_1_ur_le (string): Urina - Esterase Leucocitária.
- lab_1_ur_nit (string): Urina - Nitrito.
- lab_1_ur_leu (string): Urina - Leucócitos.
- lab_1_ur_hm (string): Urina - Hemácias.
- lab_1_ur_prot (string): Urina - Proteínas.
- lab_1_ur_cet (string): Urina - Cetonas.
- lab_1_ur_glic (string): Urina - Glicose.
- lab_1_outros (string): Exames presentes no texto que NÃO estão nas categorias padrão (ver regra OUTROS acima). Formato: "Nome Valor | Nome Valor". Ex: "TSH 0,4 | Ferritina 120 | HbA1c 8,2%".
- lab_1_conduta (string): "".

# --- BLOCO LAB 2 (EXAMES ANTERIORES) ---
- lab_2_data (string): Data do conjunto anterior.
- lab_2_hb (string): Hemoglobina.
- lab_2_ht (string): Hematócrito.
- lab_2_vcm (string): VCM.
- lab_2_hcm (string): HCM.
- lab_2_rdw (string): RDW.
- lab_2_leuco (string): Leucócitos — APENAS o total (Ex: "12500"). NÃO inclua o diferencial aqui.
- lab_2_leuco_bla (string): Diferencial — Blastos. Vazio se ausente.
- lab_2_leuco_mie (string): Diferencial — Mielócitos. Vazio se ausente.
- lab_2_leuco_meta (string): Diferencial — Metamielócitos. Vazio se ausente.
- lab_2_leuco_bast (string): Diferencial — Bastões/Bastonetes. Vazio se ausente.
- lab_2_leuco_seg (string): Diferencial — Segmentados/Neutrófilos. Vazio se ausente.
- lab_2_leuco_linf (string): Diferencial — Linfócitos. Vazio se ausente.
- lab_2_leuco_mon (string): Diferencial — Monócitos. Vazio se ausente.
- lab_2_leuco_eos (string): Diferencial — Eosinófilos. Vazio se ausente.
- lab_2_leuco_bas (string): Diferencial — Basófilos. Vazio se ausente.
- lab_2_plaq (string): Plaquetas.
- lab_2_cr (string): Creatinina.
- lab_2_ur (string): Ureia.
- lab_2_na (string): Sódio.
- lab_2_k (string): Potássio.
- lab_2_mg (string): Magnésio.
- lab_2_pi (string): Fósforo.
- lab_2_cat (string): Cálcio Total.
- lab_2_cai (string): Cálcio Iônico (sérico).
- lab_2_tgp (string): TGP / ALT.
- lab_2_tgo (string): TGO / AST.
- lab_2_fal (string): Fosfatase Alcalina.
- lab_2_ggt (string): GGT.
- lab_2_bt (string): Bilirrubina Total.
- lab_2_bd (string): Bilirrubina Direta.
- lab_2_prot_tot (string): Proteínas Totais.
- lab_2_alb (string): Albumina.
- lab_2_ldh (string): LDH (Lactato Desidrogenase).
- lab_2_amil (string): Amilase.
- lab_2_lipas (string): Lipase.
- lab_2_cpk (string): CPK.
- lab_2_cpk_mb (string): CK-MB.
- lab_2_bnp (string): BNP / NT-proBNP.
- lab_2_trop (string): Troponina.
- lab_2_pcr (string): PCR.
- lab_2_vhs (string): VHS.
- lab_2_lac (string): Lactato sérico isolado (fora da gasometria). Vazio se só existir no gás.
- lab_2_tp (string): Tempo de Protrombina (TAP / RNI).
- lab_2_ttpa (string): Tempo de Tromboplastina Parcial ativada.
- lab_2_fbrn (string): Fibrinogênio.
- lab_2_gas_tipo (string): "Arterial", "Venosa", "Pareada" ou "".
- lab_2_gas_hora (string): Hora da coleta da gasometria (horas cheias, formato "HHh", ex: "16h").
- lab_2_gas_ph (string): pH da gasometria principal.
- lab_2_gas_pco2 (string): pCO2 da gasometria principal.
- lab_2_gas_po2 (string): pO2.
- lab_2_gas_hco3 (string): HCO3.
- lab_2_gas_be (string): Base Excess.
- lab_2_gas_sat (string): SatO2.
- lab_2_gas_lac (string): Lactato.
- lab_2_gas_ag (string): Anion Gap.
- lab_2_gas_cl (string): Cloreto da gasometria.
- lab_2_gas_na (string): Sódio da gasometria.
- lab_2_gas_k (string): Potássio da gasometria.
- lab_2_gas_cai (string): Cálcio Iônico da gasometria.
- lab_2_gasv_pco2 (string): pCO2 venoso (se gasometria pareada).
- lab_2_svo2 (string): SvO2 (se gasometria pareada).
- lab_2_gas2_tipo (string): "Arterial", "Venosa", "Pareada" ou "" (2ª gasometria mais recente do mesmo dia).
- lab_2_gas2_hora (string): Hora da 2ª gasometria (HHh).
- lab_2_gas2_ph (string): pH.
- lab_2_gas2_pco2 (string): pCO2.
- lab_2_gas2_po2 (string): pO2.
- lab_2_gas2_hco3 (string): HCO3.
- lab_2_gas2_be (string): Base Excess.
- lab_2_gas2_sat (string): SatO2.
- lab_2_gas2_lac (string): Lactato.
- lab_2_gas2_ag (string): Anion Gap.
- lab_2_gas2_cl (string): Cloreto.
- lab_2_gas2_na (string): Sódio.
- lab_2_gas2_k (string): Potássio.
- lab_2_gas2_cai (string): Cálcio Iônico.
- lab_2_gas2v_pco2 (string): pCO2 venoso (se 2ª gasometria for pareada).
- lab_2_gas2_svo2 (string): SvO2 (se 2ª gasometria for pareada ou venosa).
- lab_2_gas3_tipo (string): "Arterial", "Venosa", "Pareada" ou "" (3ª gasometria mais recente do mesmo dia).
- lab_2_gas3_hora (string): Hora da 3ª gasometria (HHh).
- lab_2_gas3_ph (string): pH.
- lab_2_gas3_pco2 (string): pCO2.
- lab_2_gas3_po2 (string): pO2.
- lab_2_gas3_hco3 (string): HCO3.
- lab_2_gas3_be (string): Base Excess.
- lab_2_gas3_sat (string): SatO2.
- lab_2_gas3_lac (string): Lactato.
- lab_2_gas3_ag (string): Anion Gap.
- lab_2_gas3_cl (string): Cloreto.
- lab_2_gas3_na (string): Sódio.
- lab_2_gas3_k (string): Potássio.
- lab_2_gas3_cai (string): Cálcio Iônico.
- lab_2_gas3v_pco2 (string): pCO2 venoso (se 3ª gasometria for pareada).
- lab_2_gas3_svo2 (string): SvO2 (se 3ª gasometria for pareada ou venosa).
- lab_2_ur_dens (string): Urina - Densidade.
- lab_2_ur_le (string): Urina - Esterase Leucocitária.
- lab_2_ur_nit (string): Urina - Nitrito.
- lab_2_ur_leu (string): Urina - Leucócitos.
- lab_2_ur_hm (string): Urina - Hemácias.
- lab_2_ur_prot (string): Urina - Proteínas.
- lab_2_ur_cet (string): Urina - Cetonas.
- lab_2_ur_glic (string): Urina - Glicose.
- lab_2_outros (string): Outros exames concatenados.
- lab_2_conduta (string): "".

# --- BLOCO LAB 3 (EXAMES TERCEIRO MAIS RECENTES) ---
- lab_3_data (string): Data do 3º conjunto mais recente.
- lab_3_hb (string): Hemoglobina.
- lab_3_ht (string): Hematócrito.
- lab_3_vcm (string): VCM.
- lab_3_hcm (string): HCM.
- lab_3_rdw (string): RDW.
- lab_3_leuco (string): Leucócitos — APENAS o total (Ex: "12500"). NÃO inclua o diferencial aqui.
- lab_3_leuco_bla (string): Diferencial — Blastos. Vazio se ausente.
- lab_3_leuco_mie (string): Diferencial — Mielócitos. Vazio se ausente.
- lab_3_leuco_meta (string): Diferencial — Metamielócitos. Vazio se ausente.
- lab_3_leuco_bast (string): Diferencial — Bastões/Bastonetes. Vazio se ausente.
- lab_3_leuco_seg (string): Diferencial — Segmentados/Neutrófilos. Vazio se ausente.
- lab_3_leuco_linf (string): Diferencial — Linfócitos. Vazio se ausente.
- lab_3_leuco_mon (string): Diferencial — Monócitos. Vazio se ausente.
- lab_3_leuco_eos (string): Diferencial — Eosinófilos. Vazio se ausente.
- lab_3_leuco_bas (string): Diferencial — Basófilos. Vazio se ausente.
- lab_3_plaq (string): Plaquetas.
- lab_3_cr (string): Creatinina.
- lab_3_ur (string): Ureia.
- lab_3_na (string): Sódio.
- lab_3_k (string): Potássio.
- lab_3_mg (string): Magnésio.
- lab_3_pi (string): Fósforo.
- lab_3_cat (string): Cálcio Total.
- lab_3_cai (string): Cálcio Iônico (sérico).
- lab_3_tgp (string): TGP / ALT.
- lab_3_tgo (string): TGO / AST.
- lab_3_fal (string): Fosfatase Alcalina.
- lab_3_ggt (string): GGT.
- lab_3_bt (string): Bilirrubina Total.
- lab_3_bd (string): Bilirrubina Direta.
- lab_3_prot_tot (string): Proteínas Totais.
- lab_3_alb (string): Albumina.
- lab_3_ldh (string): LDH (Lactato Desidrogenase).
- lab_3_amil (string): Amilase.
- lab_3_lipas (string): Lipase.
- lab_3_cpk (string): CPK.
- lab_3_cpk_mb (string): CK-MB.
- lab_3_bnp (string): BNP / NT-proBNP.
- lab_3_trop (string): Troponina.
- lab_3_pcr (string): PCR.
- lab_3_vhs (string): VHS.
- lab_3_lac (string): Lactato sérico isolado (fora da gasometria). Vazio se só existir no gás.
- lab_3_tp (string): Tempo de Protrombina (TAP / RNI).
- lab_3_ttpa (string): Tempo de Tromboplastina Parcial ativada.
- lab_3_fbrn (string): Fibrinogênio.
- lab_3_gas_tipo (string): "Arterial", "Venosa", "Pareada" ou "".
- lab_3_gas_hora (string): Hora da coleta da gasometria (horas cheias, formato "HHh", ex: "16h").
- lab_3_gas_ph (string): pH da gasometria principal.
- lab_3_gas_pco2 (string): pCO2 da gasometria principal.
- lab_3_gas_po2 (string): pO2.
- lab_3_gas_hco3 (string): HCO3.
- lab_3_gas_be (string): Base Excess.
- lab_3_gas_sat (string): SatO2.
- lab_3_gas_lac (string): Lactato.
- lab_3_gas_ag (string): Anion Gap.
- lab_3_gas_cl (string): Cloreto da gasometria.
- lab_3_gas_na (string): Sódio da gasometria.
- lab_3_gas_k (string): Potássio da gasometria.
- lab_3_gas_cai (string): Cálcio Iônico da gasometria.
- lab_3_gasv_pco2 (string): pCO2 venoso (se gasometria pareada).
- lab_3_svo2 (string): SvO2 (se gasometria pareada).
- lab_3_gas2_tipo (string): "Arterial", "Venosa", "Pareada" ou "" (2ª gasometria mais recente do mesmo dia).
- lab_3_gas2_hora (string): Hora da 2ª gasometria (HHh).
- lab_3_gas2_ph (string): pH.
- lab_3_gas2_pco2 (string): pCO2.
- lab_3_gas2_po2 (string): pO2.
- lab_3_gas2_hco3 (string): HCO3.
- lab_3_gas2_be (string): Base Excess.
- lab_3_gas2_sat (string): SatO2.
- lab_3_gas2_lac (string): Lactato.
- lab_3_gas2_ag (string): Anion Gap.
- lab_3_gas2_cl (string): Cloreto.
- lab_3_gas2_na (string): Sódio.
- lab_3_gas2_k (string): Potássio.
- lab_3_gas2_cai (string): Cálcio Iônico.
- lab_3_gas2v_pco2 (string): pCO2 venoso (se 2ª gasometria for pareada).
- lab_3_gas2_svo2 (string): SvO2 (se 2ª gasometria for pareada ou venosa).
- lab_3_gas3_tipo (string): "Arterial", "Venosa", "Pareada" ou "" (3ª gasometria mais recente do mesmo dia).
- lab_3_gas3_hora (string): Hora da 3ª gasometria (HHh).
- lab_3_gas3_ph (string): pH.
- lab_3_gas3_pco2 (string): pCO2.
- lab_3_gas3_po2 (string): pO2.
- lab_3_gas3_hco3 (string): HCO3.
- lab_3_gas3_be (string): Base Excess.
- lab_3_gas3_sat (string): SatO2.
- lab_3_gas3_lac (string): Lactato.
- lab_3_gas3_ag (string): Anion Gap.
- lab_3_gas3_cl (string): Cloreto.
- lab_3_gas3_na (string): Sódio.
- lab_3_gas3_k (string): Potássio.
- lab_3_gas3_cai (string): Cálcio Iônico.
- lab_3_gas3v_pco2 (string): pCO2 venoso (se 3ª gasometria for pareada).
- lab_3_gas3_svo2 (string): SvO2 (se 3ª gasometria for pareada ou venosa).
- lab_3_ur_dens (string): Urina - Densidade.
- lab_3_ur_le (string): Urina - Esterase Leucocitária.
- lab_3_ur_nit (string): Urina - Nitrito.
- lab_3_ur_leu (string): Urina - Leucócitos.
- lab_3_ur_hm (string): Urina - Hemácias.
- lab_3_ur_prot (string): Urina - Proteínas.
- lab_3_ur_cet (string): Urina - Cetonas.
- lab_3_ur_glic (string): Urina - Glicose.
- lab_3_outros (string): Outros exames concatenados.
- lab_3_conduta (string): "".

# EXEMPLO DE SAÍDA PERFEITA
# (3 blocos: lab_1 = hoje, lab_2 = ontem, lab_3 = anteontem)
{
  "laboratoriais_notas": "",

  "lab_1_data": "04/03/2026",
  "lab_1_hb": "8.4",
  "lab_1_ht": "26",
  "lab_1_vcm": "88",
  "lab_1_hcm": "29",
  "lab_1_rdw": "15.2",
  "lab_1_leuco": "18200",
  "lab_1_leuco_bla": "",
  "lab_1_leuco_mie": "",
  "lab_1_leuco_meta": "",
  "lab_1_leuco_bast": "6%",
  "lab_1_leuco_seg": "84%",
  "lab_1_leuco_linf": "8%",
  "lab_1_leuco_mon": "2%",
  "lab_1_leuco_eos": "",
  "lab_1_leuco_bas": "",
  "lab_1_plaq": "98000",
  "lab_1_cr": "3.4",
  "lab_1_ur": "142",
  "lab_1_na": "138",
  "lab_1_k": "4.8",
  "lab_1_mg": "1.2",
  "lab_1_pi": "5.8",
  "lab_1_cat": "7.8",
  "lab_1_cai": "1.02",
  "lab_1_tgp": "68",
  "lab_1_tgo": "82",
  "lab_1_fal": "210",
  "lab_1_ggt": "195",
  "lab_1_bt": "2.1",
  "lab_1_bd": "1.4",
  "lab_1_prot_tot": "5.2",
  "lab_1_alb": "2.1",
  "lab_1_ldh": "480",
  "lab_1_amil": "",
  "lab_1_lipas": "",
  "lab_1_cpk": "320",
  "lab_1_cpk_mb": "",
  "lab_1_bnp": "1820",
  "lab_1_trop": "0.08",
  "lab_1_pcr": "188",
  "lab_1_vhs": "",
  "lab_1_lac": "",
  "lab_1_tp": "Ativ 52% (RNI 1.6)",
  "lab_1_ttpa": "42s (1.38)",
  "lab_1_fbrn": "320",
  "lab_1_gas_tipo": "Arterial",
  "lab_1_gas_hora": "6h",
  "lab_1_gas_ph": "7.30",
  "lab_1_gas_pco2": "38",
  "lab_1_gas_po2": "88",
  "lab_1_gas_hco3": "18.4",
  "lab_1_gas_be": "-7.2",
  "lab_1_gas_sat": "96",
  "lab_1_gas_lac": "3.8",
  "lab_1_gas_ag": "17.6",
  "lab_1_gas_cl": "106",
  "lab_1_gas_na": "139",
  "lab_1_gas_k": "4.9",
  "lab_1_gas_cai": "1.04",
  "lab_1_gasv_pco2": "",
  "lab_1_svo2": "",
  "lab_1_ur_dens": "",
  "lab_1_ur_le": "",
  "lab_1_ur_nit": "",
  "lab_1_ur_leu": "",
  "lab_1_ur_hm": "",
  "lab_1_ur_prot": "",
  "lab_1_ur_cet": "",
  "lab_1_ur_glic": "",
  "lab_1_outros": "TSH 0.4 | HbA1c 10.2%",
  "lab_1_conduta": "",

  "lab_2_data": "03/03/2026",
  "lab_2_hb": "9.1",
  "lab_2_ht": "28",
  "lab_2_vcm": "88",
  "lab_2_hcm": "29",
  "lab_2_rdw": "15.0",
  "lab_2_leuco": "22400",
  "lab_2_leuco_bla": "",
  "lab_2_leuco_mie": "",
  "lab_2_leuco_meta": "",
  "lab_2_leuco_bast": "8%",
  "lab_2_leuco_seg": "88%",
  "lab_2_leuco_linf": "",
  "lab_2_leuco_mon": "",
  "lab_2_leuco_eos": "",
  "lab_2_leuco_bas": "",
  "lab_2_plaq": "82000",
  "lab_2_cr": "3.1",
  "lab_2_ur": "128",
  "lab_2_na": "140",
  "lab_2_k": "5.2",
  "lab_2_mg": "",
  "lab_2_pi": "",
  "lab_2_cat": "",
  "lab_2_cai": "",
  "lab_2_tgp": "72",
  "lab_2_tgo": "91",
  "lab_2_fal": "",
  "lab_2_ggt": "",
  "lab_2_bt": "1.8",
  "lab_2_bd": "1.1",
  "lab_2_prot_tot": "",
  "lab_2_alb": "2.0",
  "lab_2_ldh": "",
  "lab_2_amil": "",
  "lab_2_lipas": "",
  "lab_2_cpk": "",
  "lab_2_cpk_mb": "",
  "lab_2_bnp": "",
  "lab_2_trop": "",
  "lab_2_pcr": "241",
  "lab_2_vhs": "",
  "lab_2_lac": "",
  "lab_2_tp": "Ativ 48% (RNI 1.8)",
  "lab_2_ttpa": "45s (1.48)",
  "lab_2_fbrn": "",
  "lab_2_gas_tipo": "Arterial",
  "lab_2_gas_hora": "8h",
  "lab_2_gas_ph": "7.26",
  "lab_2_gas_pco2": "35",
  "lab_2_gas_po2": "82",
  "lab_2_gas_hco3": "16.2",
  "lab_2_gas_be": "-9.8",
  "lab_2_gas_sat": "95",
  "lab_2_gas_lac": "5.2",
  "lab_2_gas_ag": "20.8",
  "lab_2_gas_cl": "108",
  "lab_2_gas_na": "140",
  "lab_2_gas_k": "5.1",
  "lab_2_gas_cai": "1.06",
  "lab_2_gasv_pco2": "",
  "lab_2_svo2": "",
  "lab_2_ur_dens": "1018",
  "lab_2_ur_le": "Positivo 3+",
  "lab_2_ur_nit": "Positivo",
  "lab_2_ur_leu": "82 p/campo",
  "lab_2_ur_hm": "12 p/campo",
  "lab_2_ur_prot": "Positivo 1+",
  "lab_2_ur_cet": "Negativo",
  "lab_2_ur_glic": "Negativo",
  "lab_2_outros": "",
  "lab_2_conduta": "",

  "lab_3_data": "02/03/2026",
  "lab_3_hb": "10.2",
  "lab_3_ht": "31",
  "lab_3_vcm": "87",
  "lab_3_hcm": "28",
  "lab_3_rdw": "14.8",
  "lab_3_leuco": "28600",
  "lab_3_leuco_bla": "",
  "lab_3_leuco_mie": "",
  "lab_3_leuco_meta": "",
  "lab_3_leuco_bast": "",
  "lab_3_leuco_seg": "90%",
  "lab_3_leuco_linf": "",
  "lab_3_leuco_mon": "",
  "lab_3_leuco_eos": "",
  "lab_3_leuco_bas": "",
  "lab_3_plaq": "68000",
  "lab_3_cr": "2.2",
  "lab_3_ur": "98",
  "lab_3_na": "142",
  "lab_3_k": "3.8",
  "lab_3_mg": "",
  "lab_3_pi": "",
  "lab_3_cat": "",
  "lab_3_cai": "",
  "lab_3_tgp": "",
  "lab_3_tgo": "",
  "lab_3_fal": "",
  "lab_3_ggt": "",
  "lab_3_bt": "",
  "lab_3_bd": "",
  "lab_3_prot_tot": "",
  "lab_3_alb": "",
  "lab_3_ldh": "",
  "lab_3_amil": "",
  "lab_3_lipas": "",
  "lab_3_cpk": "",
  "lab_3_cpk_mb": "",
  "lab_3_bnp": "",
  "lab_3_trop": "",
  "lab_3_pcr": "312",
  "lab_3_vhs": "",
  "lab_3_lac": "",
  "lab_3_tp": "",
  "lab_3_ttpa": "",
  "lab_3_fbrn": "",
  "lab_3_gas_tipo": "Arterial",
  "lab_3_gas_hora": "10h",
  "lab_3_gas_ph": "7.22",
  "lab_3_gas_pco2": "34",
  "lab_3_gas_po2": "76",
  "lab_3_gas_hco3": "14.1",
  "lab_3_gas_be": "-12.4",
  "lab_3_gas_sat": "92",
  "lab_3_gas_lac": "7.1",
  "lab_3_gas_ag": "24.9",
  "lab_3_gas_cl": "109",
  "lab_3_gas_na": "142",
  "lab_3_gas_k": "3.9",
  "lab_3_gas_cai": "1.10",
  "lab_3_gasv_pco2": "52",
  "lab_3_svo2": "68",
  "lab_3_ur_dens": "",
  "lab_3_ur_le": "",
  "lab_3_ur_nit": "",
  "lab_3_ur_leu": "",
  "lab_3_ur_hm": "",
  "lab_3_ur_prot": "",
  "lab_3_ur_cet": "",
  "lab_3_ur_glic": "",
  "lab_3_outros": "",
  "lab_3_conduta": ""
}
</VARIAVEIS>"""


def preencher_laboratoriais(texto, api_key, provider, modelo):
    if not texto or not str(texto).strip():
        return {"_erro": "Nenhum texto de exames fornecido. Cole os exames no campo de notas do Bloco 10."}
    r = _chamar_ia(_PROMPT_LABORATORIAIS, texto, api_key, provider, modelo, max_tokens=16000)
    if "_erro" in r:
        return r
    r.pop("_erro", None)

    # Normaliza e pós-processa gas1, gas2, gas3 em cada slot (i=1,2,3)
    # Para cada gasometria gn (1,2,3): prefixo "gas_" / "gas2_" / "gas3_"
    # chaves especiais gas1: gasv_pco2, svo2 (legado). gas2/3: gas2v_pco2, gas2_svo2, etc.
    for i in (1, 2, 3):
        for gn in (1, 2, 3):
            p      = "gas"  if gn == 1 else f"gas{gn}"
            k_tipo = f"lab_{i}_{p}_tipo"
            k_sat  = f"lab_{i}_{p}_sat"
            k_po2  = f"lab_{i}_{p}_po2"
            k_svo2 = f"lab_{i}_svo2"       if gn == 1 else f"lab_{i}_{p}_svo2"

            # Normaliza tipo vazio → None (compatível com st.pills)
            if k_tipo in r and r[k_tipo] in ("", None):
                r[k_tipo] = None

            # Se tipo já é válido e explícito (Pareada, Arterial, Venosa), não inferir
            tipo_atual = r.get(k_tipo)
            if tipo_atual not in ("Arterial", "Venosa", "Pareada"):
                # Infere tipo: pO2 → Arterial; SatO2 > 82% → Arterial; ≤ 82% → Venosa
                sat_raw = r.get(k_sat, "")
                po2_raw = r.get(k_po2, "")
                if po2_raw:
                    r[k_tipo] = "Arterial"
                elif sat_raw:
                    try:
                        sat_num = float(str(sat_raw).replace("%", "").strip())
                        if sat_num > 82:
                            r[k_tipo] = "Arterial"
                        else:
                            r[k_tipo] = "Venosa"
                            if not r.get(k_svo2):
                                r[k_svo2] = sat_raw
                            r[k_sat] = ""
                    except (ValueError, TypeError):
                        pass

            # Garante que SatO2 ≤ 82% em venosa seja movido para SvO2
            if r.get(k_tipo) == "Venosa":
                sat_raw = r.get(k_sat, "")
                if sat_raw:
                    try:
                        sat_num = float(str(sat_raw).replace("%", "").strip())
                        if sat_num <= 82 and not r.get(k_svo2):
                            r[k_svo2] = sat_raw
                            r[k_sat] = ""
                    except (ValueError, TypeError):
                        pass

    return r


# ==============================================================================
# AGENTE 10-SLOT: versão de 1 bloco para PACER (mais rápido, sem ambiguidade)
# ==============================================================================

_PROMPT_LAB_SLOT = """# CONTEXTO
Você é um extrator de dados médicos para prontuário hospitalar em Terapia Intensiva.

# OBJETIVO
Ler o laudo laboratorial fornecido e extrair os valores no JSON abaixo (apenas lab_1_*).
Preencha com string vazia ("") os campos não encontrados. Nunca use null.
A saída deve ser EXCLUSIVAMENTE um objeto JSON válido, sem markdown ao redor.

# REGRAS DE MAPEAMENTO CLÍNICO
- HEMOGRAMA: lab_1_leuco = APENAS o total (ex: "12500"). Diferencial vai nos campos leuco_bla/mie/meta/bast/seg/linf/mon/eos/bas com "%" (ex: leuco_seg="68%"). Campos ausentes → "".
- LACTATO: se vier de gasometria → lab_1_gas_lac. Se for sérico isolado → lab_1_lac. Se ambos, preencha os dois.
- CÁLCIO: lab_1_cat = Cálcio Total sérico. lab_1_cai = Cálcio Iônico sérico. lab_1_gas_cai = Cálcio Iônico da gasometria.
- COAGULAÇÃO: strings literais. Ex: lab_1_tp="Ativ 48% (RNI 1,52)"; lab_1_ttpa="33,10s (R: 1,18)".
- GASOMETRIA: gas_tipo = "Arterial", "Venosa" ou "Pareada". Se pO2 presente → Arterial. SatO2 ≤ 82% → Venosa (valor vai para svo2, sat fica ""). Hora no formato "HHh" (ex: "06h").
- OUTROS: lab_1_outros = exames NÃO cobertos pelas categorias padrão (Hemograma, Renal, Eletrólitos, Hepático, Cardio/Coag, Urina, Gasometria). Formato: "Nome Valor | Nome Valor". Ex: "TSH 0,4 | Ferritina 120".

<VARIAVEIS>
{
  "lab_1_data": "",
  "lab_1_hb": "", "lab_1_ht": "", "lab_1_vcm": "", "lab_1_hcm": "", "lab_1_rdw": "",
  "lab_1_leuco": "", "lab_1_leuco_bla": "", "lab_1_leuco_mie": "", "lab_1_leuco_meta": "",
  "lab_1_leuco_bast": "", "lab_1_leuco_seg": "", "lab_1_leuco_linf": "", "lab_1_leuco_mon": "",
  "lab_1_leuco_eos": "", "lab_1_leuco_bas": "", "lab_1_plaq": "",
  "lab_1_cr": "", "lab_1_ur": "", "lab_1_na": "", "lab_1_k": "", "lab_1_mg": "",
  "lab_1_pi": "", "lab_1_cat": "", "lab_1_cai": "",
  "lab_1_tgp": "", "lab_1_tgo": "", "lab_1_fal": "", "lab_1_ggt": "",
  "lab_1_bt": "", "lab_1_bd": "", "lab_1_prot_tot": "", "lab_1_alb": "",
  "lab_1_ldh": "", "lab_1_amil": "", "lab_1_lipas": "",
  "lab_1_cpk": "", "lab_1_cpk_mb": "", "lab_1_bnp": "", "lab_1_trop": "",
  "lab_1_pcr": "", "lab_1_vhs": "", "lab_1_lac": "",
  "lab_1_tp": "", "lab_1_ttpa": "", "lab_1_fbrn": "",
  "lab_1_gas_tipo": "", "lab_1_gas_hora": "",
  "lab_1_gas_ph": "", "lab_1_gas_pco2": "", "lab_1_gas_po2": "", "lab_1_gas_hco3": "",
  "lab_1_gas_be": "", "lab_1_gas_sat": "", "lab_1_gas_lac": "",
  "lab_1_gas_ag": "", "lab_1_gas_cl": "", "lab_1_gas_na": "", "lab_1_gas_k": "", "lab_1_gas_cai": "",
  "lab_1_gasv_pco2": "", "lab_1_svo2": "",
  "lab_1_gas2_tipo": "", "lab_1_gas2_hora": "",
  "lab_1_gas2_ph": "", "lab_1_gas2_pco2": "", "lab_1_gas2_po2": "", "lab_1_gas2_hco3": "",
  "lab_1_gas2_be": "", "lab_1_gas2_sat": "", "lab_1_gas2_lac": "",
  "lab_1_gas2_ag": "", "lab_1_gas2_cl": "", "lab_1_gas2_na": "", "lab_1_gas2_k": "", "lab_1_gas2_cai": "",
  "lab_1_gas2v_pco2": "", "lab_1_gas2_svo2": "",
  "lab_1_gas3_tipo": "", "lab_1_gas3_hora": "",
  "lab_1_gas3_ph": "", "lab_1_gas3_pco2": "", "lab_1_gas3_po2": "", "lab_1_gas3_hco3": "",
  "lab_1_gas3_be": "", "lab_1_gas3_sat": "", "lab_1_gas3_lac": "",
  "lab_1_gas3_ag": "", "lab_1_gas3_cl": "", "lab_1_gas3_na": "", "lab_1_gas3_k": "", "lab_1_gas3_cai": "",
  "lab_1_gas3v_pco2": "", "lab_1_gas3_svo2": "",
  "lab_1_ur_dens": "", "lab_1_ur_le": "", "lab_1_ur_nit": "", "lab_1_ur_leu": "",
  "lab_1_ur_hm": "", "lab_1_ur_prot": "", "lab_1_ur_cet": "", "lab_1_ur_glic": "",
  "lab_1_outros": ""
}
</VARIAVEIS>"""


def preencher_laboratoriais_slot(texto: str, api_key: str, provider: str, modelo: str) -> dict:
    """
    Versão de UM bloco do agente laboratoriais — usada pelo PACER (slot a slot).
    Mais rápida, sem ambiguidade, output muito menor que o prompt de 3 blocos.
    Retorna dict com chaves lab_1_* já com pós-processamento de gasometria.
    """
    if not texto or not str(texto).strip():
        return {"_erro": "Texto vazio."}
    r = _chamar_ia(_PROMPT_LAB_SLOT, texto, api_key, provider, modelo, max_tokens=4096)
    if "_erro" in r:
        return r
    r.pop("_erro", None)

    # Pós-processamento de gasometria (bloco 1 apenas)
    for gn in (1, 2, 3):
        p = "gas" if gn == 1 else f"gas{gn}"
        k_tipo = f"lab_1_{p}_tipo"
        k_sat  = f"lab_1_{p}_sat"
        k_po2  = f"lab_1_{p}_po2"
        k_svo2 = "lab_1_svo2" if gn == 1 else f"lab_1_{p}_svo2"

        if k_tipo in r and r[k_tipo] in ("", None):
            r[k_tipo] = None

        tipo_atual = r.get(k_tipo)
        if tipo_atual not in ("Arterial", "Venosa", "Pareada"):
            sat_raw = r.get(k_sat, "")
            po2_raw = r.get(k_po2, "")
            if po2_raw:
                r[k_tipo] = "Arterial"
            elif sat_raw:
                try:
                    sat_num = float(str(sat_raw).replace("%", "").strip())
                    if sat_num > 82:
                        r[k_tipo] = "Arterial"
                    else:
                        r[k_tipo] = "Venosa"
                        if not r.get(k_svo2):
                            r[k_svo2] = sat_raw
                        r[k_sat] = ""
                except (ValueError, TypeError):
                    pass

        if r.get(k_tipo) == "Venosa":
            sat_raw = r.get(k_sat, "")
            if sat_raw:
                try:
                    sat_num = float(str(sat_raw).replace("%", "").strip())
                    if sat_num <= 82 and not r.get(k_svo2):
                        r[k_svo2] = sat_raw
                        r[k_sat] = ""
                except (ValueError, TypeError):
                    pass

    return r
