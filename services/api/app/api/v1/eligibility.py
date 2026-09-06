from fastapi import APIRouter, Request
from app.core.rate_limit import eligibility_limiter
from app.domain.eligibility.provider import CustomerContext, get_eligibility_provider
from app.schemas.schemas import EligibilityDataSchema, EligibilityResponseSchema

router = APIRouter(prefix="/marketplace/eligibility", tags=["Eligibility"])


@router.get("", response_model=EligibilityResponseSchema)
async def get_eligibility(request: Request):
    await eligibility_limiter.check(request, "get_eligibility")
    provider = get_eligibility_provider()
    limit = await provider.get_available_limit(CustomerContext(customer_id="demo_user"))
    return EligibilityResponseSchema(
        data=EligibilityDataSchema(
            total_limit_paisa=limit.total_limit_paisa,
            used_paisa=limit.used_paisa,
            available_paisa=limit.available_paisa,
        )
    )
