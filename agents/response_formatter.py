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
        
        # Build response parts (chatbot-friendly formatting)
        response_parts = []
        
        # === TRIP OVERVIEW ===
        response_parts.append(f"## 🌏 Trip to {destination_state}")
        response_parts.append("")
        response_parts.append(f"**Duration:** {trip_duration_days} days")
        response_parts.append(f"**Travelers:** {num_travelers} people")
        
        if user_preferences:
            preferences_str = ", ".join(user_preferences)
            response_parts.append(f"**Interests:** {preferences_str}")
        
        response_parts.append("")
        
        # === TOP RECOMMENDATIONS ===
        if top_priority_pois:
            response_parts.append(f"### ⭐ Top {min(10, len(top_priority_pois))} Recommended Places")
            response_parts.append("")
            
            # Show top 10 in clean numbered list
            for i, poi in enumerate(top_priority_pois[:10], 1):
                name = poi.get("name", "Unknown")
                score = poi.get("priority_score", 0)
                response_parts.append(f"{i}. **{name}** • Priority: {score:.0f}")
            
            if len(top_priority_pois) > 10:
                response_parts.append(f"\n*...and {len(top_priority_pois) - 10} more great places to explore!*")
            
            response_parts.append("")
        
        # === ACTIVITY MIX ===
        if activity_mix:
            response_parts.append("### 🎯 Activity Breakdown")
            response_parts.append("")
            
            # Sort by percentage and show top 5
            sorted_activities = sorted(activity_mix.items(), key=lambda x: x[1], reverse=True)
            
            for category, percentage in sorted_activities[:5]:
                response_parts.append(f"• **{category.capitalize()}**: {percentage*100:.0f}%")
            
            response_parts.append("")
        
        # === DAY-BY-DAY ITINERARY ===
        if itinerary and itinerary.get("daily_itinerary"):
            daily_itinerary = itinerary["daily_itinerary"]
            total_distance_km = itinerary.get("total_distance_km", 0)
            
            response_parts.append(f"### 🗓️ Your {trip_duration_days}-Day Itinerary")
            response_parts.append(f"*Total travel distance: {total_distance_km:.1f} km*")
            response_parts.append("")
            
            # Starting point
            if centroid:
                response_parts.append(f"📍 **Starting from:** {centroid.get('name', 'Unknown')}")
                response_parts.append("")
            
            # Each day
            for day_plan in daily_itinerary:
                day_num = day_plan.get("day", 0)
                pois = day_plan.get("pois", [])
                day_distance_km = day_plan.get("total_distance_km", 0)
                
                response_parts.append(f"**Day {day_num}** • {len(pois)} stops • {day_distance_km:.1f} km")
                
                for poi in pois:
                    seq_no = poi.get("sequence_no", 0)
                    name = poi.get("google_matched_name", "Unknown")
                    distance_m = poi.get("distance_from_previous_meters", 0)
                    distance_km = distance_m / 1000
                    
                    if seq_no == 1:
                        response_parts.append(f"{seq_no}. {name}")
                    else:
                        response_parts.append(f"{seq_no}. {name} *(+{distance_km:.1f} km)*")
                
                response_parts.append("")
        
        # === SUMMARY ===
        if recommendations.get("summary_reasoning"):
            response_parts.append("### 💡 Planning Notes")
            response_parts.append("")
            response_parts.append(recommendations["summary_reasoning"])
            response_parts.append("")
        
        # Final note
        response_parts.append("---")
        response_parts.append("✅ Your itinerary is ready! Have an amazing trip! 🎉")
        
        # Join all parts
        formatted_response = "\n".join(response_parts)
        
        # Return state updates
        return {
            "messages": [AIMessage(content=formatted_response)],
            "next_step": "complete"
        }
    
    return format_response_node
