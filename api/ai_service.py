"""
LoadMoveGH — AI Microservice Entry Point
==========================================

Serves the AI/ML workloads as a separate container:
  - ML Pricing Engine
  - AI Fraud Detection
  - AI Load Matching
  - AI Assistant (OpenAI)

Deploy alongside the main API as a second Railway/Render service.
Internal traffic from the main API reaches this service via:
  - Railway internal networking: http://loadmovegh-ai.railway.internal:8001
  - Render private service: http://loadmovegh-ai:8001

Port: 8001 (default)
Docs: /ai/docs
Health: /ai/health
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="LoadMoveGH AI Service",
    description=(
        "LoadMoveGH AI Microservice — ML Pricing Engine, "
        "Fraud Detection, Load Matching & AI Assistant"
    ),
    version="1.0.0",
    docs_url="/ai/docs",
    redoc_url="/ai/redoc",
)

# CORS — only allow main API and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "https://www.loadmovegh.com",
        "https://loadmovegh.com",
        "https://admin.loadmovegh.com",
        "https://api.loadmovegh.com",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Import and mount routers ────────────────────────────────
# Lazy imports to avoid startup errors if some modules are missing
try:
    from app.api.v1.endpoints.pricing import router as pricing_router
    app.include_router(pricing_router, prefix="/ai/v1")
except ImportError:
    pass

try:
    from app.api.v1.endpoints.matching import router as matching_router
    app.include_router(matching_router, prefix="/ai/v1")
except ImportError:
    pass

try:
    from app.api.v1.endpoints.fraud import router as fraud_router
    app.include_router(fraud_router, prefix="/ai/v1")
except ImportError:
    pass

try:
    from app.api.v1.endpoints.assistant import router as assistant_router
    app.include_router(assistant_router, prefix="/ai/v1")
except ImportError:
    pass


# ── Health Check ────────────────────────────────────────────

@app.get("/ai/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "loadmovegh-ai",
        "model": settings.OPENAI_MODEL,
        "pricing_model_dir": settings.PRICING_MODEL_DIR,
    }
