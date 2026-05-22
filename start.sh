#!/bin/bash
set -e

echo ""
echo "🔍 ProspectKit — starting up..."
echo ""

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "→ Creating virtual environment..."
  python3 -m venv .venv
fi

# Install dependencies
echo "→ Installing dependencies..."
.venv/bin/pip install -q -r requirements.txt

echo ""
echo "✅ Ready! Open http://localhost:8000 in your browser."
echo "   You'll be prompted to enter your Apollo API key on first load."
echo "   (Get one free at https://app.apollo.io → Settings → API)"
echo ""

# Launch
.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload
