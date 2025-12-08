"""
Unified State Schema for LangGraph Multi-Agent Trip Planner

This state flows through all nodes in the graph:
- Input Parser extracts trip context
- Recommender generates POI recommendations
- Planner creates optimized itinerary
- Response Formatter creates user-friendly output
"""

from typing import Annotated, TypedDict, Literal, Optional
from operator import add
from langchain_core.messages import AnyMessage


class TripPlannerState(TypedDict):
    """
    Unified state for the entire trip planning workflow.
    
    State flows through nodes in this order:
    START → parse_input → recommend → plan → format_response → END
    
    Each node receives the full state and returns partial updates.
    LangGraph automatically merges the updates into the state.
    """
    
    # ===== Conversation History =====
    # Messages are automatically appended (via Annotated[list, add])
    messages: Annotated[list[AnyMessage], add]
    
    # ===== User Context (Extracted by Input Parser) =====
    destination_state: Optional[str]
    user_preferences: Optional[list[str]]
    num_travelers: Optional[int]
    trip_duration_days: Optional[int]
    preferred_pois: Optional[list[str]]
    num_pois: Optional[int]
    
    # ===== Recommender Output =====
    recommendations: Optional[dict]  # Full recommendation output
    top_priority_pois: Optional[list[dict]]  # List of POI dicts with priority_score
    activity_mix: Optional[dict]  # Activity category percentages
    
    # ===== Planner Output =====
    itinerary: Optional[dict]  # Full itinerary output
    centroid: Optional[dict]  # Selected centroid POI
    optimized_sequence: Optional[list[dict]]  # Sequenced POIs with distances
    
    # ===== Control Flow =====
    next_step: Optional[Literal["parse_input", "recommend", "plan", "format_response", "complete", "error"]]
    error_message: Optional[str]
