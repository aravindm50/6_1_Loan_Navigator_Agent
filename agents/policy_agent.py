# agents/policy_agent.py

import os
import logging
from typing import List, Dict
from dotenv import load_dotenv
from chromadb import HttpClient
from vertexai import init
from vertexai.generative_models import GenerativeModel

load_dotenv()
logging.basicConfig(level=logging.INFO)


class PolicyGuruAgent:
    """
    Policy Guru Agent:
    Performs RAG-based policy lookups using Chroma vector DB
    and synthesizes answers via Vertex AI Gemini using GenerativeModel.
    Implements a confidence threshold for fallback.
    """

    def __init__(self):
        # -----------------------------
        # Chroma DB settings
        # -----------------------------
        self.chroma_host = os.getenv("CHROMA_URL")
        self.collection_name = "policy_docs"

        # -----------------------------
        # Vertex AI settings
        # -----------------------------
        self.project = os.getenv("GCP_PROJECT")
        self.location = os.getenv("GCP_REGION")
        self.model_name = os.getenv("VERTEX_AI_MODEL")
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.75))

        # -----------------------------
        # Initialize services
        # -----------------------------
        # Initialize Vertex AI
        # Initialize Vertex AI
        init(project=self.project, location=self.location)

        # Correct way to initialize
        self.model = GenerativeModel(model_name=self.model_name)

        # Initialize Chroma client
        self.client = HttpClient(host=self.chroma_host)

    # -----------------------------
    # Query Chroma Vector DB
    # -----------------------------
    def query_chroma(self, question: str, top_k: int = 5) -> List[Dict]:
        try:
            collection = self.client.get_collection(self.collection_name)
            results = collection.query(query_texts=[question], n_results=top_k)
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            # Combine doc + metadata
            return [{"document": d, "metadata": m} for d, m in zip(documents, metadatas)]
        except Exception as e:
            logging.error(f"Error querying Chroma: {e}")
            return []

    # -----------------------------
    # Synthesize answer using Vertex AI
    # -----------------------------
    def synthesize_answer(self, question: str, contexts: List[str]) -> Dict:
        if not contexts:
            return {"answer": "No relevant policy documents found.", "fallback": True}

        context_text = "\n\n".join(contexts)
        prompt = f"""
You are an expert financial assistant. Use the following policy documents
to answer the user's question accurately and cite sources when possible.

Contexts:
{context_text}

Question:
{question}

Answer concisely with citations.
If unsure or low confidence, respond with "Cannot answer confidently."
"""

        try:
            response = self.model.generate_content(
                [prompt],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 500,
                },
            )

            answer = response.text.strip()

            # Check for fallback
            if "Cannot answer confidently" in answer or not answer:
                return {"answer": "Fallback: need more context or document.", "fallback": True}
            else:
                return {"answer": answer, "contexts": contexts, "fallback": False}

        except Exception as e:
            logging.error(f"Vertex AI synthesis failed: {e}")
            return {"answer": "Error synthesizing policy.", "fallback": True}

    # -----------------------------
    # Handle user query
    # -----------------------------
    def handle_query(self, user_question: str, top_k: int = 5) -> Dict:
        retrieved_docs = self.query_chroma(user_question, top_k=top_k)
        contexts = [doc.get("document", "") for doc in retrieved_docs]

        # Apply confidence threshold: if no docs or too few, fallback
        if not contexts or len(contexts) < 1:
            return {"answer": "No relevant policy documents found.", "fallback": True}

        return self.synthesize_answer(user_question, contexts)


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    agent = PolicyGuruAgent()
    question = "Can I prepay my loan without penalty?"
    result = agent.handle_query(question)
    print(result)
