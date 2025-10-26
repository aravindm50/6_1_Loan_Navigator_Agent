#!/bin/bash
set -e

echo "Starting ChromaDB server..."
chromadb server --host 0.0.0.0 --port 8000 --anonymized-telemetry false & --persist_directory /app/chroma_persist &

# Wait a few seconds for server to be ready
echo "Waiting for ChromaDB to initialize..."
sleep 10

echo "Running vector creation script..."
python scripts/create_vector.py
