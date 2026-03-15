"""
Pacote gerador — cada seção em seu próprio módulo.
Interface pública idêntica ao arquivo original.
"""
import streamlit as st
from ._base import (
    _get,
    _caps_para_certo,
    _caps_obs_linha,
    _sigla_upper,
    _obs_para_linhas,
    _calcular_dias,
)

from .identificacao import _secao_identificacao
from .scores import _secao_scores
from .diagnosticos import _secao_diagnosticos
from .culturas import _secao_culturas
from .dispositivos import _secao_dispositivos
from .hmpa import _secao_hmpa
from .intraoperatorio import _secao_intraoperatorio
from .muc import _secao_muc
from .comorbidades import _secao_comorbidades
from .antibioticos import _secao_antibioticos
from .complementares import _secao_complementares
from .evolucao_clinica import _secao_evolucao_clinica
from .condutas import _secao_condutas
from .prescricao import _secao_prescricao
from .sistemas import _secao_sistemas

_SECAO_MAP: dict = {}   # populado após definição das funções


def _init_secao_map():
    global _SECAO_MAP
    _SECAO_MAP = {
        "identificacao":  _secao_identificacao,
        "scores":         _secao_scores,
        "hd":             _secao_diagnosticos,
        "comorbidades":   _secao_comorbidades,
        "muc":            _secao_muc,
        "hmpa":             _secao_hmpa,
        "intraoperatorio":  _secao_intraoperatorio,
        "dispositivos":     _secao_dispositivos,
        "culturas":       _secao_culturas,
        "antibioticos":   _secao_antibioticos,
        "complementares": _secao_complementares,
        "evolucao":       _secao_evolucao_clinica,
        "sistemas":       _secao_sistemas,
        "condutas":       _secao_condutas,
        "prescricao":     _secao_prescricao,
    }


def gerar_secao(key: str) -> str:
    """Gera o texto de uma seção específica pelo seu identificador.
    Retorna string vazia se a flag inc_{key} estiver desativada."""
    if not st.session_state.get(f"inc_{key}", True):
        return ""
    if not _SECAO_MAP:
        _init_secao_map()
    fn = _SECAO_MAP.get(key)
    if fn is None:
        return ""
    linhas = fn()
    if not linhas:
        return ""
    return "\n".join(linhas)


def gerar_texto_final() -> str:
    """
    Monta o texto final do prontuário concatenando todas as seções.
    Seções com inc_{key}=False são excluídas da saída (dados preservados).
    """
    def _inc(key: str) -> bool:
        return st.session_state.get(f"inc_{key}", True)

    secoes = []

    if _inc("identificacao"):   secoes.append(_secao_identificacao())
    if _inc("scores"):          secoes.append(_secao_scores())
    if _inc("hd"):              secoes.append(_secao_diagnosticos())
    if _inc("comorbidades"):    secoes.append(_secao_comorbidades())
    if _inc("muc"):             secoes.append(_secao_muc())
    if _inc("dispositivos"):    secoes.append(_secao_dispositivos())
    if _inc("culturas"):        secoes.append(_secao_culturas())
    if _inc("hmpa"):            secoes.append(_secao_hmpa())
    if _inc("intraoperatorio"): secoes.append(_secao_intraoperatorio())
    if _inc("antibioticos"):    secoes.append(_secao_antibioticos())
    if _inc("complementares"):  secoes.append(_secao_complementares())
    if _inc("evolucao"):        secoes.append(_secao_evolucao_clinica())
    if _inc("sistemas"):        secoes.append(_secao_sistemas())
    if _inc("condutas"):        secoes.append(_secao_condutas())
    if _inc("prescricao"):      secoes.append(_secao_prescricao())

    blocos = []
    for s in secoes:
        if not s:
            continue
        while s and s[-1] == "":
            s.pop()
        if s:
            blocos.append("\n".join(s))
    texto = "\n\n".join(blocos)
    texto = texto.replace(" ml", " mL")
    return texto
