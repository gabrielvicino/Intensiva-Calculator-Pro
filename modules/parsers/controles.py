"""
Parser determinístico para Controles & Balanço Hídrico no formato padronizado:

  # Controles - 24 horas
  > 28/02/2026
  PAS: 110 - 135 mmHg | PAD: 70 - 85 mmHg | PAM: 83 - 102 mmHg | FC: 72 - 98 bpm | ...
  Balanço Hídrico Total: +420ml | Diurese: 1450ml

- # Controles - 12 ou 24 horas
- > DD/MM/YYYY (data do bloco)
- Linha de vitais: Sigla: min - max unidade
- Linha de balanço: Balanço Hídrico Total: x | Diurese: x
"""
import re
from datetime import datetime, date
from typing import Optional


def _parse_data_br(data_str: str) -> Optional[date]:
    """Converte DD/MM/YYYY ou DD/MM/YY para date."""
    data_str = data_str.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            continue
    return None


def _slot_por_data(data_exame: date, data_hoje: date) -> str:
    """Mapeia data para hoje/ontem/anteontem/ant4/ant5."""
    delta = (data_hoje - data_exame).days
    if delta == 0:
        return "hoje"
    if delta == 1:
        return "ontem"
    if delta == 2:
        return "anteontem"
    if delta == 3:
        return "ant4"
    if delta == 4:
        return "ant5"
    return None  # Ignorar datas fora do range


def _extrair_min_max(token: str, sigla: str) -> tuple[str, str] | None:
    """Extrai min e max de 'PAS: 110 - 135 mmHg'. Retorna (min, max) ou None."""
    if not token.strip().lower().startswith(sigla.lower() + ":"):
        return None
    resto = token[len(sigla) + 1:].strip()
    # Padrão: 110 - 135 mmHg ou 36,4 - 37,8 °C
    m = re.match(r"^([\d.,+\-]+)\s*[-–]\s*([\d.,+\-]+)", resto)
    if m:
        return (m.group(1).strip(), m.group(2).strip())
    return None


def parse_controles_deterministico(
    texto: str,
    data_hoje: Optional[date] = None,
) -> dict[str, str]:
    """
    Parseia texto de controles no formato padronizado.
    Retorna dict para session_state: ctrl_{dia}_{campo} = valor.
    """
    if data_hoje is None:
        data_hoje = date.today()

    resultado = {}

    # Período: # Controles - 24 horas ou # Controles - 12 horas
    m_periodo = re.search(r"#\s*Controles\s*[-–]\s*(\d+)\s*horas", texto, re.IGNORECASE)
    if m_periodo:
        horas = m_periodo.group(1).strip()
        resultado["ctrl_periodo"] = f"{horas} horas"

    # Blocos: > DD/MM/YYYY seguido de vitais e balanço
    blocos = re.split(r"(?=^\s*>\s*\d{1,2}/\d{1,2}/\d{2,4})", texto, flags=re.MULTILINE)

    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue

        # Extrai data da linha > DD/MM/YYYY
        m_data = re.match(r"^>\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*$", bloco.split("\n")[0].strip())
        if not m_data:
            continue

        data_str = m_data.group(1).strip()
        data_exame = _parse_data_br(data_str)
        if not data_exame:
            continue

        dia = _slot_por_data(data_exame, data_hoje)
        if not dia:
            continue

        resultado[f"ctrl_{dia}_data"] = data_str

        linhas = bloco.split("\n")[1:]
        vitais_linha = ""
        balanco_linha = ""

        for ln in linhas:
            ln = ln.strip()
            if not ln:
                continue
            if "Balanço Hídrico Total" in ln:
                balanco_linha = ln
            elif "PAS:" in ln or "PAD:" in ln:
                vitais_linha = ln

        # Parse vitais: PAS: 110 - 135 mmHg | PAD: 70 - 85 mmHg | ...
        MAP_VITAIS = [
            ("PAS", "pas"), ("PAD", "pad"), ("PAM", "pam"),
            ("FC", "fc"), ("FR", "fr"), ("SatO2", "sato2"),
            ("Temp", "temp"), ("Dextro", "glic"), ("Glic", "glic"),
        ]
        tokens = [t.strip() for t in vitais_linha.split("|") if t.strip()]
        for tok in tokens:
            for sigla, campo in MAP_VITAIS:
                r = _extrair_min_max(tok, sigla)
                if r:
                    resultado[f"ctrl_{dia}_{campo}_min"] = r[0]
                    resultado[f"ctrl_{dia}_{campo}_max"] = r[1]
                    break

        # Parse balanço: Balanço Hídrico Total: +420ml | Diurese: 1450ml
        if balanco_linha:
            m_bh = re.search(r"Balanço Hídrico Total:\s*([^|]+)", balanco_linha, re.IGNORECASE)
            if m_bh:
                resultado[f"ctrl_{dia}_balanco"] = m_bh.group(1).strip()
            m_diur = re.search(r"Diurese:\s*([^|]+)", balanco_linha, re.IGNORECASE)
            if m_diur:
                resultado[f"ctrl_{dia}_diurese"] = m_diur.group(1).strip()

    return resultado
