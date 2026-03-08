from ._base import *
import streamlit as st

def _secao_culturas() -> list[str]:
    """
    Agrupa culturas em 3 sub-seções por status:
      # Culturas Positivas   → Positivo com Antibiograma | Positivo aguarda isolamento
      # Culturas em Andamento → Pendente negativo
      # Culturas Negativas    → Negativo
    """
    ordem = st.session_state.get("cult_ordem", list(range(1, 9)))

    positivas  = []
    andamento  = []
    negativas  = []

    for id_real in ordem:
        sitio = _get(f"cult_{id_real}_sitio")
        if not sitio:
            continue

        status        = _get(f"cult_{id_real}_status")
        data_coleta   = _get(f"cult_{id_real}_data_coleta")
        data_resultado= _get(f"cult_{id_real}_data_resultado")
        micro         = _get(f"cult_{id_real}_micro")
        sensib        = _get(f"cult_{id_real}_sensib")

        # Linha principal
        partes = [sitio]
        if data_coleta:
            partes.append(f"coletada em {data_coleta}")
        if data_resultado:
            partes.append(f"resultado dia {data_resultado}")
        linha_principal = "; ".join(partes)

        if status in ("Positivo com Antibiograma", "Positivo aguarda isolamento"):
            # Patógeno e sensibilidade em linhas > separadas
            detalhes = []
            if micro:
                detalhes.append(f"> {micro}")
            if status == "Positivo com Antibiograma" and sensib:
                detalhes.append(f"> {sensib}")
            elif status == "Positivo aguarda isolamento":
                detalhes.append("> aguarda isolamento")
            positivas.append((linha_principal, detalhes))

        elif status == "Pendente negativo":
            partes_and = list(partes)
            if not data_resultado:
                partes_and.append("Parcialmente negativa")
            andamento.append(("; ".join(partes_and), []))

        elif status == "Negativo":
            negativas.append((linha_principal, []))

    if not positivas and not andamento and not negativas:
        return []

    corpo = []

    def _add_grupo(titulo, itens):
        if not itens:
            return
        if corpo:
            corpo.append("")
        corpo.append(titulo)
        for i, (linha, detalhes) in enumerate(itens, 1):
            corpo.append(f"{i}- {linha}")
            if isinstance(detalhes, list):
                corpo.extend(detalhes)
            elif detalhes:
                corpo.append(detalhes)

    _add_grupo("# Culturas Positivas",    positivas)
    _add_grupo("# Culturas em Andamento", andamento)
    _add_grupo("# Culturas Negativas",    negativas)

    return corpo
