from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
from .core.config import settings
from .api.v1 import auth, users, shops, customers, products, bills, admin, dashboard, udharo


# Custom middleware to ensure CORS headers are added to error responses
class CORSMiddlewareWithErrorHandling(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Add CORS headers to error responses
            error_response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
            
            for origin in settings.BACKEND_CORS_ORIGINS:
                if origin == "*":
                    error_response.headers["Access-Control-Allow-Origin"] = "*"
                    break
                request_origin = request.headers.get("origin")
                if request_origin and (origin == request_origin):
                    error_response.headers["Access-Control-Allow-Origin"] = request_origin
                    error_response.headers["Access-Control-Allow-Credentials"] = "true"
                    break
            
            error_response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
            error_response.headers["Access-Control-Allow-Headers"] = "Accept,Authorization,Content-Type,X-API-KEY"
            
            print(f"Error handled in middleware: {str(e)}")
            print(traceback.format_exc())
            return error_response


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add custom error handling middleware first
app.add_middleware(CORSMiddlewareWithErrorHandling)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(shops.router, prefix=f"{settings.API_V1_STR}/shops", tags=["shops"])
app.include_router(customers.router, prefix=f"{settings.API_V1_STR}", tags=["customers"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}", tags=["products"])
app.include_router(bills.router, prefix=f"{settings.API_V1_STR}", tags=["bills"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(udharo.router, prefix=f"{settings.API_V1_STR}/udharo", tags=["udharo"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to BillSmart API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "billsmart-api"}


# Exception handlers to ensure CORS headers are included in error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"Unexpected error: {str(exc)}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
