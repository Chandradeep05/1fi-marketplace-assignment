from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.error_codes import APIException, ErrorCode, format_error_response
from app.core.redis import close_redis
from app.core.request_id import RequestIDMiddleware

from app.api.v1.categories import router as categories_router
from app.api.v1.eligibility import router as eligibility_router
from app.api.v1.products import router as products_router
from app.api.v1.quotes import router as quotes_router
from app.api.v1.checkout_intents import router as checkout_intents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title="1Fi Marketplace API",
    version="1.0.0",
    description="Full-stack reference implementation of the 1Fi Marketplace API.",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS Middleware (ADR-011 / Spec compliance: wildcard origin requires allow_credentials=False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Retry-After"],
)

# Request ID Middleware
app.add_middleware(RequestIDMiddleware)


# Exception Handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return format_error_response(
        request=request,
        code=exc.code.value,
        message=exc.message,
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()])
    return format_error_response(
        request=request,
        code=ErrorCode.VALIDATION_ERROR.value,
        message=f"Validation failed: {error_msg}",
        status_code=422,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return format_error_response(
        request=request,
        code=ErrorCode.INTERNAL_ERROR.value,
        message=str(exc) if settings.ENVIRONMENT == "development" else "Internal server error",
        status_code=500,
    )


# Health Check
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# API v1 Routers
app.include_router(categories_router, prefix="/api/v1")
app.include_router(eligibility_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(quotes_router, prefix="/api/v1")
app.include_router(checkout_intents_router, prefix="/api/v1")
