"""
Pacote fluxo -- orquestracao de agentes, gestao de estado e bridge entre blocos.

Submodulos:
  state.py        -- _MAPA_NOTAS, atualizar_notas_ia, limpar_tudo, helpers _limpar*
  orchestration.py -- rodar_agentes_paralelo, aplicar_sistemas_deterministico
  bridge.py       -- completar_sistemas_de_outros_blocos
"""
from .state import (
    _MAPA_NOTAS,
    _limpar,
    _limpar_leuco,
    _extrair_parenteses,
    atualizar_notas_ia,
    limpar_tudo,
)
from .orchestration import (
    rodar_agentes_paralelo,
    aplicar_sistemas_deterministico,
)
from .bridge import completar_sistemas_de_outros_blocos

__all__ = [
    "_MAPA_NOTAS",
    "_limpar",
    "_limpar_leuco",
    "_extrair_parenteses",
    "atualizar_notas_ia",
    "limpar_tudo",
    "rodar_agentes_paralelo",
    "aplicar_sistemas_deterministico",
    "completar_sistemas_de_outros_blocos",
]
