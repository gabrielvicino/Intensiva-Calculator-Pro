"""
Pacote fluxo -- orquestracao de agentes e gestao de estado.

Submodulos:
  state.py        -- _MAPA_NOTAS, atualizar_notas_ia, limpar_tudo, helpers _limpar*
  orchestration.py -- rodar_agentes_paralelo, aplicar_sistemas_deterministico
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

__all__ = [
    "_MAPA_NOTAS",
    "_limpar",
    "_limpar_leuco",
    "_extrair_parenteses",
    "atualizar_notas_ia",
    "limpar_tudo",
    "rodar_agentes_paralelo",
    "aplicar_sistemas_deterministico",
]
