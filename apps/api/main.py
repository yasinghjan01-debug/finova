import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.core.config import settings
from apps.api.core.database import Base, engine
from apps.api.core.seed import seed_database
from apps.api.routers import (
    auth, dashboard, memory, people, obligations,
    reconciliation, risk, recovery, approvals,
    razorpay, assistant, simulator, audit
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FINOVA — AI Financial Memory & Revenue Recovery Controller",
    version="1.1.0",
    description="AI Financial Memory & Revenue Recovery Controller (Human-in-the-loop financial automation)"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount feature routers under API prefix
api_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(memory.router, prefix=api_prefix)
app.include_router(people.router, prefix=api_prefix)
app.include_router(obligations.router, prefix=api_prefix)
app.include_router(reconciliation.router, prefix=api_prefix)
app.include_router(risk.router, prefix=api_prefix)
app.include_router(recovery.router, prefix=api_prefix)
app.include_router(approvals.router, prefix=api_prefix)
app.include_router(razorpay.router, prefix=api_prefix)
app.include_router(assistant.router, prefix=api_prefix)
app.include_router(simulator.router, prefix=api_prefix)
app.include_router(audit.router, prefix=api_prefix)

@app.on_event("startup")
def startup_event():
    seed_database()

@app.get("/")
def root():
    return {
        "app": "FINOVA",
        "description": "AI Financial Memory & Revenue Recovery Controller",
        "version": "1.1.0",
        "philosophy": "AI investigates, recommends and prepares; human policy authorizes sensitive actions.",
        "status": "online",
        "engines": [
            "Payment Memory Engine",
            "Financial Relationship Engine",
            "Reconciliation Engine",
            "Risk & Impersonation ML Engine",
            "Recovery & Obligation Engine"
        ],
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main.app", host="127.0.0.1", port=8000, reload=True)
