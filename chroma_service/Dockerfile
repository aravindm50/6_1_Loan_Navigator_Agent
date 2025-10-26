FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install chromadb CLI & dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        chromadb[server]==0.4.3 \
        sentence-transformers \
        PyMuPDF==1.22.5

EXPOSE 8000

# Copy startup script
COPY start_chroma.sh /app/start_chroma.sh
RUN chmod +x /app/start_chroma.sh

# Start ChromaDB server and populate vector DB at runtime
CMD ["/app/start_chroma.sh"]
