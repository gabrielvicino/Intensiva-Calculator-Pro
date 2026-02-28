"""
Script de teste para verificar se a API do Google Gemini está configurada.
Execute: python testar_gemini.py

A chave deve estar em:
  - .streamlit/secrets.toml (local): GOOGLE_API_KEY = "sua-chave"
  - Ou variável de ambiente: GOOGLE_API_KEY
"""
import os

def _carregar_chave():
    # 1. Variável de ambiente
    chave = os.getenv("GOOGLE_API_KEY", "")
    if chave:
        return chave
    # 2. Streamlit secrets (quando rodando via streamlit)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    # 3. Arquivo .streamlit/secrets.toml (na raiz do projeto)
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(_root, ".streamlit", "secrets.toml")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for linha in f:
                if linha.strip().startswith("GOOGLE_API_KEY"):
                    import re
                    m = re.search(r'["\']([^"\']+)["\']', linha)
                    if m:
                        return m.group(1)
    return ""


def testar():
    chave = _carregar_chave()
    if not chave or len(chave) < 20:
        print("[X] GOOGLE_API_KEY nao encontrada!")
        print("    Configure em .streamlit/secrets.toml ou variavel de ambiente.")
        return False

    print(f"[OK] Chave carregada (...{chave[-8:]})")
    print("     Testando chamada a API Gemini...")

    try:
        import google.generativeai as genai
        genai.configure(api_key=chave)
        model = genai.GenerativeModel("gemini-2.5-flash")
        resp = model.generate_content("Responda em uma palavra: OK")
        texto = resp.text.strip() if resp.text else ""
        print(f"     Resposta: {texto[:50]}")
        print("[OK] API Gemini funcionando!")
        return True
    except Exception as e:
        print(f"[X] Erro na API: {e}")
        return False


if __name__ == "__main__":
    testar()
