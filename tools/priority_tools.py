"""
LangChain tool for priority score calculation
Wraps the PriorityScorer logic for use in agents
"""

from typing import List, Dict, Optional
from langchain.tools import tool
import sys
from pathlib import Path

# Add preprocessing to path to import PriorityScorer
sys.path.insert(0, str(Path(__file__).parent.parent / "preprocessing"))
from pois_priority_scorer import PriorityScorer


# Global scorer instance
_priority_scorer = PriorityScorer()


@tool
def calculate_priority_scores(
    pois: List[Dict],
    user_preferences: List[str],
    number_of_travelers: int,
    travel_days: int,
    target_state: Optional[str] = None,
    preferred_pois: Optional[List[str]] = None,
    verbose: bool = True
) -> List[Dict]:
    """
    Calculate contextual priority scores for POIs based on user context.
    Returns POIs sorted by priority score (highest first).
    
    This applies knowledge-based rules to transform static popularity scores
    into user-specific priority scores.
    
    Args:
        pois: List of POI dictionaries from database (must have popularity_score)
        user_preferences: User's interests (e.g., ["Art", "Culture", "Food"])
        number_of_travelers: Group size (affects safety filtering)
        travel_days: Trip duration in days (affects landmark prioritization)
        target_state: Optional state filter (POIs outside this state get 0 priority)
        preferred_pois: Optional list of specific POI names user wants to visit
        verbose: Include detailed scoring breakdown explanations
    
    Returns:
        List of enriched POI dictionaries with priority_score field, sorted descending
        
    Priority Scoring Rules:
    - Interest Match: 1.5x boost for POIs matching user interests
    - Group Safety: 0.8x penalty for unproven POIs (low reviews) when group > 2
    - Time Pressure: 1.2x boost for landmarks (high sitelinks) on short trips (< 3 days)
    - Preferred POIs: 2.0x boost for user-specified POIs (80%+ name match)
    """
    enriched_pois = _priority_scorer.enrich_pois_with_priority_scores(
        pois=pois,
        user_preferences=user_preferences,
        number_of_travelers=number_of_travelers,
        travel_days=travel_days,
        target_state=target_state,
        preferred_pois=preferred_pois,
        verbose=verbose
    )
    
    # Sort by priority score (highest first)
    sorted_pois = sorted(
        enriched_pois,
        key=lambda x: x.get("priority_score", 0),
        reverse=True
    )
    
    return sorted_pois


@tool
def get_interest_categories() -> Dict[str, List[str]]:
    """
    Get available interest categories and their associated Google Places types.
    
    Returns:
        Dictionary mapping interest categories to place types
        
    Available categories:
    - Art, Culture, Adventure, Nature, Food, Shopping, History, 
      Religion, Entertainment, Relaxation
    """
    return _priority_scorer.INTEREST_CATEGORIES


@tool
def check_interest_match(poi_types: List[str], user_preferences: List[str]) -> bool:
    """
    Check if a POI's types match any of the user's interest preferences.
    
    Args:
        poi_types: List of Google Places types for the POI
        user_preferences: User's interest categories
    
    Returns:
        True if there's a match, False otherwise
    """
    return _priority_scorer.matches_user_interest(poi_types, user_preferences)
