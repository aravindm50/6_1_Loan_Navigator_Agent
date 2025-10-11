# chroma_service/Dockerfile
FROM python:3.11
WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install chromadb sentence-transformers fitz

EXPOSE 8000
CMD ["chromadb", "run", "--host", "0.0.0.0", "--port", "8000"]
