"""
Parser determinístico para laudos do HC Unicamp (Campinas).

Detecta laudos pelo domínio HC.UNICAMP.BR no rodapé.
Retorna lista de coletas (dicts) agrupadas por (data, hora_cheia).
Cada coleta tem chaves bare (sem prefixo lab_{slot}_).

Fluxo:
  1. Encontra todos os timestamps (Recebimento material: DD/MM/YY HH:MM)
  2. Extrai valores de exames com regex por posição no texto
  3. Associa cada exame ao timestamp imediatamente posterior
  4. Agrupa por (data, hora_cheia) → uma coleta por grupo
  5. Dentro do mesmo grupo, valor do horário mais recente prevalece
"""
from __future__ import annotations

import re
from typing import Optional


def detectar(texto: str) -> bool:
    """Retorna True se o texto for de um laudo do HC Unicamp."""
    upper = texto.upper()
    return "HC.UNICAMP.BR" in upper or "UNICAMP" in upper


def _n(s: str) -> str:
    """Normaliza valor numérico: vírgula → ponto, strip."""
    return s.strip().replace(",", ".") if s else ""


def _normalizar_data(raw: str) -> str:
    """DD/MM/YY → DD/MM/YYYY."""
    partes = raw.strip().split("/")
    if len(partes) == 3 and len(partes[2]) == 2:
        partes[2] = "20" + partes[2]
    return "/".join(partes)


def _data_iso(data_br: str) -> str:
    """DD/MM/YYYY → YYYY-MM-DD para ordenação."""
    partes = data_br.split("/")
    if len(partes) == 3:
        return f"{partes[2]}-{partes[1]}-{partes[0]}"
    return data_br


def _hora_cheia(hora: str) -> int:
    """'05:08' → 5."""
    try:
        return int(hora.split(":")[0])
    except (ValueError, IndexError):
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Regex patterns — Bioquímica (formato NOME: VALOR)
# ─────────────────────────────────────────────────────────────────────────────

_BIOQ_PATTERNS: list[tuple[str, str]] = [
    (r'UR[EÉ]IA:\s*([\d,\.]+)',                        'ur'),
    (r'CREATININA:\s*([\d,\.]+)',                       'cr'),
    (r'S[OÓ]DIO:\s*([\d,\.]+)',                        'na'),
    (r'POT[AÁ]SSIO:\s*([\d,\.]+)',                     'k'),
    (r'MAGN[EÉ]SIO:\s*([\d,\.]+)',                     'mg'),
    (r'F[OÓ]SFORO:\s*([\d,\.]+)',                      'pi'),
    (r'PROTE[IÍ]NA C REATIVA:\s*([\d,\.]+)',           'pcr'),
    (r'ASPARTATO AMINOTRANSFERASE:\s*(\d[\d,\.]*)',    'tgo'),
    (r'ALANINA AMINOTRANSFERASE:\s*(\d[\d,\.]*)',      'tgp'),
    (r'BILIRRUBINAS TOTAIS:\s*([\d,\.]+)',             'bt'),
    (r'BILIRRUBINA DIRETA\s*:\s*([\d,\.]+)',           'bd'),
    (r'ALBUMINA:\s*([\d,\.]+)',                         'alb'),
    (r'DESIDROGENASE L[AÁ]C?TICA?:\s*([\d,\.]+)',     'ldh'),
    (r'FOSFATASE ALCALINA:\s*([\d,\.]+)',              'fal'),
    (r'GAMA[- ]?GLUTAMIL[^\n:]*:\s*([\d,\.]+)',       'ggt'),
    (r'AMILASE:\s*([\d,\.]+)',                          'amil'),
    (r'LIPASE:\s*([\d,\.]+)',                           'lipas'),
    (r'TROPONINA[^\n:]*:\s*([\d,\.]+)',                'trop'),
    (r'PROTE[IÍ]NA(?:S)? TOTAIS?:\s*([\d,\.]+)',      'prot_tot'),
    (r'C[AÁ]LCIO TOTAL:\s*([\d,\.]+)',                'cat'),
    (r'C[AÁ]LCIO I[OÔ]NICO:\s*([\d,\.]+)',           'cai'),
    (r'LACTATO[^:]*:\s*([\d,\.]+)',                    'lac'),
]

# ─────────────────────────────────────────────────────────────────────────────
# Regex patterns — Gasometria (formato NOME VALOR ... VR: ...)
# ─────────────────────────────────────────────────────────────────────────────

_GAS_PATTERNS: list[tuple[str, str]] = [
    (r'^pH\s+([\d,\.]+)',                'gas_ph'),
    (r'^pCO2\s+([\d,\.]+)',              'gas_pco2'),
    (r'^pO2\s+([\d,\.]+)',               'gas_po2'),
    (r'^HCO3\s+([\d,\.]+)',              'gas_hco3'),
    (r'^BE\s+([+-]?[\d,\.]+)',           'gas_be'),
    (r'^SO2\s+([\d,\.]+)',               'gas_sat'),
    (r'^LACTATO\s+([\d,\.]+)',           'gas_lac'),
    (r'^CALCIO IONICO\s+([\d,\.]+)',     'gas_cai'),
    (r'^ANION GAP \(K\)\s+([\d,\.]+)',   'gas_ag'),
    (r'^CLORO\s+([\d,\.]+)',             'gas_cl'),
    (r'^SODIO\s+([\d,\.]+)',             'gas_na'),
    (r'^POTASSIO\s+([\d,\.]+)',          'gas_k'),
]

# ─────────────────────────────────────────────────────────────────────────────
# Regex patterns — Hemograma (formato SIGLA: VALOR unidade VR:...)
# ─────────────────────────────────────────────────────────────────────────────

_HEMO_PATTERNS: list[tuple[str, str]] = [
    (r'^WBC:\s*([\d,\.]+)',   'leuco'),
    (r'^HB:\s*([\d,\.]+)',    'hb'),
    (r'^HT:\s*([\d,\.]+)',    'ht'),
    (r'^VCM:\s*([\d,\.]+)',   'vcm'),
    (r'^HCM:\s*([\d,\.]+)',   'hcm'),
    (r'^RDW:\s*([\d,\.]+)',   'rdw'),
    (r'^PLT:\s*([\d,\.]+)',   'plaq'),
]

# ─────────────────────────────────────────────────────────────────────────────
# Timestamp extraction
# ─────────────────────────────────────────────────────────────────────────────

_RE_TIMESTAMP = re.compile(
    r'Recebimento material:\s*(\d{2}/\d{2}/\d{2,4})\s+(\d{2}:\d{2})'
)


def _find_timestamps(texto: str) -> list[tuple[int, str, str]]:
    """Retorna [(posição, data_norm, hora), ...] para cada timestamp no texto."""
    return [
        (m.start(), _normalizar_data(m.group(1)), m.group(2))
        for m in _RE_TIMESTAMP.finditer(texto)
    ]


def _ts_for(pos: int, timestamps: list[tuple[int, str, str]]) -> tuple[str, str]:
    """Retorna (data, hora) do primeiro timestamp após a posição dada."""
    for ts_pos, data, hora in timestamps:
        if ts_pos > pos:
            return data, hora
    if timestamps:
        return timestamps[-1][1], timestamps[-1][2]
    return "", ""


# ─────────────────────────────────────────────────────────────────────────────
# Collector — acumula exames agrupados por col_key
# ─────────────────────────────────────────────────────────────────────────────

class _Collector:
    """Acumula exames em coletas agrupadas por (data, hora_cheia)."""

    def __init__(self, timestamps: list[tuple[int, str, str]]):
        self._ts = timestamps
        self._coletas: dict[str, dict] = {}

    def add(self, pos: int, field: str, value: str) -> None:
        data, hora = _ts_for(pos, self._ts)
        if not data:
            return
        hc = _hora_cheia(hora)
        ck = f"{data}_{hc:02d}"
        if ck not in self._coletas:
            self._coletas[ck] = {"data": data, "hora": hora, "hora_cheia": hc}
        c = self._coletas[ck]
        ts_key = f"__ts_{field}"
        if field not in c or hora >= c.get(ts_key, ""):
            c[field] = value
            c[ts_key] = hora

    def result(self) -> list[dict]:
        out = []
        for c in self._coletas.values():
            clean = {k: v for k, v in c.items() if not k.startswith("__ts_")}
            out.append(clean)
        out.sort(key=lambda x: (_data_iso(x.get("data", "")), x.get("hora_cheia", 0)))
        return out


# ─────────────────────────────────────────────────────────────────────────────
# Seções de parsing
# ─────────────────────────────────────────────────────────────────────────────

def _parse_bioq(texto: str, col: _Collector) -> None:
    """Extrai exames bioquímicos (formato NOME: VALOR)."""
    for pat, field in _BIOQ_PATTERNS:
        for m in re.finditer(pat, texto, re.IGNORECASE):
            col.add(m.start(), field, _n(m.group(1)))


def _parse_gas(texto: str, col: _Collector) -> None:
    """Extrai bloco de gasometria (formato inline sem ':'). """
    gas_m = re.search(
        r'(GASOMETRIA\s+(ARTERIAL|VENOSA|CAPILAR).+?)(?=LABORAT[ÓO]RIO DE PATOLOGIA|$)',
        texto, re.DOTALL | re.IGNORECASE,
    )
    if not gas_m:
        return

    bloco = gas_m.group(1)
    pos_base = gas_m.start()
    tipo = gas_m.group(2).strip().capitalize()

    col.add(pos_base, 'gas_tipo', tipo)

    hora_m = re.search(r'^Método:.*$', bloco, re.MULTILINE)
    gas_hora_m = re.search(
        r'Recebimento material:\s*\d{2}/\d{2}/\d{2,4}\s+(\d{2}:\d{2})', bloco
    )
    if gas_hora_m:
        h, mi = gas_hora_m.group(1).split(":")
        col.add(pos_base, 'gas_hora', f"{int(h):02d}h")

    for pat, field in _GAS_PATTERNS:
        for gm in re.finditer(pat, bloco, re.MULTILINE | re.IGNORECASE):
            col.add(pos_base + gm.start(), field, _n(gm.group(1)))


def _parse_hemo(texto: str, col: _Collector) -> None:
    """Extrai hemograma do bloco GLOBAIS."""
    hemo_m = re.search(
        r'(GLOBAIS:.+?)(?=LABORAT[ÓO]RIO DE PATOLOGIA|$)',
        texto, re.DOTALL | re.IGNORECASE,
    )
    if not hemo_m:
        return

    bloco = hemo_m.group(1)
    pos_base = hemo_m.start()

    for pat, field in _HEMO_PATTERNS:
        for hm in re.finditer(pat, bloco, re.MULTILINE | re.IGNORECASE):
            col.add(pos_base + hm.start(), field, _n(hm.group(1)))


def _parse_coag(texto: str, col: _Collector) -> None:
    """Extrai coagulação (TTPA, TP, RNI)."""
    for m in re.finditer(r'TTPA:\s*([\d,\.]+)\s*SEG', texto, re.IGNORECASE):
        seg = _n(m.group(1))
        r_m = re.search(r'R:\s*([\d,\.]+)', texto[m.end():m.end() + 100])
        if r_m:
            col.add(m.start(), 'ttpa', f"{seg}s (R {_n(r_m.group(1))})")
        else:
            col.add(m.start(), 'ttpa', f"{seg}s")

    for m in re.finditer(r'\bTP:\s*([\d,\.]+)\s*SEG', texto, re.IGNORECASE):
        seg = _n(m.group(1))
        parts = [f"{seg}s"]
        window = texto[m.end():m.end() + 200]
        ap_m = re.search(r'AP:\s*([\d,\.]+)%', window, re.IGNORECASE)
        if ap_m:
            parts.append(f"AP {_n(ap_m.group(1))}%")
        rni_m = re.search(r'RNI:\s*([\d,\.]+)', window, re.IGNORECASE)
        if rni_m:
            parts.append(f"RNI {_n(rni_m.group(1))}")
        col.add(m.start(), 'tp', " ".join(parts))


def _parse_urina(texto: str, col: _Collector) -> None:
    """Extrai EAS/urina se presente no texto."""
    _URN_PATTERNS = [
        (r'DENSIDADE:\s*([\d,\.]+)',                   'ur_dens'),
        (r'ESTERASE\s+LEUCOCIT[AÁ]RIA:\s*(\S+)',     'ur_le'),
        (r'NITRITO:\s*(\S+)',                          'ur_nit'),
        (r'LEUC[ÓO]CITOS[^\n:]*:\s*([\d,\.]+)',      'ur_leu'),
        (r'HEM[AÁ]CIAS[^\n:]*:\s*([\d,\.]+)',        'ur_hm'),
        (r'PROTE[IÍ]NAS?\s*(?:\(U\))?:\s*(\S+)',     'ur_prot'),
        (r'CORPOS CET[ÔO]NICOS:\s*(\S+)',            'ur_cet'),
        (r'GLICOSE\s*(?:\(U\))?:\s*(\S+)',           'ur_glic'),
    ]
    for pat, field in _URN_PATTERNS:
        for m in re.finditer(pat, texto, re.IGNORECASE):
            col.add(m.start(), field, m.group(1).strip())


# ─────────────────────────────────────────────────────────────────────────────
# Função pública
# ─────────────────────────────────────────────────────────────────────────────

def parsear(texto: str) -> list[dict] | None:
    """
    Parseia texto de laudo do HC Unicamp.

    Retorna lista de coleta dicts (chaves bare: 'hb', 'cr', 'data', 'hora', etc.)
    ou None se o texto não for reconhecido como HC Unicamp.
    """
    if not detectar(texto):
        return None

    timestamps = _find_timestamps(texto)
    if not timestamps:
        return None

    col = _Collector(timestamps)
    _parse_bioq(texto, col)
    _parse_gas(texto, col)
    _parse_hemo(texto, col)
    _parse_coag(texto, col)
    _parse_urina(texto, col)

    result = col.result()
    return result if result else None
