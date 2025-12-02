"""
FastAPI router for Supervisor Agent endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from agents.supervisor_agent import supervisor_agent

router = APIRouter(prefix="/supervisor", tags=["Supervisor"])


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


@router.post("/plan-trip")
async def plan_trip(request: TripPlanningRequest):
    """
    Complete trip planning using supervisor agent.
    
    The supervisor will:
    1. Get POI recommendations from Recommender Agent
    2. Create optimal itinerary from Planner Agent
    3. Return complete trip plan with routes and sequences
    """
    try:

        config = {"thread_id": "supervisor-plan-trip-001"}
        
        # Construct natural language query for supervisor
        query = f"""
        Plan a {request.trip_duration_days}-day trip to {request.destination_state} for {request.number_of_travelers} people.
        
        User interests: {', '.join(request.user_preferences)}
        """
        
        if request.preferred_poi_names:
            query += f"\nMust visit: {', '.join(request.preferred_poi_names)}"
        
        query += f"\nMax POIs per day: {request.max_pois_per_day}"
        
        # Invoke supervisor agent
        result = supervisor_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config = config
        )
        
        # Extract final response
        if result and "messages" in result:
            final_message = result["messages"][-1]
            return {
                "success": True,
                "response": final_message.content if hasattr(final_message, "content") else str(final_message)
            }
        
        return {"success": False, "error": "No response from supervisor agent"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_with_supervisor(request: NaturalLanguageRequest):
    """
    Natural language chat with supervisor agent.
    
    The supervisor understands various requests:
    - Complete trip planning
    - Just recommendations
    - Just route planning
    - Specific questions about destinations
    """
    try:

        config = {"thread_id": "supervisor-chat-001"}

        # Invoke supervisor agent
        result = supervisor_agent.invoke(
            {"messages": [{"role": "user", "content": request.query}]},
            config = config
        )
        
        # Extract final response
        if result and "messages" in result:
            final_message = result["messages"][-1]
            return {
                "success": True,
                "response": final_message.content if hasattr(final_message, "content") else str(final_message)
            }
        
        return {"success": False, "error": "No response from supervisor agent"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_supervisor_capabilities():
    """
    Get supervisor agent capabilities and available sub-agents.
    """
    return {
        "success": True,
        "supervisor": {
            "name": "Malaysia Travel Planning Supervisor",
            "description": "Coordinates specialized agents for complete trip planning"
        },
        "sub_agents": [
            {
                "name": "Recommender Agent",
                "tool": "get_poi_recommendations",
                "description": "Gets personalized POI recommendations based on user preferences",
                "capabilities": [
                    "Load POIs from database",
                    "Calculate priority scores",
                    "Apply user preference filters",
                    "Generate activity mix analysis"
                ]
            },
            {
                "name": "Planner Agent",
                "tool": "plan_itinerary",
                "description": "Creates optimal travel routes and day-by-day itineraries",
                "capabilities": [
                    "Select optimal centroid (anchor POI)",
                    "Calculate distances using PostGIS",
                    "Cluster POIs by proximity",
                    "Generate optimal sequences",
                    "Create day-by-day routing"
                ]
            }
        ],
        "workflow": [
            "1. User provides trip requirements",
            "2. Supervisor calls Recommender Agent for POI recommendations",
            "3. Supervisor calls Planner Agent for route optimization",
            "4. Supervisor combines results and presents complete itinerary"
        ],
        "example_requests": [
            "Plan a 3-day trip to Penang for 2 people who love food and culture",
            "Recommend POIs in Kuala Lumpur for a family of 5",
            "Create a 2-day itinerary in Malacca focused on history"
        ]
    }
