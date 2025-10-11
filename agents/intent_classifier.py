# agents/intent_classifier.py

from typing import Literal


class IntentClassifier:
    """
    Simple keyword-based intent classifier for Loan Navigator queries.
    Returns one of:
        - 'sql_emi'
        - 'calc_prepayment'
        - 'calc_topup'
        - 'policy_query'
        - 'general_query'
    """

    def __init__(self):
        # Keywords for each intent
        self.intent_keywords = {
            "sql_emi": ["emi", "next installment", "monthly payment", "installment due"],
            "calc_prepayment": ["prepay", "prepayment", "partial payment", "early repayment"],
            "calc_topup": ["top-up", "topup", "eligibility", "add loan"],
            "policy_query": ["policy", "rbi", "rule", "guideline", "regulation"],
        }

    def classify_intent(self, query: str) -> Literal[
        "sql_emi", "calc_prepayment", "calc_topup", "policy_query", "general_query"
    ]:
        """
        Classify user query into one of the intents.
        Fallback: 'general_query'
        """
        query_lower = query.lower()

        for intent, keywords in self.intent_keywords.items():
            if any(word in query_lower for word in keywords):
                return intent

        return "general_query"


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    classifier = IntentClassifier()
    queries = [
        "What is my next EMI?",
        "Can I prepay my loan?",
        "Am I eligible for a top-up?",
        "What is the RBI guideline on prepayment penalties?",
        "Tell me something random"
    ]

    for q in queries:
        intent = classifier.classify_intent(q)
        print(f"Query: {q} -> Intent: {intent}")
