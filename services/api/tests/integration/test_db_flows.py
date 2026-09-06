import asyncio
from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy import select, delete

from app.core.error_codes import APIException, ErrorCode
from app.domain.catalogue.repository import CatalogueRepository
from app.domain.quote.repository import QuoteRepository
from app.domain.quote.service import QuoteService
from app.domain.checkout_intent.service import CheckoutIntentService
from app.models.models import (
    Category,
    Brand,
    Product,
    ProductVariant,
    Offer,
    EmiPlanRule,
    Quote,
    CheckoutIntent,
)


async def seed_test_catalog(session):
    cat = Category(id="smartphones", name="Smartphones", icon="phone", sort_order=0)
    brand = Brand(id="apple", name="Apple", logo_url=None)
    prod = Product(
        id="iphone-17-pro",
        name="Apple iPhone 17 Pro",
        brand_id="apple",
        category_id="smartphones",
        description="Flagship iPhone",
        base_price_paisa=13490000,
        mrp_paisa=13990000,
        is_available=True,
        is_test_fixture=False,
    )
    var = ProductVariant(
        id=uuid.UUID("a0000000-0000-0000-0000-000000000001"),
        product_id="iphone-17-pro",
        attributes={"storage": "256GB"},
        price_paisa=13490000,
        available=True,
    )
    rule36 = EmiPlanRule(
        id=uuid.uuid4(),
        tenure_months=36,
        interest_rate_bps=0,
        min_amount_paisa=500000,
        max_amount_paisa=None,
        is_no_cost=True,
        product_id=None,
        brand_id=None,
        category_id=None,
    )
    session.add_all([cat, brand, prod, var, rule36])
    await session.commit()
    return prod, var


@pytest.mark.asyncio
async def test_quote_creation_with_offer_and_rules(db_session, test_session_factory):
    prod, var = await seed_test_catalog(db_session)

    # Add an active offer with 8,000 cashback
    now = datetime.now(timezone.utc)
    offer = Offer(
        id=uuid.uuid4(),
        product_id="iphone-17-pro",
        category_id=None,
        cashback_paisa=800000,
        valid_from=now - timedelta(days=1),
        valid_to=now + timedelta(days=30),
    )
    db_session.add(offer)
    await db_session.commit()

    service = QuoteService(db_session)
    quote = await service.create_quote(prod.id, var.id)

    assert quote.id.startswith("qt_")
    assert quote.product_id == "iphone-17-pro"
    assert quote.price_paisa == 13490000
    assert quote.cashback_paisa == 800000
    assert len(quote.plans_json) == 1
    assert quote.plans_json[0]["plan_id"] == "36m"
    assert quote.plans_json[0]["monthly_emi_paisa"] == 352500
    assert quote.plans_json[0]["total_payable_paisa"] == 12690000
    quote_exp = quote.expires_at if quote.expires_at.tzinfo else quote.expires_at.replace(tzinfo=timezone.utc)
    assert quote_exp > now


@pytest.mark.asyncio
async def test_quote_creation_no_eligible_rules(db_session):
    prod, var = await seed_test_catalog(db_session)
    # Clear seeded rules so that only rule_high is evaluated
    await db_session.execute(delete(EmiPlanRule))

    # Price is 13490000. Create rule requiring min 20,000,000
    rule_high = EmiPlanRule(
        id=uuid.uuid4(),
        tenure_months=12,
        interest_rate_bps=0,
        min_amount_paisa=20000000,
        is_no_cost=True,
    )
    db_session.add(rule_high)
    await db_session.commit()

    service = QuoteService(db_session)
    # Use variant with no matching rules
    with pytest.raises(APIException) as exc_info:
        await service.create_quote(prod.id, var.id)
    assert exc_info.value.code == ErrorCode.NO_ELIGIBLE_RULES
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_deterministic_offer_precedence(db_session):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)

    # 1. Global offer: ₹1,000 cashback
    global_offer = Offer(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        product_id=None,
        category_id=None,
        cashback_paisa=100000,
        valid_from=now - timedelta(days=5),
        valid_to=now + timedelta(days=30),
    )
    # 2. Category offer: ₹5,000 cashback
    cat_offer = Offer(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        product_id=None,
        category_id="smartphones",
        cashback_paisa=500000,
        valid_from=now - timedelta(days=3),
        valid_to=now + timedelta(days=30),
    )
    # 3. Product offer: ₹2,000 cashback (lower than category, but product-specific wins ADR-010!)
    prod_offer = Offer(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        product_id="iphone-17-pro",
        category_id=None,
        cashback_paisa=200000,
        valid_from=now - timedelta(days=1),
        valid_to=now + timedelta(days=30),
    )
    db_session.add_all([global_offer, cat_offer, prod_offer])
    await db_session.commit()

    repo = QuoteRepository(db_session)

    # Product-specific offer MUST win
    best = await repo.get_best_offer("iphone-17-pro", "smartphones")
    assert best is not None
    assert best.id == prod_offer.id
    assert best.cashback_paisa == 200000

    # Delete product offer -> Category offer MUST win
    await db_session.delete(prod_offer)
    await db_session.commit()
    best = await repo.get_best_offer("iphone-17-pro", "smartphones")
    assert best.id == cat_offer.id
    assert best.cashback_paisa == 500000

    # Delete category offer -> Global offer MUST win
    await db_session.delete(cat_offer)
    await db_session.commit()
    best = await repo.get_best_offer("iphone-17-pro", "smartphones")
    assert best.id == global_offer.id
    assert best.cashback_paisa == 100000


@pytest.mark.asyncio
async def test_catalogue_search_wildcard_escaping(db_session):
    cat = Category(id="accessories", name="Accessories", icon="chip", sort_order=1)
    brand = Brand(id="generic", name="Generic", logo_url=None)
    p1 = Product(id="phone-regular", name="Phone Regular Edition", brand_id="generic", category_id="accessories", base_price_paisa=100000, is_available=True)
    p2 = Product(id="phone-100-pct", name="Phone 100% Genuine", brand_id="generic", category_id="accessories", base_price_paisa=100000, is_available=True)
    p3 = Product(id="phone-case-1", name="Phone_Case_1", brand_id="generic", category_id="accessories", base_price_paisa=100000, is_available=True)
    p4 = Product(id="phone-slash", name="Phone\\Charger", brand_id="generic", category_id="accessories", base_price_paisa=100000, is_available=True)
    db_session.add_all([cat, brand, p1, p2, p3, p4])
    await db_session.commit()

    repo = CatalogueRepository(db_session)

    # 1. Search for literal "%"
    results, total = await repo.get_products(search="100%")
    assert total == 1
    assert results[0].id == "phone-100-pct"

    # 2. Search for literal "_"
    results, total = await repo.get_products(search="Phone_Case")
    assert total == 1
    assert results[0].id == "phone-case-1"

    # 3. Search for literal "\"
    results, total = await repo.get_products(search="Phone\\")
    assert total == 1
    assert results[0].id == "phone-slash"


@pytest.mark.asyncio
async def test_cashback_exceeds_or_equals_price_data_integrity(db_session):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    # Offer cashback is equal to price (13490000)
    invalid_offer = Offer(
        id=uuid.uuid4(),
        product_id="iphone-17-pro",
        category_id=None,
        cashback_paisa=13490000,
        valid_from=now - timedelta(days=1),
        valid_to=now + timedelta(days=30),
    )
    db_session.add(invalid_offer)
    await db_session.commit()

    service = QuoteService(db_session)
    with pytest.raises(APIException) as exc_info:
        await service.create_quote(prod.id, var.id)
    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_checkout_intent_quote_expired(db_session, test_session_factory):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    expired_quote = Quote(
        id="qt_expired_test_01",
        product_id=prod.id,
        variant_id=var.id,
        price_paisa=var.price_paisa,
        cashback_paisa=0,
        plans_json=[{"plan_id": "36m", "monthly_emi_paisa": 352500}],
        created_at=now - timedelta(minutes=20),
        expires_at=now - timedelta(minutes=10),
    )
    db_session.add(expired_quote)
    await db_session.commit()

    service = CheckoutIntentService(db_session, session_factory=test_session_factory)
    with pytest.raises(APIException) as exc_info:
        await service.create_intent(
            quote_id="qt_expired_test_01",
            plan_id="36m",
            idempotency_key="idemp_key_expired_test",
        )
    assert exc_info.value.code == ErrorCode.QUOTE_EXPIRED
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_checkout_intent_variant_unavailable(db_session, test_session_factory):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    valid_quote = Quote(
        id="qt_variant_unavail_test",
        product_id=prod.id,
        variant_id=var.id,
        price_paisa=var.price_paisa,
        cashback_paisa=0,
        plans_json=[{"plan_id": "36m", "monthly_emi_paisa": 352500}],
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    # Set variant available=False
    var.available = False
    db_session.add(valid_quote)
    await db_session.commit()

    service = CheckoutIntentService(db_session, session_factory=test_session_factory)
    with pytest.raises(APIException) as exc_info:
        await service.create_intent(
            quote_id="qt_variant_unavail_test",
            plan_id="36m",
            idempotency_key="idemp_key_variant_unavail",
        )
    assert exc_info.value.code == ErrorCode.VARIANT_UNAVAILABLE
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_concurrent_checkout_same_key_same_payload(db_session, test_session_factory):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    quote = Quote(
        id="qt_concurrency_race_01",
        product_id=prod.id,
        variant_id=var.id,
        price_paisa=var.price_paisa,
        cashback_paisa=0,
        plans_json=[{"plan_id": "36m", "monthly_emi_paisa": 352500}],
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    db_session.add(quote)
    await db_session.commit()

    shared_key = "idemp_concurrent_key_001"

    # Launch two independent concurrent checkouts using separate sessions
    async def run_checkout():
        async with test_session_factory() as sess:
            service = CheckoutIntentService(sess, session_factory=test_session_factory)
            return await service.create_intent(
                quote_id="qt_concurrency_race_01",
                plan_id="36m",
                idempotency_key=shared_key,
            )

    res1, res2 = await asyncio.gather(run_checkout(), run_checkout())

    # Assertions:
    # 1. Both calls return the exact same intent_id
    assert res1[0]["intent_id"] == res2[0]["intent_id"]
    # 2. One call returned 201 (created), one returned 200 (replayed)
    status_codes = sorted([res1[1], res2[1]])
    assert status_codes == [200, 201]

    # 3. Exactly one row exists in checkout_intents table
    rows = (await db_session.execute(select(CheckoutIntent).where(CheckoutIntent.idempotency_key == shared_key))).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_concurrent_checkout_same_key_different_payload(db_session, test_session_factory):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    quote = Quote(
        id="qt_concurrency_race_02",
        product_id=prod.id,
        variant_id=var.id,
        price_paisa=var.price_paisa,
        cashback_paisa=0,
        plans_json=[
            {"plan_id": "36m", "monthly_emi_paisa": 352500},
            {"plan_id": "12m", "monthly_emi_paisa": 1000000},
        ],
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    db_session.add(quote)
    await db_session.commit()

    shared_key = "idemp_conflict_key_002"

    async def run_checkout(plan_id: str):
        async with test_session_factory() as sess:
            service = CheckoutIntentService(sess, session_factory=test_session_factory)
            return await service.create_intent(
                quote_id="qt_concurrency_race_02",
                plan_id=plan_id,
                idempotency_key=shared_key,
            )

    results = await asyncio.gather(
        run_checkout("36m"),
        run_checkout("12m"),
        return_exceptions=True,
    )

    # One call succeeds (201) and the other fails with 409 IDEMPOTENCY_CONFLICT
    success = [r for r in results if not isinstance(r, Exception)]
    errors = [r for r in results if isinstance(r, APIException)]

    assert len(success) == 1
    assert success[0][1] == 201
    assert len(errors) == 1
    assert errors[0].code == ErrorCode.IDEMPOTENCY_CONFLICT
    assert errors[0].status_code == 409


@pytest.mark.asyncio
async def test_checkout_different_keys_same_quote_allowed(db_session, test_session_factory):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    quote = Quote(
        id="qt_multi_reuse_quote",
        product_id=prod.id,
        variant_id=var.id,
        price_paisa=var.price_paisa,
        cashback_paisa=0,
        plans_json=[{"plan_id": "36m", "monthly_emi_paisa": 352500}],
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    db_session.add(quote)
    await db_session.commit()

    async def run_checkout(key: str):
        async with test_session_factory() as sess:
            service = CheckoutIntentService(sess, session_factory=test_session_factory)
            return await service.create_intent(
                quote_id="qt_multi_reuse_quote",
                plan_id="36m",
                idempotency_key=key,
            )

    res1, res2 = await asyncio.gather(
        run_checkout("key_device_A"),
        run_checkout("key_device_B"),
    )

    # Per ADR-008: Quote is not single use; both succeed with distinct intent IDs
    assert res1[1] == 201
    assert res2[1] == 201
    assert res1[0]["intent_id"] != res2[0]["intent_id"]
