"""
Parser determinístico para exames laboratoriais.

Duas funções públicas:
- parse_lab_deterministico(texto, data_hoje)   → texto livre do usuário
- parse_agentes_para_slot(resultados, slot)     → saída dos agentes PACER

Formato aceito por parse_lab_deterministico:

  DD/MM/YYYY – Hb 8,8 | Ht 27% | VCM 96 | ... | Urn: Den: 1.010 / Leu Est: Neg / ...
  externo – Hb 8,8 | Ht 27% | ...   (ou admissão, adm, admissionais, externos → slot 4)

- Começa com data (DD/MM/YYYY) ou palavra-chave (admissão/adm/admissionais/externo/externos)
- Pares Sigla Valor separados por |
- Leuco pode ter diferencial entre parênteses
- Urn: tem sub-pares Den: x / Leu Est: x / ...

Atribuição de slot por ORDEM DE APARIÇÃO no texto:
  Linhas com data: 1ª → slot 1, 2ª → slot 2, 3ª → slot 3, 4ª → slot 5, ... (slot 4 reservado)
  Linhas admissão/externo: sempre slot 4 (independente da posição)
"""
import re
from datetime import datetime, date
from typing import Optional


def _parse_data_br(data_str: str) -> Optional[str]:
    """Converte DD/MM/YYYY ou DD/MM/YY para string normalizada DD/MM/YYYY. Retorna None se inválido."""
    data_str = data_str.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            d = datetime.strptime(data_str, fmt).date()
            return d.strftime("%d/%m/%Y")
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


# Slots para linhas de data (em ordem); slot 4 é reservado para admissão/externo
_SLOTS_DATA_ORDEM = [1, 2, 3, 5, 6, 7, 8, 9, 10]


def parse_lab_deterministico(
    texto: str,
    data_hoje: Optional[date] = None,
) -> dict[str, str]:
    """
    Parseia texto de exames no formato padronizado e retorna dict para session_state.
    Chaves: lab_{slot}_{campo} = valor.

    Os slots são atribuídos por ORDEM DE APARIÇÃO no texto:
      - Linhas com admissão/externo: sempre slot 4
      - Linhas com data: 1ª → slot 1, 2ª → slot 2, 3ª → slot 3, 4ª → slot 5, ...
        (a data serve apenas para preencher lab_{slot}_data — não define o slot)

    data_hoje: mantido por compatibilidade de assinatura, ignorado.
    """
    resultado = {}
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]

    slot_idx = 0  # índice em _SLOTS_DATA_ORDEM

    for ln in linhas:
        parsed = _parse_linha_exame(ln)
        if not parsed:
            continue
        data_str, campos, slot_fixo = parsed

        if slot_fixo is not None:
            slot = slot_fixo  # admissão/externo → sempre slot 4
        else:
            # Valida que tem ao menos uma data ou texto reconhecível
            if not data_str:
                continue
            if slot_idx >= len(_SLOTS_DATA_ORDEM):
                break
            slot = _SLOTS_DATA_ORDEM[slot_idx]
            slot_idx += 1

        # Grava a data no slot (normaliza se possível, mantém texto original para adm/externo)
        data_normalizada = _parse_data_br(data_str) if slot_fixo is None else None
        resultado[f"lab_{slot}_data"] = data_normalizada if data_normalizada else data_str
        for campo, valor in campos.items():
            resultado[f"lab_{slot}_{campo}"] = valor

    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# Parser formato resumido (Valdelita-style): por slot
# ─────────────────────────────────────────────────────────────────────────────

_GAS_TIPO_MAP = {
    "art": "Arterial", "arterial": "Arterial",
    "ven": "Venosa",   "venosa":   "Venosa",
    "par": "Pareada",  "pareada":  "Pareada", "mis": "Pareada",
}

_GAS_PARAMS = [
    # (regex_pattern, campo_arterial, campo_venoso)
    # pCO2: campo diferente para venosa vs. arterial
    (r"^pCO2\s+([0-9,.\-+]+)$",          "gas_pco2",  "gasv_pco2"),
    (r"^pH\s+([0-9,.\-+]+)$",            "gas_ph",    "gas_ph"),
    (r"^pO2\s+([0-9,.\-+]+)$",           "gas_po2",   "gas_po2"),
    (r"^(?:HCO3|Bic)\s+([0-9,.\-+]+)$", "gas_hco3",  "gas_hco3"),
    (r"^BE\s+([0-9,.\-+]+)$",            "gas_be",    "gas_be"),
    (r"^SvO2\s+([0-9,.]+)%?$",           "svo2",      "svo2"),
    (r"^(?:SatO2|Sat)\s+([0-9,.]+)%?$",  "gas_sat",   "gas_sat"),
    (r"^Lac\s+([0-9,.]+)$",              "gas_lac",   "gas_lac"),
    (r"^AG\s+([0-9,.]+)$",               "gas_ag",    "gas_ag"),
    (r"^Cl\s+([0-9,.]+)$",               "gas_cl",    "gas_cl"),
    (r"^Na\s+([0-9,.]+)$",               "gas_na",    "gas_na"),
    (r"^K\s+([0-9,.]+)$",                "gas_k",     "gas_k"),
    (r"^(?:Cai|CaI)\s+([0-9,.]+)$",      "gas_cai",   "gas_cai"),
]
# Pré-compilar
_GAS_PARAMS_C = [(re.compile(p, re.IGNORECASE), ca, cv) for p, ca, cv in _GAS_PARAMS]


def _parse_gas_linha(linha: str, slot: int, resultado: dict) -> bool:
    """
    Tenta parsear linha de gasometria no formato:
        Gas TYPE (HHh) pH 7,38 / pCO2 39 / HCO3 22 / ...
    Retorna True se a linha foi reconhecida como gasometria.
    """
    m = re.match(
        r"^Gas\s+(\w+)\s+\(([0-9]{1,2}[h:][0-9]{0,2})\)\s+(.+)$",
        linha, re.IGNORECASE,
    )
    if not m:
        return False

    tipo_raw = m.group(1).lower()
    hora     = m.group(2)
    partes   = [p.strip() for p in m.group(3).split("/") if p.strip()]
    tipo     = _GAS_TIPO_MAP.get(tipo_raw, "Arterial")
    is_ven   = tipo == "Venosa"

    resultado[f"lab_{slot}_gas_tipo"] = tipo
    resultado[f"lab_{slot}_gas_hora"] = hora

    for part in partes:
        for pat, campo_art, campo_ven in _GAS_PARAMS_C:
            mm = pat.match(part)
            if mm:
                campo = campo_ven if is_ven else campo_art
                resultado[f"lab_{slot}_{campo}"] = mm.group(1)
                break
    return True


def parse_lab_exames_dia(texto: str, slot: int) -> dict:
    """
    Parseia texto no formato resumido de laudo para UM slot específico.

    Formato aceito:
        [Nome Paciente Prontuário]            ← ignorado
        DD/MM/YYYY – Hb 8,2 | Ht 25% | ...  ← data + parâmetros
        TGO 14 | TGP 11 | PCR 89 | ...       ← continuação (sem data)
        Gas Ven (04h) pH 7,38 / pCO2 39 / …  ← gasometria
        Não Transcritos: ...                  ← ignorado

    Mapeia todos os valores para lab_{slot}_*.
    """
    resultado: dict[str, str] = {}
    if not texto or not texto.strip():
        return resultado

    def _apply_tokens(tokens: list[str]) -> None:
        for tok in tokens:
            tok = tok.strip()
            if not tok:
                continue
            if tok.lower().startswith("urn:"):
                for k, v in _parse_urn(tok[4:].strip()).items():
                    resultado[f"lab_{slot}_{k}"] = v
                continue
            for campo, valor in _extrair_par_sigla_valor(tok):
                resultado[f"lab_{slot}_{campo}"] = valor

    for linha in texto.strip().splitlines():
        linha = linha.strip()
        if not linha:
            continue

        # Ignorar linhas de "Não Transcritos"
        if re.match(r"^n[aã]o\s+transcritos", linha, re.IGNORECASE):
            continue

        # Gasometria
        if _parse_gas_linha(linha, slot, resultado):
            continue

        # Linha com data: DD/MM/YYYY – params
        m_data = re.match(
            r"^(\d{1,2}/\d{1,2}/\d{2,4})\s*[–\-]\s*(.+)$", linha, re.DOTALL,
        )
        if m_data:
            data_fmt = _parse_data_br(m_data.group(1))
            if data_fmt and f"lab_{slot}_data" not in resultado:
                resultado[f"lab_{slot}_data"] = data_fmt
            _apply_tokens([t.strip() for t in m_data.group(2).split("|")])
            continue

        # Linha de continuação (sem data): tenta parsear como tokens
        _apply_tokens([t.strip() for t in linha.split("|")])

    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# Parsers de saída dos agentes PACER (Grupo 2)
# ─────────────────────────────────────────────────────────────────────────────

def _norm(v: str) -> str:
    """Normaliza valor numérico: troca vírgula por ponto e remove espaços."""
    return v.strip().replace(",", ".")


def _parse_simples(texto: str, mapa: dict[str, str]) -> dict[str, str]:
    """
    Parseia texto no formato "Sigla Valor | Sigla Valor".
    Para cada token, captura o valor até '|' ou '(' (exclui parênteses).
    mapa: {sigla -> chave_lab}
    """
    if not texto:
        return {}
    out = {}
    tokens = re.split(r"\|", texto)
    for tok in tokens:
        tok = tok.strip()
        for sigla, chave in mapa.items():
            pat = re.compile(
                rf"(?<![A-Za-z]){re.escape(sigla)}\s+([^|(]+)",
                re.IGNORECASE,
            )
            m = pat.search(tok)
            if m:
                val = m.group(1).strip()
                if val:
                    out[chave] = _norm(val)
                break
    return out


# Mapeamento agente hematologia_renal → chaves lab
_MAPA_HEMATO_RENAL = {
    "Hb": "hb", "Ht": "ht", "VCM": "vcm", "HCM": "hcm", "RDW": "rdw",
    "Leuco": "leuco", "Plaq": "plaq",
    "Cr": "cr", "Ur": "ur", "Na": "na", "K": "k",
    "Mg": "mg", "Pi": "pi", "CaT": "cat", "Cai": "cai",
}

# Mapeamento agente coagulacao → chaves lab
# O agente retorna: PCR 89 | TP 14,2s (1,22) | TTPa 69,1s (2,49) | Trop 0,01 | CPK 150 | CK-MB 12
# _parse_simples captura até '(' → pega só "14,2s" para TP, sem o RNI
_MAPA_COAG = {
    "PCR": "pcr", "Trop": "trop", "CPK": "cpk", "CK-MB": "cpk_mb",
    "TP": "tp", "TTPa": "ttpa",
}


def _parse_hepatico(texto: str) -> dict[str, str]:
    """
    Parseia saída do agente hepático.
    Formato: TGO 40 | TGP 55 | BT 1,0 (0,3) | FAL 80 | GGT 90 | Alb 3,5 | Amil 60 | Lipas 70 | Prot Tot 6,5
    BT X (Y) → bt=X, bd=Y
    """
    if not texto:
        return {}
    out = {}
    mapa = {
        "TGO": "tgo", "TGP": "tgp", "FAL": "fal", "GGT": "ggt",
        "Alb": "alb", "Amil": "amil", "Lipas": "lipas", "Prot Tot": "prot_tot",
    }
    tokens = [t.strip() for t in texto.split("|")]
    for tok in tokens:
        # BT especial: BT X (Y) → bt + bd
        m_bt = re.match(r"(?i)BT\s+([\d,\.]+)\s*\(([\d,\.]+)\)", tok)
        if m_bt:
            out["bt"] = _norm(m_bt.group(1))
            out["bd"] = _norm(m_bt.group(2))
            continue
        m_bd = re.match(r"(?i)BD\s+([\d,\.]+)", tok)
        if m_bd:
            out["bd"] = _norm(m_bd.group(1))
            continue
        m_bt2 = re.match(r"(?i)BT\s+([\d,\.]+)", tok)
        if m_bt2:
            out["bt"] = _norm(m_bt2.group(1))
            continue
        for sigla, chave in mapa.items():
            if re.match(rf"(?i){re.escape(sigla)}\s+", tok):
                val = tok[len(sigla):].strip()
                if val:
                    out[chave] = _norm(val)
                break
    return out


def _parse_urina(texto: str) -> dict[str, str]:
    """
    Parseia saída do agente de urina.
    Formato: Den: 1.020 / Leu Est: Neg / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Neg / Cet: Neg / Glic: Neg
    Ou formato alternativo com | como separador.
    """
    if not texto:
        return {}
    out = {}
    urn_map = [
        ("Leu Est", "ur_le"), ("Den", "ur_dens"), ("Nit", "ur_nit"),
        ("Leuco", "ur_leu"), ("Hm", "ur_hm"), ("Prot", "ur_prot"),
        ("Cet", "ur_cet"), ("Glic", "ur_glic"),
    ]
    # Remove prefixo "Urn:" se presente
    texto = re.sub(r"(?i)^Urn:\s*", "", texto.strip())
    partes = re.split(r"[/|]", texto)
    for p in partes:
        p = p.strip()
        for chave, campo in urn_map:
            if re.match(rf"(?i){re.escape(chave)}\s*[:\s]", p):
                val = re.sub(rf"(?i)^{re.escape(chave)}\s*[:\s]\s*", "", p).strip()
                if val:
                    out[campo] = val
                break
    return out


def _extrair_campos_gas(texto: str) -> dict[str, str]:
    """
    Extrai campos de uma linha de gasometria no formato do agente:
      "pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / ..."
    Retorna dict com chaves de sufixo (ph, pco2, po2, hco3, be, sat, svo2, lac, ag, cl, na, k, cai).
    """
    valores: dict[str, str] = {}
    mapa = [
        (r"(?i)\bpH\s+([\d,\.]+)",       "ph"),
        (r"(?i)\bpCO2\s+([\d,\.]+)",     "pco2"),
        (r"(?i)\bpO2\s+([\d,\.]+)",      "po2"),
        (r"(?i)\bHCO3\s+([\d,\.]+)",     "hco3"),
        (r"(?i)\bBE\s+(-?[\d,\.]+)",     "be"),
        (r"(?i)\bSatO2\s+([\d,\.]+)",    "sat"),
        (r"(?i)\bSvO2\s+([\d,\.]+)",     "svo2"),
        (r"(?i)\bLac\s+([\d,\.]+)",      "lac"),
        (r"(?i)\bAG\s+([\d,\.]+)",       "ag"),
        (r"(?i)\bCl\s+([\d,\.]+)",       "cl"),
        (r"(?i)\bNa\s+([\d,\.]+)",       "na"),
        (r"(?i)\bK\s+([\d,\.]+)",        "k"),
        (r"(?i)\bCai\s+([\d,\.]+)",      "cai"),
    ]
    tokens = [t.strip() for t in re.split(r"/", texto)]
    for tok in tokens:
        for pattern, campo in mapa:
            m = re.search(pattern, tok)
            if m:
                val = _norm(m.group(1).rstrip("%"))
                if val:
                    valores[campo] = val
                break
    return valores


def _parse_gasometria(texto: str, slot: int) -> dict[str, str]:
    """
    Parseia saída do agente de gasometria para um slot.

    Formato real do agente (separado por newline para múltiplas leituras):
      Gas Art (04h) pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15
      Gas Ven (10h) pH 7,31 / pCO2 48 / HCO3 24 / BE -1,5 / SvO2 70% / Lac 1,8
      Gas Par (04h) pH 7,35 / ... | pCO2 48 / SvO2 70%

    Mapeamento de prefixos por índice (i):
      i=1 → lab_{slot}_gas_*  (svo2 → lab_{slot}_svo2, venosa pco2 → lab_{slot}_gasv_pco2)
      i=2 → lab_{slot}_gas2_* (svo2 → lab_{slot}_gas2_svo2, venosa pco2 → lab_{slot}_gas2v_pco2)
      i=3 → lab_{slot}_gas3_* (svo2 → lab_{slot}_gas3_svo2, venosa pco2 → lab_{slot}_gas3v_pco2)
    """
    if not texto:
        return {}
    out = {}

    linhas = [
        ln.strip() for ln in texto.splitlines()
        if ln.strip() and ln.strip().upper() != "VAZIO"
    ]

    def _pfx(i: int) -> str:
        return f"lab_{slot}_gas" if i == 1 else f"lab_{slot}_gas{i}"

    def _svo2_key(i: int) -> str:
        return f"lab_{slot}_svo2" if i == 1 else f"lab_{slot}_gas{i}_svo2"

    def _gasv_pco2_key(i: int) -> str:
        return f"lab_{slot}_gasv_pco2" if i == 1 else f"lab_{slot}_gas{i}v_pco2"

    for i, linha in enumerate(linhas[:3], start=1):
        pfx = _pfx(i)

        # Detecta tipo a partir do prefixo "Gas Art / Gas Ven / Gas Par"
        tipo = ""
        if re.search(r"Gas\s+Art", linha, re.I):
            tipo = "Arterial"
        elif re.search(r"Gas\s+Ven", linha, re.I):
            tipo = "Venosa"
        elif re.search(r"Gas\s+Par", linha, re.I):
            tipo = "Pareada"

        # Extrai hora do padrão (04h)
        m_hora = re.search(r"\((\d{1,2})h\)", linha, re.I)
        hora = (m_hora.group(1).zfill(2) + "h") if m_hora else ""

        # Separa parte arterial da venosa (pareada usa '|')
        if "|" in linha:
            parte_art, parte_ven = linha.split("|", 1)
        else:
            parte_art = linha
            parte_ven = ""

        # Extrai valores da parte principal
        valores = _extrair_campos_gas(parte_art)

        if tipo:
            out[f"{pfx}_tipo"] = tipo
        if hora:
            out[f"{pfx}_hora"] = hora

        for campo, val in valores.items():
            if campo == "svo2":
                out[_svo2_key(i)] = val
            else:
                out[f"{pfx}_{campo}"] = val

        # Extrai pCO2 e SvO2 da parte venosa (pareada)
        if parte_ven:
            ven_vals = _extrair_campos_gas(parte_ven)
            if "pco2" in ven_vals:
                out[_gasv_pco2_key(i)] = ven_vals["pco2"]
            if "svo2" in ven_vals:
                out[_svo2_key(i)] = ven_vals["svo2"]

    return out


def parse_agentes_para_slot(resultados: dict[str, Optional[str]], slot: int) -> dict[str, str]:
    """
    Recebe o dict de saídas dos 7 agentes PACER e retorna um dict
    com chaves lab_{slot}_* prontas para atualizar o session_state.

    Chaves esperadas em resultados:
      hematologia_renal, hepatico, coagulacao, urina,
      gasometria, nao_transcritos, data_coleta
    """
    out: dict[str, str] = {}

    def _merge(d: dict[str, str]) -> None:
        for k, v in d.items():
            if v:
                out[k] = v

    pfx = f"lab_{slot}_"

    # Hematologia + Renal
    hemato = _parse_simples(resultados.get("hematologia_renal") or "", _MAPA_HEMATO_RENAL)
    _merge({pfx + k: v for k, v in hemato.items()})

    # Hepático
    hepatico = _parse_hepatico(resultados.get("hepatico") or "")
    _merge({pfx + k: v for k, v in hepatico.items()})

    # Coagulação (inclui PCR, Trop, CPK, CK-MB, TP, TTPa)
    coag = _parse_simples(resultados.get("coagulacao") or "", _MAPA_COAG)
    _merge({pfx + k: v for k, v in coag.items()})

    # Urina
    urina = _parse_urina(resultados.get("urina") or "")
    _merge({pfx + k: v for k, v in urina.items()})

    # Gasometria (chaves já incluem lab_{slot}_)
    gas = _parse_gasometria(resultados.get("gasometria") or "", slot)
    _merge(gas)

    # nao_transcritos retorna apenas NOMES de exames (sem valores) → ignorado

    # Data de coleta (7º agente) — sinaliza para tab_laboratoriais
    data_coleta = (resultados.get("data_coleta") or "").strip()
    if data_coleta and data_coleta.upper() != "VAZIO":
        out[f"_data_coleta_slot_{slot}"] = data_coleta

    return out
