import streamlit as st

def get_campos():
    return {
        'conduta_final_lista': '',
    }

# Chaves excluídas da agregação (não são condutas de seção)
_EXCLUIR_CONDUTAS = {'conduta_final_lista'}


def coletar_condutas_agregadas() -> list[str]:
    """Coleta todos os campos *_conduta preenchidos do session_state, exceto os da seção 14."""
    resultado = []
    for key, val in st.session_state.items():
        if (
            key.endswith('_conduta')
            and key not in _EXCLUIR_CONDUTAS
            and isinstance(val, str)
            and val.strip()
        ):
            resultado.append(val.strip())
    return resultado


def render(_agent_btn_callback=None):
    """Renderiza a seção 15 dentro do st.form (campo de condutas + botão registrar)."""
    st.markdown('<span id="sec-15"></span>', unsafe_allow_html=True)
    st.markdown("##### 15. Plano Terapêutico & Condutas")

    with st.container(border=True):
        # Campo principal de condutas (vai para o prontuário gerado)
        with st.success("📋 Condutas do Dia"):
            st.text_area(
                "Listar condutas para hoje (uma por linha)",
                key="conduta_final_lista",
                height=150,
                placeholder="1. Manter antibiótico (D3/10)\n2. Desmame da ventilação mecânica\n3. Solicitar Parecer Cardiologia",
                label_visibility="collapsed"
            )

        # Botão de submit dedicado para registrar condutas
        st.form_submit_button(
            "Registrar Condutas",
            use_container_width=True,
            help="Clique (ou pressione Enter em qualquer campo de conduta) para atualizar a lista abaixo"
        )

        if _agent_btn_callback:
            _agent_btn_callback()


def render_condutas_registradas():
    """
    Exibe a lista 'Condutas Registradas' FORA do st.form.
    Lê session_state após o submit — sempre atual.
    """
    condutas = coletar_condutas_agregadas()

    st.markdown("##### 📋 Condutas Registradas")
    with st.container(border=True):
        if condutas:
            itens_md = "\n".join(f"{i+1}. {c}" for i, c in enumerate(condutas))
            st.markdown(itens_md)
        else:
            st.caption(
                "_Nenhuma conduta registrada ainda. "
                "Preencha os campos de conduta e pressione **Enter** ou clique em **Registrar Condutas**._"
            )
