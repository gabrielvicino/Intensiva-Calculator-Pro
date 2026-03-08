"""
12 agentes de IA para preencher os campos estruturados de cada seção
a partir do texto já fatiado pelo ia_extrator.
"""
import json
import re
import time
import streamlit as st
from openai import OpenAI
from google import genai as _genai_new
from google.genai import types as _genai_types


def _extrair_json(texto: str) -> dict | None:
    """Extrai JSON de texto que pode conter markdown ou explicações."""
    if not texto or not texto.strip():
        return None
    txt = texto.strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```\s*$", "", txt)
    txt = txt.strip()
    match = re.search(r"\{[\s\S]*\}", txt)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return None


_REGRA_DATA = """
# REGRA GLOBAL DE DATAS
- Ano padrão: se o ano não estiver explícito no texto, use sempre 2026. Ex: "04/03" → "04/03/2026"; "04/03/26" → "04/03/2026".
- Formato de saída de datas: DD/MM/AAAA (4 dígitos no ano). Nunca retorne datas com 2 dígitos no ano.
- Se outro ano estiver explícito no texto (ex: 2024, 2025), use o ano mencionado.
"""


def _chamar_ia(prompt_system: str, texto: str, api_key: str, provider: str, modelo: str,
               max_tokens: int = 8192) -> dict:
    """Helper: envia texto para a IA e retorna JSON parseado.

    Faz até 3 tentativas com backoff de 20 s / 40 s para erros 429 (rate limit).
    """
    prompt_system = prompt_system + _REGRA_DATA

    for attempt in range(3):
        try:
            if "OpenAI" in provider or "GPT" in provider:
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model=modelo if modelo.startswith("gpt") else "gpt-4o",
                    messages=[
                        {"role": "system", "content": prompt_system},
                        {"role": "user",   "content": f"TEXTO DA SEÇÃO:\n\n{texto}"}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=max_tokens,
                )
                return json.loads(resp.choices[0].message.content)
            else:
                # Fallback Google Gemini
                # gemini-2.5-pro só funciona em modo thinking (não aceita thinking_budget=0)
                # gemini-2.5-flash aceita thinking_budget=0 para respostas mais rápidas
                _modelo = modelo if modelo.startswith("gemini") else "gemini-2.0-flash"
                client = _genai_new.Client(api_key=api_key)
                cfg_kwargs: dict = {
                    "system_instruction": prompt_system,
                    "temperature": 0.0,
                }
                if "2.5-flash" in _modelo:
                    cfg_kwargs["thinking_config"] = _genai_types.ThinkingConfig(thinking_budget=0)
                resp = client.models.generate_content(
                    model=_modelo,
                    contents=f"TEXTO DA SEÇÃO:\n\n{texto}",
                    config=_genai_types.GenerateContentConfig(**cfg_kwargs),
                )
                txt = (resp.text or "").replace("```json", "").replace("```", "").strip()
                parsed = _extrair_json(txt)
                if parsed is not None:
                    return parsed
                return json.loads(txt)

        except json.JSONDecodeError as e:
            return {"_erro": f"JSON inválido: {e}"}
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "rate_limit" in err_str.lower()
            if is_rate_limit and attempt < 2:
                time.sleep(20 * (attempt + 1))   # 20 s, depois 40 s
                continue
            return {"_erro": err_str}

    return {"_erro": "Rate limit: máximo de tentativas atingido"}
