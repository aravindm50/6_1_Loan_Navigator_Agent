# supervisor/supervisor_agent.py

import sys
import os
import logging

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.sql_agent import SQLAgent
from agents.policy_agent import PolicyGuruAgent
from agents.calc_agent import WhatIfCalculatorAgent, LLMNumberExtractor
from agents.intent_classifier import IntentClassifier

logging.basicConfig(level=logging.INFO)


class SupervisorAgent:
    """
    Central orchestrator for all sub-agents.
    Handles user queries, classifies intent, extracts numeric info, and routes to appropriate agent.
    """

    def __init__(self):
        self.sql_agent = SQLAgent()
        self.policy_agent = PolicyGuruAgent()
        self.calc_agent = WhatIfCalculatorAgent()
        self.intent_classifier = IntentClassifier()
        self.extractor = LLMNumberExtractor()

    def handle_query(self, user_query, context=None):
        logging.info(f"Received query: {user_query}")
        response = {"fallback": False, "intent": None, "answer": None}
        context = context or {}

        # Step 1: classify intent
        intent = self.intent_classifier.classify_intent(user_query)
        response["intent"] = intent

        # Step 2: extract numeric values via LLM
        nums = self.extractor.extract_numbers(user_query)
        logging.info(f"LLM parsed numbers: {nums}")

        # -----------------------------
        # EMI calculation
        # -----------------------------
        if intent in ["calc_emi"]:
            required = ["loan_amount", "annual_rate", "tenure_months"]
            missing = [r for r in required if not nums.get(r)]
            if missing:
                response.update({
                    "fallback": True,
                    "answer": f"Missing required information for EMI calculation: {', '.join(missing)}"
                })
            else:
                summary = self.calc_agent.amortization_schedule(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"])
                )
                response.update({"calc_result": summary, "answer": summary})

        # -----------------------------
        # Prepayment simulation
        # -----------------------------
        elif intent == "calc_prepayment":
            required = ["loan_amount", "annual_rate", "tenure_months", "prepayment_amount"]
            missing = [r for r in required if not nums.get(r)]
            if missing:
                response.update({
                    "fallback": True,
                    "answer": f"Missing required information for prepayment simulation: {', '.join(missing)}"
                })
            else:
                prepay_result = self.calc_agent.simulate_prepayment(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"]),
                    prepayment_amount=nums["prepayment_amount"],
                    apply_month=nums.get("apply_month", 1)
                )
                response.update({"calc_result": prepay_result, "answer": prepay_result})

        # -----------------------------
        # Tenure change simulation
        # -----------------------------
        elif intent == "calc_tenure_change":
            required = ["loan_amount", "annual_rate", "new_tenure_months"]
            missing = [r for r in required if not nums.get(r)]
            if missing:
                response.update({
                    "fallback": True,
                    "answer": f"Missing required information for tenure change simulation: {', '.join(missing)}"
                })
            else:
                tenure_result = self.calc_agent.simulate_tenure_change(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"]) if nums.get("tenure_months") else nums["new_tenure_months"],
                    new_tenure_months=int(nums["new_tenure_months"])
                )
                response.update({"calc_result": tenure_result, "answer": tenure_result})

        # -----------------------------
        # Interest rate change simulation
        # -----------------------------
        elif intent == "calc_rate_change":
            required = ["loan_amount", "annual_rate", "tenure_months", "new_rate"]
            missing = [r for r in required if not nums.get(r)]
            if missing:
                response.update({
                    "fallback": True,
                    "answer": f"Missing required information for rate change simulation: {', '.join(missing)}"
                })
            else:
                rate_result = self.calc_agent.simulate_rate_change(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"]),
                    new_rate=nums["new_rate"]
                )
                response.update({"calc_result": rate_result, "answer": rate_result})

        # -----------------------------
        # Top-up eligibility
        # -----------------------------
        elif intent == "calc_topup":
            customer_id = context.get("customer_id")
            outstanding_principal = context.get("outstanding_principal")
            if customer_id and outstanding_principal is not None:
                result = self.calc_agent.check_topup_eligibility(True, outstanding_principal)
                response.update({"calc_result": result, "answer": result})
            else:
                response.update({
                    "fallback": True,
                    "answer": "Please provide your customer_id or outstanding principal for top-up eligibility."
                })

        # -----------------------------
        # Policy queries
        # -----------------------------
        elif intent == "policy_query":
            result = self.policy_agent.handle_query(user_query)
            response.update({"policy_result": result, "answer": result.get("answer")})
            if result.get("fallback"):
                response.update({"fallback": True, "answer": "Could not confidently answer policy query. Provide more context."})

        # -----------------------------
        # SQL fetch (user-specific data)
        # -----------------------------
        elif intent == "sql_fetch":
            sql_result = self.sql_agent.handle_query(user_query)
            response.update({"sql_result": sql_result})
            if "error" in sql_result or not sql_result.get("rows"):
                response.update({
                    "fallback": True,
                    "answer": "Could not fetch your loan data. Please provide customer_id or loan reference."
                })
            else:
                response["answer"] = sql_result.get("rows")

        # -----------------------------
        # Default / fallback
        # -----------------------------
        else:
            response.update({
                "fallback": True,
                "answer": "Sorry, I did not understand your request. Could you rephrase it?"
            })

        logging.info(f"Response: {response}")
        return response


# -----------------------------
# CLI / Example usage
# -----------------------------
if __name__ == "__main__":
    supervisor = SupervisorAgent()

    queries = [
        "Calculate EMI for loan amount 75000, interest 12%, tenure 12 months",
        "What if I prepay 10000 on my 75000 loan at 12% for 12 months?",
        "What if I reduce my tenure to 24 months for a 200000 loan at 10%?",
        "What if interest rate drops to 11% for my 100000 loan with 24 months tenure?",
        "Tell me about RBI prepayment guidelines",
        "Am I eligible for a top-up if my outstanding principal is 50000?",
        "Where is Blue Fin consulting located?"
    ]

    for q in queries:
        result = supervisor.handle_query(q)
        print(f"\nQuery: {q}\nResult: {result}\n")
