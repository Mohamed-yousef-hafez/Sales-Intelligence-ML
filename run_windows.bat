@echo off
REM Double-click this file. The first run installs everything (needs Python 3.10+ and internet once).
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
REM Optional password:  set APP_PASSWORD=your_password
streamlit run app.py
pause
