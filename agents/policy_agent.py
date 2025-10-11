# agents/policy_agent.py

import os
import requests
from typing import List, Dict
from google.cloud import aiplatform
from dotenv import load_dotenv

# -----------------------------
# PolicyGuruAgent Class
# -----------------------------
class PolicyGuruAgent:
    """
    Policy Guru Agent: 
    Performs RAG-based policy lookups using Chroma vector DB 
    and synthesizes answers via Vertex AI Gemini.
    """

    def __init__(self):
        self.chroma_url = os.getenv("CHROMA_URL")  # e.g. https://chroma-service-xxxx.a.run.app
        self.project = os.getenv("GCP_PROJECT")
        self.location = os.getenv("GCP_REGION", "us-central1")
        self.model = os.getenv("VERTEX_AI_MODEL", "gemini-2.0-flash")

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
            # Each result contains: 'id', 'document', 'metadata', 'score'
            return results.get("results", [])[0].get("documents", [])
        except Exception as e:
            print(f"Error querying Chroma: {e}")
            return []

    # -----------------------------
    # Use Vertex AI to synthesize answer
    # -----------------------------
    def synthesize_answer(self, question: str, contexts: List[str]) -> Dict:
        """
        Use Gemini to synthesize answer with retrieved contexts
        """
        from google.cloud.aiplatform.gapic.schema import predict
        from google.cloud.aiplatform.gapic import PredictionServiceClient
        from google.protobuf import json_format

        client = PredictionServiceClient()
        endpoint = f"projects/{self.project}/locations/{self.location}/models/{self.model}"

        context_text = "\n\n".join(contexts)
        prompt = f"""
        You are an expert financial assistant. Use the following policy documents
        to answer the user's question accurately and cite sources when possible.

        Contexts:
        {context_text}

        Question:
        {question}

        Answer concisely with citations.
        """

        instance = {"content": prompt}
        instances = [json_format.ParseDict(instance, predict.instance.Instance())]

        response = client.predict(endpoint=endpoint, instances=instances)
        predictions = response.predictions

        if predictions and len(predictions) > 0:
            answer = predictions[0].get("content", "").strip()
            return {"answer": answer, "contexts": contexts}
        else:
            return {"answer": "Sorry, I could not find relevant policy information.", "contexts": []}

    # -----------------------------
    # Main entry: handle query
    # -----------------------------
    def handle_query(self, user_question: str, top_k: int = 5) -> Dict:
        retrieved_docs = self.query_chroma(user_question, top_k=top_k)
        contexts = [doc.get("document", "") for doc in retrieved_docs]
        result = self.synthesize_answer(user_question, contexts)
        return result


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":

    load_dotenv()

    agent = PolicyGuruAgent()
    question = "Can I prepay my loan without penalty?"
    result = agent.handle_query(question)
    print(result)
