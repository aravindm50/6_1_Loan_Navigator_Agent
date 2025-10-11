# ============================================
# Dockerfile: Loan Navigator Backend + Streamlit
# ============================================

# Base image
FROM python:3.11-slim

# -----------------------------
# Set working directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Copy project files
# -----------------------------
COPY . .

# -----------------------------
# Upgrade pip and install dependencies
# -----------------------------
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# -----------------------------
# Expose ports
# -----------------------------
# 8000 = FastAPI API
# 8501 = Streamlit UI (optional)
EXPOSE 8000 8501

# -----------------------------
# Environment variables (example)
# -----------------------------
ENV LOAN_DB_BUCKET="loan-navigator-data-6-1"
ENV LOAN_DB_BLOB="LoanDB_BlueLoans4all.sqlite"
ENV CHROMA_URL="http://chroma-service:8000"
ENV GCP_PROJECT="bdc-training"
ENV GCP_REGION="us-central1"
ENV VERTEX_AI_MODEL="gemini-2.0-flash"

# -----------------------------
# Default command: FastAPI
# -----------------------------
# For production: run FastAPI as main process
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------
# Optional for dev: Streamlit
# -----------------------------
# To run Streamlit for UI demo:
# CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
