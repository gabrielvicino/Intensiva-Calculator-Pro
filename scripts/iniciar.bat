@echo off
taskkill /F /IM streamlit.exe >nul 2>&1
streamlit run "app.py"