import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from app.core.ulid_utils import generate_ulid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import APIException, ErrorCode
from app.core.redis import get_redis
from app.domain.checkout_intent.repository import CheckoutIntentRepository
from app.models.models import CheckoutIntent


class CheckoutIntentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CheckoutIntentRepository(db)

    async def create_intent(
        self,
        quote_id: str,
        plan_id: str,
        idempotency_key: str,
    ) -> Tuple[Dict[str, Any], int]:
        # Pre-flight
        if not idempotency_key or not idempotency_key.strip():
            raise APIException(
                ErrorCode.MISSING_IDEMPOTENCY_KEY,
                "Idempotency-Key header is required",
                status_code=400,
            )

        payload_to_hash = {"quote_id": quote_id, "plan_id": plan_id}
        request_hash = hashlib.sha256(
            json.dumps(payload_to_hash, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # Step 1: Redis fast-path check
        try:
            r = await get_redis()
            cached = await r.hgetall(f"idempotency:{idempotency_key}")
            if cached:
                cached_hash = cached.get("hash")
                cached_resp_raw = cached.get("response")
                if cached_hash != request_hash:
                    raise APIException(
                        ErrorCode.IDEMPOTENCY_CONFLICT,
                        "Idempotency key has already been used with a different request payload",
                        status_code=409,
                    )
                if cached_resp_raw:
                    return json.loads(cached_resp_raw), 200
        except APIException:
            raise
        except Exception:
            pass

        # Step 2: Postgres check existing row
        existing = await self.repo.get_by_idempotency_key(idempotency_key)
        if existing:
            if existing.request_hash != request_hash:
                raise APIException(
                    ErrorCode.IDEMPOTENCY_CONFLICT,
                    "Idempotency key has already been used with a different request payload",
                    status_code=409,
                )
            return existing.response_json, 200

        # Step 3: Validate quote (authoritative in Postgres, ADR-001)
        quote = await self.repo.get_quote_for_validation(quote_id)
        if not quote:
            raise APIException(
                ErrorCode.QUOTE_NOT_FOUND,
                f"Quote '{quote_id}' does not exist",
                status_code=404,
            )

        now = datetime.now(timezone.utc)
        # Handle offset-naive or offset-aware datetime from DB
        quote_expires = quote.expires_at
        if quote_expires.tzinfo is None:
            quote_expires = quote_expires.replace(tzinfo=timezone.utc)

        if quote_expires <= now:
            raise APIException(
                ErrorCode.QUOTE_EXPIRED,
                "This quote has expired. Please refresh your quote to proceed.",
                status_code=400,
            )

        # Validate plan belongs to quote (Invariant 3)
        raw_plans = quote.plans_json
        if isinstance(raw_plans, str):
            try:
                raw_plans = json.loads(raw_plans)
            except Exception:
                raw_plans = []
        valid_plans = raw_plans if isinstance(raw_plans, list) else []
        plan_ids = [p.get("plan_id") for p in valid_plans if isinstance(p, dict)]
        if plan_id not in plan_ids:
            raise APIException(
                ErrorCode.PLAN_NOT_IN_QUOTE,
                f"Plan '{plan_id}' does not belong to quote '{quote_id}'",
                status_code=400,
            )

        # Step 4: Re-validate variant availability (Invariant 9, ADR-008)
        available = await self.repo.get_variant_availability(quote.variant_id)
        if not available:
            raise APIException(
                ErrorCode.VARIANT_UNAVAILABLE,
                "The selected product variant is currently unavailable",
                status_code=409,
            )

        # Step 5: Construct response and insert
        intent_id = f"ci_{generate_ulid()}"
        response_payload = {
            "intent_id": intent_id,
            "status": "received",
            "quote_id": quote.id,
            "plan_id": plan_id,
        }

        intent = CheckoutIntent(
            id=intent_id,
            quote_id=quote.id,
            plan_id=plan_id,
            status="received",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_json=response_payload,
            created_at=now,
        )

        try:
            await self.repo.save_intent(intent)
            status_code = 201
            final_response = response_payload
        except IntegrityError:
            await self.db.rollback()
            # Concurrent winner inserted with same idempotency key
            concurrent_intent = await self.repo.get_by_idempotency_key(idempotency_key)
            if not concurrent_intent or concurrent_intent.request_hash != request_hash:
                raise APIException(
                    ErrorCode.IDEMPOTENCY_CONFLICT,
                    "Idempotency key conflict under concurrent submission",
                    status_code=409,
                )
            final_response = concurrent_intent.response_json
            status_code = 200

        # Step 6: Warm Redis cache
        try:
            r = await get_redis()
            pipe = r.pipeline()
            cache_key = f"idempotency:{idempotency_key}"
            pipe.hset(cache_key, mapping={"hash": request_hash, "response": json.dumps(final_response)})
            pipe.expire(cache_key, 86400)
            await pipe.execute()
        except Exception:
            pass

        return final_response, status_code
