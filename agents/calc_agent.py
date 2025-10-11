# agents/calc_agent.py

import math
from typing import Dict

# -----------------------------
# WhatIfCalculatorAgent Class
# -----------------------------
class WhatIfCalculatorAgent:
    """
    Performs financial simulations:
    - EMI calculation
    - Prepayment simulation
    - Top-up eligibility checks
    """

    def __init__(self):
        pass  # Stateless agent, no DB needed

    # -----------------------------
    # EMI Calculation
    # -----------------------------
    @staticmethod
    def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
        """
        Calculate EMI using formula:
        EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        """
        if principal <= 0 or tenure_months <= 0 or annual_rate < 0:
            raise ValueError("Invalid input for EMI calculation")

        monthly_rate = annual_rate / (12 * 100)
        emi = principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months) / \
              (math.pow(1 + monthly_rate, tenure_months) - 1)
        return round(emi, 2)

    # -----------------------------
    # Prepayment Simulation
    # -----------------------------
    @staticmethod
    def simulate_prepayment(principal: float, annual_rate: float, tenure_months: int,
                            months_paid: int, prepayment_amount: float) -> Dict:
        """
        Simulate prepayment scenario:
        - Calculate remaining EMI
        - Reduce principal by prepayment amount
        - Compute new EMI if tenure unchanged
        """
        if prepayment_amount > principal:
            return {"error": "Prepayment exceeds remaining principal."}

        # Calculate original EMI
        emi = WhatIfCalculatorAgent.calculate_emi(principal, annual_rate, tenure_months)

        # Remaining principal after months_paid
        monthly_rate = annual_rate / (12 * 100)
        remaining_principal = principal * math.pow(1 + monthly_rate, tenure_months) - emi * \
                              (math.pow(1 + monthly_rate, months_paid) - 1) / monthly_rate

        # Apply prepayment
        new_principal = remaining_principal - prepayment_amount
        remaining_months = tenure_months - months_paid
        if remaining_months <= 0:
            remaining_months = 1  # Avoid division by zero

        new_emi = WhatIfCalculatorAgent.calculate_emi(new_principal, annual_rate, remaining_months)

        return {
            "original_emi": emi,
            "remaining_principal": round(new_principal, 2),
            "new_emi": new_emi,
            "remaining_months": remaining_months
        }

    # -----------------------------
    # Top-up eligibility
    # -----------------------------
    @staticmethod
    def check_topup_eligibility(topup_eligible: bool, outstanding_principal: float,
                                min_amount: float = 1000) -> Dict:
        """
        Returns eligibility status and max allowable top-up
        """
        if not topup_eligible:
            return {"eligible": False, "reason": "Customer not eligible for top-up."}

        max_topup = max(outstanding_principal * 0.5, min_amount)  # example rule: 50% of remaining principal
        return {"eligible": True, "max_topup": round(max_topup, 2)}


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    agent = WhatIfCalculatorAgent()

    # Example EMI calculation
    emi = agent.calculate_emi(principal=50000, annual_rate=12, tenure_months=24)
    print("EMI:", emi)

    # Example prepayment simulation
    result = agent.simulate_prepayment(principal=50000, annual_rate=12,
                                       tenure_months=24, months_paid=6,
                                       prepayment_amount=10000)
    print("Prepayment simulation:", result)

    # Example top-up eligibility
    topup = agent.check_topup_eligibility(topup_eligible=True, outstanding_principal=30000)
    print("Top-up eligibility:", topup)
