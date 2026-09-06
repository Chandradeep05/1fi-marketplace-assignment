from decimal import Decimal, ROUND_HALF_UP
import math
from typing import List, Optional

from app.domain.emi_engine.models import (
    EmiPlanRule,
    ComputedEmiPlan,
    PlanSetResult,
    EmptyReason,
)


class EmiCalculator:
    """
    Pure, stateless EMI calculation engine.
    Rounding policy (Invariant 6):
      monthly_emi_paisa = floor(total_payable_paisa / tenure_months)
      final_emi_paisa   = total_payable_paisa - (monthly_emi_paisa * (tenure_months - 1))
    Reconciliation guarantee:
      monthly_emi_paisa * (tenure_months - 1) + final_emi_paisa == total_payable_paisa
    """

    def compute_plans(
        self,
        principal_paisa: int,
        rules: List[EmiPlanRule],
        cashback_paisa: int = 0,
        available_limit_paisa: Optional[int] = None,
    ) -> PlanSetResult:
        # Domain guards
        if principal_paisa <= 0:
            raise ValueError(f"principal_paisa must be > 0, got {principal_paisa}")
        if cashback_paisa < 0:
            raise ValueError(f"cashback_paisa must be >= 0, got {cashback_paisa}")
        if cashback_paisa >= principal_paisa:
            raise ValueError(
                f"cashback_paisa ({cashback_paisa}) must be < principal_paisa ({principal_paisa}). "
                "Financing principal cannot be zero or negative."
            )
        for r in rules:
            if r.tenure_months <= 0:
                raise ValueError(f"tenure_months must be > 0, got {r.tenure_months}")
            if r.interest_rate_bps < 0:
                raise ValueError(f"interest_rate_bps must be >= 0, got {r.interest_rate_bps}")
            if r.min_amount_paisa < 0:
                raise ValueError("min_amount_paisa must be >= 0")
            if r.max_amount_paisa is not None and r.max_amount_paisa < r.min_amount_paisa:
                raise ValueError("max_amount_paisa must be >= min_amount_paisa")

        # ADR-003: cashback reduces the financed principal
        financing_principal = principal_paisa - cashback_paisa

        # Step 1: filter rules matching amount range
        eligible_rules = [
            r for r in rules
            if r.min_amount_paisa <= financing_principal
            and (r.max_amount_paisa is None or financing_principal <= r.max_amount_paisa)
        ]

        if not eligible_rules:
            return PlanSetResult(plans=[], empty_reason=EmptyReason.NO_ELIGIBLE_RULES)

        # Step 2: compute single plans
        plans = [self._compute_single(financing_principal, rule) for rule in eligible_rules]

        # Step 3: apply eligibility cap on total_payable_paisa (ADR-009)
        if available_limit_paisa is not None:
            plans = [p for p in plans if p.total_payable_paisa <= available_limit_paisa]

        if not plans:
            return PlanSetResult(plans=[], empty_reason=EmptyReason.INSUFFICIENT_LIMIT)

        # Step 4: mark recommended (ADR-002: longest no-cost, else shortest tenure)
        no_cost = [p for p in plans if p.is_no_cost]
        if no_cost:
            rec_id = max(no_cost, key=lambda p: p.tenure_months).plan_id
        else:
            rec_id = min(plans, key=lambda p: p.tenure_months).plan_id

        final_plans = [
            ComputedEmiPlan(
                plan_id=p.plan_id,
                tenure_months=p.tenure_months,
                monthly_emi_paisa=p.monthly_emi_paisa,
                final_emi_paisa=p.final_emi_paisa,
                interest_rate_bps=p.interest_rate_bps,
                total_payable_paisa=p.total_payable_paisa,
                is_no_cost=p.is_no_cost,
                recommended=(p.plan_id == rec_id),
            )
            for p in plans
        ]

        return PlanSetResult(plans=final_plans, empty_reason=None)

    def _compute_single(self, principal_paisa: int, rule: EmiPlanRule) -> ComputedEmiPlan:
        n = rule.tenure_months

        if rule.interest_rate_bps == 0:
            total_payable = principal_paisa
        else:
            # Reducing-balance formula: r = bps / 120,000
            r = Decimal(rule.interest_rate_bps) / Decimal(120_000)
            factor = (1 + r) ** n
            emi_exact = Decimal(principal_paisa) * r * factor / (factor - 1)
            monthly_emi_exact = int(emi_exact.to_integral_value(ROUND_HALF_UP))
            total_payable = monthly_emi_exact * n

        monthly_emi = math.floor(total_payable / n)
        final_emi = total_payable - monthly_emi * (n - 1)

        # Invariant assertion
        assert monthly_emi * (n - 1) + final_emi == total_payable, (
            f"Rounding invariant violated: {monthly_emi}*{n-1} + {final_emi} != {total_payable}"
        )

        return ComputedEmiPlan(
            plan_id=f"{n}m",
            tenure_months=n,
            monthly_emi_paisa=monthly_emi,
            final_emi_paisa=final_emi,
            interest_rate_bps=rule.interest_rate_bps,
            total_payable_paisa=total_payable,
            is_no_cost=(rule.interest_rate_bps == 0),
            recommended=False,
        )
