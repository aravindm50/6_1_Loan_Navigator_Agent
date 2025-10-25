# agents/intent_classifier.py

from typing import Literal
import os
from vertexai import init
from vertexai.generative_models import GenerativeModel

# Define the allowed intents
Intents = Literal[
    "sql_emi",
    "calc_prepayment",
    "calc_topup",
    "policy_query",
    "general_query"
]


class IntentClassifier:
    """
    LLM-based intent classifier using Vertex AI Gemini 2.0 Flash.
    Classifies user queries into intents for the Loan Navigator app.
    """

    def __init__(self, project_id: str = os.getenv("GCP_PROJECT"), location: str = os.getenv("GCP_REGION")):
        init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash")

        # Intent definitions for grounding
        self.intent_definitions = {
            "sql_emi": "Questions about EMI, next installment, or monthly payment.",
            "calc_prepayment": "Questions about prepayment, early repayment, or partial payments.",
            "calc_topup": "Questions about loan top-ups, additional eligibility, or adding a new loan.",
            "policy_query": "Questions about RBI rules, loan policies, or regulations.",
            "general_query": "Anything else not covered by the above categories."
        }

    def classify_intent(self, query: str) -> Intents:
        """
        Use the Gemini LLM to classify a user query into one of the intents.
        """
        system_prompt = (
            "You are an intent classifier for a Loan Navigator application. "
            "Given a user's question, classify it into exactly one of the following intents:\n\n"
        )

        for k, v in self.intent_definitions.items():
            system_prompt += f"- {k}: {v}\n"

        system_prompt += (
            "\nRespond ONLY with one of these labels (no explanation): "
            "sql_emi, calc_prepayment, calc_topup, policy_query, general_query."
        )

        # Send both system + user text as plain strings (correct Vertex SDK format)
        response = self.model.generate_content(
            [system_prompt, f"User query: {query}"],
            generation_config={
                "temperature": 0.0,
                "max_output_tokens": 20,
            },
        )

        intent = response.text.strip().lower()
        if intent not in self.intent_definitions:
            intent = "general_query"
        return intent


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    classifier = LLMIntentClassifier(project_id="bdc-trainings")

    queries = [
        "What is my next EMI?",
        "Can I prepay my loan?",
        "Am I eligible for a top-up?",
        "What is the RBI guideline on prepayment penalties?",
        "Tell me something random",
        "Where is Blue Fin consulting",
        "Do I need to pay my loan?"
    ]

    for q in queries:
        intent = classifier.classify_intent(q)
        print(f"Query: {q} -> Intent: {intent}")
