from typing import List, Optional, Tuple
import uuid
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Category, Product, ProductVariant


class CatalogueRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_categories(self) -> List[Category]:
        stmt = select(Category).order_by(Category.sort_order.asc(), Category.name.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_products(
        self,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Product], int]:
        conditions = [
            Product.is_available.is_(True),
            Product.is_test_fixture.is_(False),
        ]

        if category_id:
            conditions.append(Product.category_id == category_id)

        if search and search.strip():
            raw_search = search.strip()
            # Escape literal wildcards in order: \ first, then %, then _
            escaped_search = (
                raw_search.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            conditions.append(Product.name.ilike(f"%{escaped_search}%", escape="\\"))

        # Count total
        count_stmt = select(func.count(Product.id)).where(and_(*conditions))
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        # Query items with stable tiebreaker sort: created_at DESC, id ASC (Review v1 fix)
        stmt = (
            select(Product)
            .where(and_(*conditions))
            .options(
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants),
            )
            .order_by(Product.created_at.desc(), Product.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_product_by_id(self, product_id: str, allow_test_fixture: bool = False) -> Optional[Product]:
        conditions = [Product.id == product_id]
        if not allow_test_fixture:
            conditions.append(Product.is_test_fixture.is_(False))

        stmt = (
            select(Product)
            .where(*conditions)
            .options(
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_variant_by_id(self, variant_id: uuid.UUID) -> Optional[ProductVariant]:
        stmt = select(ProductVariant).where(ProductVariant.id == variant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
