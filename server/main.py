"""
AMA Ceramics Cloud Backend API:
FastAPI server providing real-time synchronized REST endpoints for
Quotations, Customers, Tile Brands, Payments, and Reporting across
Windows PC and Android mobile devices.
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root is in python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse

from app.database.models import init_database
from app.database.seed_data import seed_database
from app.config import APP_VERSION, APP_NAME

# Lifespan event for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database schema and indexes exist
    init_database()
    seed_database(force=False)
    yield
    # Shutdown

app = FastAPI(
    title=f"{APP_NAME} - Cloud Sync API",
    version=APP_VERSION,
    description="Synchronized Cloud API for AMA Ceramics Quotation Management System (Windows PC & Android Phone)",
    lifespan=lifespan,
)

# CORS: Allow cross-origin requests from Android apps, web clients, and local network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and attach API routers
from server.api.quotations import router as quotations_router
from server.api.customers import router as customers_router
from server.api.brands import router as brands_router
from server.api.salespersons import router as salespersons_router
from server.api.payments import router as payments_router
from server.api.reports import router as reports_router

app.include_router(quotations_router, prefix="/api/quotations", tags=["Quotations"])
app.include_router(customers_router, prefix="/api/customers", tags=["Customers"])
app.include_router(brands_router, prefix="/api/brands", tags=["Tile Brands & Sizes"])
app.include_router(salespersons_router, prefix="/api/salespersons", tags=["Sales Team"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports & Dashboard"])


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify cloud server and database connectivity."""
    from app.database.connection import db
    from app.database.models import Quotation, Customer, SalesPerson
    try:
        db.connect(reuse_if_open=True)
        quotes_count = Quotation.select().count()
        cust_count = Customer.select().count()
        team_count = SalesPerson.select().count()
        db_connected = True
    except Exception as e:
        db_connected = False
        quotes_count = cust_count = team_count = 0

    return {
        "status": "healthy" if db_connected else "degraded",
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "database_connected": db_connected,
        "records": {
            "quotations": quotes_count,
            "customers": cust_count,
            "sales_team": team_count,
        }
    }


# Mount Static Mobile Web App
static_mobile_dir = Path(__file__).resolve().parent / "static" / "mobile"
static_mobile_dir.mkdir(parents=True, exist_ok=True)
app.mount("/mobile", StaticFiles(directory=str(static_mobile_dir), html=True), name="mobile")


@app.get("/")
def root():
    """Redirects web root to the mobile touch app."""
    return RedirectResponse(url="/mobile/")


if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 so both PC and Android devices on the local Wi-Fi can connect
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
