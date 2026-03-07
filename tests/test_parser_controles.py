"""
Testes unitarios para modules/parsers/controles.py
"""
import pytest
from datetime import date
from modules.parsers.controles import parse_controles_deterministico, _slot_por_data, _extrair_min_max


class TestSlotPorData:
    def test_hoje(self):
        assert _slot_por_data(date(2026, 3, 7), date(2026, 3, 7)) == "hoje"

    def test_ontem(self):
        assert _slot_por_data(date(2026, 3, 6), date(2026, 3, 7)) == "ontem"

    def test_anteontem(self):
        assert _slot_por_data(date(2026, 3, 5), date(2026, 3, 7)) == "anteontem"

    def test_ant4(self):
        assert _slot_por_data(date(2026, 3, 4), date(2026, 3, 7)) == "ant4"

    def test_ant5(self):
        assert _slot_por_data(date(2026, 3, 3), date(2026, 3, 7)) == "ant5"

    def test_fora_do_range_retorna_none(self):
        assert _slot_por_data(date(2026, 2, 28), date(2026, 3, 7)) is None


class TestExtrairMinMax:
    def test_pas_com_unidade(self):
        result = _extrair_min_max("PAS: 110 - 135 mmHg", "PAS")
        assert result == ("110", "135")

    def test_temperatura_decimal(self):
        result = _extrair_min_max("Temp: 36,4 - 37,8", "Temp")
        assert result == ("36,4", "37,8")

    def test_sigla_errada_retorna_none(self):
        result = _extrair_min_max("FC: 72 - 98", "PAS")
        assert result is None


class TestParseControlesDeterministico:
    TODAY = date(2026, 3, 7)

    TEXTO_BASE = """# Controles - 24 horas
> 07/03/2026
PAS: 110 - 135 mmHg | PAD: 70 - 85 mmHg | PAM: 83 - 102 mmHg | FC: 72 - 98 bpm | SatO2: 96 - 99%
Balanco Hidrico Total: +420ml | Diurese: 1450ml
"""

    def test_parse_periodo(self):
        result = parse_controles_deterministico(self.TEXTO_BASE, self.TODAY)
        assert result.get("ctrl_periodo") == "24 horas"

    def test_parse_data_hoje(self):
        result = parse_controles_deterministico(self.TEXTO_BASE, self.TODAY)
        assert result.get("ctrl_hoje_data") == "07/03/2026"

    def test_parse_pas_min_max(self):
        result = parse_controles_deterministico(self.TEXTO_BASE, self.TODAY)
        assert result.get("ctrl_hoje_pas_min") == "110"
        assert result.get("ctrl_hoje_pas_max") == "135"

    def test_parse_fc(self):
        result = parse_controles_deterministico(self.TEXTO_BASE, self.TODAY)
        assert result.get("ctrl_hoje_fc_min") == "72"
        assert result.get("ctrl_hoje_fc_max") == "98"

    def test_parse_diurese(self):
        result = parse_controles_deterministico(self.TEXTO_BASE, self.TODAY)
        assert result.get("ctrl_hoje_diurese") == "1450ml"

    def test_parse_balanco(self):
        result = parse_controles_deterministico(self.TEXTO_BASE, self.TODAY)
        assert result.get("ctrl_hoje_balanco") == "+420ml"

    def test_multiplos_dias(self):
        texto = """# Controles - 24 horas
> 07/03/2026
PAS: 110 - 130 mmHg
Balanco Hidrico Total: -350ml | Diurese: 1800ml
> 06/03/2026
PAS: 100 - 125 mmHg
Balanco Hidrico Total: +200ml | Diurese: 1200ml
"""
        result = parse_controles_deterministico(texto, self.TODAY)
        assert result.get("ctrl_hoje_pas_min") == "110"
        assert result.get("ctrl_ontem_pas_min") == "100"
        assert result.get("ctrl_hoje_diurese") == "1800ml"
        assert result.get("ctrl_ontem_diurese") == "1200ml"

    def test_data_fora_do_range_ignorada(self):
        texto = """# Controles - 24 horas
> 01/01/2026
PAS: 120 - 140 mmHg
"""
        result = parse_controles_deterministico(texto, self.TODAY)
        # Data muito antiga (delta > 4) -- nao deve gerar nada
        assert "ctrl_hoje_data" not in result
        assert "ctrl_ontem_data" not in result

    def test_texto_vazio_retorna_dict_vazio(self):
        result = parse_controles_deterministico("", self.TODAY)
        assert result == {}
