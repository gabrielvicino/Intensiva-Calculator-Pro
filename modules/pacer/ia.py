# ==============================================================================
# modules/pacer/ia.py
# Funções puras de processamento de IA — sem UI.
# Usadas pelas tabs de Exames PACER e Prescrição.
# ==============================================================================

import time
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai as _genai_new
from google.genai import types as _genai_types
from openai import OpenAI

from .prompts import (
    AGENTES_EXAMES,
    PROMPT_AGENTE_ANALISE,
    PROMPT_AGENTE_IDENTIFICACAO,
    PROMPT_AGENTE_IDENTIFICACAO_PRESCRICAO,
    PROMPT_AGENTE_DIETA,
    PROMPT_AGENTE_MEDICACOES,
    CANDIDATOS_GEMINI,
)


# ==============================================================================
# Chamada simples de IA (single-agent)
# ==============================================================================

def processar_texto(api_source: str, api_key: str, model_name: str,
                    prompt_system: str, input_text: str) -> str:
    if not input_text:
        return "⚠️ O campo de entrada está vazio."
    if not api_key:
        return f"⚠️ Configure a chave de API do {api_source}."

    try:
        if api_source == "Google Gemini":
            client = _genai_new.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=input_text,
                config=_genai_types.GenerateContentConfig(
                    system_instruction=prompt_system,
                    temperature=0.0,
                ),
            )
            return response.text

        elif api_source == "OpenAI GPT":
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": input_text},
                ],
                temperature=0.0,
                top_p=0.1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=2000,
                seed=42,
            )
            return response.choices[0].message.content

    except Exception as e:
        return f"❌ Erro na API: {str(e)}"


# ==============================================================================
# Pré-processamento conservador do texto de exames
# ==============================================================================

def preprocessar_texto_exames(texto: str) -> str:
    """Remove rodapés e cabeçalhos repetitivos sem apagar dados clínicos."""
    if not texto:
        return texto

    padroes_remover = [
        '"Todo teste laboratorial deve ser correlacionado com o quadro clínico',
        "sem o qual a interpretação do resultado é apenas relativa",
        "Impressão do Laudo:",
        "Conferência por Vídeo",
        "Rua Rua Vital Brasil",
        "CIDADE UNIVERSITÁRIA",
        "Campinas, SP - Brasil",
        "CNPJ 46.068.425",
        "Telefone (55)(19)",
        "homepage: HTTPS://WWW.HC.UNICAMP.BR/",
        "email: null",
        "Caixa Postal null",
        "LABORATÓRIO DE PATOLOGIA CLÍNICA",
        "Chefe de Serviço: EDER DE CARVALHO PINCINATO CRF: 23811",
    ]

    linhas = texto.split("\n")
    linhas_filtradas = []
    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa:
            continue
        deve_remover = any(p.lower() in linha_limpa.lower() for p in padroes_remover)
        if not deve_remover:
            linhas_filtradas.append(linha)

    texto_processado = "\n".join(linhas_filtradas)
    while "\n\n\n" in texto_processado:
        texto_processado = texto_processado.replace("\n\n\n", "\n\n")

    reducao = len(texto) - len(texto_processado)
    if reducao > 0:
        pct = reducao / len(texto) * 100
        print(f"[PRÉ-PROC] Redução: {reducao} chars ({pct:.1f}%) — dados clínicos intactos")

    return texto_processado.strip()


# ==============================================================================
# Multi-agente paralelo — exames laboratoriais
# ==============================================================================

def processar_multi_agente(api_source: str, api_key: str, model_name: str,
                           agentes_selecionados: list, input_text: str,
                           executar_analise: bool = True):
    """
    Fluxo:
    1. Agente de identificação (sequencial)
    2. Agentes selecionados em paralelo (ThreadPoolExecutor)
    3. Concatenação dos resultados
    4. Agente de análise clínica opcional (Agente 6)

    Retorna: tupla (resultado_exames: str, analise_clinica: str)
    """
    if not input_text:
        return "⚠️ O campo de entrada está vazio.", ""
    if not api_key:
        return f"⚠️ Configure a chave de API do {api_source}.", ""
    if not agentes_selecionados:
        return "⚠️ Selecione pelo menos um agente.", ""

    tempo_inicio = time.time()

    print("[PRÉ-PROC] Aplicando pré-processamento conservador...")
    input_text_limpo = preprocessar_texto_exames(input_text)

    # Passo 1: identificação (sempre sequencial)
    try:
        resultado_identificacao = processar_texto(
            api_source, api_key, model_name,
            PROMPT_AGENTE_IDENTIFICACAO,
            input_text_limpo,
        )
        if "❌" in resultado_identificacao or "⚠️" in resultado_identificacao:
            return resultado_identificacao, ""
        linhas = resultado_identificacao.strip().split("\n")
        if len(linhas) < 2:
            return "❌ Erro ao extrair identificação. Verifique o texto de entrada.", ""
        nome_hc = linhas[0].strip()
        data_linha = linhas[1].strip()
    except Exception as e:
        return f"❌ Erro no agente de identificação: {str(e)}", ""

    # Passo 2: agentes paralelos
    print(f"\n[PARALELO] Iniciando {len(agentes_selecionados)} agentes simultaneamente...")
    exames_concatenados = []

    def _worker(agente_id):
        if agente_id not in AGENTES_EXAMES:
            return None
        agente = AGENTES_EXAMES[agente_id]
        try:
            t0 = time.time()
            res = processar_texto(api_source, api_key, model_name,
                                  agente["prompt"], input_text_limpo)
            print(f"[PARALELO] '{agente['nome']}' em {time.time()-t0:.1f}s")
            if res and "❌" not in res and "⚠️" not in res:
                res_limpo = res.strip()
                if res_limpo and res_limpo.rstrip(".,:;!? ").upper() != "VAZIO":
                    return res_limpo
        except Exception as e:
            print(f"[PARALELO] Erro em '{agente_id}': {e}")
        return None

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_id = {
            executor.submit(_worker, aid): aid
            for aid in agentes_selecionados
        }
        resultados_dict = {}
        for future in as_completed(future_to_id):
            aid = future_to_id[future]
            try:
                res = future.result(timeout=60)
                if res:
                    resultados_dict[aid] = res
            except Exception as e:
                print(f"[PARALELO] Exceção em '{aid}': {e}")

    for aid in agentes_selecionados:
        if aid in resultados_dict:
            exames_concatenados.append(resultados_dict[aid])

    t_extr = time.time() - tempo_inicio
    print(f"[PARALELO] Extração em {t_extr:.1f}s | "
          f"{len(exames_concatenados)}/{len(agentes_selecionados)} agentes com dados")

    # Passo 3: montar resultado
    _AGENTES_INLINE    = ["hematologia_renal"]
    _AGENTES_BIOQUIM   = ["hepatico", "coagulacao"]
    _AGENTES_SEPARADOS = ["gasometria", "urina"]

    def _ok(txt):
        return txt and txt.strip().rstrip(".,:;!? ").upper() != "VAZIO"

    if resultados_dict:
        linhas_saida = [nome_hc]

        inline_partes = [resultados_dict[aid] for aid in _AGENTES_INLINE
                         if aid in resultados_dict and _ok(resultados_dict[aid])]
        linhas_saida.append(
            f"{data_linha} " + " | ".join(inline_partes) if inline_partes else data_linha
        )

        bioquim_partes = [resultados_dict[aid] for aid in _AGENTES_BIOQUIM
                          if aid in resultados_dict and _ok(resultados_dict[aid])]
        if bioquim_partes:
            linhas_saida.append(" | ".join(bioquim_partes))

        for aid in _AGENTES_SEPARADOS:
            if aid in resultados_dict and _ok(resultados_dict[aid]):
                linhas_saida.append(resultados_dict[aid])

        nao_trans = resultados_dict.get("nao_transcritos", "")
        if _ok(nao_trans):
            linhas_saida.append(f"Não Transcritos: {nao_trans}")

        resultado_exames = "\n".join(linhas_saida)
    else:
        resultado_exames = f"{nome_hc}\n{data_linha} (Nenhum dado laboratorial encontrado)"

    # Passo 4: análise clínica (Agente 6) — opcional
    analise_clinica = ""
    if executar_analise and exames_concatenados:
        try:
            print(f"[DEBUG] Agente 6 (Análise Clínica) com {model_name}...")
            t0 = time.time()
            analise_clinica = processar_texto(
                api_source, api_key, model_name,
                PROMPT_AGENTE_ANALISE,
                resultado_exames,
            )
            print(f"[DEBUG] Análise em {time.time()-t0:.1f}s | "
                  f"{len(analise_clinica)} chars")
            if "❌" in analise_clinica or "⚠️" in analise_clinica:
                analise_clinica = ""
        except Exception as e:
            print(f"[DEBUG] Exceção no Agente 6: {e}")
            analise_clinica = ""

    return resultado_exames, analise_clinica


# ==============================================================================
# Multi-agente sequencial — prescrição médica
# ==============================================================================

def processar_multi_agente_prescricao(api_source: str, api_key: str,
                                      model_name: str, input_text: str) -> str:
    """
    Fluxo:
    1. Agente de Identificação
    2. Agente de Dieta
    3. Agente de Medicações e Soluções

    Retorna: string completa da prescrição formatada.
    """
    if not input_text:
        return "⚠️ O campo de entrada está vazio."
    if not api_key:
        return f"⚠️ Configure a chave de API do {api_source}."

    # Identificação
    try:
        resultado_identificacao = processar_texto(
            api_source, api_key, model_name,
            PROMPT_AGENTE_IDENTIFICACAO_PRESCRICAO,
            input_text,
        )
        if "❌" in resultado_identificacao or "⚠️" in resultado_identificacao:
            return resultado_identificacao
        identificacao_completa = resultado_identificacao.strip()
    except Exception as e:
        return f"❌ Erro no agente de identificação: {str(e)}"

    # Dieta
    resultado_dieta = ""
    try:
        dieta_raw = processar_texto(api_source, api_key, model_name,
                                    PROMPT_AGENTE_DIETA, input_text)
        if dieta_raw and "❌" not in dieta_raw and "⚠️" not in dieta_raw:
            d = dieta_raw.strip()
            if d and d.upper() != "VAZIO":
                resultado_dieta = d
    except Exception:
        pass

    # Medicações e Soluções
    resultado_medicacoes = ""
    try:
        med_raw = processar_texto(api_source, api_key, model_name,
                                  PROMPT_AGENTE_MEDICACOES, input_text)
        if med_raw and "❌" not in med_raw and "⚠️" not in med_raw:
            m = med_raw.strip()
            if m and m.upper() != "VAZIO":
                resultado_medicacoes = m
    except Exception:
        pass

    partes = [identificacao_completa]
    if resultado_dieta:
        partes.append("\n" + resultado_dieta)
    if resultado_medicacoes:
        partes.append("\n" + resultado_medicacoes)
    if not resultado_dieta and not resultado_medicacoes:
        partes.append("\n(Nenhum dado de prescrição encontrado)")

    return "\n".join(partes)


# ==============================================================================
# Utilitários
# ==============================================================================

def verificar_modelos_ativos(api_key: str) -> list:
    """Testa todos os modelos da lista CANDIDATOS_GEMINI e retorna os ativos."""
    modelos_validos = []
    client = _genai_new.Client(api_key=api_key)
    status_msg = st.empty()
    for modelo in CANDIDATOS_GEMINI:
        status_msg.text(f"Testando: {modelo}...")
        try:
            client.models.generate_content(model=modelo, contents="Oi")
            modelos_validos.append(modelo)
        except Exception:
            pass
    status_msg.empty()
    return modelos_validos


def limpar_campos(lista_chaves: list) -> None:
    """Zera os valores das chaves indicadas no session_state."""
    for chave in lista_chaves:
        if chave in st.session_state:
            st.session_state[chave] = ""
