#!/bin/bash
set -e

ollama serve &
SERVER_PID=$!

echo "Waiting for Ollama to start..."
until ollama list > /dev/null 2>&1; do
    sleep 2
done
echo "Ollama is ready"

echo "Pulling embedding model: $EMBEDDING_MODEL"
ollama pull "$EMBEDDING_MODEL"

echo "Pulling generation model: $GENERATION_MODEL"
ollama pull "$GENERATION_MODEL"

echo "All models pulled successfully"
wait $SERVER_PID
