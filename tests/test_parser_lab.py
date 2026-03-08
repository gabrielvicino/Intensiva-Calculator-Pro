"""
Testes unitarios para modules/parsers/lab.py
"""
import pytest
from datetime import date
from modules.parsers.lab import parse_lab_deterministico, _extrair_par_sigla_valor, _parse_urn


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
    def test_primeira_linha_vai_para_slot1(self):
        """1ª linha com data → slot 1, independente da data."""
        texto = "08/03/2026 - Hb 8,8 | Cr 2,1 | Na 140"
        result = parse_lab_deterministico(texto)
        assert result.get("lab_1_hb") == "8,8"
        assert result.get("lab_1_cr") == "2,1"
        assert result.get("lab_1_data") == "08/03/2026"

    def test_segunda_linha_vai_para_slot2(self):
        """2ª linha com data → slot 2, independente da data."""
        texto = "08/03/2026 - Hb 8,8\n01/01/2020 - Hb 9,0"
        result = parse_lab_deterministico(texto)
        assert result.get("lab_1_hb") == "8,8"
        assert result.get("lab_2_hb") == "9,0"
        assert result.get("lab_2_data") == "01/01/2020"

    def test_keyword_admissao_vai_para_slot4(self):
        texto = "Admissao - Hb 7,1 | Cr 4,2"
        result = parse_lab_deterministico(texto)
        assert result.get("lab_4_hb") == "7,1"

    def test_keyword_externo_vai_para_slot4(self):
        texto = "Externo - Hb 10,2"
        result = parse_lab_deterministico(texto)
        assert result.get("lab_4_hb") == "10,2"

    def test_tres_linhas_de_data_slots_1_2_3(self):
        texto = "08/03/2026 - Hb 8,8\n07/03/2026 - Hb 9,0\n06/03/2026 - Hb 9,5"
        result = parse_lab_deterministico(texto)
        assert result.get("lab_1_hb") == "8,8"
        assert result.get("lab_2_hb") == "9,0"
        assert result.get("lab_3_hb") == "9,5"

    def test_quarta_linha_de_data_vai_para_slot5(self):
        """Slot 4 reservado para admissão/externo: 4 linhas de data ocupam slots 1,2,3,5."""
        texto = "08/03/2026 - Hb 8\n07/03/2026 - Hb 9\n06/03/2026 - Hb 10\nAdmissao - Hb 7\n05/03/2026 - Hb 11"
        result = parse_lab_deterministico(texto)
        assert result.get("lab_1_hb") == "8"
        assert result.get("lab_2_hb") == "9"
        assert result.get("lab_3_hb") == "10"
        assert result.get("lab_4_hb") == "7"
        assert result.get("lab_5_hb") == "11"

    def test_urn_parseia_corretamente(self):
        texto = "07/03/2026 - Hb 8,8 | Urn: Den: 1.010 / Leu Est: Neg"
        result = parse_lab_deterministico(texto)
        assert result.get("lab_1_ur_dens") == "1.010"
        assert result.get("lab_1_ur_le") == "Neg"

    def test_linha_invalida_ignorada(self):
        texto = "Linha invalida sem separador"
        result = parse_lab_deterministico(texto)
        assert result == {}

    def test_texto_vazio_retorna_dict_vazio(self):
        result = parse_lab_deterministico("")
        assert result == {}
