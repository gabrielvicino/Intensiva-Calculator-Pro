import streamlit as st

# Importando as pílulas (módulos)
# Nota: Você precisará criar os arquivos vazios nas outras pastas para não dar erro,
# ou comentar as linhas abaixo até criá-los.
from calculos import renal
# from calculos import uti  <-- Futuramente
# from calculos import cardio <-- Futuramente

st.header("🖥️ Calculadoras Médicas")

# Seletor de Categoria (Menu Principal do Hub)
categoria = st.selectbox(
    "Selecione a Especialidade / Categoria:",
    [
        "1. Função Renal",
        "2. Gravidade (UTI)",
        "3. Sepse e Choque",
        "4. Ventilação Mecânica",
        "5. Cardiologia",
        # ... outras ...
    ]
)

st.markdown("---")

# O Cérebro decide quem chamar
if "Renal" in categoria:
    renal.render_renal() # Chama a função que desenha a tela renal

elif "UTI" in categoria:
    st.warning("🚧 Módulo de UTI em construção. (Crie calculos/uti.py)")
    # uti.render_uti()

elif "Ventilação" in categoria:
    st.warning("🚧 Módulo de Ventilação em construção.")

else:
    st.info("Selecione uma categoria acima para começar.")