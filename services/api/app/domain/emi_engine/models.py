from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


@dataclass(frozen=True)
class EmiPlanRule:
    tenure_months: int
    interest_rate_bps: int
    min_amount_paisa: int
    max_amount_paisa: Optional[int] = None


class EmptyReason(str, Enum):
    NO_ELIGIBLE_RULES = "no_eligible_rules"
    INSUFFICIENT_LIMIT = "insufficient_limit"


@dataclass(frozen=True)
class ComputedEmiPlan:
    plan_id: str
    tenure_months: int
    monthly_emi_paisa: int
    final_emi_paisa: int
    interest_rate_bps: int
    total_payable_paisa: int
    is_no_cost: bool
    recommended: bool


@dataclass(frozen=True)
class PlanSetResult:
    plans: List[ComputedEmiPlan]
    empty_reason: Optional[EmptyReason] = None
