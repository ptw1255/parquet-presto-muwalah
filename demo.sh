#!/bin/bash
# Launch the Muwalah interactive terminal.
# Usage: ./demo.sh              (interactive mode)
#        ./demo.sh "question"   (single query)
cd "$(dirname "$0")"
python3 muwalah.py "$@"
