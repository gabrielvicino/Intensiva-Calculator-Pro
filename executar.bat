@echo off
cd /d "%~dp0"
py -m streamlit run app.py --server.headless true
pause
