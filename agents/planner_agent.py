"""
Planner Node - Creates optimal multi-day itinerary from recommended POIs

This node:
1. Calls plan_itinerary_logic with multi-day support
2. Uses K-Means geographic clustering to group POIs by days
3. Generates optimal visit sequence using nearest-neighbor algorithm
4. Splits sequence into day-by-day itinerary with geographic coherence
5. Calculates overnight transitions between days

No longer uses agent pattern - directly calls orchestrator function.
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from agents.state import TripPlannerState
from tools.planner_tools import plan_itinerary_logic


def create_planner_node(model=None):
    """
    Create the planner node function.
    
    Args:
        model: Not used in this node (direct tool calls only)
    
    Returns:
        Node function that creates optimal itinerary
    """
    
    def planner_node(state: TripPlannerState) -> Dict[str, Any]:
        """
        Create optimal itinerary from POI recommendations using new multi-day planner.
        
        Args:
            state: Current graph state with recommendations
            
        Returns:
            Dictionary with itinerary and next_step
        """
        
        # Extract data from state
        top_priority_pois = state.get("top_priority_pois", [])
        trip_duration_days = state.get("trip_duration_days", 3)
        max_pois_per_day = state.get("max_pois_per_day", 6)  # Get from state or default to 6
        request_type = state.get("request_type", "full_trip")
        
        # Validate inputs
        if not top_priority_pois:
            return {
                "messages": [AIMessage(content="Error: No POIs available to plan itinerary")],
                "next_step": "error",
                "error_message": "No POIs from recommender"
            }
        
        try:
            # Call the new plan_itinerary_logic with multi-day support (anchor-based only)
            result = plan_itinerary_logic(
                priority_pois=top_priority_pois,
                trip_duration_days=trip_duration_days,
                max_pois_per_day=max_pois_per_day,
                anchor_proximity_threshold=30000,  # 30km to group preferred POIs
                poi_search_radius=50000  # 50km to search for nearby POIs
            )
            
            # Check for errors
            if "error" in result:
                return {
                    "messages": [AIMessage(content=f"Planning error: {result['error']}")],
                    "next_step": "error",
                    "error_message": result["error"]
                }
            
            # Extract data from result
            centroid = result["centroid"]
            daily_itineraries = result["daily_itineraries"]
            trip_summary = result["trip_summary"]
            
            # Convert to old format for compatibility with response_formatter
            # Add global_sequence and day to each POI
            global_sequence = 1
            daily_itinerary = []
            
            for day_plan in daily_itineraries:
                day_pois = []
                for poi in day_plan["pois"]:
                    poi["global_sequence"] = global_sequence
                    poi["day"] = day_plan["day"]
                    day_pois.append(poi)
                    global_sequence += 1
                
                daily_itinerary.append({
                    "day": day_plan["day"],
                    "pois": day_pois,
                    "num_pois": day_plan["total_pois"],
                    "total_distance_meters": day_plan["total_distance_meters"],
                    "total_distance_km": round(day_plan["total_distance_meters"] / 1000, 2)
                })
            
            # Create response message
            response_content = (
                f"Created {trip_duration_days}-day itinerary with {trip_summary['total_pois']} POIs using {result['clustering_strategy_used']} clustering. "
                f"Starting from: {centroid['name']}. "
                f"Total travel distance: {trip_summary['total_distance_meters']/1000:.1f} km."
            )
            
            # Build full itinerary object (compatible with existing format)
            itinerary = {
                "trip_duration_days": trip_duration_days,
                "centroid": centroid,
                "total_pois": trip_summary["total_pois"],
                "total_distance_km": trip_summary["total_distance_meters"] / 1000,
                "daily_itinerary": daily_itinerary,
                "clusters": result.get("clusters", {}),
                "clustering_strategy": result["clustering_strategy_used"],
                "trip_summary": trip_summary  # Include full trip_summary with preferred POI stats
            }
            
            # Build optimized_sequence for backward compatibility
            optimized_sequence = []
            for day_plan in daily_itineraries:
                optimized_sequence.extend(day_plan["pois"])
            
            # Return state updates - preserve request_type
            return {
                "messages": [AIMessage(content=response_content)],
                "itinerary": itinerary,
                "centroid": centroid,
                "optimized_sequence": optimized_sequence,
                "request_type": request_type,  # Preserve request type
                "next_step": "format_response"  # Signal to format final response
            }
            
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Error planning itinerary: {str(e)}")],
                "next_step": "error",
                "error_message": str(e)
            }
    
    return planner_node