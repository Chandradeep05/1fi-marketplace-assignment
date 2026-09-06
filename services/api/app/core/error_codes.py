from enum import Enum
from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    VARIANT_NOT_FOUND = "VARIANT_NOT_FOUND"
    VARIANT_UNAVAILABLE = "VARIANT_UNAVAILABLE"
    QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"
    QUOTE_EXPIRED = "QUOTE_EXPIRED"
    PLAN_NOT_IN_QUOTE = "PLAN_NOT_IN_QUOTE"
    INSUFFICIENT_LIMIT = "INSUFFICIENT_LIMIT"
    NO_ELIGIBLE_RULES = "NO_ELIGIBLE_RULES"
    ELIGIBILITY_UNAVAILABLE = "ELIGIBILITY_UNAVAILABLE"
    MISSING_IDEMPOTENCY_KEY = "MISSING_IDEMPOTENCY_KEY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


ERROR_STATUS_MAP: Dict[ErrorCode, int] = {
    ErrorCode.PRODUCT_NOT_FOUND: 404,
    ErrorCode.VARIANT_NOT_FOUND: 404,
    ErrorCode.VARIANT_UNAVAILABLE: 409,
    ErrorCode.QUOTE_NOT_FOUND: 404,
    ErrorCode.QUOTE_EXPIRED: 400,
    ErrorCode.PLAN_NOT_IN_QUOTE: 400,
    ErrorCode.INSUFFICIENT_LIMIT: 422,
    ErrorCode.NO_ELIGIBLE_RULES: 422,
    ErrorCode.ELIGIBILITY_UNAVAILABLE: 503,
    ErrorCode.MISSING_IDEMPOTENCY_KEY: 400,
    ErrorCode.IDEMPOTENCY_CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.INTERNAL_ERROR: 500,
}


class APIException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code or ERROR_STATUS_MAP.get(code, 500)
        self.headers = headers or {}
        super().__init__(message)


def format_error_response(request: Request, code: str, message: str, status_code: int, headers: Optional[Dict[str, str]] = None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
    resp_headers = {"X-Request-ID": request_id}
    if headers:
        resp_headers.update(headers)
    return JSONResponse(status_code=status_code, content=payload, headers=resp_headers)
