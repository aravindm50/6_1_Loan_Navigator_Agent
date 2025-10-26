from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from supervisor.supervisor_agent import SupervisorAgent

# -----------------------------
# Request / Response Models
# -----------------------------
class QueryRequest(BaseModel):
    user_query: str
    context: Optional[Dict] = {}

class QueryResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    fallback: bool = False
    missing_fields: Optional[list] = None
    context: Dict

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Loan Navigator API")

# Initialize Supervisor Agent
agent = SupervisorAgent()

# -----------------------------
# API endpoint
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    try:
        result = agent.handle_query(request.user_query, context=request.context)
        return QueryResponse(
            answer=result.get("answer", "No answer available."),
            intent=result.get("intent"),
            fallback=result.get("fallback", False),
            missing_fields=result.get("missing_fields", []),
            context=result.get("context", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# -----------------------------
# Health check endpoint
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
