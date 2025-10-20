"""
FastAPI application entry point for Nexus Analyzer.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from middleware.tenant import TenantMiddleware

# Import API routers
from api import auth, tenants, users, csv_processor, business_profile, nexus_rules, liability, reports

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Sales Tax Nexus Determination Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant identification middleware
app.add_middleware(TenantMiddleware)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(csv_processor.router, prefix="/api/v1/csv", tags=["csv"])
app.include_router(business_profile.router, prefix="/api/v1/business-profile", tags=["business-profile"])
app.include_router(nexus_rules.router, prefix="/api/v1/nexus", tags=["nexus"])
app.include_router(liability.router, prefix="/api/v1/liability", tags=["liability"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
