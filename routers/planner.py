"""
FastAPI router for Planner Agent endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from tools.planner_tools import (
    select_best_centroid,
    calculate_distances_from_centroid,
    cluster_pois_by_distance,
    generate_optimal_sequence,
    get_pois_near_centroid,
    calculate_distance_between_pois,
    plan_itinerary_logic
)

router = APIRouter(prefix="/planner", tags=["Planner"])


# Request/Response Models
class PriorityPOI(BaseModel):
    """POI with priority score"""
    google_place_id: str
    name: str
    priority_score: float
    lat: float
    lon: float
    state: Optional[str] = None


class SelectCentroidRequest(BaseModel):
    """Request to select centroid"""
    priority_pois: List[PriorityPOI]
    consider_top_n: int = Field(default=5, description="Consider top N POIs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "priority_pois": [
                    {
                        "google_place_id": "ChIJ123",
                        "name": "George Town",
                        "priority_score": 95.5,
                        "lat": 5.4164,
                        "lon": 100.3327,
                        "state": "Penang"
                    }
                ],
                "consider_top_n": 5
            }
        }


class CalculateDistanceRequest(BaseModel):
    """Request to calculate distance between two POIs"""
    place_id_1: str
    place_id_2: str


class ClusterPOIsRequest(BaseModel):
    """Request to cluster POIs by distance"""
    centroid_place_id: str
    poi_list: List[Dict[str, Any]]
    max_distance_meters: int = Field(default=30000, description="30km default")


class GenerateSequenceRequest(BaseModel):
    """Request to generate optimal sequence"""
    start_place_id: str
    poi_place_ids: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_place_id": "ChIJ123",
                "poi_place_ids": ["ChIJ456", "ChIJ789", "ChIJ012"]
            }
        }


class PlanItineraryRequest(BaseModel):
    """Complete itinerary planning request"""
    priority_pois: List[PriorityPOI] = Field(..., description="POIs sorted by priority score")
    trip_duration_days: int = Field(default=1, ge=1, description="Number of days for the trip")
    max_pois_per_day: int = Field(default=6, description="Max POIs to visit per day")
    max_distance_meters: int = Field(default=30000, description="Clustering distance threshold")
    clustering_strategy: str = Field(default="kmeans", description="Day splitting strategy: 'simple' or 'kmeans'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "priority_pois": [
                    {
                        "google_place_id": "ChIJ123",
                        "name": "George Town",
                        "priority_score": 95.5,
                        "lat": 5.4164,
                        "lon": 100.3327,
                        "state": "Penang"
                    }
                ],
                "trip_duration_days": 3,
                "max_pois_per_day": 6,
                "max_distance_meters": 30000,
                "clustering_strategy": "kmeans"
            }
        }


# Endpoints

@router.post("/select-centroid")
async def select_centroid_endpoint(request: SelectCentroidRequest):
    """
    Select the best centroid from top priority POIs.
    
    Returns the POI with highest priority score as centroid.
    """
    try:

        config = {"configurable": {"thread_id": "select-centroid-001"}}

        priority_pois_list = [poi.model_dump() for poi in request.priority_pois]
        
        centroid = select_best_centroid.invoke({
            "top_priority_pois": priority_pois_list,
            "consider_top_n": request.consider_top_n
        }, config = config)
        
        return {
            "success": True,
            "centroid": centroid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting centroid: {str(e)}")


@router.post("/calculate-distance")
async def calculate_distance_endpoint(request: CalculateDistanceRequest):
    """
    Calculate distance between two POIs using PostGIS.
    
    Returns distance in meters.
    """
    try:

        config = {"configurable": {"thread_id": "calculate-distance-001"}}

        distance = calculate_distance_between_pois.invoke({
            "place_id_1": request.place_id_1,
            "place_id_2": request.place_id_2
        }, config = config)
        
        if distance == -1.0:
            raise HTTPException(status_code=404, detail="One or both POIs not found")
        
        return {
            "success": True,
            "distance_meters": distance,
            "distance_km": round(distance / 1000, 2)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating distance: {str(e)}")


@router.post("/cluster-pois")
async def cluster_pois_endpoint(request: ClusterPOIsRequest):
    """
    Cluster POIs into 'nearby' and 'far' based on distance from centroid.
    
    Uses PostGIS to calculate distances.
    """
    try:

        config = {"configurable": {"thread_id": "cluster-pois-001"}}

        clusters = cluster_pois_by_distance.invoke({
            "centroid_place_id": request.centroid_place_id,
            "poi_list": request.poi_list,
            "max_distance_meters": request.max_distance_meters
        }, config = config)
        
        return {
            "success": True,
            "clusters": clusters,
            "summary": {
                "nearby_count": clusters.get("nearby_count", 0),
                "far_count": clusters.get("far_count", 0),
                "threshold_km": request.max_distance_meters / 1000
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clustering POIs: {str(e)}")


@router.post("/generate-sequence")
async def generate_sequence_endpoint(request: GenerateSequenceRequest):
    """
    Generate optimal visit sequence using nearest neighbor algorithm.
    
    Returns sequenced itinerary with distances.
    """
    try:

        config = {"configurable": {"thread_id": "generate-sequence-001"}}

        sequence = generate_optimal_sequence.invoke({
            "poi_place_ids": request.poi_place_ids,
            "start_place_id": request.start_place_id
        }, config = config)
        
        # Calculate total distance
        total_distance = sum(
            item.get("distance_from_previous_meters", 0) 
            for item in sequence
        )
        
        return {
            "success": True,
            "sequence": sequence,
            "summary": {
                "total_pois": len(sequence),
                "total_distance_meters": total_distance,
                "total_distance_km": round(total_distance / 1000, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sequence: {str(e)}")


@router.post("/plan-itinerary")
async def plan_itinerary_endpoint(request: PlanItineraryRequest):
    """
    Complete itinerary planning workflow with multi-day support:
    1. Select centroid from top priority POIs
    2. Cluster POIs by distance (nearby vs far)
    3. Generate optimal sequence
    4. Split into daily itineraries using k-means or simple strategy
    
    Returns complete multi-day sequenced itinerary.
    """
    try:
        priority_pois_list = [poi.model_dump() for poi in request.priority_pois]
        
        # Call the orchestrator logic directly
        result = plan_itinerary_logic(
            priority_pois=priority_pois_list,
            trip_duration_days=request.trip_duration_days,
            max_pois_per_day=request.max_pois_per_day,
            max_distance_threshold=request.max_distance_meters,
            clustering_strategy=request.clustering_strategy
        )
        
        # Check for errors
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning itinerary: {str(e)}")


@router.get("/nearby-pois/{place_id}")
async def get_nearby_pois_endpoint(
    place_id: str,
    radius_meters: int = 50000,
    max_results: int = 20
):
    """
    Get POIs near a specific location using PostGIS spatial query.
    
    Args:
        place_id: Google Place ID of center point
        radius_meters: Search radius in meters (default 50km)
        max_results: Maximum number of results (default 20)
    """
    try:

        config = {"configurable": {"thread_id": "nearby-pois-001"}}

        nearby = get_pois_near_centroid.invoke({
            "centroid_place_id": place_id,
            "radius_meters": radius_meters,
            "max_results": max_results
        }, config = config)
        
        return {
            "success": True,
            "center_place_id": place_id,
            "radius_km": radius_meters / 1000,
            "pois": nearby,
            "count": len(nearby)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding nearby POIs: {str(e)}")
