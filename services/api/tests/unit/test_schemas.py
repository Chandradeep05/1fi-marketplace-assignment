import pytest
from pydantic import ValidationError
from app.schemas.schemas import (
    QuoteRequestSchema,
    CheckoutIntentRequestSchema,
    EmiPlanSchema,
)


def test_quote_request_validation():
    # Valid
    req = QuoteRequestSchema(
        product_id="iphone-17-pro",
        variant_id="a0000000-0000-0000-0000-000000000001",
    )
    assert req.product_id == "iphone-17-pro"

    # Invalid UUID
    with pytest.raises(ValidationError):
        QuoteRequestSchema(
            product_id="iphone-17-pro",
            variant_id="not-a-uuid",
        )


def test_checkout_intent_request_validation():
    req = CheckoutIntentRequestSchema(
        quote_id="qt_01JXYZ",
        plan_id="36m",
    )
    assert req.quote_id == "qt_01JXYZ"
    assert req.plan_id == "36m"


def test_emi_plan_schema_paisa_fields():
    plan = EmiPlanSchema(
        plan_id="36m",
        tenure_months=36,
        monthly_emi_paisa=352500,
        final_emi_paisa=352500,
        interest_rate_bps=0,
        total_payable_paisa=12690000,
        is_no_cost=True,
        recommended=True,
    )
    assert plan.monthly_emi_paisa == 352500
    assert plan.total_payable_paisa == 12690000
    # Invariant 6: integer paisa
    assert isinstance(plan.monthly_emi_paisa, int)
