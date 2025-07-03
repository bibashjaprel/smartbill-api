from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1 import auth, users, shops, customers, products, bills, admin

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(shops.router, prefix=f"{settings.API_V1_STR}/shops", tags=["shops"])
app.include_router(customers.router, prefix=f"{settings.API_V1_STR}", tags=["customers"])
app.include_router(products.router, prefix=f"{settings.API_V1_STR}", tags=["products"])
app.include_router(bills.router, prefix=f"{settings.API_V1_STR}", tags=["bills"])


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
