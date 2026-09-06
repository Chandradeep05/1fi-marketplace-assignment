import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import uuid
from app.core.ulid_utils import generate_ulid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import APIException, ErrorCode
from app.core.redis import get_redis
from app.domain.catalogue.repository import CatalogueRepository
from app.domain.eligibility.provider import CustomerContext, get_eligibility_provider
from app.domain.emi_engine.calculator import EmiCalculator
from app.domain.emi_engine.models import EmptyReason
from app.domain.emi_engine.rule_resolver import resolve_rules_for_product
from app.domain.quote.repository import QuoteRepository
from app.models.models import Quote

logger = logging.getLogger(__name__)


class QuoteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.catalogue_repo = CatalogueRepository(db)
        self.quote_repo = QuoteRepository(db)
        self.emi_calculator = EmiCalculator()
        self.eligibility_provider = get_eligibility_provider()

    async def create_quote(self, product_id: str, variant_id: uuid.UUID) -> Quote:
        # Step 1: Validate product
        product = await self.catalogue_repo.get_product_by_id(product_id)
        if not product or not product.is_available:
            raise APIException(ErrorCode.PRODUCT_NOT_FOUND, f"Product '{product_id}' not found or unavailable")

        # Step 2: Validate variant
        variant = await self.catalogue_repo.get_variant_by_id(variant_id)
        if not variant or variant.product_id != product.id:
            raise APIException(ErrorCode.VARIANT_NOT_FOUND, f"Variant '{variant_id}' not found for product")

        # Step 3: Check variant availability and price integrity
        if not variant.available:
            raise APIException(ErrorCode.VARIANT_UNAVAILABLE, "Selected variant is currently out of stock")
        if variant.price_paisa <= 0:
            raise APIException(ErrorCode.VALIDATION_ERROR, "Product variant price must be greater than zero")

        # Step 4: Resolve commercial rules (offers/cashback)
        offer = await self.quote_repo.get_best_offer(product.id, product.category_id)
        cashback_paisa = offer.cashback_paisa if offer else 0
        if cashback_paisa >= variant.price_paisa:
            logger.error(
                "Offer cashback equals or exceeds variant price — data integrity violation: "
                "offer_id=%s product_id=%s variant_id=%s cashback_paisa=%d price_paisa=%d",
                offer.id if offer else None,
                product.id,
                variant.id,
                cashback_paisa,
                variant.price_paisa,
            )
            raise APIException(
                ErrorCode.INTERNAL_ERROR,
                "An internal pricing configuration error occurred. Please contact support.",
                status_code=500,
            )

        # Step 5: Resolve eligibility
        ctx = CustomerContext(customer_id="demo_user")
        try:
            limit = await self.eligibility_provider.get_available_limit(ctx)
            available_limit_paisa = limit.available_paisa
        except Exception:
            raise APIException(ErrorCode.ELIGIBILITY_UNAVAILABLE, "Unable to verify eligibility limit")

        # Step 6: Resolve scoped EMI rules (ADR-007)
        rules = await resolve_rules_for_product(
            self.db,
            product_id=product.id,
            brand_id=product.brand_id,
            category_id=product.category_id,
        )

        # Step 7: Compute EMI plans
        try:
            result = self.emi_calculator.compute_plans(
                principal_paisa=variant.price_paisa,
                rules=rules,
                cashback_paisa=cashback_paisa,
                available_limit_paisa=available_limit_paisa,
            )
        except ValueError as val_err:
            raise APIException(ErrorCode.VALIDATION_ERROR, str(val_err))

        if result.empty_reason == EmptyReason.INSUFFICIENT_LIMIT:
            raise APIException(
                ErrorCode.INSUFFICIENT_LIMIT,
                "Purchase exceeds available credit limit. No eligible EMI plans.",
                status_code=422,
            )
        elif result.empty_reason == EmptyReason.NO_ELIGIBLE_RULES:
            raise APIException(
                ErrorCode.NO_ELIGIBLE_RULES,
                "No eligible EMI rules are configured for this product and price band.",
                status_code=422,
            )

        plans_dicts = [
            {
                "plan_id": p.plan_id,
                "tenure_months": p.tenure_months,
                "monthly_emi_paisa": p.monthly_emi_paisa,
                "final_emi_paisa": p.final_emi_paisa,
                "interest_rate_bps": p.interest_rate_bps,
                "total_payable_paisa": p.total_payable_paisa,
                "is_no_cost": p.is_no_cost,
                "recommended": p.recommended,
            }
            for p in result.plans
        ]

        # Step 8: Freeze immutable quote (10 minute validity)
        quote_id = f"qt_{generate_ulid()}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=600)

        quote = Quote(
            id=quote_id,
            product_id=product.id,
            variant_id=variant.id,
            price_paisa=variant.price_paisa,
            cashback_paisa=cashback_paisa,
            plans_json=plans_dicts,
            created_at=now,
            expires_at=expires_at,
        )

        saved_quote = await self.quote_repo.save_quote(quote)

        # Step 9: Set Redis cache index (optimization, ADR-001)
        try:
            r = await get_redis()
            await r.set(f"quote:{quote_id}", "active", ex=600)
        except Exception as exc:
            logger.warning("Redis cache operation failed; continuing with database authority: %s", exc)

        return saved_quote
