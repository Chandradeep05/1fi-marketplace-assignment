from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class CategorySchema(BaseModel):
    id: str
    name: str
    icon: str
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class BrandSchema(BaseModel):
    id: str
    name: str
    logo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductImageSchema(BaseModel):
    id: uuid.UUID
    url: str
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProductVariantSchema(BaseModel):
    id: uuid.UUID
    attributes: Dict[str, Any]
    price_paisa: int
    available: bool = True
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductSchema(BaseModel):
    id: str
    name: str
    brand: BrandSchema
    category_id: str
    description: str
    base_price_paisa: int
    mrp_paisa: Optional[int] = None
    is_available: bool = True
    images: List[ProductImageSchema] = []
    variants: List[ProductVariantSchema] = []

    model_config = ConfigDict(from_attributes=True)


class PaginationSchema(BaseModel):
    page: int
    limit: int
    total: int
    has_next_page: bool


class ProductsResponseSchema(BaseModel):
    data: List[ProductSchema]
    pagination: PaginationSchema


class CategoriesResponseSchema(BaseModel):
    data: List[CategorySchema]


class EligibilityDataSchema(BaseModel):
    total_limit_paisa: int
    used_paisa: int
    available_paisa: int


class EligibilityResponseSchema(BaseModel):
    data: EligibilityDataSchema


class QuoteRequestSchema(BaseModel):
    product_id: str = Field(..., max_length=100)
    variant_id: uuid.UUID


class EmiPlanSchema(BaseModel):
    plan_id: str
    tenure_months: int
    monthly_emi_paisa: int
    final_emi_paisa: int
    interest_rate_bps: int
    total_payable_paisa: int
    is_no_cost: bool
    recommended: bool


class QuoteResponseSchema(BaseModel):
    quote_id: str
    product_price_paisa: int
    cashback_paisa: int
    financing_principal_paisa: int
    expires_at: datetime
    plans: List[EmiPlanSchema]


class CheckoutIntentRequestSchema(BaseModel):
    quote_id: str = Field(..., max_length=100)
    plan_id: str = Field(..., max_length=50)


class CheckoutIntentResponseSchema(BaseModel):
    intent_id: str
    status: str
    quote_id: str
    plan_id: str
    request_id: Optional[str] = None
