import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}
        assert "X-Request-ID" in res.headers


@pytest.mark.asyncio
async def test_eligibility_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/marketplace/eligibility")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_limit_paisa"] == 20000000
        assert data["used_paisa"] == 5000000
        assert data["available_paisa"] == 15000000


@pytest.mark.asyncio
async def test_checkout_intent_missing_idempotency_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Deliberately omit Idempotency-Key header
        payload = {"quote_id": "qt_01JXYZ", "plan_id": "36m"}
        res = await client.post("/api/v1/marketplace/checkout-intents", json=payload)
        assert res.status_code == 400
        body = res.json()
        assert body["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"
        assert "Idempotency-Key header is required" in body["error"]["message"]
        assert "request_id" in body["error"]


@pytest.mark.asyncio
async def test_quote_request_validation_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid variant_id (not a UUID)
        payload = {"product_id": "iphone-17-pro", "variant_id": "not-valid-uuid"}
        res = await client.post("/api/v1/marketplace/quotes", json=payload)
        assert res.status_code == 422
        body = res.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "request_id" in body["error"]


@pytest.mark.asyncio
async def test_custom_request_id_propagation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        custom_rid = "req_custom_trace_999"
        res = await client.get("/api/v1/health", headers={"X-Request-ID": custom_rid})
        assert res.status_code == 200
        assert res.headers["X-Request-ID"] == custom_rid


@pytest.mark.asyncio
async def test_idempotency_replay_bypasses_rate_limit(monkeypatch):
    from unittest.mock import AsyncMock
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async def mock_replay(self, quote_id, plan_id, idempotency_key):
            return {
                "intent_id": "ci_replayed_intent_123",
                "status": "received",
                "quote_id": quote_id,
                "plan_id": plan_id,
            }
        monkeypatch.setattr("app.domain.checkout_intent.service.CheckoutIntentService.check_existing_replay", mock_replay)

        for _ in range(7):
            res = await client.post(
                "/api/v1/marketplace/checkout-intents",
                json={"quote_id": "qt_mock_1", "plan_id": "12m"},
                headers={"Idempotency-Key": "same_key_retry"},
            )
            assert res.status_code == 200
            assert res.json()["intent_id"] == "ci_replayed_intent_123"
