# main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supervisor.supervisor_agent import SupervisorAgent

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(
    title="Loan Navigator Agent API",
    description="API to handle loan-related queries using SQL, Policy, and What-If Calculator Agents",
    version="1.0"
)

# -----------------------------
# Initialize SupervisorAgent
# -----------------------------
agent = SupervisorAgent()

# -----------------------------
# Request model
# -----------------------------
class QueryRequest(BaseModel):
    question: str

# -----------------------------
# Health check endpoint
# -----------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Loan Navigator Agent is running"}

# -----------------------------
# Ask endpoint
# -----------------------------
@app.post("/ask")
def ask_question(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        result = agent.handle_query(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# -----------------------------
# Optional: root endpoint
# -----------------------------
@app.get("/")
def root():
    return {"message": "Welcome to Loan Navigator Agent API. Use /ask endpoint to query."}
