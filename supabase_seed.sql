-- ============================================================
-- INTENSIVA CALCULATOR — Seed das tabelas de referência
-- Execute no SQL Editor do Supabase
-- ============================================================

-- ── Função merge_evolucao (MERGE seguro de JSONB) ─────────────
-- Garante que um upsert parcial nunca apaga campos existentes.
-- Em vez de substituir dados, faz: dados_existentes || dados_novos
-- Execute este bloco uma vez no SQL Editor do Supabase:
CREATE OR REPLACE FUNCTION merge_evolucao(
    p_prontuario  text,
    p_nome        text,
    p_dados       jsonb,
    p_atualizado  timestamptz
) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO evolucoes (prontuario, nome, dados, atualizado)
    VALUES (p_prontuario, p_nome, p_dados, p_atualizado)
    ON CONFLICT (prontuario)
    DO UPDATE SET
        dados      = evolucoes.dados || EXCLUDED.dados,
        nome       = EXCLUDED.nome,
        atualizado = EXCLUDED.atualizado;
END;
$$;

-- ── Tabela DB_IOT (drogas de intubação) ──────────────────────
CREATE TABLE IF NOT EXISTS db_iot (
  id             BIGSERIAL PRIMARY KEY,
  nome_formatado TEXT    NOT NULL,
  conc           NUMERIC NOT NULL,
  dose_min       NUMERIC NOT NULL,
  dose_hab       NUMERIC NOT NULL,
  dose_max       NUMERIC NOT NULL
);

INSERT INTO db_iot (nome_formatado, conc, dose_min, dose_hab, dose_max) VALUES
  ('Midazolam 3ml (5mg/ml)',           5,   0.1,  0.2,  0.3),
  ('Midazolam 5ml (1mg/ml)',           1,   0.1,  0.2,  0.3),
  ('Midazolam 10ml (5mg/ml)',          5,   0.1,  0.2,  0.3),
  ('Propofol 10ml (10mg/ml)',          10,  1.0,  2.0,  3.0),
  ('Propofol 20ml (10mg/ml)',          10,  1.0,  2.0,  3.0),
  ('Propofol 50ml (10mg/ml)',          10,  1.0,  2.0,  3.0),
  ('Propofol 50ml (20mg/ml)',          20,  1.0,  2.0,  3.0),
  ('Escetamina 2ml (50mg/ml)',         50,  1.0,  1.5,  2.0),
  ('Etomidato 10ml (2mg/ml)',          2,   0.2,  0.3,  0.3),
  ('Fentanil 2ml (50mcg/ml)',          50,  1.0,  2.0,  3.0),
  ('Fentanil 5ml (50mcg/ml)',          50,  1.0,  2.0,  3.0),
  ('Fentanil 10ml (50mcg/ml)',         50,  1.0,  2.0,  3.0),
  ('Remifentanil 2mg (20mcg/ml)',      20,  1.5,  1.5,  1.5),
  ('Remifentanil 5mg (50mcg/ml)',      50,  1.5,  1.5,  1.5),
  ('Rocurônio 5ml (10mg/ml)',          10,  1.0,  1.2,  1.5),
  ('Atracúrio 5ml (10mg/ml)',          10,  0.5,  0.6,  0.6),
  ('Cisatracúrio 5ml (2mg/ml)',        2,   0.15, 0.2,  0.2),
  ('Cisatracúrio 10ml (2mg/ml)',       2,   0.15, 0.2,  0.2),
  ('Succinilcolina 100mg (10mg/ml)',   10,  0.6,  1.0,  1.5),
  ('Succinilcolina 500mg (50mg/ml)',   50,  0.6,  1.0,  1.5),
  ('Lidocaína 1,8ml (20mg/ml)',        20,  1.5,  1.5,  1.5),
  ('Lidocaína 5ml (20mg/ml)',          20,  1.5,  1.5,  1.5),
  ('Lidocaína 20ml (20mg/ml)',         20,  1.5,  1.5,  1.5);


-- ── Tabela DB_INFUSAO (drogas de infusão contínua) ───────────
CREATE TABLE IF NOT EXISTS db_infusao (
  id               BIGSERIAL PRIMARY KEY,
  nome_formatado   TEXT    NOT NULL,
  mg_amp           NUMERIC NOT NULL,
  vol_amp          NUMERIC NOT NULL,
  dose_min         NUMERIC NOT NULL,
  dose_max_hab     NUMERIC NOT NULL,
  dose_max_tol     NUMERIC NOT NULL,
  unidade          TEXT    NOT NULL,
  qtd_amp_padrao   INTEGER NOT NULL,
  diluente_padrao  INTEGER NOT NULL
);

INSERT INTO db_infusao (nome_formatado, mg_amp, vol_amp, dose_min, dose_max_hab, dose_max_tol, unidade, qtd_amp_padrao, diluente_padrao) VALUES
  ('Atracúrio 2.5ml (10mg/ml)',           25,    2.5,  5,     20,   20,   'mcg/kg/min',4,   90),
  ('Atracúrio 5ml (10mg/ml)',             50,    5,    5,     20,   20,   'mcg/kg/min',2,   90),
  ('Cisatracúrio 5ml (2mg/ml)',           10,    5,    1,     3,    10,   'mcg/kg/min',10, 100),
  ('Dexmedetomidina 2ml (100mcg/ml)',     0.2,   2,    0.1,   0.7,  1.5,  'mcg/kg/h',  2,   96),
  ('Dobutamina 20ml (12.5mg/ml)',         250,   20,   2.5,   20,   40,   'mcg/kg/min',1,  230),
  ('Dopamina 10ml (5mg/ml)',              50,    10,   5,     20,   50,   'mcg/kg/min',5,  200),
  ('Esmolol 10ml (10mg/ml)',              100,   10,   50,    200,  300,  'mcg/kg/min',1,    0),
  ('Esmolol 250ml (10mg/ml)',             2500,  250,  50,    200,  300,  'mcg/kg/min',1,    0),
  ('Fentanil 2ml (50mcg/ml)',             0.1,   2,    0.5,   5,    10,   'mcg/kg/h',  1,    0),
  ('Fentanil 5ml (50mcg/ml)',             0.25,  5,    0.5,   5,    10,   'mcg/kg/h',  1,    0),
  ('Fentanil 10ml (50mcg/ml)',            0.5,   10,   0.5,   5,    10,   'mcg/kg/h',  1,    0),
  ('Lidocaína 20ml (20mg/ml)',            400,   20,   1,     4,    4,    'mg/min',    2,  210),
  ('Midazolam 3ml (5mg/ml)',              15,    3,    0.02,  0.2,  1,    'mg/kg/h',   7,   79),
  ('Midazolam 5ml (1mg/ml)',              5,     5,    0.02,  0.2,  1,    'mg/kg/h',   20,   0),
  ('Midazolam 10ml (5mg/ml)',             50,    10,   0.02,  0.2,  1,    'mg/kg/h',   2,   80),
  ('Morfina 1ml (10mg/ml)',               10,    1,    2,     4,    10,   'mg/h',      10,  90),
  ('Nitroglicerina 5ml (5mg/ml)',         25,    5,    5,     200,  400,  'mcg/min',   2,  240),
  ('Nitroprussiato 2ml (25mg/ml)',        50,    2,    0.25,  5,    10,   'mcg/kg/min',1,  248),
  ('Norepinefrina 4ml (1mg/ml)',          4,     4,    0.01,  1,    2,    'mcg/kg/min',4,  234),
  ('Norepinefrina 4ml (2mg/ml)',          8,     4,    0.01,  1,    2,    'mcg/kg/min',2,  242),
  ('Propofol 1% 20ml (10mg/ml)',          200,   20,   5,     50,   80,   'mcg/kg/min',1,    0),
  ('Propofol 1% 50ml (10mg/ml)',          500,   50,   5,     50,   80,   'mcg/kg/min',1,    0),
  ('Propofol 2% 50ml (20mg/ml)',          1000,  50,   5,     50,   80,   'mcg/kg/min',1,    0),
  ('Remifentanil 2mg (Pó)',               2,     0,    0.01,  0.5,  1,    'mcg/kg/min',1,  100),
  ('Remifentanil 5mg (Pó)',               5,     0,    0.01,  0.5,  1,    'mcg/kg/min',1,  100),
  ('Rocurônio 5ml (10mg/ml)',             50,    5,    3,     12,   16,   'mcg/kg/min',2,   90),
  ('Vasopressina 1ml (20UI/ml)',          20,    1,    0.01,  0.04, 0.06, 'UI/min',    1,   99),
  ('Cetamina 2ml (50mg/ml)',              100,   2,    0.05,  0.5,  1,    'mg/kg/h',   5,   90),
  ('Adrenalina 1ml (1mg/ml)',             1,     1,    0.01,  1,    2,    'mcg/kg/min',4,  246),
  ('Terbutalina 1ml (0.5mg/ml)',          0.5,   1,    0.1,   0.4,  0.6,  'mcg/kg/min',5,   95),
  ('Octreotida 1ml (0,1mg/ml)',           0.1,   1,    50,    50,   50,   'mcg/h',     5,   95);
