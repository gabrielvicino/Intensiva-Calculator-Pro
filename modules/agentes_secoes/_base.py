"""
12 agentes de IA para preencher os campos estruturados de cada seção
a partir do texto já fatiado pelo ia_extrator.
"""
import json
import re
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


def _chamar_ia(prompt_system: str, texto: str, api_key: str, provider: str, modelo: str) -> dict:
    """Helper: envia texto para a IA e retorna JSON parseado."""
    prompt_system = prompt_system + _REGRA_DATA
    try:
        if "OpenAI" in provider or "GPT" in provider:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=modelo if modelo.startswith("gpt") else "gpt-4o",
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user",   "content": f"TEXTO DA SEÇÃO:\n\n{texto}"}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        else:
            _modelo = modelo if modelo.startswith("gemini") else "gemini-2.5-pro"
            client = _genai_new.Client(api_key=api_key)
            resp = client.models.generate_content(
                model=_modelo,
                contents=f"TEXTO DA SEÇÃO:\n\n{texto}",
                config=_genai_types.GenerateContentConfig(
                    system_instruction=prompt_system,
                    temperature=0.0,
                    thinking_config=_genai_types.ThinkingConfig(thinking_budget=0),
                ),
            )
            txt = (resp.text or "").replace("```json", "").replace("```", "").strip()
            parsed = _extrair_json(txt)
            if parsed is not None:
                return parsed
            return json.loads(txt)
    except json.JSONDecodeError as e:
        return {"_erro": f"JSON inválido: {e}"}
    except Exception as e:
        return {"_erro": str(e)}
