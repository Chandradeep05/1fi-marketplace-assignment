import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.models import (
    Category,
    Brand,
    Product,
    ProductImage,
    ProductVariant,
    Offer,
    EmiPlanRule,
)

CATEGORIES = [
    {"id": "smartphones", "name": "Smartphones", "icon": "phone-portrait", "sort_order": 0},
    {"id": "laptops", "name": "Laptops", "icon": "laptop", "sort_order": 1},
    {"id": "audio", "name": "Audio", "icon": "headset", "sort_order": 2},
    {"id": "accessories", "name": "Accessories", "icon": "hardware-chip", "sort_order": 3},
]

BRANDS = [
    {"id": "apple", "name": "Apple", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"},
    {"id": "samsung", "name": "Samsung", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/2/24/Samsung_Logo.svg"},
    {"id": "sony", "name": "Sony", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/c/ca/Sony_logo.svg"},
    {"id": "generic", "name": "Generic", "logo_url": None},
]

PRODUCTS = [
    {
        "id": "iphone-17-pro",
        "name": "Apple iPhone 17 Pro",
        "brand_id": "apple",
        "category_id": "smartphones",
        "description": "The most powerful iPhone ever with A19 Pro chip, titanium design, and revolutionary camera system.",
        "base_price_paisa": 13490000,  # ₹1,34,900
        "mrp_paisa": 13990000,         # ₹1,39,900
        "is_available": True,
        "is_test_fixture": False,
    },
    {
        "id": "galaxy-s25-ultra",
        "name": "Samsung Galaxy S25 Ultra",
        "brand_id": "samsung",
        "category_id": "smartphones",
        "description": "Galaxy AI powered flagship with built-in S Pen, 200MP camera, and titanium frame.",
        "base_price_paisa": 12999900,  # ₹1,29,999
        "mrp_paisa": 13499900,         # ₹1,34,999
        "is_available": True,
        "is_test_fixture": False,
    },
    {
        "id": "macbook-pro-m4",
        "name": "Apple MacBook Pro 14\" M4",
        "brand_id": "apple",
        "category_id": "laptops",
        "description": "Pro power unleashed with Apple M4 chip, Liquid Retina XDR display, and 24-hour battery life.",
        "base_price_paisa": 16990000,  # ₹1,69,900
        "mrp_paisa": 17990000,         # ₹1,79,900
        "is_available": True,
        "is_test_fixture": False,
    },
    {
        "id": "sony-wh1000xm5",
        "name": "Sony WH-1000XM5 Wireless Headphones",
        "brand_id": "sony",
        "category_id": "audio",
        "description": "Industry-leading noise cancellation with two processors, 8 microphones, and ultra-comfortable design.",
        "base_price_paisa": 2999000,   # ₹29,990
        "mrp_paisa": 3499000,          # ₹34,990
        "is_available": True,
        "is_test_fixture": False,
    },
    {
        "id": "test-cable-7m",
        "name": "Test Cable (remainder test fixture)",
        "brand_id": "generic",
        "category_id": "accessories",
        "description": "Reference cable for testing exact remainder absorption math (₹9,991 over 7 months).",
        "base_price_paisa": 999100,    # ₹9,991
        "mrp_paisa": 1299100,          # ₹12,991 (satisfies mrp_paisa >= base_price_paisa)
        "is_available": True,
        "is_test_fixture": True,
    },
]

VARIANTS = [
    # iPhone 17 Pro
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000001"),
        "product_id": "iphone-17-pro",
        "attributes": {"Storage": "256GB", "Color": "Black Titanium"},
        "price_paisa": 13490000,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&q=80",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000002"),
        "product_id": "iphone-17-pro",
        "attributes": {"Storage": "512GB", "Color": "Natural Titanium"},
        "price_paisa": 15490000,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&q=80",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000003"),
        "product_id": "iphone-17-pro",
        "attributes": {"Storage": "1TB", "Color": "Desert Titanium"},
        "price_paisa": 17490000,
        "available": False,  # Out of stock for testing variant unavailable
        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80",
    },
    # Galaxy S25 Ultra
    {
        "id": uuid.UUID("b0000000-0000-0000-0000-000000000001"),
        "product_id": "galaxy-s25-ultra",
        "attributes": {"Storage": "256GB", "Color": "Titanium Black"},
        "price_paisa": 12999900,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800&q=80",
    },
    {
        "id": uuid.UUID("b0000000-0000-0000-0000-000000000002"),
        "product_id": "galaxy-s25-ultra",
        "attributes": {"Storage": "512GB", "Color": "Titanium Gray"},
        "price_paisa": 14499900,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800&q=80",
    },
    # MacBook Pro M4
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000001"),
        "product_id": "macbook-pro-m4",
        "attributes": {"Storage": "512GB SSD", "Memory": "16GB", "Color": "Space Black"},
        "price_paisa": 16990000,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80",
    },
    # Sony WH-1000XM5
    {
        "id": uuid.UUID("d0000000-0000-0000-0000-000000000001"),
        "product_id": "sony-wh1000xm5",
        "attributes": {"Color": "Black"},
        "price_paisa": 2999000,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80",
    },
    {
        "id": uuid.UUID("d0000000-0000-0000-0000-000000000002"),
        "product_id": "sony-wh1000xm5",
        "attributes": {"Color": "Silver"},
        "price_paisa": 2999000,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800&q=80",
    },
    # Test Cable
    {
        "id": uuid.UUID("e0000000-0000-0000-0000-000000000001"),
        "product_id": "test-cable-7m",
        "attributes": {"Length": "2m", "Color": "Braided White"},
        "price_paisa": 999100,
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=800&q=80",
    },
]

IMAGES = [
    {"id": uuid.uuid4(), "product_id": "iphone-17-pro", "url": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&q=80", "sort_order": 0},
    {"id": uuid.uuid4(), "product_id": "iphone-17-pro", "url": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&q=80", "sort_order": 1},
    {"id": uuid.uuid4(), "product_id": "galaxy-s25-ultra", "url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800&q=80", "sort_order": 0},
    {"id": uuid.uuid4(), "product_id": "macbook-pro-m4", "url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80", "sort_order": 0},
    {"id": uuid.uuid4(), "product_id": "sony-wh1000xm5", "url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80", "sort_order": 0},
    {"id": uuid.uuid4(), "product_id": "test-cable-7m", "url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=800&q=80", "sort_order": 0},
]

OFFERS = [
    {
        "id": uuid.UUID("f0000000-0000-0000-0000-000000000001"),
        "product_id": "iphone-17-pro",
        "category_id": None,
        "cashback_paisa": 800000,  # ₹8,000 instant financing cashback (ADR-003)
        "valid_from": datetime.now(timezone.utc) - timedelta(days=1),
        "valid_to": datetime.now(timezone.utc) + timedelta(days=365),
    },
    {
        "id": uuid.UUID("f0000000-0000-0000-0000-000000000002"),
        "product_id": "galaxy-s25-ultra",
        "category_id": None,
        "cashback_paisa": 500000,  # ₹5,000 instant financing cashback
        "valid_from": datetime.now(timezone.utc) - timedelta(days=1),
        "valid_to": datetime.now(timezone.utc) + timedelta(days=365),
    },
]

EMI_RULES = [
    # Global Rules
    {"id": uuid.UUID("10000000-0000-0000-0000-000000000003"), "tenure_months": 3,  "interest_rate_bps": 0, "min_amount_paisa": 300000, "max_amount_paisa": None, "is_no_cost": True, "product_id": None, "brand_id": None, "category_id": None},
    {"id": uuid.UUID("10000000-0000-0000-0000-000000000006"), "tenure_months": 6,  "interest_rate_bps": 0, "min_amount_paisa": 500000, "max_amount_paisa": None, "is_no_cost": True, "product_id": None, "brand_id": None, "category_id": None},
    {"id": uuid.UUID("10000000-0000-0000-0000-000000000012"), "tenure_months": 12, "interest_rate_bps": 0, "min_amount_paisa": 1000000, "max_amount_paisa": None, "is_no_cost": True, "product_id": None, "brand_id": None, "category_id": None},
    {"id": uuid.UUID("10000000-0000-0000-0000-000000000024"), "tenure_months": 24, "interest_rate_bps": 0, "min_amount_paisa": 2000000, "max_amount_paisa": None, "is_no_cost": True, "product_id": None, "brand_id": None, "category_id": None},
    {"id": uuid.UUID("10000000-0000-0000-0000-000000000036"), "tenure_months": 36, "interest_rate_bps": 0, "min_amount_paisa": 3000000, "max_amount_paisa": None, "is_no_cost": True, "product_id": None, "brand_id": None, "category_id": None},

    # Apple Brand-Scoped Rule: 60 months at 850 bps (8.5% p.a.) (ADR-007)
    {"id": uuid.UUID("10000000-0000-0000-0000-000000000060"), "tenure_months": 60, "interest_rate_bps": 850, "min_amount_paisa": 5000000, "max_amount_paisa": None, "is_no_cost": False, "product_id": None, "brand_id": "apple", "category_id": None},

    # Uneven remainder test rule (product-scoped)
    {"id": uuid.UUID("10000000-0000-0000-0000-000000000007"), "tenure_months": 7,  "interest_rate_bps": 0, "min_amount_paisa": 100000, "max_amount_paisa": 1500000, "is_no_cost": True, "product_id": "test-cable-7m", "brand_id": None, "category_id": None},
]


async def seed():
    print("Seeding database (idempotent via on_conflict_do_nothing)...")
    async with async_session_factory() as session:
        # Categories
        for cat in CATEGORIES:
            stmt = insert(Category).values(cat).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # Brands
        for brand in BRANDS:
            stmt = insert(Brand).values(brand).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # Products
        for prod in PRODUCTS:
            stmt = insert(Product).values(prod).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # Product Variants
        for var in VARIANTS:
            stmt = insert(ProductVariant).values(var).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # Product Images
        for img in IMAGES:
            stmt = insert(ProductImage).values(img).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # Offers
        for off in OFFERS:
            stmt = insert(Offer).values(off).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        # EMI Rules
        for rule in EMI_RULES:
            stmt = insert(EmiPlanRule).values(rule).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        await session.commit()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
