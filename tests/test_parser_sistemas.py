"""
Testes unitarios para modules/parsers/sistemas.py
"""
import pytest
from modules.parsers.sistemas import (
    parse_sistemas_deterministico,
    _parse_neuro,
    _parse_resp,
    _parse_cardio,
    _parse_renal,
    _parse_infec,
    _parse_hemato,
    _parse_pele,
    _extrair_secao,
)


TEXTO_COMPLETO = """
# Evolucao por sistemas
- Neurologico
ECG 15 | RASS -2
CAM-ICU: Negativo
Pupilas: Normais, simetricas, fotoreagentes
Sem deficit focal

- Respiratorio
EF: MV+ bilateral
Ventilacao Mecanica; PSV, Pressao 8, FiO2 35%, PEEP 5

- Cardiovascular
FC 82 | PAM 78 mmHg
Exame Cardiologico: 2BNRF, nao ausculto sopros
Perfusao: Normal, TEC: 2 seg
fluidotolerante

- Renal
Diurese 1800 mL | BH +350 mL
Cr: 2.8 - 2.5 - 2.1
Em TRS, Cateter femoral D

- Infeccioso
Febre: Ausente
Isolamento: Contato
Patogenos: Klebsiella pneumoniae

- Hematologico
Anticoagulacao: Profilatica
Sem sangramento

- Pele
Edema presente, 1+
Sem LPP
"""


class TestExtrairSecao:
    def test_extrai_neurologico(self):
        bloco = _extrair_secao(TEXTO_COMPLETO, "Neurologico")
        assert "ECG 15" in bloco

    def test_extrai_renal(self):
        bloco = _extrair_secao(TEXTO_COMPLETO, "Renal")
        assert "Diurese" in bloco

    def test_secao_inexistente_retorna_string_vazia(self):
        bloco = _extrair_secao(TEXTO_COMPLETO, "Inexistente")
        assert bloco == ""


class TestParseNeuro:
    def test_ecg(self):
        result = _parse_neuro("ECG 15 | RASS -2")
        assert result.get("sis_neuro_ecg") == "15"

    def test_rass_negativo(self):
        result = _parse_neuro("ECG 15 | RASS -2")
        assert result.get("sis_neuro_rass") == "-2"

    def test_cam_icu_negativo(self):
        result = _parse_neuro("CAM-ICU: Negativo")
        assert result.get("sis_neuro_cam_icu") == "Negativo"

    def test_sem_deficit_focal(self):
        result = _parse_neuro("Sem deficit focal")
        assert result.get("sis_neuro_deficits_ausente") == "Ausente"


class TestParseResp:
    def test_ausculta(self):
        result = _parse_resp("EF: MV+ bilateral")
        assert result.get("sis_resp_ausculta") == "MV+ bilateral"

    def test_vm_detectada(self):
        result = _parse_resp("Ventilacao Mecanica; PSV, Pressao 8, FiO2 35%, PEEP 5")
        assert result.get("sis_resp_modo") == "Ventilacao Mecanica"
        assert result.get("sis_resp_modo_vent") == "PSV"
        assert result.get("sis_resp_peep") == "5"
        assert result.get("sis_resp_fio2") == "35"


class TestParseCardio:
    def test_fc_e_pam(self):
        result = _parse_cardio("FC 82 bpm, PAM 78 mmHg")
        assert result.get("sis_cardio_fc") == "82"
        assert result.get("sis_cardio_pam") == "78"

    def test_perfusao_normal(self):
        result = _parse_cardio("Perfusao: Normal, TEC: 2 seg")
        assert result.get("sis_cardio_perfusao") == "Normal"

    def test_fluido_tolerante(self):
        result = _parse_cardio("fluidotolerante")
        assert result.get("sis_cardio_fluido_tolerante") == "Sim"


class TestParseRenal:
    def test_diurese_e_bh(self):
        result = _parse_renal("Diurese 1800 mL | BH +350 mL")
        assert "1800" in result.get("sis_renal_diurese", "")

    def test_trs(self):
        result = _parse_renal("Em TRS, Cateter femoral D")
        assert result.get("sis_renal_trs") == "Sim"

    def test_cr_evolucao(self):
        result = _parse_renal("Cr: 2.8 - 2.5 - 2.1")
        assert result.get("sis_renal_cr_antepen") == "2.8"
        assert result.get("sis_renal_cr_ult") == "2.5"
        assert result.get("sis_renal_cr_hoje") == "2.1"


class TestParseHemato:
    def test_anticoagulacao(self):
        result = _parse_hemato("Anticoagulacao: Profilatica")
        assert result.get("sis_hemato_anticoag") == "Sim"

    def test_sem_sangramento(self):
        result = _parse_hemato("Sem sangramento")
        assert result.get("sis_hemato_sangramento") == "Nao"


class TestParsePele:
    def test_edema_presente(self):
        result = _parse_pele("Edema presente, 1+")
        assert result.get("sis_pele_edema") == "Presente"
        assert result.get("sis_pele_edema_cruzes") == "1"

    def test_sem_lpp(self):
        result = _parse_pele("Sem LPP")
        assert result.get("sis_pele_lpp") == "Nao"


class TestParseSistemasDeterministico:
    def test_parse_texto_completo(self):
        result = parse_sistemas_deterministico(TEXTO_COMPLETO)
        assert result.get("sis_neuro_ecg") == "15"
        assert result.get("sis_renal_trs") == "Sim"
        assert result.get("sis_pele_lpp") == "Nao"

    def test_texto_vazio_retorna_dict_vazio(self):
        result = parse_sistemas_deterministico("")
        assert result == {}
