import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True)  # slug
    name = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    products = relationship("Product", back_populates="category")


class Brand(Base):
    __tablename__ = "brands"

    id = Column(String, primary_key=True)  # slug
    name = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)

    products = relationship("Product", back_populates="brand")


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)  # slug
    name = Column(String, nullable=False)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    description = Column(Text, default="", nullable=False)
    base_price_paisa = Column(Integer, nullable=False)
    mrp_paisa = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    is_test_fixture = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    brand = relationship("Brand", back_populates="products")
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("base_price_paisa > 0", name="chk_product_base_price_positive"),
        CheckConstraint("mrp_paisa IS NULL OR mrp_paisa >= base_price_paisa", name="chk_product_mrp_gte_base"),
        Index("idx_products_category", "category_id"),
        Index("idx_products_brand", "brand_id"),
        Index("idx_products_created_id", "created_at", "id"),
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    product = relationship("Product", back_populates="images")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    attributes = Column(JSON_TYPE, nullable=False)  # {"color": "Black", "storage": "256GB"}
    price_paisa = Column(Integer, nullable=False)
    available = Column(Boolean, default=True, nullable=False)
    image_url = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="variants")

    __table_args__ = (
        CheckConstraint("price_paisa > 0", name="chk_variant_price_positive"),
        Index("idx_variants_product", "product_id"),
    )


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    cashback_paisa = Column(Integer, default=0, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("cashback_paisa >= 0", name="chk_offer_cashback_non_negative"),
        CheckConstraint(
            """
            (product_id IS NOT NULL AND category_id IS NULL) OR
            (product_id IS NULL AND category_id IS NOT NULL) OR
            (product_id IS NULL AND category_id IS NULL)
            """,
            name="chk_offer_scope",
        ),
    )


class EmiPlanRule(Base):
    __tablename__ = "emi_plan_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenure_months = Column(Integer, nullable=False)
    interest_rate_bps = Column(Integer, default=0, nullable=False)
    min_amount_paisa = Column(Integer, nullable=False)
    max_amount_paisa = Column(Integer, nullable=True)
    is_no_cost = Column(Boolean, default=False, nullable=False)

    # Scopes: product > brand > category > global (all NULL)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    brand_id = Column(String, ForeignKey("brands.id"), nullable=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            """
            (product_id IS NOT NULL AND brand_id IS NULL AND category_id IS NULL) OR
            (product_id IS NULL AND brand_id IS NOT NULL AND category_id IS NULL) OR
            (product_id IS NULL AND brand_id IS NULL AND category_id IS NOT NULL) OR
            (product_id IS NULL AND brand_id IS NULL AND category_id IS NULL)
            """,
            name="chk_single_scope"
        ),
        CheckConstraint("tenure_months > 0", name="chk_emi_rule_tenure_positive"),
        CheckConstraint("interest_rate_bps >= 0", name="chk_emi_rule_interest_non_negative"),
        CheckConstraint("min_amount_paisa >= 0", name="chk_emi_rule_min_amount_non_negative"),
        CheckConstraint("max_amount_paisa IS NULL OR max_amount_paisa >= min_amount_paisa", name="chk_emi_rule_max_gte_min"),
        CheckConstraint(
            "(interest_rate_bps = 0 AND is_no_cost = TRUE) OR (interest_rate_bps > 0 AND is_no_cost = FALSE)",
            name="chk_emi_rule_no_cost_consistency",
        ),
        Index("idx_emi_rules_scope", "product_id", "brand_id", "category_id"),
    )

    @property
    def is_no_cost_derived(self) -> bool:
        return self.interest_rate_bps == 0


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(String, primary_key=True)  # qt_ + ULID
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False)
    price_paisa = Column(Integer, nullable=False)
    cashback_paisa = Column(Integer, default=0, nullable=False)
    plans_json = Column(JSON_TYPE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("price_paisa > 0", name="chk_quote_price_positive"),
        CheckConstraint("cashback_paisa >= 0 AND cashback_paisa < price_paisa", name="chk_quote_cashback_valid"),
        Index("idx_quotes_expires_at", "expires_at"),
    )


class CheckoutIntent(Base):
    __tablename__ = "checkout_intents"

    id = Column(String, primary_key=True)  # ci_ + ULID
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    plan_id = Column(String, nullable=False)
    status = Column(String, default="received", nullable=False)
    idempotency_key = Column(String, unique=True, nullable=False)
    request_hash = Column(String, nullable=False)
    response_json = Column(JSON_TYPE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('received', 'processing', 'completed', 'failed')",
            name="chk_checkout_intent_status"
        ),
        Index("idx_intents_quote", "quote_id"),
    )
