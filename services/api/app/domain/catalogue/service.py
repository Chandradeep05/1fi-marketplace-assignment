from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.catalogue.repository import CatalogueRepository
from app.models.models import Category, Product


class CatalogueService:
    def __init__(self, db: AsyncSession):
        self.repo = CatalogueRepository(db)

    async def list_categories(self) -> List[Category]:
        return await self.repo.get_categories()

    async def list_products(
        self,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Product], int]:
        offset = (page - 1) * limit
        return await self.repo.get_products(
            category_id=category_id,
            search=search,
            limit=limit,
            offset=offset,
        )

    async def get_product(self, product_id: str) -> Optional[Product]:
        return await self.repo.get_product_by_id(product_id)
