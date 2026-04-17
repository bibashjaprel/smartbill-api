import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .core.config import settings
from .core.database import init_db
from .core.observability import RequestLoggingMiddleware, check_database_readiness
from .utils.api_response import success_response
from .api.v1 import (
    admin,
    audit,
    auth,
    billing,
    credits,
    customers_mgmt,
    dashboard,
    inventory,
    notifications,
    products,
    reports,
    shops,
    suppliers,
    subscriptions,
    users,
)

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def _error_body(request: Request, code: str, message: str, details=None) -> dict:
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": getattr(request.state, "request_id", None),
        },
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Using DATABASE_URL: %s", settings.masked_database_url())
    if settings.AUTO_INIT_DB:
        logger.warning("AUTO_INIT_DB is enabled; running Base.metadata.create_all via init_db()")
        init_db()
    else:
        logger.info("AUTO_INIT_DB is disabled; expecting schema managed by Alembic migrations")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Add request context first
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RequestLoggingMiddleware)

if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(shops.router, prefix=f"{settings.API_V1_STR}/shops", tags=["shops"])
app.include_router(suppliers.router, prefix=f"{settings.API_V1_STR}", tags=["suppliers"])
app.include_router(customers_mgmt.router, prefix=f"{settings.API_V1_STR}", tags=["customers"])
app.include_router(credits.router, prefix=f"{settings.API_V1_STR}", tags=["credit"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}", tags=["products"])
app.include_router(billing.router, prefix=f"{settings.API_V1_STR}", tags=["billing"])
app.include_router(inventory.router, prefix=f"{settings.API_V1_STR}", tags=["inventory"])
app.include_router(subscriptions.router, prefix=f"{settings.API_V1_STR}", tags=["subscriptions"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}", tags=["notifications"])
app.include_router(audit.router, prefix=f"{settings.API_V1_STR}", tags=["audit"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])


@app.get("/")
def read_root(request: Request):
    return success_response(
        {
            "message": "Welcome to BillSmart API",
            "version": settings.VERSION,
            "docs_url": f"{settings.API_V1_STR}/docs",
        },
        request_id=getattr(request.state, "request_id", None),
    )


@app.get("/health")
def health_check(request: Request):
    return success_response(
        {"service": "billsmart-api", "health": "healthy"},
        request_id=getattr(request.state, "request_id", None),
    )


@app.get("/ready")
def readiness_check(request: Request):
    try:
        from .core.database import SessionLocal

        db = SessionLocal()
        try:
            check_database_readiness(db)
        finally:
            db.close()

        return success_response(
            {"service": "billsmart-api", "ready": True},
            request_id=getattr(request.state, "request_id", None),
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content=_error_body(
                request,
                code="READINESS_ERROR",
                message="Service not ready",
                details=[{"msg": str(exc)}],
            ),
        )


# Exception handlers to ensure CORS headers are included in error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            request,
            code="HTTP_ERROR",
            message=str(exc.detail),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"loc": list(err.get("loc", [])), "msg": err.get("msg")} for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content=_error_body(
            request,
            code="VALIDATION_ERROR",
            message="Validation failed",
            details=errors,
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception. request_id=%s", getattr(request.state, "request_id", None))
    return JSONResponse(
        status_code=500,
        content=_error_body(
            request,
            code="INTERNAL_SERVER_ERROR",
            message="Internal server error",
        ),
    )
