import pytest
from app.domain.emi_engine.calculator import EmiCalculator
from app.domain.emi_engine.models import EmiPlanRule, EmptyReason


@pytest.fixture
def calculator() -> EmiCalculator:
    return EmiCalculator()


def test_no_cost_even_division(calculator: EmiCalculator):
    # Principal: 1,26,90,000 paisa (₹1,26,900) over 36 months no-cost
    rules = [
        EmiPlanRule(tenure_months=36, interest_rate_bps=0, min_amount_paisa=500000)
    ]
    result = calculator.compute_plans(
        principal_paisa=13490000,
        rules=rules,
        cashback_paisa=800000,
    )
    assert result.empty_reason is None
    assert len(result.plans) == 1
    plan = result.plans[0]
    assert plan.plan_id == "36m"
    assert plan.tenure_months == 36
    assert plan.monthly_emi_paisa == 352500
    assert plan.final_emi_paisa == 352500
    assert plan.total_payable_paisa == 12690000
    assert plan.is_no_cost is True
    assert plan.recommended is True
    # Invariant: reconciliation exact
    assert plan.monthly_emi_paisa * 35 + plan.final_emi_paisa == plan.total_payable_paisa


def test_no_cost_uneven_division_remainder_absorption(calculator: EmiCalculator):
    # Principal: ₹9,991 (999100 paisa) over 7 months no-cost
    # 999100 / 7 = 142728.5714...
    # monthly_emi = floor(999100 / 7) = 142728
    # final_emi   = 999100 - (142728 * 6) = 999100 - 856368 = 142732
    rules = [
        EmiPlanRule(tenure_months=7, interest_rate_bps=0, min_amount_paisa=100000)
    ]
    result = calculator.compute_plans(
        principal_paisa=999100,
        rules=rules,
        cashback_paisa=0,
    )
    assert result.empty_reason is None
    assert len(result.plans) == 1
    plan = result.plans[0]
    assert plan.plan_id == "7m"
    assert plan.monthly_emi_paisa == 142728
    assert plan.final_emi_paisa == 142732
    assert plan.total_payable_paisa == 999100
    assert plan.monthly_emi_paisa != plan.final_emi_paisa
    # Invariant: reconciliation exact
    assert plan.monthly_emi_paisa * 6 + plan.final_emi_paisa == plan.total_payable_paisa


def test_interest_bearing_reducing_balance(calculator: EmiCalculator):
    # Principal: 1,26,90,000 paisa, 60m at 850 bps (8.5% p.a.)
    rules = [
        EmiPlanRule(tenure_months=60, interest_rate_bps=850, min_amount_paisa=1000000)
    ]
    result = calculator.compute_plans(
        principal_paisa=13490000,
        rules=rules,
        cashback_paisa=800000,
    )
    assert result.empty_reason is None
    assert len(result.plans) == 1
    plan = result.plans[0]
    assert plan.plan_id == "60m"
    assert plan.tenure_months == 60
    assert plan.monthly_emi_paisa == 260355
    assert plan.final_emi_paisa == 260355
    assert plan.total_payable_paisa == 15621300
    assert plan.is_no_cost is False
    assert plan.monthly_emi_paisa * 59 + plan.final_emi_paisa == plan.total_payable_paisa


def test_recommended_selection_longest_no_cost(calculator: EmiCalculator):
    rules = [
        EmiPlanRule(tenure_months=12, interest_rate_bps=0, min_amount_paisa=100000),
        EmiPlanRule(tenure_months=24, interest_rate_bps=0, min_amount_paisa=100000),
        EmiPlanRule(tenure_months=36, interest_rate_bps=0, min_amount_paisa=100000),
        EmiPlanRule(tenure_months=60, interest_rate_bps=850, min_amount_paisa=100000),
    ]
    result = calculator.compute_plans(
        principal_paisa=5000000,
        rules=rules,
        cashback_paisa=0,
    )
    assert result.empty_reason is None
    rec_plans = [p for p in result.plans if p.recommended]
    assert len(rec_plans) == 1
    assert rec_plans[0].plan_id == "36m"


def test_eligibility_cap_filters_plans(calculator: EmiCalculator):
    rules = [
        EmiPlanRule(tenure_months=12, interest_rate_bps=0, min_amount_paisa=100000),
        EmiPlanRule(tenure_months=60, interest_rate_bps=850, min_amount_paisa=100000),
    ]
    # Principal 1,00,000. 12m total: 1,00,000. 60m total: ~1,23,000.
    # Limit: 1,10,000. Only 12m should qualify.
    result = calculator.compute_plans(
        principal_paisa=10000000,
        rules=rules,
        cashback_paisa=0,
        available_limit_paisa=11000000,
    )
    assert result.empty_reason is None
    assert len(result.plans) == 1
    assert result.plans[0].plan_id == "12m"


def test_empty_reason_no_eligible_rules(calculator: EmiCalculator):
    rules = [
        EmiPlanRule(tenure_months=12, interest_rate_bps=0, min_amount_paisa=5000000, max_amount_paisa=10000000)
    ]
    # Principal 1,000 is lower than min_amount_paisa
    result = calculator.compute_plans(
        principal_paisa=100000,
        rules=rules,
        cashback_paisa=0,
    )
    assert len(result.plans) == 0
    assert result.empty_reason == EmptyReason.NO_ELIGIBLE_RULES


def test_empty_reason_insufficient_limit(calculator: EmiCalculator):
    rules = [
        EmiPlanRule(tenure_months=12, interest_rate_bps=0, min_amount_paisa=100000)
    ]
    # Limit 50,000, principal 1,00,000
    result = calculator.compute_plans(
        principal_paisa=10000000,
        rules=rules,
        cashback_paisa=0,
        available_limit_paisa=5000000,
    )
    assert len(result.plans) == 0
    assert result.empty_reason == EmptyReason.INSUFFICIENT_LIMIT


def test_domain_guard_cashback_exceeds_principal(calculator: EmiCalculator):
    rules = [EmiPlanRule(tenure_months=12, interest_rate_bps=0, min_amount_paisa=100000)]
    with pytest.raises(ValueError, match="cashback_paisa.*must be < principal_paisa"):
        calculator.compute_plans(
            principal_paisa=100000,
            rules=rules,
            cashback_paisa=150000,
        )


def test_domain_guard_negative_principal(calculator: EmiCalculator):
    rules = [EmiPlanRule(tenure_months=12, interest_rate_bps=0, min_amount_paisa=100000)]
    with pytest.raises(ValueError, match="principal_paisa must be > 0"):
        calculator.compute_plans(principal_paisa=-10, rules=rules)
