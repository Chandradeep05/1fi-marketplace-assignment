import hashlib
import json


def test_idempotency_hash_key_order_invariance():
    payload1 = {"quote_id": "qt_01HXYZ", "plan_id": "36m"}
    payload2 = {"plan_id": "36m", "quote_id": "qt_01HXYZ"}

    hash1 = hashlib.sha256(json.dumps(payload1, sort_keys=True).encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(json.dumps(payload2, sort_keys=True).encode("utf-8")).hexdigest()

    assert hash1 == hash2

    # Different payload must produce different hash
    payload3 = {"quote_id": "qt_01HXYZ", "plan_id": "60m"}
    hash3 = hashlib.sha256(json.dumps(payload3, sort_keys=True).encode("utf-8")).hexdigest()
    assert hash1 != hash3
