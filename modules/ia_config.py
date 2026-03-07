"""
ia_config.py — Fonte única de verdade para configuração de modelos de IA.

Para mudar o modelo de qualquer tarefa: edite apenas o dict _CONFIGS abaixo.
Formato de cada entrada: "tarefa": ("provedor", "id_do_modelo")
  - provedor: "google" | "openai"
  - id_do_modelo: string exata aceita pela API (ex: "gemini-2.5-pro", "gpt-4o")
"""

# ── Configurações por tarefa ───────────────────────────────────────────────────

_CONFIGS: dict[str, tuple[str, str]] = {
    # ── Infraestrutura ─────────────────────────────────────────────────────────
    "ia_extrator":   ("google", "gemini-2.5-pro"),    # fatiamento do prontuário bruto
    "pacer_exames":  ("google", "gemini-2.5-flash"),  # extração PACER de laboratoriais
    "prescricao":    ("google", "gemini-2.5-flash"),  # formatação de prescrição

    # ── Agentes — modelos fortes ───────────────────────────────────────────────
    "laboratoriais": ("google", "gemini-2.5-pro"),    # parsing denso + gasometrias
    "sistemas":      ("google", "gemini-2.5-pro"),    # múltiplos subsistemas
    "hd":            ("google", "gemini-2.5-pro"),    # diagnósticos + CID
    "culturas":      ("google", "gemini-2.5-pro"),    # antibiograma + sensibilidade
    "hmpa":          ("openai", "gpt-4o"),            # texto narrativo longo

    # ── Agentes — modelo padrão (flash) ───────────────────────────────────────
    # Seções não listadas acima usam _DEFAULT automaticamente:
    # identificacao, comorbidades, muc, dispositivos,
    # antibioticos, complementares, controles, evolucao
}

_DEFAULT: tuple[str, str] = ("google", "gemini-2.5-flash")

_PROVIDER_STRINGS: dict[str, str] = {
    "google": "Google Gemini",
    "openai": "OpenAI GPT",
}


def get_ia_config(tarefa: str, google_key: str, openai_key: str) -> tuple[str, str, str]:
    """Retorna (api_key, provider_string, modelo) para a tarefa solicitada.

    Args:
        tarefa:     Nome da tarefa (ex: "laboratoriais", "ia_extrator", "pacer_exames").
        google_key: Chave da API Google Gemini.
        openai_key: Chave da API OpenAI.

    Returns:
        Tupla (api_key, provider_str, modelo) pronta para passar a _chamar_ia.
    """
    provedor, modelo = _CONFIGS.get(tarefa, _DEFAULT)
    api_key = google_key if provedor == "google" else openai_key
    provider_str = _PROVIDER_STRINGS[provedor]
    return api_key, provider_str, modelo
