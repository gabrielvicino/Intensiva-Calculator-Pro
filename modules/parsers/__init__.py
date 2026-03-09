"""
Pacote parsers — parsers deterministicos para cada tipo de dado clinico.

  parsers/lab.py          — parse_lab_deterministico()
  parsers/hc_unicamp.py   — parser HC Unicamp (determinístico)
  parsers/controles.py    — parse_controles_deterministico()
  parsers/sistemas.py     — parse_sistemas_deterministico()
"""
from .lab import parse_lab_deterministico, parse_agentes_para_slot, parse_agentes_bare
from .hc_unicamp import parsear as parsear_hc_unicamp, detectar as detectar_hc_unicamp
from .controles import parse_controles_deterministico
from .sistemas import parse_sistemas_deterministico

__all__ = [
    "parse_lab_deterministico",
    "parse_agentes_para_slot",
    "parse_agentes_bare",
    "parsear_hc_unicamp",
    "detectar_hc_unicamp",
    "parse_controles_deterministico",
    "parse_sistemas_deterministico",
]
