#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || echo "Activate your venv manually"
python3 server.py
