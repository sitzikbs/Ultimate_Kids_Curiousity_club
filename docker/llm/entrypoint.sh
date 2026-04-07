#!/bin/bash
set -euo pipefail
ollama serve &
sleep 5
if ! ollama list | grep -q "gemma4"; then
    echo "Pulling Gemma 4 model..."
    ollama pull gemma4:26b-a4b
fi
wait
