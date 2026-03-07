"""
conftest.py -- configuracao pytest para o projeto Intensiva Calculator.
Adiciona a raiz do projeto ao sys.path para que os imports funcionem.
"""
import sys
import os

# Adiciona a raiz do projeto ao path de importacao
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
