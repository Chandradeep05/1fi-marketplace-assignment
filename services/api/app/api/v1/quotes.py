from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import quotes_limiter
from app.domain.quote.service import QuoteService
from app.schemas.schemas import QuoteRequestSchema, QuoteResponseSchema, EmiPlanSchema

router = APIRouter(prefix="/marketplace/quotes", tags=["Quotes"])


@router.post("", response_model=QuoteResponseSchema)
async def create_quote(
    payload: QuoteRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await quotes_limiter.check(request, "create_quote")
    service = QuoteService(db)
    quote = await service.create_quote(
        product_id=payload.product_id,
        variant_id=payload.variant_id,
    )
    financing_principal = quote.price_paisa - quote.cashback_paisa

    raw_plans = quote.plans_json
    if isinstance(raw_plans, str):
        import json
        try:
            raw_plans = json.loads(raw_plans)
        except Exception:
            raw_plans = []
    plans = [EmiPlanSchema.model_validate(p) for p in (raw_plans if isinstance(raw_plans, list) else [])]

    return QuoteResponseSchema(
        quote_id=quote.id,
        product_price_paisa=quote.price_paisa,
        cashback_paisa=quote.cashback_paisa,
        financing_principal_paisa=financing_principal,
        expires_at=quote.expires_at,
        plans=plans,
    )
