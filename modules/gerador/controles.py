from ._base import *
import streamlit as st

def _secao_controles() -> list[str]:
    """
    Gera a saída determinística dos Controles & Balanço Hídrico.

    Por dia:
        > {data}
        {linha vitais: campos preenchidos com ' | '}
        {Diurese x | BH x}
    """
    _PARAMS_MM = [
        ("PAS",   "pas"),   ("PAD",   "pad"),   ("PAM",   "pam"),
        ("FC",    "fc"),    ("FR",    "fr"),     ("SatO2", "sato2"),
        ("Temp",  "temp"),  ("Dextro", "glic"),
    ]

    def _linha_dia(dia):
        data    = _get(f"ctrl_{dia}_data").strip()
        vitais  = []
        for label, chave in _PARAMS_MM:
            vmin = _get(f"ctrl_{dia}_{chave}_min").strip()
            vmax = _get(f"ctrl_{dia}_{chave}_max").strip()
            if vmin and vmax:
                vitais.append(f"{label} {vmin}-{vmax}")
            elif vmin:
                vitais.append(f"{label} {vmin}")
        diurese = _get(f"ctrl_{dia}_diurese").strip()
        balanco = _get(f"ctrl_{dia}_balanco").strip()

        if not any([data, vitais, diurese, balanco]):
            return None

        linhas = []
        if data:
            linhas.append(f">{data}")
        if vitais:
            linhas.append(" | ".join(vitais))
        bh_parts = []
        if diurese:
            bh_parts.append(f"Diurese {diurese}")
        if balanco:
            bh_parts.append(f"BH {balanco}")
        if bh_parts:
            linhas.append(" | ".join(bh_parts))
        return linhas

    dias = ["hoje", "ontem", "anteontem", "ant4", "ant5"]
    slots = [s for d in dias for s in [_linha_dia(d)] if s]

    if not slots:
        return []

    periodo = (_get("ctrl_periodo") or "24 horas").strip()
    resultado = ["# Controles & Balanço Hídrico"]
    if periodo == "12 horas":
        resultado.append(">> 12 horas <<")
        resultado.append("")
    for slot in slots:
        resultado.extend(slot)

    return resultado
