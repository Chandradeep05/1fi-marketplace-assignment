from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Quote, Offer


class QuoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_quote(self, quote: Quote) -> Quote:
        self.db.add(quote)
        await self.db.commit()
        await self.db.refresh(quote)
        return quote

    async def get_quote_by_id(self, quote_id: str) -> Optional[Quote]:
        stmt = select(Quote).where(Quote.id == quote_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_best_offer(self, product_id: str, category_id: str) -> Optional[Offer]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Offer)
            .where(
                and_(
                    Offer.valid_from <= now,
                    Offer.valid_to >= now,
                    or_(
                        Offer.product_id == product_id,
                        and_(Offer.category_id == category_id, Offer.product_id.is_(None)),
                        and_(Offer.product_id.is_(None), Offer.category_id.is_(None)),  # Global active tier
                    ),
                )
            )
            .order_by(
                # Precedence: product (0) > category (1) > global (2) (ADR-010)
                case(
                    (Offer.product_id == product_id, 0),
                    (and_(Offer.category_id == category_id, Offer.product_id.is_(None)), 1),
                    else_=2,
                ),
                Offer.cashback_paisa.desc(),
                Offer.valid_from.desc(),
                Offer.id.asc(),
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
