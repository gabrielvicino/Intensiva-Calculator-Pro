"""
ia_config.py — Fonte única de verdade para configuração de modelos de IA.

Prioridade:
  1. OpenAI GPT-4o  — usado em TODAS as tarefas se a chave OpenAI estiver disponível.
  2. Google Gemini  — fallback por tarefa caso a chave OpenAI esteja ausente.

Para ajustar o fallback Gemini por tarefa: edite _CONFIGS_FALLBACK abaixo.
"""

# ── Fallback por tarefa (usado apenas quando a chave OpenAI NÃO está disponível) ──

_CONFIGS_FALLBACK: dict[str, tuple[str, str]] = {
    # ── Infraestrutura ─────────────────────────────────────────────────────────
    "ia_extrator":   ("google", "gemini-2.5-pro"),    # fatiamento do prontuário bruto
    "pacer_exames":  ("google", "gemini-2.5-flash"),  # extração PACER de laboratoriais
    "prescricao":    ("google", "gemini-2.5-flash"),  # formatação de prescrição

    # ── Agentes — modelos fortes ───────────────────────────────────────────────
    "laboratoriais": ("google", "gemini-2.5-pro"),    # parsing denso + gasometrias
    "sistemas":      ("google", "gemini-2.5-pro"),    # múltiplos subsistemas
    "hd":            ("google", "gemini-2.5-pro"),    # diagnósticos + CID
    "culturas":      ("google", "gemini-2.5-pro"),    # antibiograma + sensibilidade
    "hmpa":          ("google", "gemini-2.5-pro"),    # texto narrativo longo

    # ── Agentes — modelo padrão (flash) ───────────────────────────────────────
    # Seções não listadas acima usam _DEFAULT_FALLBACK automaticamente:
    # identificacao, comorbidades, muc, dispositivos,
    # antibioticos, complementares, controles, evolucao
}

_DEFAULT_FALLBACK: tuple[str, str] = ("google", "gemini-2.5-flash")

_PROVIDER_STRINGS: dict[str, str] = {
    "google": "Google Gemini",
    "openai": "OpenAI GPT",
}


def get_ia_config(tarefa: str, google_key: str, openai_key: str) -> tuple[str, str, str]:
    """Retorna (api_key, provider_string, modelo) para a tarefa solicitada.

    Prioridade:
      1. Se openai_key disponível → OpenAI GPT-4o para qualquer tarefa.
      2. Caso contrário → fallback Gemini conforme _CONFIGS_FALLBACK.

    Args:
        tarefa:     Nome da tarefa (ex: "laboratoriais", "ia_extrator", "pacer_exames").
        google_key: Chave da API Google Gemini.
        openai_key: Chave da API OpenAI.

    Returns:
        Tupla (api_key, provider_str, modelo) pronta para passar a _chamar_ia.
    """
    if openai_key and openai_key.strip():
        return openai_key, "OpenAI GPT", "gpt-4o"

    # Fallback: Gemini conforme configuração por tarefa
    provedor, modelo = _CONFIGS_FALLBACK.get(tarefa, _DEFAULT_FALLBACK)
    api_key = google_key if provedor == "google" else openai_key
    return api_key, _PROVIDER_STRINGS[provedor], modelo
