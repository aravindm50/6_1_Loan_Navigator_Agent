# supervisor/supervisor_agent.py

import os
from typing import Dict
from dotenv import load_dotenv

import sys
# add parent folder (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sql_agent import SQLAgent
from agents.policy_agent import PolicyGuruAgent
from agents.calc_agent import WhatIfCalculatorAgent
from agents.intent_classifier import IntentClassifier

# -----------------------------
# SupervisorAgent Class
# -----------------------------
class SupervisorAgent:
    """
    Central orchestrator for Loan Navigator:
    - Receives user queries
    - Classifies intent using IntentClassifier
    - Routes to appropriate sub-agents
    - Combines responses
    """

    def __init__(self):
        self.sql_agent = SQLAgent()
        self.policy_agent = PolicyGuruAgent()
        self.calc_agent = WhatIfCalculatorAgent()
        self.intent_classifier = IntentClassifier()  # New modular classifier

    # -----------------------------
    # Main handler
    # -----------------------------
    def handle_query(self, user_query: str) -> Dict:
        intent = self.intent_classifier.classify_intent(user_query)
        response = {}

        if intent == "sql_emi":
            sql_result = self.sql_agent.handle_query(user_query)
            response["sql_result"] = sql_result
            response["answer"] = f"Here is the loan data: {sql_result.get('rows')}"

        elif intent == "calc_prepayment":
            # Example values; in production parse from query or LLM
            result = self.calc_agent.simulate_prepayment(
                principal=50000,
                annual_rate=12,
                tenure_months=24,
                months_paid=6,
                prepayment_amount=10000
            )
            response["calc_result"] = result
            response["answer"] = f"Prepayment simulation result: {result}"

        elif intent == "calc_topup":
            # Example values; in production parse from query or LLM
            result = self.calc_agent.check_topup_eligibility(
                topup_eligible=True,
                outstanding_principal=30000
            )
            response["calc_result"] = result
            response["answer"] = f"Top-up eligibility: {result}"

        elif intent == "policy_query":
            policy_result = self.policy_agent.handle_query(user_query)
            response["policy_result"] = policy_result
            response["answer"] = policy_result.get("answer", "No policy info found")

        else:  # general fallback
            response["answer"] = "Sorry, I could not understand your question. Please rephrase."

        response["intent"] = intent
        return response


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    load_dotenv()

    agent = SupervisorAgent()
    
    queries = [
        "What is my next EMI?",
        "Can I prepay my loan?",
        "Am I eligible for a top-up?",
        "What is the RBI guideline on prepayment penalties?",
        "Tell me something random"
    ]
    
    for q in queries:
        result = agent.handle_query(q)
        print(f"Query: {q}")
        print(f"Result: {result}")
        print("-" * 50)
