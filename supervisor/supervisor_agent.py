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

from dotenv import load_dotenv

load_dotenv()


class SupervisorAgent:
    """
    Central orchestrator for all sub-agents.
    Handles user queries, classifies intent, tracks context across turns,
    and manages fallback for missing info.
    """

    def __init__(self):
        self.sql_agent = SQLAgent()
        self.policy_agent = PolicyGuruAgent()
        self.calc_agent = WhatIfCalculatorAgent()
        self.intent_classifier = IntentClassifier()
        self.number_extractor = LLMNumberExtractor()

    def handle_query(self, user_query: str, context: dict = None) -> dict:
        logging.info(f"Received query: {user_query}")
        context = context or {}
        response = {
            "fallback": False,
            "intent": None,
            "answer": None,
            "agent_results": {},
            "context": context.copy(),
            "missing_fields": []
        }

        # Step 1: classify intent
        intent = self.intent_classifier.classify_intent(user_query)
        response["intent"] = intent

        try:
            # -----------------------------
            # EMI / SQL fetch
            # -----------------------------
            if intent in ["sql_fetch", "calc_emi"]:
                customer_id = context.get("customer_id")
                loan_id = context.get("loan_id")
                missing = []
                if not customer_id:
                    missing.append("customer_id")
                if not loan_id:
                    missing.append("loan_id")

                if missing:
                    response.update({
                        "fallback": True,
                        "answer": "Missing or invalid info. Please provide valid values.",
                        "missing_fields": missing
                    })
                else:
                    sql_result = self.sql_agent.handle_query(user_query, customer_id=customer_id, loan_id=loan_id)
                    response["agent_results"]["sql_agent"] = sql_result
                    if "error" in sql_result or not sql_result.get("rows"):
                        response.update({
                            "fallback": True,
                            "answer": "Could not fetch your loan data. Please check your entries."
                        })
                    else:
                        response["answer"] = f"Your EMI details: {sql_result.get('rows')}"

            # -----------------------------
            # Prepayment simulation
            # -----------------------------
            elif intent == "calc_prepayment":
                nums = self.number_extractor.extract_numbers(user_query)
                required = ["loan_amount", "annual_rate", "tenure_months", "prepayment_amount"]
                missing = [k for k in required if not nums.get(k)]
                if missing:
                    response.update({
                        "fallback": True,
                        "answer": f"Missing required values for prepayment: {', '.join(missing)}",
                        "missing_fields": missing
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
                nums = self.number_extractor.extract_numbers(user_query)
                required = ["loan_amount", "annual_rate", "tenure_months", "new_tenure_months"]
                missing = [k for k in required if not nums.get(k)]
                if missing:
                    response.update({
                        "fallback": True,
                        "answer": f"Missing required values for tenure change: {', '.join(missing)}",
                        "missing_fields": missing
                    })
                else:
                    tenure_result = self.calc_agent.simulate_tenure_change(
                        loan_amount=nums["loan_amount"],
                        annual_rate=nums["annual_rate"],
                        tenure_months=int(nums["tenure_months"]),
                        new_tenure_months=int(nums["new_tenure_months"])
                    )
                    response.update({"calc_result": tenure_result, "answer": tenure_result})

            # -----------------------------
            # Top-up eligibility
            # -----------------------------
            elif intent == "calc_topup":
                customer_id = context.get("customer_id")
                outstanding_principal = context.get("outstanding_principal")
                missing = []
                if not customer_id:
                    missing.append("customer_id")
                if outstanding_principal is None:
                    missing.append("outstanding_principal")
                if missing:
                    response.update({
                        "fallback": True,
                        "answer": f"Missing required values for top-up eligibility: {', '.join(missing)}",
                        "missing_fields": missing
                    })
                else:
                    topup_result = self.calc_agent.check_topup_eligibility(True, outstanding_principal)
                    response.update({"calc_result": topup_result, "answer": topup_result})

            # -----------------------------
            # Policy queries
            # -----------------------------
            elif intent == "policy_query":
                policy_result = self.policy_agent.handle_query(user_query)
                response["agent_results"]["policy_agent"] = policy_result
                response["answer"] = policy_result.get("answer")
                if policy_result.get("fallback"):
                    response.update({
                        "fallback": True,
                        "answer": "Could not confidently answer policy query. Provide more context."
                    })

            # -----------------------------
            # Default fallback
            # -----------------------------
            else:
                response.update({
                    "fallback": True,
                    "answer": "Sorry, I did not understand your request. Could you rephrase it?"
                })

        except Exception as e:
            logging.error(f"Error during query handling: {e}")
            response.update({
                "fallback": True,
                "answer": f"An error occurred while processing your request: {str(e)}"
            })

        response["context"] = context
        return response
