"""
infusao_data.py -- dados estaticos de drogas de infusao continua.

Contém a lista _DADOS_INFUSAO_PADRAO usada por utils.sync_infusao_to_sheet().
Separado de utils.py para facilitar atualizacoes de medicamentos sem alterar
a logica de infraestrutura.
"""

_DADOS_INFUSAO_PADRAO = [
    {"nome_formatado": "Amiodarona 3ml (50mg/ml)", "mg_amp": 150.0, "vol_amp": 3.0, "dose_min": 0.0, "dose_max_hab": 0.0, "dose_max_tol": 0.0, "unidade": "mg/min", "qtd_amp_padrao": 2, "diluente_padrao": 244},
    {"nome_formatado": "Atracurio 2.5ml (10mg/ml)", "mg_amp": 25.0, "vol_amp": 2.5, "dose_min": 5.0, "dose_max_hab": 20.0, "dose_max_tol": 20.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 4, "diluente_padrao": 90},
    {"nome_formatado": "Atracurio 5ml (10mg/ml)", "mg_amp": 50.0, "vol_amp": 5.0, "dose_min": 5.0, "dose_max_hab": 20.0, "dose_max_tol": 20.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 2, "diluente_padrao": 90},
    {"nome_formatado": "Cisatracurio 5ml (2mg/ml)", "mg_amp": 10.0, "vol_amp": 5.0, "dose_min": 1.0, "dose_max_hab": 3.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 10, "diluente_padrao": 50},
    {"nome_formatado": "Dexmedetomidina 2ml (100mcg/ml)", "mg_amp": 0.2, "vol_amp": 2.0, "dose_min": 0.1, "dose_max_hab": 0.7, "dose_max_tol": 1.5, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 48},
    {"nome_formatado": "Dobutamina 20ml (12.5mg/ml)", "mg_amp": 250.0, "vol_amp": 20.0, "dose_min": 2.5, "dose_max_hab": 20.0, "dose_max_tol": 40.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 230},
    {"nome_formatado": "Dopamina 10ml (5mg/ml)", "mg_amp": 50.0, "vol_amp": 10.0, "dose_min": 5.0, "dose_max_hab": 20.0, "dose_max_tol": 50.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 5, "diluente_padrao": 200},
    {"nome_formatado": "Esmolol 10ml (10mg/ml)", "mg_amp": 100.0, "vol_amp": 10.0, "dose_min": 50.0, "dose_max_hab": 200.0, "dose_max_tol": 300.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Esmolol 250ml (10mg/ml)", "mg_amp": 2500.0, "vol_amp": 250.0, "dose_min": 50.0, "dose_max_hab": 200.0, "dose_max_tol": 300.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Fentanil 2ml (50mcg/ml)", "mg_amp": 0.1, "vol_amp": 2.0, "dose_min": 0.5, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Fentanil 5ml (50mcg/ml)", "mg_amp": 0.25, "vol_amp": 5.0, "dose_min": 0.5, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Fentanil 10ml (50mcg/ml)", "mg_amp": 0.5, "vol_amp": 10.0, "dose_min": 0.5, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/h", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Lidocaina 20ml (20mg/ml)", "mg_amp": 400.0, "vol_amp": 20.0, "dose_min": 1.0, "dose_max_hab": 4.0, "dose_max_tol": 4.0, "unidade": "mg/min", "qtd_amp_padrao": 2, "diluente_padrao": 210},
    {"nome_formatado": "Midazolam 3ml (5mg/ml)", "mg_amp": 15.0, "vol_amp": 3.0, "dose_min": 0.02, "dose_max_hab": 0.2, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 7, "diluente_padrao": 79},
    {"nome_formatado": "Midazolam 5ml (1mg/ml)", "mg_amp": 5.0, "vol_amp": 5.0, "dose_min": 0.02, "dose_max_hab": 0.2, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 20, "diluente_padrao": 0},
    {"nome_formatado": "Midazolam 10ml (5mg/ml)", "mg_amp": 50.0, "vol_amp": 10.0, "dose_min": 0.02, "dose_max_hab": 0.2, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 2, "diluente_padrao": 80},
    {"nome_formatado": "Morfina 1ml (10mg/ml)", "mg_amp": 10.0, "vol_amp": 1.0, "dose_min": 2.0, "dose_max_hab": 4.0, "dose_max_tol": 10.0, "unidade": "mg/h", "qtd_amp_padrao": 10, "diluente_padrao": 90},
    {"nome_formatado": "Nitroglicerina 5ml (5mg/ml)", "mg_amp": 25.0, "vol_amp": 5.0, "dose_min": 5.0, "dose_max_hab": 200.0, "dose_max_tol": 400.0, "unidade": "mcg/min", "qtd_amp_padrao": 2, "diluente_padrao": 240},
    {"nome_formatado": "Nitroprussiato 2ml (25mg/ml)", "mg_amp": 50.0, "vol_amp": 2.0, "dose_min": 0.25, "dose_max_hab": 5.0, "dose_max_tol": 10.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 248},
    {"nome_formatado": "Norepinefrina 4ml (1mg/ml)", "mg_amp": 4.0, "vol_amp": 4.0, "dose_min": 0.01, "dose_max_hab": 1.0, "dose_max_tol": 2.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 4, "diluente_padrao": 234},
    {"nome_formatado": "Norepinefrina 4ml (2mg/ml)", "mg_amp": 8.0, "vol_amp": 4.0, "dose_min": 0.01, "dose_max_hab": 1.0, "dose_max_tol": 2.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 2, "diluente_padrao": 242},
    {"nome_formatado": "Propofol 1% 20ml (10mg/ml)", "mg_amp": 200.0, "vol_amp": 20.0, "dose_min": 5.0, "dose_max_hab": 50.0, "dose_max_tol": 80.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Propofol 1% 50ml (10mg/ml)", "mg_amp": 500.0, "vol_amp": 50.0, "dose_min": 5.0, "dose_max_hab": 50.0, "dose_max_tol": 80.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Propofol 2% 50ml (20mg/ml)", "mg_amp": 1000.0, "vol_amp": 50.0, "dose_min": 5.0, "dose_max_hab": 50.0, "dose_max_tol": 80.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 0},
    {"nome_formatado": "Remifentanil 2mg (Po)", "mg_amp": 2.0, "vol_amp": 0.0, "dose_min": 0.01, "dose_max_hab": 0.5, "dose_max_tol": 1.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 50},
    {"nome_formatado": "Remifentanil 5mg (Po)", "mg_amp": 5.0, "vol_amp": 0.0, "dose_min": 0.01, "dose_max_hab": 0.5, "dose_max_tol": 1.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 50},
    {"nome_formatado": "Rocuronio 5ml (10mg/ml)", "mg_amp": 50.0, "vol_amp": 5.0, "dose_min": 3.0, "dose_max_hab": 12.0, "dose_max_tol": 16.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 2, "diluente_padrao": 90},
    {"nome_formatado": "Vasopressina 1ml (20UI/ml)", "mg_amp": 20.0, "vol_amp": 1.0, "dose_min": 0.01, "dose_max_hab": 0.04, "dose_max_tol": 0.06, "unidade": "UI/min", "qtd_amp_padrao": 1, "diluente_padrao": 99},
    {"nome_formatado": "Cetamina 2ml (50mg/ml)", "mg_amp": 100.0, "vol_amp": 2.0, "dose_min": 0.05, "dose_max_hab": 0.5, "dose_max_tol": 1.0, "unidade": "mg/kg/h", "qtd_amp_padrao": 5, "diluente_padrao": 40},
    {"nome_formatado": "Adrenalina 1ml (1mg/ml)", "mg_amp": 1.0, "vol_amp": 1.0, "dose_min": 0.01, "dose_max_hab": 1.0, "dose_max_tol": 2.0, "unidade": "mcg/kg/min", "qtd_amp_padrao": 4, "diluente_padrao": 246},
    {"nome_formatado": "Terbutalina 1ml (0.5mg/ml)", "mg_amp": 0.5, "vol_amp": 1.0, "dose_min": 0.1, "dose_max_hab": 0.4, "dose_max_tol": 0.6, "unidade": "mcg/kg/min", "qtd_amp_padrao": 1, "diluente_padrao": 49},
    {"nome_formatado": "Octreotida 1ml (0,1mg/ml)", "mg_amp": 0.1, "vol_amp": 1.0, "dose_min": 50.0, "dose_max_hab": 50.0, "dose_max_tol": 50.0, "unidade": "mcg/h", "qtd_amp_padrao": 5, "diluente_padrao": 95},
]
