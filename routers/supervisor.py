"""
FastAPI router for Supervisor Graph endpoints (LangGraph-based)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.supervisor_graph import create_supervisor_graph, create_supervisor_graph_simple
from config.settings import settings

router = APIRouter(prefix="/supervisor", tags=["Supervisor"])

# Initialize model and graph (singleton pattern for reuse)
_model = None
_graph = None
_graph_simple = None


def get_graph():
    """Get or create the supervisor graph (with formatting)."""
    global _model, _graph
    if _graph is None:
        _model = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )
        _graph = create_supervisor_graph(_model)
    return _graph


def get_graph_simple():
    """Get or create the simple supervisor graph (without formatting)."""
    global _model, _graph_simple
    if _graph_simple is None:
        if _model is None:
            _model = ChatGoogleGenerativeAI(
                model=settings.DEFAULT_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        _graph_simple = create_supervisor_graph_simple(_model)
    return _graph_simple


def transform_to_mobile_format(result: dict) -> dict:
    """
    Transform graph result to mobile-optimized format.
    
    Extracts only essential data for mobile app:
    - Google Place IDs with sequence numbers
    - Day assignments
    - Minimal trip summary
    
    Args:
        result: Full graph execution result
        
    Returns:
        Mobile-optimized response dictionary
    """
    pois_sequence = []
    
    itinerary = result.get("itinerary", {})
    daily_plans = itinerary.get("daily_itinerary", [])
    
    # Extract POIs with sequence numbers
    for day_plan in daily_plans:
        for poi in day_plan.get("pois", []):
            # Validate Google Place ID exists
            place_id = poi.get("google_place_id")
            if place_id is None:
                # Handle POIs without Google Place ID (skip or use alternative ID)
                place_id = f"unknown_{poi.get('global_sequence', 0)}"
            
            pois_sequence.append({
                "google_place_id": place_id,
                "sequence_number": poi.get("global_sequence", poi.get("sequence_no", 0)),
                "day": poi.get("day", day_plan.get("day", 1)),
                "name": poi.get("google_matched_name") or poi.get("name", "Unknown POI")
            })
    
    return {
        "success": True,
        "trip_summary": {
            "destination": result.get("destination_state"),
            "duration_days": result.get("trip_duration_days"),
            "travelers": result.get("num_travelers"),
            "preferences": result.get("user_preferences", []),
            "centroid_name": itinerary.get("centroid", {}).get("name")
        },
        "pois_sequence": pois_sequence,
        "total_pois": len(pois_sequence),
        "total_distance_km": round(itinerary.get("total_distance_km", 0.0), 2),
        "error_message": result.get("error_message")
    }


class TripPlanningRequest(BaseModel):
    """Request for complete trip planning"""
    destination_state: str = Field(..., description="Target state (e.g., 'Penang', 'Kuala Lumpur')")
    user_preferences: List[str] = Field(..., description="User interest categories")
    number_of_travelers: int = Field(..., ge=1, description="Number of travelers")
    trip_duration_days: int = Field(..., ge=1, description="Trip duration in days")
    preferred_poi_names: Optional[List[str]] = Field(default=None, description="Specific POI names user wants to visit")
    max_pois_per_day: int = Field(default=6, ge=3, le=10, description="Maximum POIs per day")
    
    class Config:
        json_schema_extra = {
            "example": {
                "destination_state": "Penang",
                "user_preferences": ["Food", "Culture", "Art"],
                "number_of_travelers": 2,
                "trip_duration_days": 3,
                "preferred_poi_names": ["Kek Lok Si Temple", "Penang Hill"],
                "max_pois_per_day": 6
            }
        }


class NaturalLanguageRequest(BaseModel):
    """Natural language trip planning request"""
    query: str = Field(..., description="Natural language trip planning request")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Plan a 3-day trip to Penang for 2 people who love food and culture. Must visit Kek Lok Si Temple."
            }
        }


class MobilePOI(BaseModel):
    """Lightweight POI data structure for mobile app"""
    google_place_id: Optional[str] = Field(..., description="Google Place ID for fetching POI details")
    sequence_number: int = Field(..., description="Global sequence number (1-N) for entire trip")
    day: int = Field(..., description="Day number of the trip")
    name: str = Field(..., description="POI name for reference")


class MobileItineraryResponse(BaseModel):
    """Mobile-optimized trip itinerary response"""
    success: bool
    trip_summary: dict = Field(..., description="Trip overview information")
    pois_sequence: List[MobilePOI] = Field(..., description="Sequential list of POIs with place IDs")
    total_pois: int = Field(..., description="Total number of POIs in itinerary")
    total_distance_km: float = Field(..., description="Total travel distance in kilometers")
    error_message: Optional[str] = Field(default=None, description="Error message if any")


@router.post("/plan-trip")
async def plan_trip(request: TripPlanningRequest):
    """
    Complete trip planning using supervisor graph.
    
    The graph will:
    1. Parse the structured request
    2. Get POI recommendations from Recommender Node
    3. Create optimal itinerary from Planner Node
    4. Return complete trip plan with routes and sequences (no formatting)
    """
    try:
        # Get simple graph (without formatting for API)
        graph = get_graph_simple()
        
        # Construct natural language query
        query = f"""
        Plan a {request.trip_duration_days}-day trip to {request.destination_state} for {request.number_of_travelers} people.
        
        User interests: {', '.join(request.user_preferences)}
        """
        
        if request.preferred_poi_names:
            query += f"\nMust visit: {', '.join(request.preferred_poi_names)}"
        
        # Invoke graph
        result = graph.invoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": "api_plan_trip"}}
        )
        
        # Extract structured data
        return {
            "success": True,
            "trip_context": {
                "destination_state": result.get("destination_state"),
                "trip_duration_days": result.get("trip_duration_days"),
                "num_travelers": result.get("num_travelers"),
                "user_preferences": result.get("user_preferences"),
            },
            "recommendations": {
                "top_priority_pois": result.get("top_priority_pois", []),
                "activity_mix": result.get("activity_mix", {}),
                "summary": result.get("recommendations", {}).get("summary_reasoning")
            },
            "itinerary": result.get("itinerary"),
            "error_message": result.get("error_message")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan-trip/mobile", response_model=MobileItineraryResponse)
async def plan_trip_mobile(request: TripPlanningRequest):
    """
    Mobile-optimized trip planning endpoint.
    
    Returns minimal data structure optimized for mobile app consumption:
    - Google Place IDs with global sequence numbers (1-N across entire trip)
    - Day assignments for each POI
    - Trip summary metadata
    - Total distance and POI count
    
    The mobile app can use google_place_id to fetch full POI details
    from Google Places API as needed.
    
    Response is significantly smaller than /plan-trip endpoint.
    """
    try:
        # Get simple graph (without formatting for API)
        graph = get_graph_simple()
        
        # Construct natural language query
        query = f"""
        Plan a {request.trip_duration_days}-day trip to {request.destination_state} for {request.number_of_travelers} people.
        
        User interests: {', '.join(request.user_preferences)}
        """
        
        if request.preferred_poi_names:
            query += f"\nMust visit: {', '.join(request.preferred_poi_names)}"
        
        # Invoke graph
        result = graph.invoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": "api_mobile_plan"}}
        )
        
        # Transform to mobile-optimized format
        mobile_response = transform_to_mobile_format(result)
        
        return mobile_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_with_supervisor(request: NaturalLanguageRequest):
    """
    Natural language chat with supervisor graph.
    
    The graph understands various requests:
    - Complete trip planning
    - Just recommendations
    - Specific questions about destinations
    
    Returns a formatted, user-friendly response.
    """
    try:
        # Get full graph (with formatting)
        graph = get_graph()
        
        # Invoke graph
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.query)]},
            config={"configurable": {"thread_id": "api_chat"}}
        )
        
        # Extract final formatted message
        if result and result.get("messages"):
            final_message = result["messages"][-1]
            return {
                "success": True,
                "response": final_message.content,
                "trip_context": {
                    "destination_state": result.get("destination_state"),
                    "trip_duration_days": result.get("trip_duration_days"),
                    "num_travelers": result.get("num_travelers"),
                }
            }
        
        return {"success": False, "error": "No response from supervisor graph"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_supervisor_capabilities():
    """
    Get supervisor graph capabilities and node descriptions.
    """
    return {
        "success": True,
        "architecture": "LangGraph StateGraph",
        "supervisor": {
            "name": "Malaysia Travel Planning Supervisor Graph",
            "description": "LangGraph-based orchestration of specialized nodes for complete trip planning",
            "pattern": "Deterministic node routing with conditional edges"
        },
        "nodes": [
            {
                "name": "Input Parser",
                "description": "Parses natural language into structured trip context",
                "outputs": ["destination_state", "user_preferences", "trip_duration_days", "num_travelers"]
            },
            {
                "name": "Recommender",
                "description": "Generates personalized POI recommendations",
                "capabilities": [
                    "Load POIs from database",
                    "Calculate priority scores based on user context",
                    "Apply preference matching and contextual boosts",
                    "Generate activity mix analysis"
                ]
            },
            {
                "name": "Planner",
                "description": "Creates optimal travel routes and itineraries",
                "capabilities": [
                    "Select optimal centroid (starting POI)",
                    "Calculate distances using haversine formula",
                    "Cluster POIs by proximity (30km threshold)",
                    "Generate optimal sequences via nearest-neighbor",
                    "Split into day-by-day routing"
                ]
            },
            {
                "name": "Response Formatter",
                "description": "Formats results into user-friendly output",
                "outputs": ["formatted trip overview", "activity breakdown", "day-by-day itinerary"]
            }
        ],
        "workflow": [
            "1. START → Input Parser: Extract trip context from user query",
            "2. Input Parser → Recommender: Generate POI recommendations",
            "3. Recommender → Planner: Create optimized itinerary",
            "4. Planner → Response Formatter: Format final output",
            "5. Response Formatter → END: Return to user"
        ],
        "state_schema": {
            "messages": "Conversation history (auto-appended)",
            "destination_state": "Target Malaysian state",
            "user_preferences": "List of interest categories",
            "num_travelers": "Group size",
            "trip_duration_days": "Trip length",
            "top_priority_pois": "Recommended POIs with scores",
            "activity_mix": "Category distribution",
            "itinerary": "Complete day-by-day plan",
            "next_step": "Control flow routing"
        },
        "example_requests": [
            "Plan a 3-day trip to Penang for 2 people who love food and culture",
            "Recommend POIs in Kuala Lumpur for a family of 5 with adventure interests",
            "Create a 2-day itinerary in Malacca focused on history, must visit A Famosa"
        ]
    }
