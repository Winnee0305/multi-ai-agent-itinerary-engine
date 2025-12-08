"""
Recommender Node - Generates POI recommendations based on user context

This node:
1. Loads POIs from database for the destination state
2. Calculates priority scores based on user preferences
3. Returns top N POIs with activity mix analysis

No longer uses agent pattern - directly calls tool functions.
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from agents.state import TripPlannerState
from tools.recommender_tools import recommend_pois_for_trip_logic


def create_recommender_node(model=None):
    """
    Create the recommender node function.
    
    Args:
        model: Not used in this node (direct tool calls only)
    
    Returns:
        Node function that generates POI recommendations
    """
    
    def recommender_node(state: TripPlannerState) -> Dict[str, Any]:
        """
        Generate POI recommendations based on user context.
        
        Args:
            state: Current graph state with trip context
            
        Returns:
            Dictionary with recommendations and next_step
        """
        
        # Extract context from state
        destination_state = state.get("destination_state")
        user_preferences = state.get("user_preferences", ["Culture", "Food", "Nature"])
        num_travelers = state.get("num_travelers", 2)
        trip_duration_days = state.get("trip_duration_days", 3)
        preferred_pois = state.get("preferred_pois")
        num_pois = state.get("num_pois", 50)
        
        # Validate required fields
        if not destination_state:
            return {
                "messages": [AIMessage(content="Error: Destination state is required")],
                "next_step": "error",
                "error_message": "Missing destination_state"
            }
        
        try:
            # Call the recommendation logic directly (no agent needed)
            recommendations = recommend_pois_for_trip_logic(
                destination_state=destination_state,
                user_preferences=user_preferences,
                number_of_travelers=num_travelers,
                trip_duration_days=trip_duration_days,
                preferred_poi_names=preferred_pois,
                top_n=num_pois
            )
            
            # Check for errors
            if "error" in recommendations:
                return {
                    "messages": [AIMessage(content=f"Recommendation error: {recommendations['error']}")],
                    "next_step": "error",
                    "error_message": recommendations["error"]
                }
            
            # Extract key data
            top_priority_pois = recommendations.get("top_priority_pois", [])
            activity_mix = recommendations.get("recommended_activity_mix", {})
            summary = recommendations.get("summary_reasoning", "")
            
            # Create response message
            num_pois_found = len(top_priority_pois)
            top_categories = list(activity_mix.keys())[:3]
            categories_str = ", ".join([cat.title() for cat in top_categories])
            
            response_content = (
                f"Found {num_pois_found} POIs in {destination_state}. "
                f"Top activity categories: {categories_str}. "
                f"{summary}"
            )
            
            # Return state updates
            return {
                "messages": [AIMessage(content=response_content)],
                "recommendations": recommendations,
                "top_priority_pois": top_priority_pois,
                "activity_mix": activity_mix,
                "next_step": "plan"  # Signal to move to planner
            }
            
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Error generating recommendations: {str(e)}")],
                "next_step": "error",
                "error_message": str(e)
            }
    
    return recommender_node