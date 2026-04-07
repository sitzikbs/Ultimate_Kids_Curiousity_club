#!/bin/bash
set -euo pipefail

# Start ollama server in background
ollama serve &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for ollama server..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:11435/api/tags > /dev/null 2>&1; then
        echo "Ollama server ready"
        break
    fi
    sleep 2
done

if ! curl -sf http://localhost:11435/api/tags > /dev/null 2>&1; then
    echo "ERROR: ollama server failed to start within 60s" >&2
    exit 1
fi

# Pull model if not present
MODEL="${LLM_MODEL:-gemma4:26b-a4b}"
if ! ollama list | grep -q "${MODEL%%:*}"; then
    echo "Pulling model: $MODEL"
    ollama pull "$MODEL"
fi

echo "LLM service ready with model: $MODEL"
wait $SERVER_PID
