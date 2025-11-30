"""
Multi-Agent Itinerary Engine - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import planner

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Itinerary Engine",
    description="AI-powered travel itinerary planning system with multiple specialized agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(planner.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multi-Agent Itinerary Engine API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "planner": "/planner/*"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
