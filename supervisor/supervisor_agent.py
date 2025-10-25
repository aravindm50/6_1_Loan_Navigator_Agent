# supervisor/supervisor_agent.py

import re
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from agents.sql_agent import SQLAgent
from agents.policy_agent import PolicyGuruAgent
from agents.calc_agent import WhatIfCalculatorAgent
from agents.intent_classifier import IntentClassifier

logging.basicConfig(level=logging.INFO)

class SupervisorAgent:
    """
    Central orchestrator for all agents.
    Handles user queries, routes to appropriate agents,
    and manages fallback prompts for missing information.
    """

    def __init__(self):
        self.sql_agent = SQLAgent()
        self.policy_agent = PolicyGuruAgent()
        self.calc_agent = WhatIfCalculatorAgent()
        self.intent_classifier = IntentClassifier()

    def handle_query(self, user_query, context=None):
        """
        Handles user query, routes to appropriate agent(s),
        and returns a structured response.
        context: optional dict for already known info (e.g., customer_id)
        """
        logging.info(f"Received query: {user_query}")
        response = {"fallback": False, "intent": None, "answer": None}
        context = context or {}

        # Step 1: Classify intent
        intent = self.intent_classifier.classify_intent(user_query)
        response["intent"] = intent

        # -----------------------------
        # SQL Query Handling (EMI / loan data)
        # -----------------------------
        if intent == "sql_emi":
            sql_result = self.sql_agent.handle_query(user_query)
            response["sql_result"] = sql_result

            if "error" in sql_result or not sql_result.get("rows"):
                response["fallback"] = True
                response["answer"] = (
                    "Could not find relevant loan data. "
                    "Please provide your customer_id or loan reference."
                )
            else:
                response["answer"] = sql_result.get("rows")

        # -----------------------------
        # Prepayment Simulation
        # -----------------------------
        elif intent == "calc_prepayment":
            # Attempt to extract numbers from query
            numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", user_query)]
            required_fields = ["principal", "annual_rate", "tenure_months", "months_paid", "prepayment_amount"]

            if len(numbers) == len(required_fields):
                principal, annual_rate, tenure_months, months_paid, prepayment_amount = numbers
                result = self.calc_agent.simulate_prepayment(
                    principal=principal,
                    annual_rate=annual_rate,
                    tenure_months=int(tenure_months),
                    months_paid=int(months_paid),
                    prepayment_amount=prepayment_amount
                )
                response.update({"calc_result": result, "answer": result})
                if result.get("error"):
                    response["fallback"] = True
            else:
                # Missing values → ask user for them
                missing_fields = required_fields[len(numbers):]
                response["fallback"] = True
                response["answer"] = (
                    f"To perform prepayment simulation, please provide the following missing information: "
                    f"{', '.join(missing_fields)}"
                )

        # -----------------------------
        # Top-up Eligibility
        # -----------------------------
        elif intent == "calc_topup":
            # Check if customer_id or outstanding principal exists in context
            customer_id = context.get("customer_id")
            outstanding_principal = context.get("outstanding_principal")

            if customer_id and outstanding_principal is not None:
                result = self.calc_agent.check_topup_eligibility(True, outstanding_principal)
                response.update({"calc_result": result, "answer": result})
            else:
                response["fallback"] = True
                response["answer"] = (
                    "To check top-up eligibility, please provide your customer_id "
                    "or outstanding principal amount."
                )

        # -----------------------------
        # Policy Queries
        # -----------------------------
        elif intent == "policy_query":
            result = self.policy_agent.handle_query(user_query)
            response.update({"policy_result": result, "answer": result.get("answer")})
            if result.get("fallback"):
                response["fallback"] = True
                response["answer"] = (
                    "Could not confidently answer your query. "
                    "Please provide more context or specify the policy document."
                )

        # -----------------------------
        # Unknown Intent
        # -----------------------------
        else:
            response["fallback"] = True
            response["answer"] = "Sorry, I did not understand your request. Could you clarify?"

        # -----------------------------
        # Log final response
        # -----------------------------
        logging.info(f"Response: {response}")
        return response

# supervisor_agent.py

if __name__ == "__main__":
    from agents.intent_classifier import IntentClassifier
    from agents.sql_agent import SQLAgent
    from agents.policy_agent import PolicyGuruAgent

    supervisor = SupervisorAgent()

    queries = [
        "What is my next EMI?",
        "Can I prepay my loan without penalty?",
        "Am I eligible for a top-up?",
        "Tell me the RBI guideline on prepayment."
    ]

    for q in queries:
        result = supervisor.handle_query(q)
        print(f"Query: {q}\nResult: {result}\n")
