"""
Parser determinístico para exames laboratoriais no formato padronizado:

  DD/MM/YYYY – Hb 8,8 | Ht 27% | VCM 96 | ... | Urn: Den: 1.010 / Leu Est: Neg / ...
  externo – Hb 8,8 | Ht 27% | ...   (ou admissão, adm, admissionais, externos → slot 4)

- Começa com data (DD/MM/YYYY) ou palavra-chave (admissão/adm/admissionais/externo/externos)
- Pares Sigla Valor separados por |
- Leuco pode ter diferencial entre parênteses
- Urn: tem sub-pares Den: x / Leu Est: x / ...
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


# Palavras-chave que vão para slot 4 (Laboratoriais Admissão / Externo)
_LAB_EXTERNO_KEYWORDS = frozenset(
    w.lower() for w in [
        "admissão", "admissao", "adm", "admissionais", "admissional",
        "externo", "externos", "externa", "externas",
    ]
)


# Ordem: siglas mais longas primeiro (Prot Tot antes de Prot)
_SIGLAS_CAMPOS = [
    ("Prot Tot", "prot_tot"), ("CPK-MB", "cpk_mb"), ("Leu Est", "ur_le"),
    ("Hb", "hb"), ("Ht", "ht"), ("VCM", "vcm"), ("HCM", "hcm"), ("RDW", "rdw"),
    ("Leuco", "leuco"), ("Plaq", "plaq"), ("Cr", "cr"), ("Ur", "ur"),
    ("Na", "na"), ("K", "k"), ("Mg", "mg"), ("Pi", "pi"), ("CaT", "cat"), ("Cai", "cai"),
    ("TGP", "tgp"), ("TGO", "tgo"), ("FAL", "fal"), ("GGT", "ggt"),
    ("BT", "bt"), ("BD", "bd"), ("Alb", "alb"), ("Amil", "amil"), ("Lipas", "lipas"),
    ("CPK", "cpk"), ("BNP", "bnp"), ("Trop", "trop"), ("PCR", "pcr"), ("VHS", "vhs"),
    ("TP", "tp"), ("TTPa", "ttpa"),
]


def _extrair_par_sigla_valor(token: str) -> list[tuple[str, str]]:
    """
    Extrai (campo, valor) de um token como "Hb 8,8" ou "Leuco 16.640 (Bast 1% / ...)".
    Pode retornar 2 pares para BT 1,0 (0,3) → bt e bd.
    """
    token = token.strip()
    if not token:
        return []
    for sigla, campo in _SIGLAS_CAMPOS:
        if token.startswith(sigla + " "):
            valor = token[len(sigla):].strip()
            if not valor:
                return []
            if campo == "bt" and "(" in valor and ")" in valor:
                m = re.match(r"^([^(]+)\s*\(([^)]+)\)\s*$", valor)
                if m:
                    return [("bt", m.group(1).strip()), ("bd", m.group(2).strip())]
            return [(campo, valor)]
    return []


def _parse_urn(resto: str) -> dict[str, str]:
    """Parseia bloco Urn: Den: x / Leu Est: x / Leuco 1.000.000 / Hm : 702.000 / ..."""
    out = {}
    # Chaves conhecidas (ordem: mais longas primeiro)
    urn_map = [
        ("Leu Est", "ur_le"), ("Den", "ur_dens"), ("Nit", "ur_nit"),
        ("Leuco", "ur_leu"), ("Hm", "ur_hm"), ("Prot", "ur_prot"),
        ("Cet", "ur_cet"), ("Glic", "ur_glic"),
    ]
    partes = re.split(r"\s*/\s*", resto)
    for p in partes:
        p = p.strip()
        for chave, campo in urn_map:
            if p.startswith(chave):
                suf = p[len(chave):].strip()
                # Suf pode ser ": 702.000" ou "1.000.000" (Leuco sem colon)
                val = suf.lstrip(": ").strip() if suf.startswith(":") else suf
                if val:
                    out[campo] = val
                break
    return out


def _parse_linha_exame(linha: str) -> tuple[str, dict[str, str], int | None] | None:
    """
    Parseia uma linha no formato: DD/MM/YYYY – Hb 8,8 | ... ou externo – Hb 8,8 | ...
    Retorna (prefix_str, dict de campo->valor, slot_fixo) ou None.
    slot_fixo: None = calcular por data; 4 = forçar slot 4 (admissão/externo).
    """
    linha = linha.strip()
    if not linha:
        return None

    # Formato: PREFIX – resto (PREFIX = data ou palavra-chave)
    m = re.match(r"^([^\s–\-]+(?:\s+[^\s–\-]+)?)\s*[–\-]\s*(.*)$", linha, re.DOTALL)
    if not m:
        return None

    prefix = m.group(1).strip()
    resto = m.group(2).strip()

    # Verifica se é palavra-chave para slot 4 (admissão/externo)
    primeira = prefix.split()[0].lower() if prefix else ""
    if primeira in _LAB_EXTERNO_KEYWORDS:
        data_str = prefix  # ex: "Externo" ou "Admissão"
        slot_fixo = 4
    else:
        # Tenta interpretar como data
        data_str = prefix
        slot_fixo = None
    if not resto:
        return (data_str, {}, slot_fixo)

    resultado = {}

    # Tokens separados por |
    tokens = [t.strip() for t in resto.split("|") if t.strip()]

    for tok in tokens:
        if tok.startswith("Urn:"):
            urn_bloco = tok[4:].strip()  # remove "Urn:"
            for k, v in _parse_urn(urn_bloco).items():
                resultado[k] = v
            continue
        pares = _extrair_par_sigla_valor(tok)
        for campo, valor in pares:
            resultado[campo] = valor

    return (data_str, resultado, slot_fixo)


def _slot_por_data(data_exame: date, data_hoje: date) -> int:
    """
    Mapeia data do exame para slot (1-10).
    Slot 1 = hoje, 2 = ontem, 3 = anteontem, 4 = Laboratoriais Externos, 5+ = mais antigos.
    """
    delta = (data_hoje - data_exame).days
    if delta == 0:
        return 1  # Hoje
    if delta == 1:
        return 2  # Ontem
    if delta == 2:
        return 3  # Anteontem
    if delta in (3, 4):
        return 4  # Laboratoriais Externos (entre anteontem e 5 dias)
    if delta >= 5:
        # 5 dias atrás = slot 5, 6 dias = slot 6, etc.
        return min(4 + (delta - 4), 10)
    return 4  # Data futura (improvável) → Lab Externos


def parse_lab_deterministico(
    texto: str,
    data_hoje: Optional[date] = None,
) -> dict[str, str]:
    """
    Parseia texto de exames no formato padronizado e retorna dict para session_state.
    Chaves: lab_{slot}_{campo} = valor.
    data_hoje: data de referência (hoje). Se None, usa date.today().
    """
    if data_hoje is None:
        data_hoje = date.today()

    resultado = {}
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]

    for ln in linhas:
        parsed = _parse_linha_exame(ln)
        if not parsed:
            continue
        data_str, campos, slot_fixo = parsed

        if slot_fixo is not None:
            slot = slot_fixo  # admissão/externo → slot 4
        else:
            data_exame = _parse_data_br(data_str)
            if not data_exame:
                continue
            slot = _slot_por_data(data_exame, data_hoje)

        resultado[f"lab_{slot}_data"] = data_str
        for campo, valor in campos.items():
            resultado[f"lab_{slot}_{campo}"] = valor

    return resultado
