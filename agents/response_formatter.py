"""
Response Formatter Node - Creates user-friendly final response

This node formats the complete trip planning results into a structured,
readable format for the user, including:
- Trip overview
- Top POI recommendations
- Activity mix breakdown
- Day-by-day itinerary with distances
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from agents.state import TripPlannerState


def create_response_formatter_node(model=None):
    """
    Create the response formatter node function.
    
    Args:
        model: Not used in this node (formatting only)
    
    Returns:
        Node function that formats final response
    """
    
    def format_response_node(state: TripPlannerState) -> Dict[str, Any]:
        """
        Format the complete trip planning results into user-friendly response.
        
        Args:
            state: Current graph state with recommendations and itinerary
            
        Returns:
            Dictionary with formatted response message and next_step=complete
        """
        
        # Extract data from state
        destination_state = state.get("destination_state", "Unknown")
        trip_duration_days = state.get("trip_duration_days", 0)
        num_travelers = state.get("num_travelers", 0)
        user_preferences = state.get("user_preferences", [])
        
        recommendations = state.get("recommendations", {})
        top_priority_pois = state.get("top_priority_pois", [])
        activity_mix = state.get("activity_mix", {})
        
        itinerary = state.get("itinerary", {})
        centroid = state.get("centroid", {})
        
        # Build response parts
        response_parts = []
        
        # === TRIP OVERVIEW ===
        response_parts.append("=" * 60)
        response_parts.append(f"🌏 TRIP TO {destination_state.upper()}")
        response_parts.append("=" * 60)
        response_parts.append(f"📅 Duration: {trip_duration_days} days")
        response_parts.append(f"👥 Travelers: {num_travelers}")
        
        if user_preferences:
            preferences_str = ", ".join(user_preferences)
            response_parts.append(f"❤️  Interests: {preferences_str}")
        
        response_parts.append("")
        
        # === TOP RECOMMENDATIONS ===
        if top_priority_pois:
            response_parts.append("=" * 60)
            response_parts.append(f"⭐ TOP {len(top_priority_pois)} RECOMMENDED POIs")
            response_parts.append("=" * 60)
            
            # Show top 10 with scores
            for i, poi in enumerate(top_priority_pois[:10], 1):
                name = poi.get("name", "Unknown")
                score = poi.get("priority_score", 0)
                response_parts.append(f"{i:2d}. {name} (Priority: {score:.2f})")
            
            if len(top_priority_pois) > 10:
                response_parts.append(f"    ... and {len(top_priority_pois) - 10} more POIs")
            
            response_parts.append("")
        
        # === ACTIVITY MIX ===
        if activity_mix:
            response_parts.append("=" * 60)
            response_parts.append("🎯 RECOMMENDED ACTIVITY MIX")
            response_parts.append("=" * 60)
            
            # Sort by percentage
            sorted_activities = sorted(activity_mix.items(), key=lambda x: x[1], reverse=True)
            
            for category, percentage in sorted_activities:
                bar_length = int(percentage * 40)  # Scale to 40 chars max
                bar = "█" * bar_length
                response_parts.append(f"{category.capitalize():15s} {bar} {percentage*100:5.1f}%")
            
            response_parts.append("")
        
        # === DAY-BY-DAY ITINERARY ===
        if itinerary and itinerary.get("daily_itinerary"):
            daily_itinerary = itinerary["daily_itinerary"]
            total_distance_km = itinerary.get("total_distance_km", 0)
            
            response_parts.append("=" * 60)
            response_parts.append(f"🗓️  {trip_duration_days}-DAY ITINERARY (Total: {total_distance_km:.1f} km)")
            response_parts.append("=" * 60)
            
            # Starting point
            if centroid:
                response_parts.append(f"📍 Starting Point: {centroid.get('name', 'Unknown')}")
                response_parts.append("")
            
            # Each day
            for day_plan in daily_itinerary:
                day_num = day_plan.get("day", 0)
                pois = day_plan.get("pois", [])
                day_distance_km = day_plan.get("total_distance_km", 0)
                
                response_parts.append(f"--- DAY {day_num} ({len(pois)} POIs, {day_distance_km:.1f} km) ---")
                
                for poi in pois:
                    seq_no = poi.get("sequence_no", 0)
                    name = poi.get("google_matched_name", "Unknown")
                    distance_m = poi.get("distance_from_previous_meters", 0)
                    distance_km = distance_m / 1000
                    
                    if seq_no == 1:
                        response_parts.append(f"  {seq_no}. {name} (START)")
                    else:
                        response_parts.append(f"  {seq_no}. {name} (+{distance_km:.1f} km)")
                
                response_parts.append("")
        
        # === SUMMARY ===
        if recommendations.get("summary_reasoning"):
            response_parts.append("=" * 60)
            response_parts.append("💡 PLANNING INSIGHTS")
            response_parts.append("=" * 60)
            response_parts.append(recommendations["summary_reasoning"])
            response_parts.append("")
        
        # Final note
        response_parts.append("=" * 60)
        response_parts.append("✅ Trip planning complete! Safe travels!")
        response_parts.append("=" * 60)
        
        # Join all parts
        formatted_response = "\n".join(response_parts)
        
        # Return state updates
        return {
            "messages": [AIMessage(content=formatted_response)],
            "next_step": "complete"
        }
    
    return format_response_node
