"""
Planner Node - Creates optimal itinerary from recommended POIs

This node:
1. Selects a centroid (anchor POI) from top recommendations
2. Clusters POIs by distance from centroid
3. Generates optimal visit sequence using nearest-neighbor algorithm
4. Splits sequence into day-by-day itinerary

No longer uses agent pattern - directly calls tool functions.
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from agents.state import TripPlannerState
from tools.planner_tools import (
    select_best_centroid,
    cluster_pois_by_distance,
    generate_optimal_sequence
)


def split_sequence_into_days(
    sequence: List[Dict[str, Any]],
    trip_duration_days: int,
    max_pois_per_day: int = 5
) -> List[Dict[str, Any]]:
    """
    Split optimized sequence into day-by-day itinerary.
    
    Args:
        sequence: Optimized sequence of POIs with distances
        trip_duration_days: Number of days for the trip
        max_pois_per_day: Maximum POIs to visit per day
        
    Returns:
        List of daily itinerary dictionaries
    """
    daily_itinerary = []
    total_pois = len(sequence)
    
    # Calculate POIs per day
    pois_per_day = min(max_pois_per_day, (total_pois + trip_duration_days - 1) // trip_duration_days)
    
    start_idx = 0
    global_sequence = 1  # Global sequence number across all days
    
    for day in range(1, trip_duration_days + 1):
        end_idx = min(start_idx + pois_per_day, total_pois)
        
        if start_idx >= total_pois:
            break
        
        day_pois = sequence[start_idx:end_idx]
        
        # Add global sequence number and day to each POI
        for poi in day_pois:
            poi["global_sequence"] = global_sequence
            poi["day"] = day
            global_sequence += 1
        
        # Calculate total distance for the day
        total_distance_meters = sum(poi.get("distance_from_previous_meters", 0) for poi in day_pois)
        total_distance_km = round(total_distance_meters / 1000, 2)
        
        daily_itinerary.append({
            "day": day,
            "pois": day_pois,
            "num_pois": len(day_pois),
            "total_distance_meters": total_distance_meters,
            "total_distance_km": total_distance_km
        })
        
        start_idx = end_idx
    
    return daily_itinerary


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
        Create optimal itinerary from POI recommendations.
        
        Args:
            state: Current graph state with recommendations
            
        Returns:
            Dictionary with itinerary and next_step
        """
        
        # Extract data from state
        top_priority_pois = state.get("top_priority_pois", [])
        trip_duration_days = state.get("trip_duration_days", 3)
        
        # Validate inputs
        if not top_priority_pois:
            return {
                "messages": [AIMessage(content="Error: No POIs available to plan itinerary")],
                "next_step": "error",
                "error_message": "No POIs from recommender"
            }
        
        try:
            # Step 1: Select centroid (best starting POI)
            centroid = select_best_centroid(top_priority_pois, consider_top_n=5)
            
            if "error" in centroid:
                return {
                    "messages": [AIMessage(content=f"Centroid selection error: {centroid['error']}")],
                    "next_step": "error",
                    "error_message": centroid["error"]
                }
            
            centroid_id = centroid["google_place_id"]
            centroid_name = centroid["name"]
            
            # Step 2: Cluster POIs by distance from centroid
            clusters = cluster_pois_by_distance(
                centroid_place_id=centroid_id,
                poi_list=top_priority_pois,
                max_distance_meters=50000  # 50km threshold (increased for larger states)
            )
            
            # Focus on nearby POIs (within 50km)
            nearby_pois = clusters.get("nearby", [])
            
            # If not enough nearby POIs, include some far POIs
            if len(nearby_pois) < 10:
                far_pois = clusters.get("far", [])
                # Add closest far POIs to reach a minimum of 10 total POIs
                additional_count = min(10 - len(nearby_pois), len(far_pois))
                nearby_pois.extend(far_pois[:additional_count])
            
            if len(nearby_pois) <= 1:  # Only centroid found
                return {
                    "messages": [AIMessage(content=f"Not enough POIs found near centroid: {centroid_name}")],
                    "next_step": "error",
                    "error_message": "Insufficient POIs for itinerary planning"
                }
            
            # Step 3: Generate optimal sequence (nearest-neighbor algorithm)
            # Extract place IDs from nearby POIs
            nearby_place_ids = [poi["google_place_id"] for poi in nearby_pois]
            
            # Remove centroid from list to avoid duplication
            if centroid_id in nearby_place_ids:
                nearby_place_ids.remove(centroid_id)
            
            optimized_sequence = generate_optimal_sequence(
                poi_place_ids=nearby_place_ids,
                start_place_id=centroid_id
            )
            
            # Step 4: Split into day-by-day itinerary
            daily_itinerary = split_sequence_into_days(
                sequence=optimized_sequence,
                trip_duration_days=trip_duration_days,
                max_pois_per_day=5
            )
            
            # Calculate total metrics
            total_distance_km = sum(day["total_distance_km"] for day in daily_itinerary)
            total_pois = len(optimized_sequence)
            
            # Create response message
            response_content = (
                f"Created {trip_duration_days}-day itinerary with {total_pois} POIs. "
                f"Starting from: {centroid_name}. "
                f"Total travel distance: {total_distance_km:.1f} km."
            )
            
            # Build full itinerary object
            itinerary = {
                "trip_duration_days": trip_duration_days,
                "centroid": centroid,
                "total_pois": total_pois,
                "total_distance_km": total_distance_km,
                "daily_itinerary": daily_itinerary,
                "clusters": clusters
            }
            
            # Return state updates
            return {
                "messages": [AIMessage(content=response_content)],
                "itinerary": itinerary,
                "centroid": centroid,
                "optimized_sequence": optimized_sequence,
                "next_step": "format_response"  # Signal to format final response
            }
            
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Error planning itinerary: {str(e)}")],
                "next_step": "error",
                "error_message": str(e)
            }
    
    return planner_node