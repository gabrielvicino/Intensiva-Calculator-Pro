import streamlit as st
from datetime import datetime

__all__ = [
    "st", "datetime",
    "_get", "_caps_para_certo", "_caps_obs_linha", "_sigla_upper",
    "_obs_para_linhas", "_calcular_dias",
]


# Palavras curtas do português que NÃO são siglas — ficam em minúsculas / title case normal
_PALAVRAS_COMUNS_PT = {
    # artigos
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    # preposições
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "por", "pelo", "pela", "pelos", "pelas", "para", "com", "sem",
    "sob", "num", "numa", "ao", "aos",
    # conjunções / conectivos
    "e", "ou", "mas", "que", "se", "nem", "pois", "logo",
    # pronomes / determinantes
    "eu", "tu", "ele", "ela", "lhe", "seu", "sua", "seus", "suas",
    # advérbios / outros comuns curtos
    "dia", "vez", "fim", "mal", "bem", "bom", "boa", "sim",
    "uso", "via", "pos", "pre", "pra", "ali", "ato", "ago",
    "mes", "ano", "ate", "apos", "nao",
}


def _caps_para_certo(val):
    """
    Converte texto em CAPS LOCK para escrita correta.
    Regras:
    - Palavras de 2-4 letras que NÃO são palavras comuns do português → MAIÚSCULAS (são siglas).
    - Palavras comuns curtas (em, no, na, dia, sem, …) → minúsculas/title case normal.
    - Palavras longas (5+ letras) → Title Case.
    Ex: "GABRIEL SOFA EED EM UTI" → "Gabriel Sofa EED em UTI"
    """
    if val is None:
        return val
    if not isinstance(val, str):
        return val
    s = str(val).strip()
    if not s:
        return val
    # Só aplica se o texto estiver totalmente em maiúsculas (CAPS LOCK)
    if s != s.upper():
        return val
    # Não altera valores puramente numéricos
    if s.replace(".", "").replace(",", "").replace("-", "").replace("+", "").replace(" ", "").isdigit():
        return val
    palavras = s.split()
    resultado = []
    for i, p in enumerate(palavras):
        p_lower = p.lower()
        p_alpha = p.replace("-", "").replace(".", "")
        # Palavras comuns curtas: minúsculas (exceto na 1ª posição)
        if i > 0 and p_lower in _PALAVRAS_COMUNS_PT:
            resultado.append(p_lower)
        # Sigla: 2-4 letras, só letras, não é palavra comum → MAIÚSCULAS
        elif p_alpha.isalpha() and 2 <= len(p_alpha) <= 4 and p_lower not in _PALAVRAS_COMUNS_PT:
            resultado.append(p.upper())
        # Resto → Title Case
        else:
            resultado.append(p_lower.capitalize())
    return " ".join(resultado)


def _caps_obs_linha(val: str) -> str:
    """
    Converte linha de obs (diagnósticos) de CAPS para forma gramatical.
    Aplica as mesmas regras de _caps_para_certo (siglas 2-4 letras em maiúsculas).
    Nomes científicos de bactérias: Gênero com 1ª maiúscula, espécie em minúsculas.
    Ex: ENTEROCCOCUS FEACALIS e PROTEUS MIRABILIS -> Enterococcus faecalis e Proteus mirabilis
    """
    if val is None or not isinstance(val, str):
        return val
    s = str(val).strip()
    if not s or s != s.upper():
        return val
    palavras = s.split()
    resultado = []
    i = 0
    while i < len(palavras):
        p = palavras[i]
        p_lower = p.lower()
        p_alpha = p.replace("-", "").replace(".", "")
        # Palavras comuns curtas → minúsculas (exceto 1ª posição)
        if i > 0 and p_lower in _PALAVRAS_COMUNS_PT:
            resultado.append(p_lower)
            i += 1
            continue
        # Par GÊNERO ESPÉCIE (ambos ≥5 letras, ambos não-conjunção) → "Gênero espécie"
        so_letras = p_alpha.isalpha()
        if so_letras and len(p_alpha) >= 5 and i + 1 < len(palavras):
            prox = palavras[i + 1]
            prox_lower = prox.lower()
            prox_alpha = prox.replace("-", "").replace(".", "")
            if prox_alpha.isalpha() and len(prox_alpha) >= 5 and prox_lower not in _PALAVRAS_COMUNS_PT:
                resultado.append(p_lower.capitalize())
                resultado.append(prox_lower)
                i += 2
                continue
        # Sigla: 2-4 letras, só letras, não é palavra comum → MAIÚSCULAS
        if p_alpha.isalpha() and 2 <= len(p_alpha) <= 4 and p_lower not in _PALAVRAS_COMUNS_PT:
            resultado.append(p.upper())
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
    """
    Percorre cada palavra do valor e converte para MAIÚSCULAS as que forem siglas
    (2-4 letras, só letras, não são palavras comuns do português).
    Ex: "Vjid" → "VJID", "Art Radial Esquerda" → "ART Radial Esquerda"
    """
    if not val or not isinstance(val, str):
        return val
    partes = val.split()
    resultado = []
    for p in partes:
        p_alpha = p.replace("-", "").replace(".", "")
        if p_alpha.isalpha() and 2 <= len(p_alpha) <= 4 and p.lower() not in _PALAVRAS_COMUNS_PT:
            resultado.append(p.upper())
        else:
            resultado.append(p)
    return " ".join(resultado)
