# ==============================================================================
# modules/pacer/tab_debug_agentes.py
# Aba de debug para inspecionar a saída bruta de cada agente de extração
# e o resultado do parser determinístico — útil para diagnosticar erros.
# ==============================================================================

from __future__ import annotations

import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.pacer.pdf_extractor import _chamar_agente, _AGENTES
from modules.parsers.lab import parse_agentes_para_slot


# Nomes legíveis para cada agente
_NOMES_AGENTES = {
    "hematologia_renal": "🩸 Hematologia / Renal",
    "hepatico":          "🫀 Hepático / Pancreático",
    "coagulacao":        "🧬 Coagulação / Inflamação",
    "urina":             "🧪 Urina (EAS)",
    "gasometria":        "💨 Gasometria",
    "nao_transcritos":   "📋 Não Transcritos",
    "data_coleta":       "📅 Data de Coleta",
}

# Mapeamento agente → campos que ele alimenta (para exibição contextual)
_CAMPOS_AGENTE = {
    "hematologia_renal": ["hb", "ht", "vcm", "hcm", "rdw", "leuco", "plaq", "cr", "ur", "na", "k", "mg", "pi", "cat", "cai"],
    "hepatico":          ["tgo", "tgp", "fal", "ggt", "bt", "bd", "alb", "amil", "lipas", "prot_tot"],
    "coagulacao":        ["pcr", "trop", "cpk", "cpk_mb", "tp", "ttpa"],
    "urina":             ["ur_dens", "ur_le", "ur_nit", "ur_leu", "ur_hm", "ur_prot", "ur_cet", "ur_glic"],
    "gasometria":        ["gas_tipo", "gas_hora", "gas_ph", "gas_pco2", "gas_po2", "gas_hco3", "gas_be", "gas_sat", "svo2", "gas_lac", "gas_ag", "gas_cl", "gas_na", "gas_k", "gas_cai"],
    "nao_transcritos":   ["outros"],
    "data_coleta":       ["data"],
}


def _rodar_todos_agentes(
    texto: str,
    api_key: str,
    modelo: str,
    provider: str = "OpenAI GPT",
) -> tuple[dict[str, str | None], dict[str, str]]:
    """
    Roda os 7 agentes em paralelo e retorna:
    - resultados_brutos: {agente_id: texto_bruto_ia}
    - campos_finais:     {lab_1_campo: valor}  (saída do parser)
    """
    resultados_brutos: dict[str, str | None] = {}

    def _worker(nome: str, prompt: str):
        saida = _chamar_agente(prompt, texto, api_key, modelo, provider)
        return nome, saida

    with ThreadPoolExecutor(max_workers=7) as ex:
        futures = {ex.submit(_worker, n, p): n for n, p in _AGENTES.items()}
        for future in as_completed(futures):
            nome, saida = future.result(timeout=90)
            resultados_brutos[nome] = saida

    campos_finais = parse_agentes_para_slot(resultados_brutos, slot=1)
    return resultados_brutos, campos_finais


def _exibir_resultado_agente(
    agente_id: str,
    saida_bruta: str | None,
    campos: dict[str, str],
) -> None:
    """Renderiza o card de resultado de um agente individual."""
    nome = _NOMES_AGENTES.get(agente_id, agente_id)
    campos_esperados = _CAMPOS_AGENTE.get(agente_id, [])

    # Filtra campos que pertencem a este agente
    campos_agente = {
        k.replace("lab_1_", ""): v
        for k, v in campos.items()
        if any(k.endswith(f"_{c}") or k == f"lab_1_{c}" for c in campos_esperados)
        and not k.startswith("_")
    }

    tem_saida = bool(saida_bruta)
    tem_campos = bool(campos_agente)

    status = "✅" if tem_saida else "⬜"
    with st.expander(f"{status} {nome}", expanded=tem_saida):
        col_bruta, col_parse = st.columns([1, 1], gap="medium")

        with col_bruta:
            st.markdown("**🤖 Saída bruta da IA**")
            if saida_bruta:
                st.code(saida_bruta, language="text")
            else:
                st.info("Nenhuma saída retornada (VAZIO ou erro).")

        with col_parse:
            st.markdown("**⚙️ Campos extraídos pelo parser**")
            if agente_id == "nao_transcritos":
                # Agente de não-transcritos retorna só nomes, sem campos no parser
                if saida_bruta:
                    st.markdown("*Exames identificados (não mapeiam para campos):*")
                    for item in saida_bruta.split("|"):
                        st.markdown(f"- `{item.strip()}`")
                else:
                    st.info("Nenhum exame extra identificado.")
            elif agente_id == "data_coleta":
                data_campo = campos.get("_data_coleta_slot_1", "")
                if data_campo:
                    st.success(f"**Data extraída:** `{data_campo}`")
                else:
                    st.info("Data não extraída pelo agente.")
            elif tem_campos:
                rows = []
                for campo, valor in sorted(campos_agente.items()):
                    rows.append({"Campo": f"`lab_1_{campo}`", "Valor": valor})
                st.table(rows)
            else:
                st.warning("Parser não extraiu campos deste agente.")


def render(api_key: str = "", modelo: str = "gpt-4o") -> None:
    """Renderiza a aba completa de debug dos agentes de extração."""

    # Aplica limpeza pendente ANTES de renderizar o widget
    if st.session_state.pop("_debug_limpar_pendente", False):
        st.session_state["_debug_texto_entrada"] = ""
        st.session_state.pop("_debug_resultados", None)

    st.subheader("🔍 Debug — Agentes de Extração de Exames")
    st.caption(
        "Cole um laudo laboratorial e clique em **Rodar Todos os Agentes** para ver "
        "a saída bruta de cada IA e o que o parser determinístico extraiu. "
        "Use isso para identificar onde estão os erros de extração."
    )

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.markdown("**Entrada — Laudo Bruto**")
        texto = st.text_area(
            "Cole o laudo aqui:",
            height=350,
            key="_debug_texto_entrada",
            label_visibility="collapsed",
            placeholder="Cole aqui o texto do laudo laboratorial...",
        )

        c_lim, c_proc = st.columns([1, 3])
        with c_lim:
            if st.button("Limpar", key="_debug_btn_limpar"):
                st.session_state["_debug_limpar_pendente"] = True
                st.rerun()
        with c_proc:
            rodar = st.button(
                "▶ Rodar Todos os Agentes",
                key="_debug_btn_rodar",
                type="primary",
                use_container_width=True,
                disabled=not api_key,
            )

        if not api_key:
            st.warning("⚠️ Chave de API não configurada.")

        # Legenda dos agentes
        with st.expander("ℹ️ O que cada agente faz", expanded=False):
            for aid, nome in _NOMES_AGENTES.items():
                campos_str = " · ".join(_CAMPOS_AGENTE.get(aid, []))
                st.markdown(f"**{nome}**  \n`{campos_str}`")

    with col_out:
        st.markdown("**Resultado por Agente**")

        if rodar:
            texto_atual = st.session_state.get("_debug_texto_entrada", "").strip()
            if not texto_atual:
                st.warning("⚠️ Cole o texto do laudo antes de rodar os agentes.")
            else:
                with st.spinner("🔬 Rodando 7 agentes em paralelo..."):
                    brutos, campos = _rodar_todos_agentes(
                        texto_atual, api_key, modelo
                    )
                st.session_state["_debug_resultados"] = (brutos, campos)

        if "_debug_resultados" in st.session_state:
            brutos, campos = st.session_state["_debug_resultados"]

            # Sumário rápido no topo
            total_brutos = sum(1 for v in brutos.values() if v)
            total_campos = len([k for k in campos if not k.startswith("_")])
            c1, c2, c3 = st.columns(3)
            c1.metric("Agentes com retorno", f"{total_brutos}/7")
            c2.metric("Campos extraídos", total_campos)
            c3.metric("Agentes vazios", f"{7 - total_brutos}/7")

            st.divider()

            # Resultado completo agregado (como apareceria no prontuário)
            campos_texto = {k: v for k, v in campos.items() if not k.startswith("_")}
            if campos_texto:
                with st.expander("📄 Campos finais (lab_1_*) — visão completa", expanded=False):
                    st.json(campos_texto)

            st.divider()

            # Um card por agente
            for agente_id in _NOMES_AGENTES:
                _exibir_resultado_agente(agente_id, brutos.get(agente_id), campos)

        else:
            st.info("Aguardando execução...")
