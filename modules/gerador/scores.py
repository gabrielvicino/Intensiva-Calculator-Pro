from ._base import _get


def _secao_scores() -> list[str]:
    """
    Gera as linhas da seção '# Scores Clínicos'.
    Campos vazios/zero não geram linha.
    """
    corpo = []

    # ── SAPS ────────────────────────────────────────────────────────────────
    saps_partes = []
    saps3 = _get("saps3")
    if saps3:
        saps_partes.append(f"SAPS 3: {saps3}")
    saps2 = _get("saps2")
    if saps2:
        saps_partes.append(f"SAPS 2: {saps2}")
    if saps_partes:
        corpo.append("  ".join(saps_partes))

    # ── APACHE ──────────────────────────────────────────────────────────────
    apache_partes = []
    apache3 = _get("apache3")
    if apache3:
        apache_partes.append(f"APACHE 3: {apache3}")
    apache2 = _get("apache2")
    if apache2:
        apache_partes.append(f"APACHE 2: {apache2}")
    apache4 = _get("apache4")
    if apache4:
        apache_partes.append(f"APACHE 4: {apache4}")
    if apache_partes:
        corpo.append("  ".join(apache_partes))

    # ── SOFA — admissão + cadeia de evolução ────────────────────────────────
    sofa_adm = _get("sofa_adm", 0)
    try:
        sofa_adm = int(sofa_adm)
    except (ValueError, TypeError):
        sofa_adm = 0

    sofa_vals = []
    for i in range(1, 5):
        v = _get(f"sofa_d{i}", 0)
        try:
            v = int(v)
        except (ValueError, TypeError):
            v = 0
        if v:
            sofa_vals.append(v)

    if sofa_adm and sofa_vals:
        chain = " → ".join(str(v) for v in [sofa_adm] + sofa_vals)
        corpo.append(f"SOFA Admissão: {sofa_adm}  EVOLUÇÃO DO SOFA: {chain}")
    elif sofa_adm:
        corpo.append(f"SOFA Admissão: {sofa_adm}")

    # ── PPS ─────────────────────────────────────────────────────────────────
    pps = _get("pps")
    if pps:
        corpo.append(f"PPS: {pps}")

    # ── mRS ─────────────────────────────────────────────────────────────────
    mrs = _get("mrs")
    if mrs:
        corpo.append(f"mRS prévio: {mrs}")

    # ── CFS ─────────────────────────────────────────────────────────────────
    cfs = _get("cfs")
    if cfs:
        corpo.append(f"CFS: {cfs}")

    if not corpo:
        return []
    return ["# Scores Clínicos"] + corpo
