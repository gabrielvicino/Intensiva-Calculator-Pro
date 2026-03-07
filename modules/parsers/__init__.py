"""
Pacote parsers — parsers deterministicos para cada tipo de dado clinico.

  parsers/lab.py       — parse_lab_deterministico()
  parsers/controles.py — parse_controles_deterministico()
  parsers/sistemas.py  — parse_sistemas_deterministico()
"""
from .lab import parse_lab_deterministico
from .controles import parse_controles_deterministico
from .sistemas import parse_sistemas_deterministico

__all__ = [
    "parse_lab_deterministico",
    "parse_controles_deterministico",
    "parse_sistemas_deterministico",
]
