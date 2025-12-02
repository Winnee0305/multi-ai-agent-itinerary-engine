"""
FastAPI router for Recommender Agent endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# FIXED: Import the Logic Functions, not the Tools
from tools.recommender_tools import (
    load_pois_from_database,
    recommend_pois_for_trip_logic, # Note: This name changed in the refactor
    INTEREST_CATEGORIES
)

router = APIRouter(prefix="/recommender", tags=["Recommender"])


# Request/Response Models
class RecommendationRequest(BaseModel):
    """Request for trip recommendations"""
    destination_state: str = Field(..., description="Target state (e.g., 'Penang', 'Kuala Lumpur')")
    user_preferences: List[str] = Field(..., description="User interest categories")
    number_of_travelers: int = Field(..., ge=1, description="Number of travelers")
    trip_duration_days: int = Field(..., ge=1, description="Trip duration in days")
    preferred_poi_names: Optional[List[str]] = Field(default=None, description="Specific POI names user wants to visit")
    top_n: int = Field(default=50, ge=1, le=100, description="Number of top POIs to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "destination_state": "Penang",
                "user_preferences": ["Food", "Culture", "Art"],
                "number_of_travelers": 2,
                "trip_duration_days": 3,
                "preferred_poi_names": ["Kek Lok Si Temple", "Penang Hill"],
                "top_n": 50
            }
        }


class LoadPOIsRequest(BaseModel):
    """Request to load POIs from database"""
    state: Optional[str] = Field(default=None, description="Filter by state name")
    golden_only: bool = Field(default=True, description="Only return golden list POIs")
    min_popularity: int = Field(default=50, ge=0, description="Minimum popularity score")


@router.post("/recommend")
async def get_recommendations(request: RecommendationRequest):
    """
    Get complete trip recommendations with priority-scored POIs.
    """
    try:
        # FIXED: Call the function directly (No .invoke, no config needed here)
        result = recommend_pois_for_trip_logic(
            destination_state=request.destination_state,
            user_preferences=request.user_preferences,
            number_of_travelers=request.number_of_travelers,
            trip_duration_days=request.trip_duration_days,
            preferred_poi_names=request.preferred_poi_names,
            top_n=request.top_n
        )
        
        # Check for error in result dict
        if "error" in result:
             return {"success": False, "error": result["error"]}

        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-pois")
async def load_pois(request: LoadPOIsRequest):
    """
    Load POIs from Supabase database with filters.
    """
    try:
        # FIXED: Call the function directly
        pois = load_pois_from_database(
            state=request.state,
            golden_only=request.golden_only,
            min_popularity=request.min_popularity
        )
        
        return {
            "success": True,
            "count": len(pois),
            "pois": pois
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/states")
async def get_available_states():
    """
    Get list of available states in the database.
    """
    try:
        # FIXED: Call the function directly
        # We load all POIs to extract unique states
        all_pois = load_pois_from_database(
            state=None,
            golden_only=True,
            min_popularity=0
        )
        
        # Extract unique states
        states = sorted(list(set([poi.get("state") for poi in all_pois if poi.get("state")])))
        
        return {
            "success": True,
            "states": states,
            "count": len(states)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interest-categories")
async def get_interest_categories():
    """
    Get available interest categories for user preferences.
    """
    # FIXED: Imported INTEREST_CATEGORIES at the top of the file
    
    return {
        "success": True,
        "categories": list(INTEREST_CATEGORIES.keys()),
        "category_details": {
            category: types 
            for category, types in INTEREST_CATEGORIES.items()
        }
    }