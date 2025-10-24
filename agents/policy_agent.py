# agents/policy_agent.py

import os
import requests
import logging
from typing import List, Dict
from google.cloud import aiplatform
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

class PolicyGuruAgent:
    """
    Policy Guru Agent: 
    Performs RAG-based policy lookups using Chroma vector DB 
    and synthesizes answers via Vertex AI Gemini using aiplatform SDK.
    """

    def __init__(self):
        self.chroma_url = os.getenv("CHROMA_URL")  # e.g., http://localhost:8000
        self.project = os.getenv("GCP_PROJECT")
        self.location = os.getenv("GCP_REGION", "us-central1")
        self.model = os.getenv("VERTEX_AI_MODEL", "gemini-2.0-flash")
        self.confidence_threshold = 0.75

        # Initialize Vertex AI
        aiplatform.init(project=self.project, location=self.location)

    # -----------------------------
    # Query Chroma Vector DB
    # -----------------------------
    def query_chroma(self, question: str, top_k: int = 5) -> List[Dict]:
        """
        Send query to Chroma DB REST API and return top-k relevant chunks
        """
        endpoint = f"{self.chroma_url}/collections/policy_docs/query"
        payload = {
            "query_texts": [question],
            "n_results": top_k
        }
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            results = response.json()
            return results.get("results", [])[0].get("documents", [])
        except Exception as e:
            logging.error(f"Error querying Chroma: {e}")
            return []

    # -----------------------------
    # Synthesize answer using Vertex AI SDK
    # -----------------------------
    def synthesize_answer(self, question: str, contexts: List[str]) -> Dict:
        context_text = "\n\n".join(contexts)
        prompt = f"""
        You are an expert financial assistant. Use the following policy documents
        to answer the user's question accurately and cite sources when possible.

        Contexts:
        {context_text}

        Question:
        {question}

        Answer concisely with citations.
        If you cannot answer confidently, respond with: "Cannot answer confidently."
        """

        try:
            # Use Vertex AI Text Generation
            response = aiplatform.TextGenerationModel.from_pretrained(self.model).predict(
                prompt,
                max_output_tokens=500,
                temperature=0.2
            )
            answer = response.text.strip()

            if "Cannot answer confidently" in answer or not answer:
                return {"answer": "Fallback: need more context or document.", "fallback": True}
            else:
                return {"answer": answer, "contexts": contexts, "fallback": False}

        except Exception as e:
            logging.error(f"Vertex AI synthesis failed: {e}")
            return {"answer": "Error synthesizing policy.", "fallback": True}

    # -----------------------------
    # Main entry: handle query
    # -----------------------------
    def handle_query(self, user_question: str, top_k: int = 5) -> Dict:
        retrieved_docs = self.query_chroma(user_question, top_k=top_k)
        contexts = [doc.get("document", "") for doc in retrieved_docs]
        if not contexts:
            return {"answer": "No relevant policy documents found.", "fallback": True}
        result = self.synthesize_answer(user_question, contexts)
        return result


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    agent = PolicyGuruAgent()
    question = "Can I prepay my loan without penalty?"
    result = agent.handle_query(question)
    print(result)
