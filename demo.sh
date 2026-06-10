#!/bin/bash
# Launch the Muwalah interactive terminal.
# Usage: ./demo.sh              (interactive mode)
#        ./demo.sh "question"   (single query)
#
# First run handles: pip install, ollama model pull, then launch.
# CSV -> Parquet conversion is separate (python3 data/convert.py).
set -e
cd "$(dirname "$0")"

# Install Python deps if rich is missing (proxy for first run)
if ! python3 -c "import rich" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Pull Granite model if not already present
if ! curl -s "${OLLAMA_URL:-http://localhost:11434}/api/tags" 2>/dev/null | python3 -c "
import sys, json
models = [m['name'] for m in json.load(sys.stdin).get('models', [])]
sys.exit(0 if any('granite-4.0' in m for m in models) else 1)
" 2>/dev/null; then
    echo "Pulling Granite model (one-time download)..."
    ollama pull sam860/granite-4.0:7b
fi

python3 muwalah.py "$@"
