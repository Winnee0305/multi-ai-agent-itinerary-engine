"""
Tools for Recommender Agent - Load POIs and calculate priority scores
"""

from langchain_core.tools import StructuredTool
from typing import List, Dict, Any, Optional
from database.supabase_client import get_supabase

# Category mapping for user interests
INTEREST_CATEGORIES = {
    "Art": ["art_gallery", "museum", "painter", "art_studio", "craft"],
    "Culture": ["museum", "art_gallery", "cultural_center", "library", "historical_landmark", "landmark", "place_of_worship"],
    "Adventure": ["amusement_park", "theme_park", "water_park", "zoo", "aquarium", "park", "hiking_area", "campground"],
    "Nature": ["park", "natural_feature", "hiking_area", "campground", "beach", "waterfall", "mountain", "forest", "lake", "river"],
    "Food": ["restaurant", "cafe", "food", "bar", "bakery", "meal_takeaway", "meal_delivery", "food_court"],
    "Shopping": ["shopping_mall", "department_store", "store", "market", "supermarket", "clothing_store", "jewelry_store", "book_store"],
    "History": ["historical_landmark", "museum", "monument", "heritage", "archaeological_site", "castle", "fort", "memorial"],
    "Religion": ["place_of_worship", "church", "mosque", "temple", "hindu_temple", "buddhist_temple", "synagogue"],
    "Entertainment": ["night_club", "bar", "movie_theater", "casino", "bowling_alley", "amusement_park", "tourist_attraction"],
    "Relaxation": ["spa", "beauty_salon", "park", "beach", "resort", "tourist_attraction", "scenic_overlook"]
}

# ==============================================================================
# 1. CORE LOGIC (Public Functions)
# These are standard Python functions that can be called by other functions
# ==============================================================================

def load_pois_from_database(state: Optional[str] = None, golden_only: bool = True, min_popularity: int = 50) -> List[Dict[str, Any]]:
    """Internal logic to load POIs from Supabase."""
    supabase = get_supabase()
    
    # Build query
    query = supabase.table("osm_pois").select("*")
    
    if state:
        query = query.eq("state", state)
    
    if golden_only:
        query = query.eq("in_golden_list", True)
    
    if min_popularity > 0:
        query = query.gte("popularity_score", min_popularity)
    
    # Execute query
    result = query.execute()
    
    return result.data if result.data else []


def calculate_priority_scores(
    pois: List[Dict[str, Any]],
    user_preferences: List[str],
    number_of_travelers: int,
    travel_days: int,
    preferred_poi_names: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Internal logic to calculate scores."""
    scored_pois = []
    
    for poi in pois:
        # Get base data
        base_score = poi.get("popularity_score", 0)
        
        if base_score == 0:
            continue
        
        poi_name = poi.get("name", "")
        google_types = poi.get("google_types") or []
        google_reviews = poi.get("google_reviews", 0)
        wikidata_sitelinks = poi.get("wikidata_sitelinks", 0)
        
        current_score = float(base_score)
        
        # Layer 0: Preferred POI Boost
        if preferred_poi_names:
            try:
                from fuzzywuzzy import fuzz
                max_similarity = 0
                for preferred in preferred_poi_names:
                    similarity = fuzz.ratio(poi_name.lower(), preferred.lower())
                    if similarity > max_similarity:
                        max_similarity = similarity
                
                if max_similarity >= 80:
                    current_score *= 2.0
            except ImportError:
                for preferred in preferred_poi_names:
                    if preferred.lower() in poi_name.lower() or poi_name.lower() in preferred.lower():
                        current_score *= 2.0
                        break
        
        # Layer 1: Interest Match Boost
        interest_match = False
        for preference in user_preferences:
            if preference in INTEREST_CATEGORIES:
                relevant_types = INTEREST_CATEGORIES[preference]
                for poi_type in google_types:
                    if poi_type in relevant_types:
                        interest_match = True
                        break
                if interest_match:
                    break
        
        if interest_match:
            current_score *= 1.5
        
        # Layer 2: Group Safety Filter
        if number_of_travelers > 2:
            if google_reviews < 50 or wikidata_sitelinks < 5:
                current_score *= 0.8
        
        # Layer 3: Time Pressure Boost
        if travel_days < 3 and wikidata_sitelinks >= 20:
            current_score *= 1.2
        
        # Normalize
        priority_score = min(current_score / 100.0, 1.0)
        
        scored_pois.append({
            **poi,
            "priority_score": round(priority_score, 2)
        })
    
    scored_pois.sort(key=lambda x: x["priority_score"], reverse=True)
    return scored_pois


def get_top_priority_pois(scored_pois: List[Dict[str, Any]], top_n: int = 50) -> List[Dict[str, Any]]:
    """Internal logic to filter top N."""
    top_pois = scored_pois[:top_n]
    return [
        {
            "google_place_id": poi.get("google_place_id"),
            "name": poi.get("name"),
            "priority_score": poi.get("priority_score"),
            "lat": poi.get("lat"),
            "lon": poi.get("lon"),
            "state": poi.get("state")
        }
        for poi in top_pois
    ]


def calculate_activity_mix(top_pois: List[Dict[str, Any]], scored_pois: List[Dict[str, Any]]) -> Dict[str, float]:
    """Internal logic to calculate mix."""
    top_place_ids = {poi["google_place_id"] for poi in top_pois}
    
    top_pois_full = [
        poi for poi in scored_pois 
        if poi.get("google_place_id") in top_place_ids
    ]
    
    category_counts = {k.lower(): 0 for k in INTEREST_CATEGORIES.keys()}
    total = len(top_pois_full)
    
    if total == 0:
        return category_counts
    
    # Map categories based on INTEREST_CATEGORIES keys
    category_mapping = {k: k.lower() for k in INTEREST_CATEGORIES.keys()}
    
    for poi in top_pois_full:
        google_types = poi.get("google_types") or []
        
        for cat_name, cat_key in category_mapping.items():
            if cat_name in INTEREST_CATEGORIES:
                relevant_types = INTEREST_CATEGORIES[cat_name]
                for poi_type in google_types:
                    if poi_type in relevant_types:
                        category_counts[cat_key] += 1
                        break
    
    activity_mix = {
        cat: round(count / total, 2) if total > 0 else 0.0
        for cat, count in category_counts.items()
    }
    
    # Filter zeros and sort
    activity_mix = {k: v for k, v in activity_mix.items() if v > 0}
    return dict(sorted(activity_mix.items(), key=lambda x: x[1], reverse=True))


def generate_recommendation_output(
    destination_state: str,
    trip_duration_days: int,
    top_priority_pois: List[Dict[str, Any]],
    activity_mix: Dict[str, float],
    user_preferences: List[str]
) -> Dict[str, Any]:
    """Internal logic to format output."""
    preferences_str = ", ".join([p.lower() for p in user_preferences])
    top_categories = list(activity_mix.keys())[:3]
    categories_str = ", ".join(top_categories)
    
    summary = f"Prioritized based on user preferences for {preferences_str}. "
    summary += f"Recommended activity mix focuses on {categories_str}. "
    summary += f"Selected {len(top_priority_pois)} POIs optimized for {trip_duration_days}-day trip."
    
    return {
        "destination_state": destination_state,
        "trip_duration_days": trip_duration_days,
        "top_priority_pois": [
            {
                "google_place_id": poi["google_place_id"],
                "name": poi["name"],
                "priority_score": poi["priority_score"],
                "lat": poi.get("lat"),
                "lon": poi.get("lon"),
                "state": poi.get("state")
            }
            for poi in top_priority_pois
        ],
        "recommended_activity_mix": activity_mix,
        "summary_reasoning": summary
    }


def recommend_pois_for_trip_logic(
    destination_state: str,
    user_preferences: List[str],
    number_of_travelers: int,
    trip_duration_days: int,
    preferred_poi_names: Optional[List[str]] = None,
    top_n: int = 50
) -> Dict[str, Any]:
    """
    Orchestrator function that calls other internal functions.
    This replaces the tool-calling-tool pattern.
    """
    # Step 1: Call internal logic (Public functions now)
    pois = load_pois_from_database(state=destination_state, golden_only=True, min_popularity=50)
    
    if not pois:
        return {
            "error": f"No POIs found for state: {destination_state}",
            "destination_state": destination_state,
            "trip_duration_days": trip_duration_days,
            "top_priority_pois": [],
            "recommended_activity_mix": {},
            "summary_reasoning": "No POIs available for this destination."
        }
    
    # Step 2: Call internal logic
    scored_pois = calculate_priority_scores(
        pois=pois,
        user_preferences=user_preferences,
        number_of_travelers=number_of_travelers,
        travel_days=trip_duration_days,
        preferred_poi_names=preferred_poi_names
    )
    
    # Step 3: Call internal logic
    top_pois = get_top_priority_pois(scored_pois=scored_pois, top_n=top_n)
    
    # Step 4: Call internal logic
    activity_mix = calculate_activity_mix(top_pois=top_pois, scored_pois=scored_pois)
    
    # Step 5: Call internal logic
    output = generate_recommendation_output(
        destination_state=destination_state,
        trip_duration_days=trip_duration_days,
        top_priority_pois=top_pois,
        activity_mix=activity_mix,
        user_preferences=user_preferences
    )
    
    return output

# ==============================================================================
# 2. EXPORTED TOOLS (Wrappers)
# These are what the Agent sees and uses
# ==============================================================================

load_pois_tool = StructuredTool.from_function(
    func=load_pois_from_database,
    name="load_pois_from_database",
    description="Load POIs from Supabase database. Args: state, golden_only, min_popularity."
)

calculate_priority_scores_tool = StructuredTool.from_function(
    func=calculate_priority_scores,
    name="calculate_priority_scores",
    description="Calculate priority scores for POIs based on user context."
)

get_top_priority_pois_tool = StructuredTool.from_function(
    func=get_top_priority_pois,
    name="get_top_priority_pois",
    description="Get top N POIs by priority score."
)

calculate_activity_mix_tool = StructuredTool.from_function(
    func=calculate_activity_mix,
    name="calculate_activity_mix",
    description="Calculate recommended activity mix based on top POIs."
)

generate_recommendation_output_tool = StructuredTool.from_function(
    func=generate_recommendation_output,
    name="generate_recommendation_output",
    description="Generate final recommendation output format."
)

# This is the MAIN tool your agent will likely use
recommend_pois_for_trip_tool = StructuredTool.from_function(
    func=recommend_pois_for_trip_logic,
    name="recommend_pois_for_trip",
    description="Complete workflow: Loads POIs, calculates scores, and generates recommendations for a trip."
)