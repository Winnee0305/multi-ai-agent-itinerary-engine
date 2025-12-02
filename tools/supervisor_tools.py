"""
Supervisor Tools - Wrap sub-agents (Recommender and Planner) as StructuredTools
Using StructuredTool.from_function() for programmatic orchestration
"""

from langchain_core.tools import StructuredTool
from typing import Dict, Any
from agents.recommender_agent import recommender_agent
from agents.planner_agent import planner_agent


def _get_poi_recommendations(request: str) -> str:
    """Get personalized POI recommendations for a trip.
    
    Args:
        request: Natural language request describing the trip requirements.
                 Should include: destination state, user preferences (interests),
                 number of travelers, trip duration, and any specific POI requests.
    
    Returns:
        JSON string with recommended POIs, priority scores, and activity mix
    """
    # Invoke the recommender agent
    config = {"configurable": {"thread_id": "recommender-trip-001"}}
    result = recommender_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config = config
    )
    
    # Return the final response from the agent
    if result and "messages" in result:
        return result["messages"][-1].content
    
    return "Error: Unable to get recommendations"


def _plan_itinerary(request: str) -> str:
    """Plan optimal daily itinerary from recommended POIs.
    
    Args:
        request: Natural language request with POI recommendations and planning requirements.
                 Should include: list of priority POIs (with google_place_id, name, priority_score),
                 max POIs per day, max distance threshold, trip duration.
    
    Returns:
        JSON string with day-by-day itinerary, sequences, distances, and routing logic
    """
    # Invoke the planner agent
    config = {"configurable": {"thread_id": "planner-trip-001"}}
    result = planner_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config = config
    )
    
    # Return the final response from the agent
    if result and "messages" in result:
        return result["messages"][-1].content
    
    return "Error: Unable to plan itinerary"


# Create StructuredTool instances
get_poi_recommendations = StructuredTool.from_function(
    func=_get_poi_recommendations,
    name="get_poi_recommendations",
    description="""Get personalized POI recommendations for a trip.

Use this tool when you need to:
- Get POI recommendations based on user preferences, destination, and trip details
- Calculate priority scores for POIs
- Generate activity mix recommendations
- Find top-rated POIs for a specific state/destination

The recommender agent will:
1. Load POIs from the database based on destination
2. Calculate contextual priority scores using user preferences
3. Return top N POIs ranked by priority
4. Provide activity mix analysis

Example requests:
    "Find top 50 POIs in Penang for 2 people on a 3-day trip. 
     Interests: Food, Culture, Art. Must visit: Kek Lok Si Temple"
    
    "Recommend POIs in Kuala Lumpur for a family of 5, 4-day trip.
     Preferences: Adventure, Shopping, Food"
"""
)

plan_itinerary = StructuredTool.from_function(
    func=_plan_itinerary,
    name="plan_itinerary",
    description="""Plan optimal daily itinerary from recommended POIs.

Use this tool when you need to:
- Create a day-by-day travel itinerary
- Select a centroid (anchor POI) for the trip
- Cluster POIs by distance for efficient routing
- Generate optimal visit sequences to minimize travel time
- Build logical daily routes

The planner agent will:
1. Select the best centroid from top priority POIs
2. Calculate distances between POIs using PostGIS
3. Cluster POIs into nearby and far groups
4. Generate optimal visit sequence using nearest neighbor algorithm
5. Create day-by-day itinerary with travel distances

Example requests:
    "Plan a 3-day itinerary with these POIs: [POI list with place IDs and scores].
     Max 6 POIs per day, prefer POIs within 30km of each other."
    
    "Create optimal route for visiting these 20 POIs over 4 days.
     Minimize travel distance, start from highest priority POI."
"""
)
