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


def detectar(texto: str) -> bool:
    """Retorna True se o texto for de um laudo do HC Unicamp."""
    upper = texto.upper()
    return "HC.UNICAMP.BR" in upper or "UNICAMP" in upper


def _n(s: str) -> str:
    """Normaliza valor numérico: vírgula → ponto, strip."""
    return s.strip().replace(",", ".") if s else ""


def _fmt(s: str, decimals: int) -> str:
    """Formata valor numérico para N casas decimais. Preserva strings não-numéricas."""
    try:
        f = float(s)
        return str(int(round(f))) if decimals == 0 else f"{f:.{decimals}f}"
    except (ValueError, TypeError):
        return s


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
    (r'UR[EÉ]IA:\s*([\d,\.]+)',                                'ur'),
    (r'CREATININA:\s*([\d,\.]+)',                               'cr'),
    (r'S[OÓ]DIO:\s*([\d,\.]+)',                                'na'),
    (r'POT[AÁ]SSIO:\s*([\d,\.]+)',                             'k'),
    (r'MAGN[EÉ]SIO:\s*([\d,\.]+)',                             'mg'),
    (r'F[OÓ]SFORO:\s*([\d,\.]+)',                              'pi'),
    (r'PROTE[IÍ]NA C REATIVA:\s*([\d,\.]+)',                   'pcr'),
    (r'\bVHS:\s*([\d,\.]+)',                                    'vhs'),
    (r'FIBROGEN[IÍ]O:\s*([\d,\.]+)',                           'fbrn'),
    (r'ASPARTATO AMINOTRANSFERASE:\s*(\d[\d,\.]*)',            'tgo'),
    (r'ALANINA AMINOTRANSFERASE:\s*(\d[\d,\.]*)',              'tgp'),
    (r'BILIRRUBINAS TOTAIS:\s*([\d,\.]+)',                     'bt'),
    (r'BILIRRUBINA DIRETA\s*:\s*([\d,\.]+)',                   'bd'),
    (r'ALBUMINA:\s*([\d,\.]+)',                                 'alb'),
    (r'DESIDROGENASE L[AÁ]C?TICA?:\s*([\d,\.]+)',             'ldh'),
    (r'\bLDH:\s*([\d,\.]+)',                                    'ldh'),
    (r'FOSFATASE ALCALINA(?:\s+TOTAL)?:\s*([\d,\.]+)',         'fal'),
    (r'GAMA[- ]?GLUTAMIL[^\n:]*:\s*([\d,\.]+)',               'ggt'),
    (r'AMILASE:\s*([\d,\.]+)',                                  'amil'),
    (r'LIPASE:\s*([\d,\.]+)',                                   'lipas'),
    (r'TROPONINA[^\n:]*:\s*([\d,\.]+)',                        'trop'),
    (r'PROTE[IÍ]NA(?:S)? TOTAIS?:\s*([\d,\.]+)',              'prot_tot'),
    (r'C[AÁ]LCIO TOTAL:\s*([\d,\.]+)',                        'cat'),
    (r'C[AÁ]LCIO I[OÔ]NICO:\s*([\d,\.]+)',                   'cai'),
    (r'LACTATO\s+S[EÉ]RICO:\s*([\d,\.]+)',                     'lac'),
    (r'^GLICOSE:\s*([\d,\.]+)\s*mg/dL\b',                      'glic'),
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
    (r'^CALCIO IONICO\s+([\d,\.]+)',                'gas_cai'),
    # Gasometria venosa: "Ca Ionico(7,4) 1,10" (temperatura corrigida)
    (r'^Ca\s+Ionico\(7,4\)\w*\s+([\d,\.]+)',       'gas_cai'),
    (r'^ANION GAP \(K\)\s+([\d,\.]+)',              'gas_ag'),
    (r'^CLORO\s+([\d,\.]+)',                        'gas_cl'),
    (r'^SODIO\s+([\d,\.]+)',                        'gas_na'),
    (r'^POTASSIO\s+([\d,\.]+)',                     'gas_k'),
    (r'^HEMOGLOBINA\s+([\d,\.]+)',                  'gas_hb'),
    # Gasometria venosa: "tHb 6,9 g/dL" (hemoglobina total)
    (r'^tHb\s+([\d,\.]+)',                          'gas_hb'),
    (r'^HEMATOCRITO\s+([\d,\.]+)',                  'gas_ht'),
]

# ─────────────────────────────────────────────────────────────────────────────
# Regex patterns — Hemograma (formato SIGLA: VALOR unidade VR:...)
# ─────────────────────────────────────────────────────────────────────────────

_HEMO_PATTERNS: list[tuple[str, str]] = [
    (r'^WBC\s*:\s*([\d,\.]+)',             'leuco'),
    (r'^HB\s*:\s*([\d,\.]+)',              'hb'),
    (r'^HT\s*:\s*([\d,\.]+)',              'ht'),
    (r'^VCM\s*:\s*([\d,\.]+)',             'vcm'),
    (r'^HCM\s*:\s*([\d,\.]+)',             'hcm'),
    (r'^RDW\s*:\s*([\d,\.]+)',             'rdw'),
    (r'^PLT\s*:\s*([\d,\.]+)',             'plaq'),
    # Diferencial — nomes mapeados para os sufixos corretos do session_state
    (r'^SEG\s*:\s*([\d,\.]+)',             'leuco_seg'),
    (r'^BAST[ÕO]ES\s*:\s*([\d,\.]+)',     'leuco_bast'),
    (r'^LINFO\s*:\s*([\d,\.]+)',           'leuco_linf'),
    (r'^MONO\s*:\s*([\d,\.]+)',            'leuco_mon'),
    (r'^EOSINO\s*:\s*([\d,\.]+)',          'leuco_eos'),
    (r'^BASO\s*:\s*([\d,\.]+)',            'leuco_bas'),
    (r'^BLASTO\s*:\s*([\d,\.]+)',          'leuco_bla'),
    (r'^MIELO\s*:\s*([\d,\.]+)',           'leuco_mie'),
    (r'^META\s*:\s*([\d,\.]+)',            'leuco_meta'),
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

_RE_LIQUIDO_BIOLOGICO = re.compile(
    r'L[IÍ]QUIDO(?:S)?\s+BIOL[OÓ]GICO|L[IÍ]Q(?:UIDO)?\.\s*ASC[IÍ]TICO|'
    r'Material\s+LIQUIDO\s+DE\s+ASCITE|Material\s+LIQUIDO\s+PLEURAL',
    re.IGNORECASE,
)


def _parse_bioq(texto: str, col: _Collector) -> None:
    """Extrai exames bioquímicos (formato NOME: VALOR).
    Ignora seções de Líquidos Biológicos (ascítico, pleural)."""
    liq_ranges = [(m.start(), m.start() + 3000) for m in _RE_LIQUIDO_BIOLOGICO.finditer(texto)]

    def _in_liquido(pos: int) -> bool:
        return any(s <= pos <= e for s, e in liq_ranges)

    for pat, field in _BIOQ_PATTERNS:
        for m in re.finditer(pat, texto, re.IGNORECASE | re.MULTILINE):
            if not _in_liquido(m.start()):
                col.add(m.start(), field, _n(m.group(1)))


def _parse_gas(texto: str, col: _Collector) -> None:
    """Extrai TODOS os blocos de gasometria (formato inline sem ':').
    O terminador usa 'Conferência por Vídeo' (assinatura do laudo) em vez
    do cabeçalho de página, resolvendo o bug de quebra de página quando
    GASOMETRIA ARTERIAL cai no fim de uma folha e os dados ficam na seguinte.
    """
    for gas_m in re.finditer(
        r'(GASOMETRIA\s+(ARTERIAL|VENOSA|CAPILAR).+?'
        r'(?:Confer[eê]ncia\s+por\s+V[íi]deo|$))',
        texto, re.DOTALL | re.IGNORECASE,
    ):
        bloco = gas_m.group(1)
        pos_base = gas_m.start()
        tipo = gas_m.group(2).strip().capitalize()

        col.add(pos_base, 'gas_tipo', tipo)

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
    """Extrai hemograma — aceita GLOBAIS: ou HEMOGRAMA COMPLETO :
    Usa 'Conferência por Vídeo' como terminador para corretamente cruzar
    quebras de página quando o hemograma é divido entre páginas.
    """
    for hemo_m in re.finditer(
        r'((?:GLOBAIS|HEMOGRAMA\s+COMPLETO)\s*:.+?'
        r'(?:Confer[eê]ncia\s+por\s+V[íi]deo|$))',
        texto, re.DOTALL | re.IGNORECASE,
    ):
        bloco = hemo_m.group(1)
        pos_base = hemo_m.start()

        for pat, field in _HEMO_PATTERNS:
            for hm in re.finditer(pat, bloco, re.MULTILINE | re.IGNORECASE):
                col.add(pos_base + hm.start(), field, _n(hm.group(1)))


def _parse_coag(texto: str, col: _Collector) -> None:
    """Extrai coagulação (TTPA, TP, RNI).
    Formato de saída: "30.1s (R 1.05)" / "25.3s (AP 85% RNI 1.10)"
    """
    for m in re.finditer(r'TTPA:\s*([\d,\.]+)\s*SEG', texto, re.IGNORECASE):
        seg = _fmt(_n(m.group(1)), 1)
        r_m = re.search(r'R:\s*([\d,\.]+)', texto[m.end():m.end() + 100])
        if r_m:
            col.add(m.start(), 'ttpa', f"{seg}s (R {_fmt(_n(r_m.group(1)), 2)})")
        else:
            col.add(m.start(), 'ttpa', f"{seg}s")

    for m in re.finditer(r'\bTP:\s*([\d,\.]+)\s*SEG', texto, re.IGNORECASE):
        seg = _fmt(_n(m.group(1)), 1)
        window = texto[m.end():m.end() + 200]
        ap_m  = re.search(r'AP:\s*([\d,\.]+)%', window, re.IGNORECASE)
        rni_m = re.search(r'RNI:\s*([\d,\.]+)', window, re.IGNORECASE)
        ap_str  = f"AP {_fmt(_n(ap_m.group(1)), 0)}%"        if ap_m  else ""
        rni_str = f"RNI {_fmt(_n(rni_m.group(1)), 2)}" if rni_m else ""
        paren   = " ".join(filter(None, [ap_str, rni_str]))
        col.add(m.start(), 'tp', f"{seg}s ({paren})" if paren else f"{seg}s")


def _parse_urina(texto: str, col: _Collector) -> None:
    """Extrai EAS/urina no formato antigo (com dois-pontos)."""
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


def _parse_urina_analise(texto: str, col: _Collector) -> None:
    """Extrai EAS no formato URINA I(URINA) — sem dois-pontos.

    Formato típico do HC Unicamp:
        DENSIDADE 1013  VR: 1010 a 1025
        LEUCOCITO - ESTERASE NEGATIVO  VR: Negativo
        HEMÁCIAS 3 /campo  VR: até 5/campo
        LEUCÓCITOS INFERIOR A 1 /campo  VR: até 5/campo
    """
    _URN_ANALISE_PATTERNS: list[tuple[str, str]] = [
        (r'^DENSIDADE\s+([\d,\.]+)',                                      'ur_dens'),
        (r'^LEUC[OÓ]CITO\s*[-\s]*ESTERASE\s+(\S+)',                     'ur_le'),
        (r'^NITRITO\s+(\S+)',                                             'ur_nit'),
        (r'^PROTE[IÍ]NA\s+(\S+)',                                        'ur_prot'),
        (r'^GLICOSE\s+(\S+)',                                             'ur_glic'),
        (r'^CORPOS\s+CET[ÔO]NICOS?\s+(\S+)',                            'ur_cet'),
        (r'^HEM[AÁ]CIAS\s+(INFERIOR\s+A\s+[\d,\.]+|[\d,\.]+)',         'ur_hm'),
        (r'^LEUC[ÓO]CITOS?\s+(INFERIOR\s+A\s+[\d,\.]+|[\d,\.]+)',      'ur_leu'),
    ]

    for urn_m in re.finditer(
        r'(URINA\s+I\s*\(URINA\).+?(?:Confer[eê]ncia\s+por\s+V[íi]deo|$))',
        texto, re.DOTALL | re.IGNORECASE,
    ):
        bloco = urn_m.group(1)
        pos_base = urn_m.start()

        for pat, field in _URN_ANALISE_PATTERNS:
            for m in re.finditer(pat, bloco, re.MULTILINE | re.IGNORECASE):
                val = m.group(1).strip()
                inf_m = re.match(r'INFERIOR\s+A\s+([\d,\.]+)', val, re.IGNORECASE)
                if inf_m:
                    val = f"< {_n(inf_m.group(1))}"
                elif re.match(r'^[\d,\.]+$', val):
                    val = _n(val)
                col.add(pos_base + m.start(), field, val)


# ─────────────────────────────────────────────────────────────────────────────
# Formatação de saída — casas decimais por campo
# ─────────────────────────────────────────────────────────────────────────────

_FIELD_DECIMALS: dict[str, int] = {
    # Hemograma
    'hb': 1, 'ht': 0, 'vcm': 0, 'hcm': 0, 'rdw': 1,
    # Renal / Eletrólitos
    'cr': 1, 'ur': 0, 'na': 0, 'k': 1, 'mg': 1, 'pi': 1, 'cat': 1, 'cai': 2,
    # Hepático / Pancreático
    'tgo': 0, 'tgp': 0, 'fal': 0, 'ggt': 0,
    'bt': 1, 'bd': 1, 'alb': 1, 'prot_tot': 1, 'ldh': 0, 'amil': 0, 'lipas': 0,
    # Cardio / Inflamatório
    'pcr': 0, 'vhs': 0, 'lac': 1, 'trop': 2, 'cpk': 0, 'bnp': 0, 'fbrn': 0,
    # Gasometria
    'gas_ph': 2, 'gas_pco2': 0, 'gas_po2': 0, 'gas_hco3': 1, 'gas_be': 1,
    'gas_sat': 0, 'gas_lac': 1, 'gas_ag': 1, 'gas_cl': 0, 'gas_na': 0,
    'gas_k': 1, 'gas_cai': 2, 'gas_hb': 1, 'gas_ht': 0,
}

_DIFF_FIELDS = frozenset({
    'leuco_seg', 'leuco_bast', 'leuco_linf', 'leuco_mon',
    'leuco_eos', 'leuco_bas', 'leuco_bla', 'leuco_mie', 'leuco_meta',
})


def _aplicar_formato(coletas: list[dict]) -> list[dict]:
    """Aplica conversão de unidades e formatação de casas decimais às coletas.

    - WBC e PLT: x10³/µL → valor absoluto (ex: 5.01 → 5010)
    - Diferencial leucocitário: adiciona "%" (ex: 84 → "84%")
    - Demais campos numéricos: arredonda para casas decimais padrão clínico
    """
    for c in coletas:
        for campo in ('leuco', 'plaq'):
            if c.get(campo):
                try:
                    c[campo] = str(int(round(float(c[campo]) * 1000)))
                except (ValueError, TypeError):
                    pass

        for campo in _DIFF_FIELDS:
            if c.get(campo) and not c[campo].endswith('%'):
                c[campo] = f"{_fmt(c[campo], 0)}%"

        for field, decimals in _FIELD_DECIMALS.items():
            if c.get(field):
                c[field] = _fmt(c[field], decimals)

    return coletas


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
    _parse_urina_analise(texto, col)

    result = col.result()
    result = _aplicar_formato(result)
    return result if result else None
