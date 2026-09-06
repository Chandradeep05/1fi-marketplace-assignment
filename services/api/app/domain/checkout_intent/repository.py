from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CheckoutIntent, Quote, ProductVariant


class CheckoutIntentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[CheckoutIntent]:
        stmt = select(CheckoutIntent).where(CheckoutIntent.idempotency_key == idempotency_key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quote_for_validation(self, quote_id: str, lock: bool = False) -> Optional[Quote]:
        stmt = select(Quote).where(Quote.id == quote_id)
        if lock:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_variant_availability(self, variant_id, lock: bool = False) -> Optional[bool]:
        stmt = select(ProductVariant.available).where(ProductVariant.id == variant_id)
        if lock:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_intent(self, intent: CheckoutIntent) -> CheckoutIntent:
        self.db.add(intent)
        await self.db.flush()
        return intent
