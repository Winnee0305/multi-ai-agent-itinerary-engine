"""
FastAPI router for Supervisor Graph endpoints (LangGraph-based)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
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


def _generate_reason_from_poi(poi: dict, user_preferences: list, llm=None) -> str:
    """Generate a meaningful reason using LLM based on POI metadata."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    
    # Check if preferred
    if poi.get("is_preferred"):
        return "Your preferred must-visit location."
    
    poi_name = poi.get("name", "")
    poi_types = poi.get("google_types", [])
    rating = poi.get("google_rating", 0)
    reviews = poi.get("google_reviews", 0)
    
    # Handle both list and string formats for google_types
    if isinstance(poi_types, str):
        poi_types = [poi_types]
    
    # Build context for LLM
    context = f"POI: {poi_name}\n"
    if poi_types:
        context += f"Type: {poi_types[0]}\n"
    if rating:
        context += f"Rating: {rating:.1f}★\n"
    if user_preferences:
        context += f"User interests: {', '.join(user_preferences)}"
    
    try:
        # Reuse provided LLM instance or create new one
        if llm is None:
            llm = ChatGoogleGenerativeAI(
                model=settings.DEFAULT_LLM_MODEL,
                temperature=0.5,
                timeout=3  # Increased timeout to handle slower models
            )
    
        prompt = f"""In one short sentence (max 12 words), explain why this POI is worth visiting.

{context}

Requirements:
- Specific and engaging based on type
- Do not include the POI name
- No period at end

Reason:"""
        
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        reason = response.content.strip().rstrip('.')
        
        if reason and len(reason) > 3:
            return reason
    except Exception as e:
        print(f"LLM reason generation failed for {poi_name}: {e}")
    
    # Smart fallback: Use type first, then name patterns
    # This ensures we get meaningful reasons even if LLM fails
    
    poi_types_str = " ".join([str(t).lower() for t in poi_types])
    poi_name_lower = poi_name.lower()
    
    # Primary: Type-based mapping
    type_map = {
        "temple": "Important cultural and historical landmark",
        "mosque": "Iconic place of worship with architectural significance",
        "church": "Historic religious site worth visiting",
        "restaurant": "Popular dining destination with local cuisine",
        "cafe": "Great spot for coffee and local ambiance",
        "market": "Local market offering authentic products",
        "park": "Beautiful natural space for relaxation",
        "waterfall": "Natural wonder with spectacular water views",
        "mountain": "Scenic peak with panoramic views",
        "museum": "Museum showcasing art, history, or culture",
        "hiking": "Scenic hiking trail for nature lovers",
        "beach": "Scenic coastal destination for beach activities",
        "garden": "Beautiful garden destination showcasing flora",
        "shrine": "Sacred religious site with cultural value",
        "viewpoint": "Stunning viewpoint with panoramic views",
        "gurdwara": "Important Sikh place of worship",
        "memorial": "Historical memorial site with cultural significance",
        "monument": "Notable monument with historical importance",
        "gallery": "Gallery featuring local and contemporary art",
    }
    
    # Check types first (primary fallback)
    for type_key, reason in type_map.items():
        if type_key in poi_types_str:
            if rating >= 4.5:
                return f"{reason} (Rated {rating:.1f}★)"
            return reason
    
    # Secondary: Name-based patterns
    name_patterns = {
        "garden": "Beautiful garden showcasing local flora",
        "temple": "Sacred site with cultural and architectural value",
        "shrine": "Sacred site with cultural and architectural value",
        "waterfall": "Scenic waterfall with stunning natural beauty",
        "fall": "Scenic waterfall with stunning natural beauty",
        "market": "Traditional market with authentic local products",
        "bazaar": "Traditional bazaar with local crafts",
        "gurdwara": "Important Sikh place of worship",
        "curry house": "Authentic local dining with traditional cuisine",
        "restaurant": "Authentic local dining establishment",
        "valley": "Scenic valley offering beautiful landscape",
        "cafe": "Cozy café with local ambiance",
        "coffee": "Cozy café with coffee and local atmosphere",
        "gunung": "Mountain peak with scenic hiking trails",
        "mountain": "Mountain peak with scenic hiking trails",
        "peak": "Mountain peak with scenic views",
        "house": "Local destination worth exploring",
    }
    
    for pattern_key, reason in name_patterns.items():
        if pattern_key in poi_name_lower:
            return reason
    
    # Tertiary: Rating-based fallback
    if rating and rating >= 4.7 and reviews and reviews >= 100:
        return f"Top-rated attraction ({rating:.1f}★ from {reviews}+ reviews)"
    elif rating and rating >= 4.7:
        return f"Highly-rated destination ({rating:.1f}★)"
    elif rating and rating >= 4.0:
        return f"Well-reviewed destination ({rating:.1f}★)"
    
    # Final fallback
    return "Popular local attraction worth visiting"


def transform_to_mobile_format(result: dict) -> dict:
    """
    Transform graph result to mobile-optimized format.
    
    Extracts only essential data for mobile app:
    - Google Place IDs with global sequence numbers (1-N across entire trip)
    - Day assignments
    - Preferred POI flags
    - Minimal trip summary
    - Meaningful recommendation reasons based on POI descriptions
    
    Args:
        result: Full graph execution result with itinerary.daily_itinerary structure
        
    Returns:
        Mobile-optimized response dictionary
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    pois_sequence = []
    
    itinerary = result.get("itinerary", {})
    daily_plans = itinerary.get("daily_itinerary", [])
    user_preferences = result.get("user_preferences", [])
    
    # Create single LLM instance for all POIs (more efficient)
    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=0.5,
            timeout=20
        )
    except Exception:
        llm = None
    
    # Extract POIs with sequence numbers that restart each day
    for day_plan in daily_plans:
        day_number = day_plan.get("day", 1)
        day_sequence = 1  # Reset sequence for each day
        
        for poi in day_plan.get("pois", []):
            # Validate Google Place ID exists
            place_id = poi.get("google_place_id")
            if not place_id:
                # Skip POIs without valid Google Place ID
                continue
            
            # Generate meaningful reason based on POI data
            reason = _generate_reason_from_poi(poi, user_preferences, llm)
            
            pois_sequence.append({
                "google_place_id": place_id,
                "sequence_number": day_sequence,
                "osm_type": poi.get("osm_type", "N/A"),
                "day": poi.get("day", day_number),
                "name": poi.get("google_matched_name") or poi.get("name", "Unknown POI"),
                "is_preferred": poi.get("is_preferred", False),
                "distance_from_previous_meters": poi.get("distance_from_previous_meters", 0),
                "recommendation_reason": reason
            })
            
            day_sequence += 1
    
    # Calculate trip summary stats
    trip_summary = itinerary.get("trip_summary", {})
    
    return {
        "success": True,
        "trip_summary": {
            "destination": result.get("destination_state"),
            "duration_days": result.get("trip_duration_days"),
            "travelers": result.get("num_travelers"),
            "preferences": result.get("user_preferences", []),
            "centroid_name": itinerary.get("centroid", {}).get("name"),
            "preferred_pois_requested": trip_summary.get("preferred_pois_requested", 0),
            "preferred_pois_included": trip_summary.get("preferred_pois_included", 0)
        },
        "pois_sequence": pois_sequence,
        "total_pois": len(pois_sequence),
        "total_distance_km": round(itinerary.get("total_distance_km", 0.0), 2),
        "clustering_strategy": itinerary.get("clustering_strategy", "anchor_based"),
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
                "destination_state": "Pahang",
                "user_preferences": ["Food", "Culture", "Art", "Nature"],
                "number_of_travelers": 2,
                "trip_duration_days": 7,
                "preferred_poi_names": ["Cameron Highlands", "Lavender Garden"],
                "max_pois_per_day": 4
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
    google_place_id: str = Field(..., description="Google Place ID for fetching POI details")
    sequence_number: int = Field(..., description="Global sequence number (1-N) for entire trip")
    day: int = Field(..., description="Day number of the trip")
    name: str = Field(..., description="POI name for reference")
    is_preferred: bool = Field(default=False, description="User explicitly requested this POI")
    distance_from_previous_meters: float = Field(default=0, description="Distance from previous POI in sequence")
    recommendation_reason: str = Field(default="", description="Why this POI is recommended based on description and context")


class MobileItineraryResponse(BaseModel):
    """Mobile-optimized trip itinerary response"""
    success: bool
    trip_summary: dict = Field(..., description="Trip overview information including preferred POI stats")
    pois_sequence: List[MobilePOI] = Field(..., description="Sequential list of POIs with place IDs (1-N across entire trip)")
    total_pois: int = Field(..., description="Total number of POIs in itinerary")
    total_distance_km: float = Field(..., description="Total travel distance in kilometers")
    clustering_strategy: str = Field(default="anchor_based", description="Clustering strategy used (simple or kmeans)")
    error_message: Optional[str] = Field(default=None, description="Error message if any")


@router.post("/plan-trip")
async def plan_trip(request: TripPlanningRequest):
    """
    Complete trip planning using supervisor graph.
    
    The graph will:
    1. Parse the structured request (bypasses LLM parser for reliability)
    2. Get POI recommendations from Recommender Node
    3. Create optimal itinerary from Planner Node
    4. Return complete trip plan with routes and sequences (no formatting)
    
    Direct state population ensures preferred POIs are never lost in translation.
    """
    try:
        # Get simple graph (without formatting for API)
        graph = get_graph_simple()
        
        # FIXED: For structured API requests, populate state directly instead of using LLM parser
        # This ensures preferred_poi_names are not lost in LLM translation
        initial_state = {
            "messages": [HumanMessage(content=f"Plan a {request.trip_duration_days}-day trip to {request.destination_state}")],
            "destination_state": request.destination_state,
            "user_preferences": request.user_preferences,
            "num_travelers": request.number_of_travelers,
            "trip_duration_days": request.trip_duration_days,
            "preferred_pois": request.preferred_poi_names,  # Direct mapping - no LLM parsing needed
            "max_pois_per_day": request.max_pois_per_day,
            "next_step": "recommend"  # Skip input parser, go straight to recommender
        }
        
        # Invoke graph with pre-populated state
        result = graph.invoke(
            initial_state,
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
                "preferred_pois": result.get("preferred_pois"),
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
    Mobile-optimized trip planning endpoint with preferred POI support.
    
    Returns minimal data structure optimized for mobile app consumption:
    - Google Place IDs with global sequence numbers (1-N across entire trip)
    - Day assignments for each POI (handles multi-day trips)
    - Preferred POI flags (is_preferred: true for user-requested POIs)
    - Distance from previous POI in sequence
    - Trip summary with preferred POI inclusion stats
    - Anchor-based clustering for optimal day splitting with guaranteed preferred POI inclusion
    
    The mobile app can use google_place_id to fetch full POI details
    from Google Places API as needed.
    
    Features:
    - Ensures preferred POIs are included in final itinerary (100% inclusion rate)
    - Uses anchor-based clustering where preferred POIs define the trip skeleton
    - Handles trips with more days than available POIs (flexible days)
    - Response is significantly smaller than /plan-trip endpoint
    - Direct state population bypasses LLM parsing for reliability
    """
    try:
        # Get simple graph (without formatting for API)
        graph = get_graph_simple()
        
        # FIXED: For structured API requests, populate state directly instead of using LLM parser
        # This ensures preferred_poi_names are not lost in LLM translation
        initial_state = {
            "messages": [HumanMessage(content=f"Plan a {request.trip_duration_days}-day trip to {request.destination_state}")],
            "destination_state": request.destination_state,
            "user_preferences": request.user_preferences,
            "num_travelers": request.number_of_travelers,
            "trip_duration_days": request.trip_duration_days,
            "preferred_pois": request.preferred_poi_names,  # Direct mapping - no LLM parsing needed
            "max_pois_per_day": request.max_pois_per_day,
            "next_step": "recommend"  # Skip input parser, go straight to recommender
        }
        
        # Invoke graph with pre-populated state
        result = graph.invoke(
            initial_state,
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
    
    Supports two modes:
    1. Trip Planning: If user asks for trip plans, hotels, POIs, etc.
       → Routes through full planning workflow
    2. General Chat: Simple greetings, questions about Malaysia, etc.
       → Returns conversational response via LLM
    
    The graph intelligently detects planning vs. chat requests.
    """
    try:
        # Get shared model instance
        global _model
        if _model is None:
            _model = ChatGoogleGenerativeAI(
                model=settings.DEFAULT_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE
            )
        
        query_lower = request.query.lower().strip()
        
        # Quick check: Is this a planning request or general chat?
        planning_keywords = [
            "plan", "trip", "itinerary", "recommend", "poi", "visit", "days",
            "hotel", "where to", "what to do", "travel", "vacation", "tour",
            "attractions", "things to do", "must visit", "best", "explore",
            "destination", "state", "duration"
        ]
        
        is_planning_request = any(keyword in query_lower for keyword in planning_keywords)
        
        if not is_planning_request and len(query_lower) < 30:
            # This looks like general chat - respond conversationally without planning
            response = _model.invoke([
                SystemMessage(content="You are a friendly Malaysia tourism assistant. Answer questions conversationally and warmly. Keep responses concise (2-3 sentences)."),
                HumanMessage(content=request.query)
            ])
            
            return {
                "success": True,
                "response": response.content,
                "mode": "conversational",
                "trip_context": None
            }
        
        # Otherwise, route through planning workflow
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
                "mode": "planning",
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


class PackingListRequest(BaseModel):
    """Request for smart packing list generation"""
    daily_itineraries: List[dict] = Field(..., description="Daily itinerary plans from planner")
    trip_duration_days: int = Field(..., ge=1, description="Trip duration in days")
    destination_state: str = Field(..., description="Malaysian state destination")
    
    class Config:
        json_schema_extra = {
            "example": {
                "daily_itineraries": [
                    {
                        "day": 1,
                        "pois": [
                            {"name": "Lavender Garden Cameron", "category": "nature"},
                            {"name": "Gunung Brinchang", "category": "hiking"}
                        ]
                    }
                ],
                "trip_duration_days": 5,
                "destination_state": "Pahang"
            }
        }


@router.post("/generate-packing-list/mobile")
async def generate_packing_list_mobile(request: PackingListRequest):
    """
    Generate a smart, categorized packing list for mobile app.
    
    Analyzes the trip itinerary (POIs, activities, climate) and uses LLM 
    to generate practical packing recommendations with categories, quantities,
    and reasons for each item.
    
    Returns:
        - trip_summary: Analysis of activities and climate
        - categories: List of packing categories with items
        - smart_tips: Practical tips for the specific trip
    """
    from tools.planner_tools import analyze_trip_context, generate_packing_list_with_llm
    
    try:
        # Get shared model instance (reuse singleton from supervisor graph)
        global _model
        if _model is None:
            _model = ChatGoogleGenerativeAI(
                model=settings.DEFAULT_LLM_MODEL,
                temperature=0.3  # Lower temperature for consistent packing lists
            )
        
        # Analyze trip context from itinerary
        trip_context = analyze_trip_context(
            request.daily_itineraries,
            request.destination_state
        )
        
        # Generate packing list with LLM (pass model instance)
        packing_data = generate_packing_list_with_llm(
            trip_context,
            request.trip_duration_days,
            request.destination_state,
            _model  # Reuse singleton model
        )
        
        # Build mobile-optimized response
        return {
            "success": True,
            "trip_summary": {
                "destination": request.destination_state,
                "duration_days": request.trip_duration_days,
                "activities": trip_context["activities"],
                "climate": trip_context["climate"]
            },
            "categories": packing_data.get("categories", []),
            "smart_tips": packing_data.get("smart_tips", [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate packing list: {str(e)}"
        )
