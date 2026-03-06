from ._base import *
import streamlit as st

def _secao_condutas() -> list[str]:
    """
    Gera a seção '# Condutas'.
    Inclui: conduta_final_lista (manual) + condutas agregadas dos campos *_conduta (diagnósticos, sistemas, etc.).
    Cada linha recebe prefixo '- '. A conduta NUNCA aparece em Diagnósticos — só aqui.
    """
    from modules.secoes import condutas as _cond_mod

    corpo = []
    for linha in _cond_mod.coletar_condutas_agregadas():
        if linha.strip():
            corpo.append(f"- {linha.strip()}" if not linha.strip().startswith("- ") else linha.strip())

    lista = _get("conduta_final_lista").strip()
    for linha in lista.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if not linha.startswith("- "):
            linha = f"- {linha}"
        corpo.append(linha)

    if not corpo:
        return []
    return ["# Condutas"] + corpo
