"""
Simple FastAPI app for testing Planner Agent
Run with: python test_planner_api.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers.planner import router as planner_router

# Create FastAPI app
app = FastAPI(
    title="Planner Agent Test API",
    description="Test endpoints for Planner Agent tools",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include planner router
app.include_router(planner_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Planner Agent Test API",
        "status": "online",
        "endpoints": {
            "select_centroid": "POST /planner/select-centroid",
            "calculate_distance": "POST /planner/calculate-distance",
            "cluster_pois": "POST /planner/cluster-pois",
            "generate_sequence": "POST /planner/generate-sequence",
            "plan_itinerary": "POST /planner/plan-itinerary (Complete workflow)",
            "nearby_pois": "GET /planner/nearby-pois/{place_id}"
        },
        "docs": "http://localhost:8001/docs"
    }


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🗺️  PLANNER AGENT TEST API")
    print("="*80)
    print("\n📍 Server: http://localhost:8001")
    print("📚 Docs: http://localhost:8001/docs")
    print("\nAvailable Endpoints:")
    print("  • POST /planner/select-centroid - Select best centroid")
    print("  • POST /planner/calculate-distance - Distance between 2 POIs")
    print("  • POST /planner/cluster-pois - Cluster by distance")
    print("  • POST /planner/generate-sequence - Optimal sequence")
    print("  • POST /planner/plan-itinerary - Complete workflow ⭐")
    print("  • GET /planner/nearby-pois/{place_id} - Find nearby POIs")
    print("\n" + "="*80 + "\n")
    
    uvicorn.run(
        "test_planner_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
