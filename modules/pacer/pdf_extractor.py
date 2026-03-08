"""
modules/pacer/pdf_extractor.py
Extração híbrida de texto de PDFs + 7 agentes em paralelo.

Fluxo:
1. pdfplumber → extrai texto do PDF
2. Se texto < 100 chars (PDF escaneado):
       Gemini Vision → PDF inline como bytes
3. 7 agentes em paralelo:
       hematologia_renal, hepatico, coagulacao, urina, gasometria,
       nao_transcritos, data_coleta
4. Resultados mapeados para lab_{slot}_* via parse_agentes_para_slot
5. Regra de data: preenche lab_{slot}_data somente se estiver vazio
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import pdfplumber as _pdfplumber
    _PDFPLUMBER_OK = True
except ImportError:
    _PDFPLUMBER_OK = False

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GEMINI_OK = True
except ImportError:
    _GEMINI_OK = False

try:
    from openai import OpenAI as _OpenAI
    _OPENAI_OK = True
except ImportError:
    _OPENAI_OK = False

from modules.extrator_exames import (
    _PROMPT_HEMATOLOGIA_RENAL,
    _PROMPT_HEPATICO,
    _PROMPT_COAGULACAO,
    _PROMPT_URINA,
    _PROMPT_GASOMETRIA,
    _PROMPT_NAO_TRANSCRITOS,
)
from modules.parsers import parse_agentes_para_slot


def _is_openai(provider: str, modelo: str) -> bool:
    """Retorna True se o provider/modelo for OpenAI."""
    p = (provider or "").lower()
    m = (modelo or "").lower()
    return (
        "openai" in p
        or "gpt" in p
        or "gpt" in m
        or re.match(r"o\d", m) is not None
    )

# ==============================================================================
# Prompt — 7º agente: data de coleta
# ==============================================================================

_PROMPT_DATA_COLETA = """# ATUE COMO
Extrator de data de coleta de laudos laboratoriais brasileiros.

# TAREFA
Extraia a data mais próxima da COLETA DO MATERIAL do exame.

# ORDEM DE PRIORIDADE (use a primeira que encontrar)
1. "Data da coleta", "Coleta:", "Data coleta", "Data material", "Data amostra",
   "Colhido em", "Data do pedido", "Data requisição"
2. "Recebimento material:", "Recebido em:" — em sistemas hospitalares brasileiros
   (ex: HC/Unicamp, HCFMRP) o recebimento do material equivale à coleta.

# IGNORE COMPLETAMENTE
- "Impressão do Laudo", "Impresso em", "Data de impressão"
- "Liberado em", "Data de emissão", "Resultado em", "Validação"

# REGRAS
- Retorne APENAS a data no formato DD/MM/AAAA ou DD/MM/AA.
- Se houver múltiplas datas válidas, retorne a MAIS ANTIGA (data da coleta mais antiga).
- Se não encontrar nenhuma data de coleta ou recebimento, retorne exatamente: VAZIO

# FORMATO DE RESPOSTA
Apenas a data (ex: 04/12/2025) ou VAZIO. Sem texto extra, sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""


# ==============================================================================
# Extração de texto do PDF
# ==============================================================================

def extrair_texto_pdf(pdf_bytes: bytes) -> str:
    """
    Tenta extrair texto de PDF nativo via pdfplumber.
    Retorna string vazia se falhar ou PDF for escaneado.
    """
    if not _PDFPLUMBER_OK or not pdf_bytes:
        return ""
    try:
        import io
        with _pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            paginas = []
            for pagina in pdf.pages:
                txt = pagina.extract_text()
                if txt:
                    paginas.append(txt)
            return "\n\n".join(paginas).strip()
    except Exception as e:
        print(f"[PDF] pdfplumber falhou: {e}")
        return ""


def _extrair_via_gemini_vision(pdf_bytes: bytes, api_key: str, modelo: str) -> str:
    """
    Envia o PDF para o Gemini Vision e extrai o texto bruto (PDFs escaneados).
    Usa inline bytes com mime_type='application/pdf'.
    """
    if not _GEMINI_OK:
        return ""
    try:
        client = _genai.Client(api_key=api_key)
        resposta = client.models.generate_content(
            model=modelo,
            contents=[
                _genai_types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf",
                ),
                "Transcreva INTEGRALMENTE o conteúdo deste laudo laboratorial. "
                "Preserve todos os valores, datas e campos exatamente como aparecem. "
                "Sem formatação markdown.",
            ],
            config=_genai_types.GenerateContentConfig(temperature=0.0),
        )
        return resposta.text.strip() if resposta.text else ""
    except Exception as e:
        print(f"[PDF] Gemini Vision falhou: {e}")
        return ""


def _obter_texto_pdf(
    pdf_bytes: bytes,
    api_key: str,
    modelo: str,
    provider: str = "",
    google_api_key: str = "",
) -> str:
    """
    Abordagem híbrida:
    1. pdfplumber → texto nativo
    2. Se insuficiente (<100 chars) → Gemini Vision como fallback universal
       (funciona independente do provider dos agentes; usa google_api_key se disponível)
    """
    texto = extrair_texto_pdf(pdf_bytes)
    if len(texto) >= 100:
        print(f"[PDF] pdfplumber OK — {len(texto)} chars extraídos")
        return texto

    print(f"[PDF] pdfplumber insuficiente ({len(texto)} chars) → Gemini Vision")

    # Gemini Vision é sempre o fallback para PDFs escaneados.
    # Se o provider for OpenAI, usa google_api_key (separada) para a visão.
    gemini_key = google_api_key if _is_openai(provider, modelo) else api_key
    if gemini_key and _GEMINI_OK:
        # Para vision, usa gemini-2.0-flash (suporta PDF inline e é rápido)
        texto_vision = _extrair_via_gemini_vision(pdf_bytes, gemini_key, "gemini-2.0-flash")
        if texto_vision:
            print(f"[PDF] Gemini Vision OK — {len(texto_vision)} chars extraídos")
            return texto_vision

    print("[PDF] Gemini Vision indisponível. Texto parcial utilizado.")
    return texto


# ==============================================================================
# Chamada de agente individual
# ==============================================================================

def _chamar_agente(
    prompt: str,
    texto: str,
    api_key: str,
    modelo: str,
    provider: str = "",
) -> str | None:
    """
    Chama o modelo de IA com um prompt de agente e retorna a resposta.
    Suporta OpenAI (gpt-4o, o3, etc.) e Google Gemini.
    """
    prompt_completo = prompt.replace("{{TEXTO_INPUT}}", texto)
    try:
        if _is_openai(provider, modelo):
            # ── OpenAI ──────────────────────────────────────────────────────
            if not _OPENAI_OK:
                print("[AGENTE] OpenAI não instalada.")
                return None
            client = _OpenAI(api_key=api_key)
            is_o_series = bool(re.match(r"^o\d", modelo.strip()))
            kwargs: dict = {
                "model": modelo,
                "messages": [{"role": "user", "content": prompt_completo}],
            }
            if is_o_series:
                kwargs["max_completion_tokens"] = 1500
            else:
                kwargs["temperature"] = 0.0
                kwargs["top_p"] = 0.1
                kwargs["max_tokens"] = 1500
                kwargs["seed"] = 42
                kwargs["frequency_penalty"] = 0.0
                kwargs["presence_penalty"] = 0.0
            resp = client.chat.completions.create(**kwargs)
            txt = (resp.choices[0].message.content or "").strip()
        else:
            # ── Gemini ──────────────────────────────────────────────────────
            if not _GEMINI_OK:
                print("[AGENTE] google-genai não instalada.")
                return None
            client = _genai.Client(api_key=api_key)
            # gemini-2.5-pro exige thinking obrigatório; flash aceita budget=0
            is_pro = "pro" in modelo.lower()
            cfg_kwargs: dict = {"temperature": 0.0}
            if not is_pro:
                cfg_kwargs["thinking_config"] = _genai_types.ThinkingConfig(thinking_budget=0)
            resposta = client.models.generate_content(
                model=modelo,
                contents=prompt_completo,
                config=_genai_types.GenerateContentConfig(**cfg_kwargs),
            )
            txt = (resposta.text or "").strip()

        return None if (not txt or txt.upper() == "VAZIO") else txt

    except Exception as e:
        print(f"[AGENTE] Erro ({modelo}): {e}")
        return None


# ==============================================================================
# Processamento core — reutilizado por texto e PDF
# ==============================================================================

_AGENTES = {
    "hematologia_renal": _PROMPT_HEMATOLOGIA_RENAL,
    "hepatico":          _PROMPT_HEPATICO,
    "coagulacao":        _PROMPT_COAGULACAO,
    "urina":             _PROMPT_URINA,
    "gasometria":        _PROMPT_GASOMETRIA,
    "nao_transcritos":   _PROMPT_NAO_TRANSCRITOS,
    "data_coleta":       _PROMPT_DATA_COLETA,
}


def _normalizar_data(raw: str) -> str:
    """Normaliza data para DD/MM/AAAA ou DD/MM."""
    raw = raw.replace(".", "/")
    partes = raw.split("/")
    if len(partes) == 2:
        return f"{partes[0].zfill(2)}/{partes[1].zfill(2)}"
    if len(partes) == 3:
        ano = ("20" + partes[2]) if len(partes[2]) == 2 else partes[2]
        return f"{partes[0].zfill(2)}/{partes[1].zfill(2)}/{ano}"
    return raw


def _processar_com_agentes(
    texto: str,
    slot: int,
    api_key: str,
    modelo: str,
    provider: str,
    data_atual: str = "",
) -> tuple[dict[str, str], int]:
    """
    Roda os 7 agentes em paralelo sobre `texto` e retorna
    (campos lab_{slot}_*, quantidade de campos preenchidos).
    Respeita data já preenchida: só preenche lab_{slot}_data se `data_atual` vazio.
    """
    resultados: dict[str, str | None] = {}

    def _worker(agente_id: str, prompt: str):
        return agente_id, _chamar_agente(prompt, texto, api_key, modelo, provider)

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(_worker, aid, prompt): aid
            for aid, prompt in _AGENTES.items()
        }
        for future in as_completed(futures):
            aid, resultado = future.result(timeout=90)
            resultados[aid] = resultado

    campos = parse_agentes_para_slot(resultados, slot)

    # Preenche data apenas se estiver vazia
    if not data_atual:
        data_extraida = (resultados.get("data_coleta") or "").strip()

        # Tenta extrair data do retorno do agente
        data_final = ""
        if data_extraida and data_extraida.upper() != "VAZIO":
            m = re.search(r'\d{1,2}[/\.]\d{1,2}(?:[/\.]\d{2,4})?', data_extraida)
            if m:
                data_final = _normalizar_data(m.group(0))

        # Fallback: extrai a primeira data do texto bruto
        # (ignora padrões de impressão/liberação)
        if not data_final:
            _IGNORAR = re.compile(
                r'(impress[aã]o|liberado|emiss[aã]o|valida[çc][aã]o)',
                re.IGNORECASE,
            )
            for linha in texto.splitlines():
                if _IGNORAR.search(linha):
                    continue
                m = re.search(r'\b(\d{2}/\d{2}/\d{2,4})\b', linha)
                if m:
                    data_final = _normalizar_data(m.group(1))
                    break

        if data_final:
            campos[f"lab_{slot}_data"] = data_final

    n = len([v for v in campos.values() if v and not v.startswith("_")])
    return campos, n


# ==============================================================================
# Entrada via texto direto
# ==============================================================================

def processar_texto_slot(
    slot: int,
    texto: str,
    api_key: str,
    provider: str,
    modelo: str,
    data_atual: str = "",
) -> tuple[dict[str, str], int]:
    """
    Processa texto bruto de laudo para o slot informado via 7 agentes.
    Equivalente a processar_pdf_slot mas sem leitura de PDF.
    """
    if not texto or not texto.strip():
        return {}, 0
    return _processar_com_agentes(texto, slot, api_key, modelo, provider, data_atual)


# ==============================================================================
# Entrada via PDF
# ==============================================================================

def processar_pdf_slot(
    slot: int,
    api_key: str,
    provider: str,
    modelo: str,
    google_api_key: str = "",
) -> tuple[dict[str, str], int]:
    """
    Processa o PDF carregado no slot informado.
    1. Extrai texto (pdfplumber → Gemini Vision fallback)
    2. Roda 7 agentes em paralelo via _processar_com_agentes
    """
    import streamlit as st

    pdf_bytes: bytes | None = st.session_state.get(f"lab_{slot}_pdf_bytes")
    if not pdf_bytes:
        return {}, 0

    texto = _obter_texto_pdf(pdf_bytes, api_key, modelo, provider, google_api_key)
    if not texto:
        return {"_erro": "Não foi possível extrair texto do PDF."}, 0

    data_atual = st.session_state.get(f"lab_{slot}_data", "")
    return _processar_com_agentes(texto, slot, api_key, modelo, provider, data_atual)
