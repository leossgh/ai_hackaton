#!/usr/bin/env bash
# Start the dashboard on localhost:8501. From your laptop: ssh -L 8501:localhost:8501 <vm>, then open http://localhost:8501
cd "$(dirname "$0")"
exec uv run --quiet --with streamlit --with pandas --with py3Dmol --with stmol --with ipython_genutils \
  streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
