#!/usr/bin/env bash
# Launch the SmartFile application.
set -e
cd "$(dirname "$0")"

echo "Starting SmartFile ..."
echo "Open http://localhost:8501 in your browser once the server is ready."
echo

python3 -m streamlit run app/main.py
