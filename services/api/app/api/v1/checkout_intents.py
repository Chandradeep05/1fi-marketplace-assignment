from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.error_codes import APIException, ErrorCode
from app.core.rate_limit import checkout_limiter
from app.domain.checkout_intent.service import CheckoutIntentService
from app.schemas.schemas import (
    CheckoutIntentRequestSchema,
    CheckoutIntentResponseSchema,
)

router = APIRouter(prefix="/marketplace/checkout-intents", tags=["Checkout"])


@router.post("", response_model=CheckoutIntentResponseSchema)
async def create_checkout_intent(
    payload: CheckoutIntentRequestSchema,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not idempotency_key or not idempotency_key.strip():
        raise APIException(
            ErrorCode.MISSING_IDEMPOTENCY_KEY,
            "Idempotency-Key header is required",
            status_code=400,
        )

    await checkout_limiter.check(request, "create_checkout_intent")
    service = CheckoutIntentService(db)
    response_data, status_code = await service.create_intent(
        quote_id=payload.quote_id,
        plan_id=payload.plan_id,
        idempotency_key=idempotency_key.strip(),
    )

    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response_data["request_id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=response_data,
        headers={"X-Request-ID": request_id} if request_id else None,
    )
