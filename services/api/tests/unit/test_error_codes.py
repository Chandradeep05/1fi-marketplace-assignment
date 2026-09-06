from app.core.error_codes import ErrorCode, ERROR_STATUS_MAP


def test_canonical_error_codes_mapping():
    assert ERROR_STATUS_MAP[ErrorCode.PRODUCT_NOT_FOUND] == 404
    assert ERROR_STATUS_MAP[ErrorCode.VARIANT_NOT_FOUND] == 404
    assert ERROR_STATUS_MAP[ErrorCode.VARIANT_UNAVAILABLE] == 409
    assert ERROR_STATUS_MAP[ErrorCode.QUOTE_NOT_FOUND] == 404
    assert ERROR_STATUS_MAP[ErrorCode.QUOTE_EXPIRED] == 400
    assert ERROR_STATUS_MAP[ErrorCode.PLAN_NOT_IN_QUOTE] == 400
    assert ERROR_STATUS_MAP[ErrorCode.INSUFFICIENT_LIMIT] == 422
    assert ERROR_STATUS_MAP[ErrorCode.NO_ELIGIBLE_RULES] == 422
    assert ERROR_STATUS_MAP[ErrorCode.ELIGIBILITY_UNAVAILABLE] == 503
    assert ERROR_STATUS_MAP[ErrorCode.MISSING_IDEMPOTENCY_KEY] == 400
    assert ERROR_STATUS_MAP[ErrorCode.IDEMPOTENCY_CONFLICT] == 409
    assert ERROR_STATUS_MAP[ErrorCode.RATE_LIMITED] == 429
    assert ERROR_STATUS_MAP[ErrorCode.VALIDATION_ERROR] == 422
    assert ERROR_STATUS_MAP[ErrorCode.INTERNAL_ERROR] == 500
