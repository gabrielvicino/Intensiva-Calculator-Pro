"""
Parser determinístico para Controles & Balanço Hídrico no formato padronizado:

  # Controles - 24 horas          ← pode ser 12 ou 24 horas
  > 28/02/2026                    ← data do bloco
  PAS: 110 - 135 mmHg | PAD: 70 - 85 mmHg | PAM: 83 - 102 mmHg | FC: 72 - 98 bpm | ...
  Balanço Hídrico Total: +420ml | Diurese: 1450ml

Atribuição de slot (hoje / ontem / anteontem / ant4 / ant5):
  1. Prioridade: slot cujo ctrl_{dia}_data já contém aquela data (DD/MM ou DD/MM/YYYY)
     → respeita o que o usuário configurou manualmente
  2. Fallback: ordem de aparição dos blocos no texto
     → 1º bloco com data → próximo slot disponível, e assim por diante
"""
import re
from datetime import datetime, date
from typing import Optional


_DIAS_ORDEM = ["hoje", "ontem", "anteontem", "ant4", "ant5",
               "ant6", "ant7", "ant8", "ant9", "ant10"]

# Siglas vitais → chave do campo (min_max=True)
_MAP_VITAIS = [
    ("PAS",    "pas"),
    ("PAD",    "pad"),
    ("PAM",    "pam"),
    ("FC",     "fc"),
    ("FR",     "fr"),
    ("SatO2",  "sato2"),
    ("Temp",   "temp"),
    ("Dextro", "glic"),
    ("Glic",   "glic"),
]

# Regex para detectar linha de vitais (qualquer sigla conhecida seguida de ":")
_RE_VITAIS = re.compile(
    r"\b(?:PAS|PAD|PAM|FC|FR|SatO2|Temp|Dextro|Glic)\s*:", re.IGNORECASE
)
# Regex para detectar linha de balanço
_RE_BALANCO = re.compile(r"balan[çc]o\s+h[ií]drico", re.IGNORECASE)


def _parse_data_br(data_str: str) -> Optional[str]:
    """Converte DD/MM/YYYY ou DD/MM/YY para string DD/MM/YYYY. Retorna None se inválido."""
    data_str = data_str.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            d = datetime.strptime(data_str, fmt).date()
            return d.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return None


def _datas_coincidem(slot_data: str, bloco_data: str) -> bool:
    """
    Verifica se a data de um slot casa com a data de um bloco.
    Aceita qualquer combinação de DD/MM, DD/MM/YY ou DD/MM/YYYY:
    o critério mínimo é o prefixo DD/MM ser igual.
    """
    if not slot_data or not bloco_data:
        return False
    s = slot_data.strip()
    b = bloco_data.strip()
    if s == b:
        return True
    # Compara só os primeiros 5 chars (DD/MM) — ignora diferença de ano
    return len(s) >= 5 and len(b) >= 5 and s[:5] == b[:5]


def _extrair_min_max(token: str, sigla: str) -> tuple[str, str] | None:
    """
    Extrai (min, max) de 'PAS: 106 - 160 mmHg' ou (val, '') de 'PAS: 120 mmHg'.
    Retorna None se o token não corresponder à sigla.
    """
    if not token.strip().lower().startswith(sigla.lower() + ":"):
        return None
    resto = token[len(sigla) + 1:].strip()
    # range: dois valores separados por hífen ou en-dash
    m = re.match(r"^([+\-]?[\d.,]+)\s*[-–]\s*([+\-]?[\d.,]+)", resto)
    if m:
        return (m.group(1).strip(), m.group(2).strip())
    # valor único → vai para _min, _max fica vazio
    m_single = re.match(r"^([+\-]?[\d.,]+)", resto)
    if m_single:
        return (m_single.group(1).strip(), "")
    return None


def _parse_vitais(linha: str, dia: str, resultado: dict) -> None:
    """Popula resultado com os vitais de uma linha separada por '|'."""
    tokens = [t.strip() for t in linha.split("|") if t.strip()]
    for tok in tokens:
        for sigla, campo in _MAP_VITAIS:
            r = _extrair_min_max(tok, sigla)
            if r:
                resultado[f"ctrl_{dia}_{campo}_min"] = r[0]
                resultado[f"ctrl_{dia}_{campo}_max"] = r[1]
                break


def _parse_balanco(linha: str, dia: str, resultado: dict) -> None:
    """Popula resultado com BH total e diurese de uma linha de balanço."""
    # BH total – captura valor com sinal opcional (+315ml, -500ml, 420ml)
    m_bh = re.search(
        r"balan[çc]o\s+h[ií]drico(?:\s+total)?:\s*([+\-]?[\d.,]+\s*(?:m[lL])?)",
        linha, re.IGNORECASE,
    )
    if m_bh:
        resultado[f"ctrl_{dia}_balanco"] = m_bh.group(1).strip()

    # Diurese
    m_diur = re.search(r"diurese:\s*([^|\n]+)", linha, re.IGNORECASE)
    if m_diur:
        resultado[f"ctrl_{dia}_diurese"] = m_diur.group(1).strip()


def parse_controles_dia(texto: str, dia: str) -> dict:
    """
    Extrai controles de um texto livre de UM único dia e mapeia para ctrl_{dia}_*.

    Não tenta identificar múltiplos blocos: tudo que estiver no texto vai para `dia`.
    Extrai data se encontrar padrão DD/MM/YYYY (não altera a coluna — só preenche o campo data).
    """
    resultado: dict[str, str] = {}
    if not texto or not texto.strip():
        return resultado

    for ln in texto.strip().split("\n"):
        ln = ln.strip()
        if not ln:
            continue

        # Data: extrai primeira ocorrência DD/MM/YYYY ou DD/MM/YY
        if not resultado.get(f"ctrl_{dia}_data"):
            m_dt = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", ln)
            if m_dt:
                data_fmt = _parse_data_br(m_dt.group(1))
                if data_fmt:
                    resultado[f"ctrl_{dia}_data"] = data_fmt

        if _RE_BALANCO.search(ln):
            _parse_balanco(ln, dia, resultado)
        if _RE_VITAIS.search(ln):
            _parse_vitais(ln, dia, resultado)

    return resultado


def parse_controles_deterministico(
    texto: str,
    data_hoje: Optional[date] = None,
    existing_dates: Optional[dict] = None,
) -> dict[str, str]:
    """
    Parseia texto de controles no formato padronizado.

    Atribuição de slot:
      1. Match por data: se existing_dates contém a data do bloco em algum slot, usa esse slot.
      2. Fallback por ordem: 1º bloco sem match → próximo slot disponível (hoje, ontem, …).

    Args:
        texto:          Texto colado pelo usuário.
        data_hoje:      Não usado (mantido por compatibilidade de assinatura).
        existing_dates: Dict {dia: "DD/MM" | "DD/MM/YYYY"} com datas já nos slots
                        (ex.: {"hoje": "07/03/2026", "ontem": "06/03"}).
                        Usado para priorizar match por data configurada.

    Returns:
        Dict para session_state: ctrl_{dia}_{campo} = valor.
    """
    resultado: dict[str, str] = {}

    # Período: # Controles - 24 horas  ou  # Controles - 12 horas
    m_periodo = re.search(
        r"#\s*Controles\s*[-–]\s*(\d+)\s*horas?", texto, re.IGNORECASE
    )
    if m_periodo:
        resultado["ctrl_periodo"] = f"{m_periodo.group(1)} horas"

    # ── Coleta os blocos válidos (aqueles que têm ">" data) ──────────────────
    raw_blocos = re.split(
        r"(?=^\s*>\s*\d{1,2}/\d{1,2}/\d{2,4})",
        texto,
        flags=re.MULTILINE,
    )

    valid_blocks: list[tuple[str | None, list[str]]] = []
    for bloco in raw_blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
        primeira = bloco.split("\n")[0].strip()
        m_data = re.match(r"^>\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*$", primeira)
        if not m_data:
            continue
        data_fmt = _parse_data_br(m_data.group(1))   # "DD/MM/YYYY" ou None
        linhas = bloco.split("\n")[1:]
        valid_blocks.append((data_fmt, linhas))

    # Ordena blocos com data: mais recente primeiro → hoje, ontem, anteontem...
    # Blocos sem data ficam no final.
    def _bloco_key(bloco):
        data_fmt = bloco[0]
        if not data_fmt:
            return datetime.min.date()
        try:
            return datetime.strptime(data_fmt, "%d/%m/%Y").date()
        except Exception:
            return datetime.min.date()

    valid_blocks.sort(key=_bloco_key, reverse=True)

    # ── Atribuição de slots ───────────────────────────────────────────────────
    used_slots: set[str] = set()
    fallback_idx = 0   # próximo slot disponível na ordem padrão

    for data_fmt, linhas in valid_blocks:
        dia: str | None = None

        # Prioridade 1 — match por data configurada pelo usuário
        if existing_dates and data_fmt:
            for slot in _DIAS_ORDEM:
                if slot in used_slots:
                    continue
                slot_data = (existing_dates.get(slot) or "").strip()
                if _datas_coincidem(slot_data, data_fmt):
                    dia = slot
                    break

        # Fallback — próximo slot disponível na ordem
        if dia is None:
            while fallback_idx < len(_DIAS_ORDEM) and _DIAS_ORDEM[fallback_idx] in used_slots:
                fallback_idx += 1
            if fallback_idx < len(_DIAS_ORDEM):
                dia = _DIAS_ORDEM[fallback_idx]
                fallback_idx += 1

        if dia is None:
            continue

        used_slots.add(dia)

        # Grava a data completa no slot
        if data_fmt:
            resultado[f"ctrl_{dia}_data"] = data_fmt

        # Processa linhas do bloco
        for ln in linhas:
            ln = ln.strip()
            if not ln:
                continue
            if _RE_BALANCO.search(ln):
                _parse_balanco(ln, dia, resultado)
            if _RE_VITAIS.search(ln):
                _parse_vitais(ln, dia, resultado)

    return resultado
