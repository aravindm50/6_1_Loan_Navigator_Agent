# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from supervisor.supervisor_agent import SupervisorAgent
import logging

import os
import sys
# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Loan Navigator API")
agent = SupervisorAgent()

class QueryRequest(BaseModel):
    query: str
    context: dict = {}

@app.post("/query")  # make sure it's POST, not GET
def query_endpoint(req: QueryRequest):
    try:
        result = agent.handle_query(req.query, context=req.context)
        return result
    except Exception as e:
        logging.error(f"Error in /query: {e}")
        return {"error": str(e)}



# -----------------------------
# Health check endpoint
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
