import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.error_codes import APIException, ErrorCode
from app.core.rate_limit import products_limiter
from app.domain.catalogue.service import CatalogueService
from app.schemas.schemas import (
    PaginationSchema,
    ProductSchema,
    ProductsResponseSchema,
)

router = APIRouter(prefix="/marketplace/products", tags=["Products"])


@router.get("", response_model=ProductsResponseSchema)
async def list_products(
    request: Request,
    category: Optional[str] = Query(None, max_length=100),
    search: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await products_limiter.check(request, "list_products")
    service = CatalogueService(db)
    products, total = await service.list_products(
        category_id=category,
        search=search,
        page=page,
        limit=limit,
    )
    has_next = (page * limit) < total

    return ProductsResponseSchema(
        data=[ProductSchema.model_validate(p) for p in products],
        pagination=PaginationSchema(
            page=page,
            limit=limit,
            total=total,
            has_next_page=has_next,
        ),
    )


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(
    product_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await products_limiter.check(request, "get_product")
    service = CatalogueService(db)
    product = await service.get_product(product_id)
    if not product:
        raise APIException(
            ErrorCode.PRODUCT_NOT_FOUND,
            f"Product '{product_id}' not found",
            status_code=404,
        )
    return ProductSchema.model_validate(product)
