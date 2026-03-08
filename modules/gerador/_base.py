import streamlit as st
from datetime import datetime

__all__ = [
    "st", "datetime",
    "_get", "_caps_para_certo", "_caps_obs_linha", "_sigla_upper",
    "_obs_para_linhas", "_calcular_dias",
]


def _caps_para_certo(val):
    """
    Converte texto em CAPS LOCK para escrita correta.
    Ex: GABRIEL -> Gabriel, TOMOGRAFIA DE CRANIO -> Tomografia de Cranio.
    Preposições (de, da, do, e, em, etc.) ficam em minúsculas.
    """
    if val is None:
        return val
    if not isinstance(val, str):
        return val
    s = str(val).strip()
    if not s:
        return val
    # Só aplica se estiver em maiúsculas (CAPS LOCK)
    if s != s.upper():
        return val
    # Não altera números ou valores numéricos
    if s.replace(".", "").replace(",", "").replace("-", "").replace("+", "").replace(" ", "").isdigit():
        return val
    # Title case com exceções para preposições em português
    exceto = {"de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "a", "o", "as", "os", "no", "na"}
    palavras = s.split()
    resultado = []
    for i, p in enumerate(palavras):
        p_lower = p.lower()
        if i > 0 and p_lower in exceto:
            resultado.append(p_lower)
        else:
            resultado.append(p_lower.capitalize())
    return " ".join(resultado)


def _caps_obs_linha(val: str) -> str:
    """
    Converte linha de obs (diagnósticos) de CAPS para forma gramatical.
    Nomes científicos de bactérias: Gênero com 1ª maiúscula, espécie em minúsculas.
    Ex: ENTEROCCOCUS FEACALIS e PROTEUS MIRABILIS -> Enterococcus faecalis e Proteus mirabilis
    """
    if val is None or not isinstance(val, str):
        return val
    s = str(val).strip()
    if not s or s != s.upper():
        return val
    exceto = {"de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "a", "o", "as", "os", "no", "na"}
    palavras = s.split()
    resultado = []
    i = 0
    while i < len(palavras):
        p = palavras[i]
        p_lower = p.lower()
        # Palavra só com letras = candidata a nome científico
        so_letras = p.replace("-", "").replace(".", "").isalpha()
        # Par GÊNERO ESPÉCIE (ambos caps, ambos não-conjunção) -> "Gênero espécie"
        if so_letras and p_lower not in exceto and i + 1 < len(palavras):
            prox = palavras[i + 1]
            prox_lower = prox.lower()
            prox_letras = prox.replace("-", "").replace(".", "").isalpha()
            if prox_letras and prox_lower not in exceto:
                resultado.append(p_lower.capitalize())
                resultado.append(prox_lower)  # espécie em minúsculas
                i += 2
                continue
        if p_lower in exceto:
            resultado.append(p_lower)
        else:
            resultado.append(p_lower.capitalize())
        i += 1
    return " ".join(resultado)


def _get(key, default=""):
    """Lê do session_state de forma segura. Normaliza CAPS LOCK em texto."""
    val = st.session_state.get(key, default)
    if isinstance(val, str) and val:
        return _caps_para_certo(val)
    return val


def _obs_para_linhas(obs: str, excluir_conduta: bool = False) -> list[str]:
    """
    Converte o campo obs (multiline) em linhas prefixadas com '> '.
    Se excluir_conduta=True, não inclui linhas que começam com 'Conduta:' (vão para Condutas Registradas).
    Cada linha é convertida de CAPS para forma gramatical (evitar tudo em maiúsculas).
    """
    linhas = []
    raw_obs = obs if isinstance(obs, str) else ""
    for linha in raw_obs.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if excluir_conduta and linha.lower().startswith("conduta:"):
            continue
        # Remove marcadores de lista ("- " ou "• ") que precedem o texto
        if linha.startswith("- "):
            linha = linha[2:].strip()
        elif linha.startswith("• "):
            linha = linha[2:].strip()
        linha = _caps_obs_linha(linha)
        linhas.append(f"> {linha}")
    return linhas


def _calcular_dias(data_ini: str, data_fim: str) -> str:
    """Calcula diferença em dias entre duas datas DD/MM/AAAA. Retorna '' se não for possível."""
    try:
        d1 = datetime.strptime(data_ini.strip(), "%d/%m/%Y")
        d2 = datetime.strptime(data_fim.strip(), "%d/%m/%Y")
        dias = (d2 - d1).days
        if dias > 0:
            return f"{dias} dias"
    except Exception:
        pass
    return ""


def _sigla_upper(val: str) -> str:
    """Retorna sigla em maiúsculas se for 2-5 letras (CVC, SVD, ITU, PAV)."""
    if not val or not isinstance(val, str):
        return val
    s = val.strip()
    if 2 <= len(s) <= 5 and s.replace(" ", "").isalpha():
        return s.upper()
    return val
