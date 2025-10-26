FROM python:3.11-slim
 
# Set working directory
WORKDIR /app
 
# Copy requirements if you have any (optional)
COPY . .
 
# Install dependencies and required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    fuse \
&& rm -rf /var/lib/apt/lists/*
 
# Install ChromaDB server
RUN pip install --upgrade pip && \
    pip install --no-cache-dir "chromadb" 
# Chroma persistent path (inside container)
ENV CHROMA_PATH="/app/chroma_data"
RUN mkdir -p $CHROMA_PATH
VOLUME ["$CHROMA_PATH"]
 
# Expose the port Cloud Run uses
ENV PORT=8000
EXPOSE $PORT
 
# Start ChromaDB server
CMD ["chroma", "run", "--host", "0.0.0.0", "--port", "8000", "--path", "/app/chroma_data"]

 