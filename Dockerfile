FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Cloud Run only cares about one port
EXPOSE 8000

# Environment variables
ENV LOAN_DB_BUCKET="loan-navigator-data-6-1"
ENV LOAN_DB_BLOB="LoanDB_BlueLoans4all.sqllite"
ENV CHROMA_URL="https://chroma-service-456822750436.us-central1.run.app"
ENV GCP_PROJECT="bdc-trainings"
ENV GCP_REGION="us-central1"
ENV VERTEX_AI_MODEL="gemini-2.0-flash"

# Run FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
