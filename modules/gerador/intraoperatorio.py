from ._base import *
import re


def _parse_vol(val: str) -> int:
    """Extrai inteiro de string de volume: '500', '500ml', '500 ml' → 500. Retorna 0 se inválido."""
    if not val:
        return 0
    m = re.search(r'\d+', str(val))
    return int(m.group()) if m else 0


def _secao_intraoperatorio() -> list[str]:
    """
    Gera a seção '# Intraoperatório'.

    Formato de saída:
        # Intraoperatório
        Cirurgia: ...; Data: ...
        Duração total: ...
        Entradas: Solução Xml, Solução Xml
        Saídas: Diurese -Xml, Solução -Xml
        Balanço Total: ±Xml | Diurese: -Xml
        Intercorrências: ...
        Obs: ...
    """
    cirurgia        = _get("io_cirurgia").strip()
    data            = _get("io_data").strip()
    duracao         = _get("io_duracao").strip()
    diurese_vol     = _parse_vol(_get("io_diurese"))
    intercorrencias = _get("io_intercorrencias").strip()
    obs             = _get("io_obs").strip()

    # ── Entradas ──────────────────────────────────────────────────────────────
    entradas_parts = []
    total_ent = 0
    for i in range(1, 6):
        sol = _get(f"io_ent_{i}_sol").strip()
        vol = _parse_vol(_get(f"io_ent_{i}_vol"))
        if sol and vol:
            entradas_parts.append(f"{sol} {vol}ml")
            total_ent += vol

    # ── Saídas ────────────────────────────────────────────────────────────────
    # Diurese aparece primeiro na linha de Saídas
    saidas_parts = []
    total_sai = 0
    if diurese_vol:
        saidas_parts.append(f"Diurese -{diurese_vol}ml")
        total_sai += diurese_vol
    for i in range(1, 5):
        sol = _get(f"io_sai_{i}_sol").strip()
        vol = _parse_vol(_get(f"io_sai_{i}_vol"))
        if sol and vol:
            saidas_parts.append(f"{sol} -{vol}ml")
            total_sai += vol

    # ── Verifica se há conteúdo ───────────────────────────────────────────────
    tem_conteudo = any([cirurgia, data, duracao, entradas_parts, saidas_parts,
                        intercorrencias, obs])
    if not tem_conteudo:
        return []

    linhas = ["# Intraoperatório"]

    # Cirurgia + Data
    cab = []
    if cirurgia:
        cab.append(f"Cirurgia: {cirurgia}")
    if data:
        cab.append(f"Data: {data}")
    if cab:
        linhas.append("; ".join(cab))

    if duracao:
        linhas.append(f"Duração total: {duracao}")

    if entradas_parts:
        linhas.append("Entradas: " + ", ".join(entradas_parts))

    if saidas_parts:
        linhas.append("Saídas: " + ", ".join(saidas_parts))

    # Balanço Total (calculado automaticamente, pode ser negativo)
    if entradas_parts or saidas_parts:
        balanco = total_ent - total_sai
        bal_str = f"+{balanco}ml" if balanco > 0 else f"{balanco}ml"
        diu_str = f" | Diurese: -{diurese_vol}ml" if diurese_vol else ""
        linhas.append(f"Balanço Total: {bal_str}{diu_str}")

    if intercorrencias:
        linhas.append(f"Intercorrências: {intercorrencias}")

    if obs:
        linhas.append(f"Obs: {obs}")

    return linhas
