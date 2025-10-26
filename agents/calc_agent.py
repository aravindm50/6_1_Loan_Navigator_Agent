#!/usr/bin/env python3

from math import pow, isclose
from typing import Dict, Any, List, Optional

import os

import logging
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()

from vertexai import init
from vertexai.generative_models import GenerativeModel

# -----------------------------
# Utilities
# -----------------------------
def _round(x: float) -> float:
    return round(x + 1e-12, 2)

# -----------------------------
# Payment Row
# -----------------------------
class PaymentRow:
    def __init__(self, month, payment, principal, interest, balance):
        self.month = month
        self.payment = payment
        self.principal = principal
        self.interest = interest
        self.balance = balance

    def to_dict(self):
        return {
            "month": self.month,
            "payment": _round(self.payment),
            "principal": _round(self.principal),
            "interest": _round(self.interest),
            "balance": _round(self.balance),
        }

# -----------------------------
# WhatIfCalculatorAgent
# -----------------------------
class WhatIfCalculatorAgent:
    def calculate_emi(self, loan_amount: float, annual_rate: float, tenure_months: int):
        P = float(loan_amount)
        N = int(tenure_months)
        R = float(annual_rate) / (12 * 100)
        if isclose(R, 0.0):
            return P / N
        return (P * R * pow(1 + R, N)) / (pow(1 + R, N) - 1)

    def amortization_schedule(self, loan_amount: float, annual_rate: float, tenure_months: int, emi=None):
        P = float(loan_amount)
        N = int(tenure_months)
        R = float(annual_rate) / (12 * 100)
        if emi is None:
            emi = self.calculate_emi(P, annual_rate, N)

        schedule: List[PaymentRow] = []
        balance = P
        for month in range(1, N + 1):
            interest = balance * R
            principal = emi - interest
            if principal > balance:
                principal = balance
                emi_payment = principal + interest
            else:
                emi_payment = emi
            balance -= principal
            schedule.append(PaymentRow(month, emi_payment, principal, interest, balance))
            if balance <= 1e-9:
                break

        total_payment = sum(p.payment for p in schedule)
        total_interest = sum(p.interest for p in schedule)

        return {
            "emi": _round(emi),
            "schedule": [p.to_dict() for p in schedule],
            "total_payment": _round(total_payment),
            "total_interest": _round(total_interest),
        }

    def simulate_prepayment(self, loan_amount: float, annual_rate: float, tenure_months: int, prepayment_amount: float, apply_month=None):
        apply_month = 1 if apply_month is None else int(apply_month)

        summary = self.amortization_schedule(loan_amount, annual_rate, tenure_months)
        schedule = summary["schedule"]

        if apply_month > len(schedule):
            return {"error": "Apply month beyond tenure"}

        outstanding = schedule[apply_month - 1]["balance"]
        remaining_principal = outstanding - prepayment_amount

        if remaining_principal < 0:
            remaining_principal = 0.0

        # Recalculate amortization for remaining months
        remaining_months = len(schedule) - apply_month + 1
        if remaining_principal > 0:
            new_summary = self.amortization_schedule(
                remaining_principal, annual_rate, remaining_months
            )
            new_schedule = schedule[:apply_month] + new_summary["schedule"]
            interest_saved = summary["total_interest"] - new_summary["total_interest"]
        else:
            # Loan fully repaid
            new_schedule = schedule[:apply_month]
            interest_saved = summary["total_interest"]

        return {
            "mode": "reduce_tenure",
            "interest_saved": _round(interest_saved),
            "new_schedule": new_schedule,
            "new_tenure": len(new_schedule),
        }


    def simulate_tenure_change(
        self,
        loan_amount: float,
        annual_rate: float,
        tenure_months: int,
        new_tenure_months: int,
    ) -> Dict[str, Any]:
        old_summary = self.amortization_schedule(loan_amount, annual_rate, original_tenure)
        new_summary = self.amortization_schedule(loan_amount, annual_rate, new_tenure_months)

        delta_emi = _round(new_summary["emi"] - old_summary["emi"])
        interest_saved = _round(old_summary["total_interest"] - new_summary["total_interest"])

        return {
            "original_summary": old_summary,
            "new_summary": new_summary,
            "delta_emi": delta_emi,
            "interest_saved": interest_saved,
        }



    def simulate_rate_change(self, loan_amount: float, annual_rate: float, tenure_months: int, new_rate: float):
        old_summary = self.amortization_schedule(loan_amount, annual_rate, tenure_months)
        new_summary = self.amortization_schedule(loan_amount, new_rate, tenure_months)
        return {
            "original_summary": old_summary,
            "new_summary": new_summary,
            "emi_delta": _round(new_summary["emi"] - old_summary["emi"]),
            "interest_delta": _round(new_summary["total_interest"] - old_summary["total_interest"]),
        }

# -----------------------------
# LLM-like number extraction simulation
# -----------------------------
def llm_extract_numbers(query: str) -> Dict[str, Any]:
    """
    Simulate LLM number extraction from query.
    Only for demonstration purposes.
    """
    # Very naive mapping for demonstration
    numbers = {
        "loan_amount": None,
        "annual_rate": None,
        "tenure_months": None,
        "prepayment_amount": None,
        "apply_month": 1,
        "new_tenure_months": None,
        "new_rate": None,
        "outstanding_principal": None,
    }
    q = query.lower()
    words = q.replace("%", "").replace(",", "").split()
    for i, w in enumerate(words):
        if w in ("loan", "amount"):
            try:
                numbers["loan_amount"] = float(words[i + 1])
            except: pass
        if w in ("interest", "rate"):
            try:
                numbers["annual_rate"] = float(words[i + 1])
            except: pass
        if w in ("tenure", "months"):
            try:
                numbers["tenure_months"] = float(words[i + 1])
            except: pass
        if w in ("prepay", "prepayment"):
            try:
                numbers["prepayment_amount"] = float(words[i + 1])
            except: pass
        if w in ("new", "reduce"):
            try:
                numbers["new_tenure_months"] = float(words[i + 1])
            except: pass
    return numbers

class LLMNumberExtractor:
    """
    Extract numeric parameters from a user query using Vertex AI Gemini 2.0.
    """

    def __init__(self, project_id: str = None, location: str = None):
        project_id = project_id or os.getenv("GCP_PROJECT")
        location = location or os.getenv("GCP_REGION")
        init(project=project_id, location=location)
        self.model = GenerativeModel(os.getenv("VERTEX_AI_MODEL"))

    def extract_numbers(self, query: str) -> Dict[str, float]:
        """
        Ask the LLM to parse numbers from the query into a structured JSON dictionary.
        Keys: loan_amount, annual_rate, tenure_months, prepayment_amount,
              apply_month, new_tenure_months, new_rate, outstanding_principal
        """
        system_prompt = (
            "You are a precise assistant. Extract all numeric values from the user's query "
            "and return them in JSON format with the following keys: "
            "loan_amount, annual_rate, tenure_months, prepayment_amount, "
            "apply_month, new_tenure_months, new_rate, outstanding_principal. "
            "If a value is not present, return null. "
            "Return ONLY JSON, without any markdown code fences or extra text."
        )

        user_prompt = f"User query: {query}"

        response = self.model.generate_content(
            [system_prompt, user_prompt],
            generation_config={"temperature": 0.0, "max_output_tokens": 150}
        )

        text = response.text.strip()

        # Remove ```json or ``` fences if present
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        if text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        logging.info(f"LLM parsed numbers: {text}")

        try:
            import json
            nums = json.loads(text)
            # Convert nulls to None
            for k in nums:
                if nums[k] is None:
                    nums[k] = None
            return nums
        except Exception as e:
            logging.error(f"LLM number extraction failed: {e}")
            return {
                "loan_amount": None,
                "annual_rate": None,
                "tenure_months": None,
                "prepayment_amount": None,
                "apply_month": 1,
                "new_tenure_months": None,
                "new_rate": None,
                "outstanding_principal": None,
            }


if __name__ == "__main__":
    agent = WhatIfCalculatorAgent()
    extractor = LLMNumberExtractor()

    queries = [
        "Calculate EMI for loan amount 75000, interest 12%, tenure 12 months",
        "What if I prepay 10000 on my 75000 loan at 12% for 12 months?",
        "What if I reduce my tenure to 24 months for a 200000 loan at 10%?",
        "What if interest rate drops to 11% for my 100000 loan with 24 months tenure?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        nums = extractor.extract_numbers(query)

        try:
            if nums.get("loan_amount") and nums.get("annual_rate") and nums.get("tenure_months") and not nums.get("prepayment_amount"):
                summary = agent.amortization_schedule(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"])
                )
                print("Amortization schedule / EMI calculation:")
                print(summary)

            elif nums.get("prepayment_amount"):
                prepay_result = agent.simulate_prepayment(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"]),
                    prepayment_amount=nums["prepayment_amount"],
                    apply_month=nums.get("apply_month", 1)
                )
                print("Prepayment simulation result:")
                print(prepay_result)

            elif nums.get("new_tenure_months"):
                tenure_result = agent.simulate_tenure_change(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"]) if nums["tenure_months"] else None,
                    new_tenure_months=int(nums["new_tenure_months"])
                )
                print("Tenure change simulation result:")
                print(tenure_result)

            elif nums.get("new_rate"):
                rate_result = agent.simulate_rate_change(
                    loan_amount=nums["loan_amount"],
                    annual_rate=nums["annual_rate"],
                    tenure_months=int(nums["tenure_months"]),
                    new_rate=nums["new_rate"]
                )
                print("Interest rate change simulation result:")
                print(rate_result)

            else:
                print("LLM did not extract enough numbers:", nums)

        except Exception as e:
            print("Error during calculation:", e)
