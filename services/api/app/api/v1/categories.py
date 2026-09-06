from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.catalogue.service import CatalogueService
from app.schemas.schemas import CategoriesResponseSchema, CategorySchema

router = APIRouter(prefix="/marketplace/categories", tags=["Categories"])


@router.get("", response_model=CategoriesResponseSchema)
async def get_categories(db: AsyncSession = Depends(get_db)):
    service = CatalogueService(db)
    categories = await service.list_categories()
    return CategoriesResponseSchema(
        data=[CategorySchema.model_validate(c) for c in categories]
    )
