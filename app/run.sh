#!/bin/bash
# Simple script to run the MIDAS Graph Explorer app

echo "🧬 Starting MIDAS..."
cd /home/ubuntu/MIDAS
uv run streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0

