from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.api.routes import router
from app.services.scheduler import start_scheduler
import os

app = FastAPI(title="RiskLattice API", version="1.0.0")

# CORS middleware - must be added BEFORE the router
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers including X-Session-Id
    expose_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["api"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on startup."""
    init_db()
    print("Database initialized")
    start_scheduler()
    print("Application started")


@app.get("/")
async def root():
    return {"message": "RiskLattice API", "docs": "/docs"}

