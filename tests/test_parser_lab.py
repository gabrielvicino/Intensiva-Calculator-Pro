"""
Testes unitarios para modules/parsers/lab.py
"""
import pytest
from datetime import date
from modules.parsers.lab import parse_lab_deterministico, _extrair_par_sigla_valor, _parse_urn, _slot_por_data


class TestSlotPorData:
    def test_hoje(self):
        hoje = date(2026, 3, 7)
        assert _slot_por_data(date(2026, 3, 7), hoje) == 1

    def test_ontem(self):
        hoje = date(2026, 3, 7)
        assert _slot_por_data(date(2026, 3, 6), hoje) == 2

    def test_anteontem(self):
        hoje = date(2026, 3, 7)
        assert _slot_por_data(date(2026, 3, 5), hoje) == 3

    def test_delta_3_vai_para_slot4(self):
        hoje = date(2026, 3, 7)
        assert _slot_por_data(date(2026, 3, 4), hoje) == 4

    def test_delta_5_vai_para_slot5(self):
        hoje = date(2026, 3, 7)
        assert _slot_por_data(date(2026, 3, 2), hoje) == 5

    def test_delta_10_vai_para_slot10(self):
        hoje = date(2026, 3, 15)
        # delta=10 -> min(4+(10-4), 10) = min(10,10) = 10
        assert _slot_por_data(date(2026, 3, 5), hoje) == 10

    def test_delta_muito_grande_limitado_a_10(self):
        hoje = date(2026, 3, 20)
        # delta=20 -> min(4+(20-4), 10) = min(20,10) = 10
        assert _slot_por_data(date(2026, 3, 1), hoje) == 10


class TestExtrairParSiglaValor:
    def test_hb(self):
        result = _extrair_par_sigla_valor("Hb 8,8")
        assert result == [("hb", "8,8")]

    def test_leuco_com_diferencial(self):
        result = _extrair_par_sigla_valor("Leuco 16.640 (Bast 1% / Seg 78%)")
        assert len(result) == 1
        assert result[0][0] == "leuco"
        assert "16.640" in result[0][1]

    def test_bt_com_bd(self):
        result = _extrair_par_sigla_valor("BT 3,2 (0,8)")
        assert len(result) == 2
        assert ("bt", "3,2") in result
        assert ("bd", "0,8") in result

    def test_sigla_desconhecida_retorna_vazio(self):
        result = _extrair_par_sigla_valor("Xpto 99")
        assert result == []

    def test_prot_tot_antes_de_prot(self):
        result = _extrair_par_sigla_valor("Prot Tot 7,5")
        assert result == [("prot_tot", "7,5")]

    def test_cpk_mb_antes_de_cpk(self):
        result = _extrair_par_sigla_valor("CPK-MB 12")
        assert result == [("cpk_mb", "12")]


class TestParseUrn:
    def test_parse_urn_completo(self):
        result = _parse_urn("Den: 1.010 / Leu Est: Neg / Leuco: 50.000 / Hm: 100")
        assert result.get("ur_dens") == "1.010"
        assert result.get("ur_le") == "Neg"

    def test_parse_urn_parcial(self):
        result = _parse_urn("Den: 1.015")
        assert result.get("ur_dens") == "1.015"
        assert "ur_le" not in result


class TestParseLabDeterministico:
    TODAY = date(2026, 3, 7)

    def test_linha_de_hoje(self):
        texto = "07/03/2026 - Hb 8,8 | Cr 2,1 | Na 140"
        result = parse_lab_deterministico(texto, self.TODAY)
        assert result.get("lab_1_hb") == "8,8"
        assert result.get("lab_1_cr") == "2,1"
        assert result.get("lab_1_na") == "140"
        assert result.get("lab_1_data") == "07/03/2026"

    def test_linha_de_ontem(self):
        texto = "06/03/2026 - Hb 9,0 | Cr 2,3"
        result = parse_lab_deterministico(texto, self.TODAY)
        assert result.get("lab_2_hb") == "9,0"

    def test_keyword_admissao_vai_para_slot4(self):
        texto = "Admissao - Hb 7,1 | Cr 4,2"
        result = parse_lab_deterministico(texto, self.TODAY)
        assert result.get("lab_4_hb") == "7,1"

    def test_keyword_externo_vai_para_slot4(self):
        texto = "Externo - Hb 10,2"
        result = parse_lab_deterministico(texto, self.TODAY)
        assert result.get("lab_4_hb") == "10,2"

    def test_multiplas_linhas(self):
        texto = "07/03/2026 - Hb 8,8\n06/03/2026 - Hb 9,0\n05/03/2026 - Hb 9,5"
        result = parse_lab_deterministico(texto, self.TODAY)
        assert result.get("lab_1_hb") == "8,8"
        assert result.get("lab_2_hb") == "9,0"
        assert result.get("lab_3_hb") == "9,5"

    def test_urn_parseia_corretamente(self):
        texto = "07/03/2026 - Hb 8,8 | Urn: Den: 1.010 / Leu Est: Neg"
        result = parse_lab_deterministico(texto, self.TODAY)
        assert result.get("lab_1_ur_dens") == "1.010"
        assert result.get("lab_1_ur_le") == "Neg"

    def test_linha_invalida_ignorada(self):
        texto = "Linha invalida sem separador"
        result = parse_lab_deterministico(texto, self.TODAY)
        assert result == {}

    def test_texto_vazio_retorna_dict_vazio(self):
        result = parse_lab_deterministico("", self.TODAY)
        assert result == {}
