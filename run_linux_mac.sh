#!/usr/bin/env bash
# Usage: ./run_linux_mac.sh      (needs Python 3.10+)
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Optional password:  export APP_PASSWORD=your_password
streamlit run app.py
