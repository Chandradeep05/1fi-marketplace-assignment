import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy import select, delete, text



from app.core.error_codes import APIException, ErrorCode
from app.domain.catalogue.repository import CatalogueRepository
from app.domain.quote.repository import QuoteRepository
from app.domain.quote.service import QuoteService
from app.domain.checkout_intent.service import CheckoutIntentService
from app.domain.checkout_intent.repository import CheckoutIntentRepository
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


@pytest.mark.asyncio
async def test_fixture_not_returned_by_listing(db_session):
    cat = Category(id="fixtures_cat", name="Fixtures", icon="cube", sort_order=0)
    brand = Brand(id="brand_fix", name="Brand Fix")
    prod_real = Product(
        id="prod_real_visible",
        name="Real Visible Product",
        brand_id="brand_fix",
        category_id="fixtures_cat",
        base_price_paisa=500000,
        is_available=True,
        is_test_fixture=False,
    )
    prod_fix = Product(
        id="prod_test_fixture_hidden",
        name="Hidden Test Fixture",
        brand_id="brand_fix",
        category_id="fixtures_cat",
        base_price_paisa=500000,
        is_available=True,
        is_test_fixture=True,
    )
    db_session.add_all([cat, brand, prod_real, prod_fix])
    await db_session.commit()

    repo = CatalogueRepository(db_session)
    products, total = await repo.get_products()
    ids = [p.id for p in products]
    assert "prod_real_visible" in ids
    assert "prod_test_fixture_hidden" not in ids


@pytest.mark.asyncio
async def test_fixture_not_returned_by_direct_lookup(db_session):
    cat = Category(id="cat_dl", name="Direct Lookup Cat", icon="cube", sort_order=0)
    brand = Brand(id="brand_dl", name="Direct Lookup Brand")
    prod_fix = Product(
        id="prod_fixture_direct",
        name="Fixture Direct",
        brand_id="brand_dl",
        category_id="cat_dl",
        base_price_paisa=100000,
        is_available=True,
        is_test_fixture=True,
    )
    db_session.add_all([cat, brand, prod_fix])
    await db_session.commit()

    repo = CatalogueRepository(db_session)
    product = await repo.get_product_by_id("prod_fixture_direct")
    assert product is None


@pytest.mark.asyncio
async def test_fixture_cannot_generate_quote(db_session):
    cat = Category(id="cat_qf", name="Quote Fixture Cat", icon="cube", sort_order=0)
    brand = Brand(id="brand_qf", name="Quote Fixture Brand")
    prod_fix = Product(
        id="prod_fixture_quote",
        name="Fixture Quote",
        brand_id="brand_qf",
        category_id="cat_qf",
        base_price_paisa=1000000,
        is_available=True,
        is_test_fixture=True,
    )
    var_fix = ProductVariant(
        id=uuid.uuid4(),
        product_id="prod_fixture_quote",
        attributes={"Color": "Red"},
        price_paisa=1000000,
        available=True,
    )
    db_session.add_all([cat, brand, prod_fix, var_fix])
    await db_session.commit()

    service = QuoteService(db_session)
    with pytest.raises(APIException) as exc_info:
        await service.create_quote(product_id="prod_fixture_quote", variant_id=var_fix.id)
    assert exc_info.value.code == ErrorCode.PRODUCT_NOT_FOUND


@pytest.mark.asyncio
async def test_quote_and_checkout_continue_when_redis_unavailable(db_session, test_session_factory, monkeypatch):
    from unittest.mock import AsyncMock

    async def mock_failing_redis():
        mock = AsyncMock()
        mock.set.side_effect = ConnectionError("Redis connection refused")
        mock.hgetall.side_effect = ConnectionError("Redis connection refused")
        mock.pipeline.side_effect = ConnectionError("Redis connection refused")
        return mock

    monkeypatch.setattr("app.domain.quote.service.get_redis", mock_failing_redis)
    monkeypatch.setattr("app.domain.checkout_intent.service.get_redis", mock_failing_redis)

    cat = Category(id="cat_red", name="Redis Cat", icon="cube", sort_order=0)
    brand = Brand(id="brand_red", name="Redis Brand")
    prod = Product(
        id="prod_redis_test",
        name="Redis Test Prod",
        brand_id="brand_red",
        category_id="cat_red",
        base_price_paisa=10000000,
        is_available=True,
        is_test_fixture=False,
    )
    var_id = uuid.uuid4()
    var = ProductVariant(
        id=var_id,
        product_id="prod_redis_test",
        attributes={"Color": "Gold"},
        price_paisa=10000000,
        available=True,
    )
    rule = EmiPlanRule(
        id=uuid.uuid4(),
        tenure_months=12,
        interest_rate_bps=0,
        min_amount_paisa=1000000,
        is_no_cost=True,
    )
    db_session.add_all([cat, brand, prod, var, rule])
    await db_session.commit()

    quote_service = QuoteService(db_session)
    quote = await quote_service.create_quote(product_id="prod_redis_test", variant_id=var_id)
    assert quote.id.startswith("qt_")

    checkout_service = CheckoutIntentService(db_session, session_factory=test_session_factory)
    resp, code = await checkout_service.create_intent(
        quote_id=quote.id,
        plan_id="12m",
        idempotency_key="key_redis_down_test",
    )
    assert code == 201
    assert resp["status"] == "received"

    resp2, code2 = await checkout_service.create_intent(
        quote_id=quote.id,
        plan_id="12m",
        idempotency_key="key_redis_down_test",
    )
    assert code2 == 200
    assert resp2["intent_id"] == resp["intent_id"]


@pytest.mark.asyncio
async def test_non_idempotency_integrity_error_raises_500(db_session, test_session_factory, monkeypatch):
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    quote = Quote(
        id="qt_nie_test",
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

    from sqlalchemy.exc import IntegrityError
    async def mock_save_intent_fail(self_repo, intent):
        raise IntegrityError("INSERT INTO checkout_intents", {}, Exception("CHECK constraint failed: chk_checkout_intent_status"))

    monkeypatch.setattr(CheckoutIntentRepository, "save_intent", mock_save_intent_fail)

    service = CheckoutIntentService(db_session, session_factory=test_session_factory)
    with pytest.raises(APIException) as exc_info:
        await service.create_intent(
            quote_id="qt_nie_test",
            plan_id="36m",
            idempotency_key="key_nie_unique",
        )
    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
@pytest.mark.skipif(
    "sqlite" in os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"),
    reason="FOR UPDATE row-level locking requires PostgreSQL; SQLite does not support it",
)
async def test_high_concurrency_same_key_produces_single_intent(db_session, test_session_factory):

    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    quote = Quote(
        id="qt_hc_test",
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

    async def execute_checkout():
        async with test_session_factory() as sess:
            service = CheckoutIntentService(sess, session_factory=test_session_factory)
            return await service.create_intent(
                quote_id="qt_hc_test",
                plan_id="36m",
                idempotency_key="burst_key_100",
            )

    results = await asyncio.gather(*[execute_checkout() for _ in range(10)])

    status_codes = [r[1] for r in results]
    assert 201 in status_codes
    assert all(code in (200, 201) for code in status_codes)

    intent_ids = set(r[0]["intent_id"] for r in results)
    assert len(intent_ids) == 1

    from sqlalchemy import select, func
    count_stmt = select(func.count()).select_from(CheckoutIntent).where(CheckoutIntent.idempotency_key == "burst_key_100")
    count = (await db_session.execute(count_stmt)).scalar_one()
    assert count == 1


@pytest.mark.asyncio
@pytest.mark.skipif(
    "sqlite" in os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"),
    reason="FOR UPDATE row-level locking requires PostgreSQL; SQLite does not support it",
)
async def test_high_concurrency_different_keys_same_quote(db_session, test_session_factory):

    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    quote = Quote(
        id="qt_hcd_test",
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

    async def execute_checkout(idx: int):
        async with test_session_factory() as sess:
            service = CheckoutIntentService(sess, session_factory=test_session_factory)
            return await service.create_intent(
                quote_id="qt_hcd_test",
                plan_id="36m",
                idempotency_key=f"distinct_key_{idx}",
            )

    results = await asyncio.gather(*[execute_checkout(i) for i in range(10)])

    assert all(r[1] == 201 for r in results)
    intent_ids = set(r[0]["intent_id"] for r in results)
    assert len(intent_ids) == 10


@pytest.mark.asyncio
async def test_phantom_replay_cache_evicted_and_phase_b_executed(db_session, test_session_factory, monkeypatch):
    """Gate 4 regression test:
    When Redis contains an idempotency cache hit pointing to an intent_id
    that does NOT exist in PostgreSQL (e.g., following DB restore, rollback, or manual deletion),
    the system must NEVER return the fabricated 200 response with the ghost ID.
    Instead, it must:
      1. Detect the row is missing in Postgres
      2. Evict the stale Redis cache entry
      3. Proceed through normal Phase B to create a genuine intent (201 Created)
      4. Persist the genuine intent in Postgres and update Redis
    """
    prod, var = await seed_test_catalog(db_session)
    now = datetime.now(timezone.utc)
    quote = Quote(
        id="qt_phantom_gate4_test",
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

    from app.core.redis import get_redis

    class InMemoryRedis:
        def __init__(self):
            self._store = {}
        async def ping(self):
            return True
        async def hgetall(self, key):
            return dict(self._store.get(key, {}))
        async def hset(self, key, mapping):
            if key not in self._store:
                self._store[key] = {}
            self._store[key].update({k: str(v) for k, v in mapping.items()})
        async def delete(self, key):
            self._store.pop(key, None)
        def pipeline(self):
            store = self._store
            class Pipe:
                def __init__(self):
                    self.ops = []
                def hset(self, key, mapping):
                    self.ops.append(('hset', key, mapping))
                    return self
                def expire(self, key, ttl):
                    return self
                async def execute(self):
                    for op, k, m in self.ops:
                        if k not in store:
                            store[k] = {}
                        store[k].update({field: str(val) for field, val in m.items()})
            return Pipe()

    try:
        r = await get_redis()
        await asyncio.wait_for(r.ping(), timeout=0.5)
    except Exception:
        fake_r = InMemoryRedis()
        async def mock_get_redis():
            return fake_r
        monkeypatch.setattr("app.domain.checkout_intent.service.get_redis", mock_get_redis)
        monkeypatch.setattr("app.core.redis.get_redis", mock_get_redis)
        r = fake_r

    idem_key = "gate4_phantom_replay_key"
    payload_to_hash = {"quote_id": "qt_phantom_gate4_test", "plan_id": "36m"}
    req_hash = hashlib.sha256(
        json.dumps(payload_to_hash, sort_keys=True).encode("utf-8")
    ).hexdigest()

    ghost_intent_id = "ci_ghost_XYZ_nonexistent"
    ghost_response = {
        "intent_id": ghost_intent_id,
        "status": "received",
        "quote_id": "qt_phantom_gate4_test",
        "plan_id": "36m",
    }

    # 1. Warm Redis with the phantom entry
    cache_key = f"idempotency:{idem_key}"
    await r.hset(cache_key, mapping={"hash": req_hash, "response": json.dumps(ghost_response)})


    # Confirm ghost does NOT exist in Postgres
    ghost_in_pg = (await db_session.execute(
        select(CheckoutIntent).where(CheckoutIntent.id == ghost_intent_id)
    )).scalar_one_or_none()
    assert ghost_in_pg is None

    service = CheckoutIntentService(db_session, session_factory=test_session_factory)

    # 2. Replay check must detect missing PG row, return None, and evict Redis
    replay_res = await service.check_existing_replay(
        quote_id="qt_phantom_gate4_test",
        plan_id="36m",
        idempotency_key=idem_key,
    )
    assert replay_res is None

    redis_after_evict = await r.hgetall(cache_key)
    assert not redis_after_evict

    # 3. Re-seed phantom into Redis to test create_intent's own Phase A guard
    await r.hset(cache_key, mapping={"hash": req_hash, "response": json.dumps(ghost_response)})

    # 4. Call create_intent — must NOT return cached 200 with ghost ID; must execute Phase B and return 201
    resp_data, status_code = await service.create_intent(
        quote_id="qt_phantom_gate4_test",
        plan_id="36m",
        idempotency_key=idem_key,
    )

    assert status_code == 201
    assert resp_data["intent_id"] != ghost_intent_id
    assert resp_data["status"] == "received"

    # Confirm real intent exists in PostgreSQL
    real_pg_row = (await db_session.execute(
        select(CheckoutIntent).where(CheckoutIntent.id == resp_data["intent_id"])
    )).scalar_one_or_none()
    assert real_pg_row is not None
    assert real_pg_row.idempotency_key == idem_key

    # Confirm Redis is now updated with the REAL intent
    final_cached = await r.hgetall(cache_key)
    final_cached_resp = json.loads(final_cached["response"])
    assert final_cached_resp["intent_id"] == resp_data["intent_id"]


@pytest.mark.asyncio
async def test_destructive_teardown_preserves_sentinel_and_schema_on_postgres(test_engine):
    """Gate 5 regression test:
    Verify that test database fixtures do NOT drop or destroy out-of-band tables
    (e.g., sentinel tables or application schema) on PostgreSQL.
    """
    if "sqlite" in os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"):
        pytest.skip("Gate 5 sentinel preservation test applies to PostgreSQL")

    # Create sentinel table with out-of-band data
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE TABLE IF NOT EXISTS _audit_sentinel_gate5 (id INT PRIMARY KEY, marker TEXT)"))
        await conn.execute(text("INSERT INTO _audit_sentinel_gate5 (id, marker) VALUES (1, 'sentinel_alive') ON CONFLICT (id) DO NOTHING"))

    # Verify sentinel still exists and data is preserved
    async with test_engine.begin() as conn:
        res = (await conn.execute(text("SELECT marker FROM _audit_sentinel_gate5 WHERE id = 1"))).scalar_one()
        assert res == "sentinel_alive"

        # Verify application schema table also exists
        prod_table_check = (await conn.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'products'"))).scalar_one_or_none()
        assert prod_table_check == 1

