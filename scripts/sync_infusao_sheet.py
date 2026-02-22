"""
Script para sincronizar os dados de infusão para o Google Sheets.
Execute: streamlit run scripts/sync_infusao_sheet.py
"""
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz))

import streamlit as st
from utils import sync_infusao_to_sheet, SHEET_URL

st.set_page_config(page_title="Sincronizar Infusão", page_icon="💉", layout="centered")
st.title("💉 Sincronizar DB_INFUSAO para Google Sheets")

st.markdown("""
Envia os dados de **pré-carregamento** (número de ampolas e diluente padrão) 
para a aba **DB_INFUSAO** no Google Sheets.

**Ex.:** Adrenalina: 4 ampolas, 246 ml; Norepinefrina: 4 ampolas, 234 ml.
""")

if st.button("🔄 Sincronizar agora", type="primary"):
    with st.spinner("Enviando dados para o Google Sheets..."):
        ok = sync_infusao_to_sheet()
    if ok:
        st.success("✅ Dados sincronizados! A aba DB_INFUSAO foi atualizada.")
    else:
        st.error("Falha na sincronização. Verifique a conexão com o Google Sheets.")

st.markdown("---")
st.caption(f"Planilha: {SHEET_URL}")
