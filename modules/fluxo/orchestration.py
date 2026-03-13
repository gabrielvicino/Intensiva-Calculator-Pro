"""
orchestration.py -- execucao paralela de agentes e aplicacao de parsers.
"""
import concurrent.futures
import streamlit as st
from utils import verificar_rate_limit

# Pré-importa módulos pesados no nível do módulo para não repetir a cada chamada
from modules import agentes_secoes as _agentes_secoes
from modules.ia_config import get_ia_config as _get_ia_config

# Máximo de agentes simultâneos — sem batching, todas as seções em paralelo
_MAX_WORKERS = 16


def rodar_agentes_paralelo(
    secoes: list,
    google_key: str,
    openai_key: str,
    on_progress=None,
) -> tuple:
    """Executa os agentes das secoes em paralelo, cada um com seu modelo configurado.

    on_progress: callable(concluidos, total, nome_secao) -- chamado a cada agente concluido.
    Retorna (n_preenchidos, lista_erros).
    """
    permitido, msg = verificar_rate_limit()
    if not permitido:
        return 0, [f"Rate limit: {msg}"]

    tarefas = [
        (sec, st.session_state.get(_agentes_secoes._NOTAS_MAP[sec], "").strip())
        for sec in secoes
        if st.session_state.get(_agentes_secoes._NOTAS_MAP[sec], "").strip()
    ]
    if not tarefas:
        return 0, []

    concluidos = 0
    erros = []
    resultados = {}

    # Pre-resolve configurações de IA fora das threads (mais seguro + rápido)
    configs = {
        sec: _get_ia_config(sec, google_key, openai_key)
        for sec, _ in tarefas
    }

    def _rodar(secao, texto):
        fn = _agentes_secoes._AGENTES[secao]
        api_key, provider, modelo = configs[secao]
        return secao, fn(texto, api_key, provider, modelo)

    # Todas as seções em paralelo (sem batching)
    n_workers = min(len(tarefas), _MAX_WORKERS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(_rodar, s, t): s for s, t in tarefas}
        for future in concurrent.futures.as_completed(futures):
            concluidos += 1
            nome = ""
            try:
                secao, dados = future.result()
                nome = _agentes_secoes.NOMES_SECOES.get(secao, secao)
                if "_erro" in dados:
                    erros.append(f"{nome}: {dados['_erro']}")
                else:
                    resultados[secao] = dados
            except Exception as exc:
                sec = futures[future]
                nome = _agentes_secoes.NOMES_SECOES.get(sec, sec)
                erros.append(f"{nome}: {exc}")
            if on_progress:
                on_progress(concluidos, len(tarefas), nome)

    staging = st.session_state.get("_agent_staging", {})
    for dados in resultados.values():
        for k, v in dados.items():
            if not (isinstance(v, str) and v.strip() == ""):
                staging[k] = v
    st.session_state["_agent_staging"] = staging
    return len(resultados), erros


def aplicar_sistemas_deterministico(texto_sist: str) -> None:
    """Roda o parser de sistemas + aplica defaults e coloca no staging."""
    from modules.parsers import parse_sistemas_deterministico
    from modules.secoes.sistemas import get_campos as _get_campos_sistemas

    dados = parse_sistemas_deterministico(texto_sist)
    staging = st.session_state.get("_agent_staging", {})
    for k, v in dados.items():
        if v is not None and str(v).strip() != "":
            staging[k] = v
    for k, v in _get_campos_sistemas().items():
        if k.startswith("sis_") and k not in staging and v and str(v).strip():
            staging[k] = v
    st.session_state["_agent_staging"] = staging
    cnt = sum(1 for k in staging if k.startswith("sis_") and staging.get(k))
    st.toast(f"Sistemas: {cnt} campos preenchidos.", icon="📋")
    st.rerun()
