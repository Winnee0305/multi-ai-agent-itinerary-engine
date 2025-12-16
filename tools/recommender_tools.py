"""
Tools for Recommender Agent - Load POIs and calculate priority scores
"""
import random
import hashlib
from datetime import datetime
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
    preferred_poi_names: Optional[List[str]] = None,
    user_behavior: Optional[Dict[str, List[str]]] = None
) -> List[Dict[str, Any]]:
    """
    Calculate contextual priority scores based on user context with optional behavioral signals.
    
    NEW: When preferred_poi_names are specified, POIs are geographically filtered to only include
    those within 50km of the preferred POI region. This prevents "Cameron Highlands" searches from
    returning far-away "Genting Highlands" results.
    
    Args:
        user_behavior: Optional dict with keys:
            - viewed_place_ids: List of place_ids user viewed
            - collected_place_ids: List of place_ids user bookmarked
            - trip_place_ids: List of place_ids in user's saved trips
    
    Original description:
    
    Score Range: 0-200+ (unbounded, can exceed 100)
    - Base popularity score: 0-100
    - Multipliers can boost score beyond 100
    - Higher scores = higher priority
    
    Multipliers:
    - Preferred POI: ×2.0
    - Interest match: ×1.5
    - Group safety penalty: ×0.8
    - Landmark boost: ×1.2
    
    Args:
        pois: List of POIs with popularity_score field
        user_preferences: List of interest categories
        number_of_travelers: Group size
        travel_days: Trip duration in days
        preferred_poi_names: Optional list of specific POI names
        
    Returns:
        List of POIs with priority_score field (sorted descending)
    """
    # Geographic filtering: If user specifies preferred POIs, scope results to that region
    if preferred_poi_names:
        from tools.planner_tools import haversine_distance
        
        # Find matching preferred POIs using fuzzy matching
        try:
            from fuzzywuzzy import fuzz
            use_fuzzy = True
        except ImportError:
            use_fuzzy = False
        
        preferred_pois = []
        threshold = 60
        
        for poi in pois:
            poi_name = poi.get("name", "")
            
            if use_fuzzy:
                max_similarity = 0
                for preferred in preferred_poi_names:
                    similarity = fuzz.ratio(poi_name.lower(), preferred.lower())
                    if similarity > max_similarity:
                        max_similarity = similarity
                
                if max_similarity >= threshold:
                    preferred_pois.append(poi)
            else:
                for preferred in preferred_poi_names:
                    if preferred.lower() in poi_name.lower() or poi_name.lower() in preferred.lower():
                        preferred_pois.append(poi)
                        break
        
        # If preferred POIs found, filter by geographic proximity
        if preferred_pois:
            centroid_lat = sum(p["lat"] for p in preferred_pois) / len(preferred_pois)
            centroid_lon = sum(p["lon"] for p in preferred_pois) / len(preferred_pois)
            
            # Filter to 50km radius (expand to 80km if too few results)
            radius_meters = 50000
            filtered_pois = []
            
            for poi in pois:
                distance = haversine_distance(
                    centroid_lat, centroid_lon,
                    poi["lat"], poi["lon"]
                )
                if distance <= radius_meters:
                    filtered_pois.append(poi)
            
            # Always include preferred POIs themselves
            for pref_poi in preferred_pois:
                if pref_poi not in filtered_pois:
                    filtered_pois.append(pref_poi)
            
            # If too few results, expand radius
            if len(filtered_pois) < 20:
                filtered_pois = []
                radius_meters = 80000
                for poi in pois:
                    distance = haversine_distance(
                        centroid_lat, centroid_lon,
                        poi["lat"], poi["lon"]
                    )
                    if distance <= radius_meters:
                        filtered_pois.append(poi)
                
                for pref_poi in preferred_pois:
                    if pref_poi not in filtered_pois:
                        filtered_pois.append(pref_poi)
            
            pois = filtered_pois  # Use filtered POIs for scoring
    
    # Extract behavioral signals (default to empty sets)
    viewed_ids = set(user_behavior.get("viewed_place_ids", [])) if user_behavior else set()
    collected_ids = set(user_behavior.get("collected_place_ids", [])) if user_behavior else set()
    trip_ids = set(user_behavior.get("trip_place_ids", [])) if user_behavior else set()
    
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
        is_preferred = False  # Track if this POI was explicitly requested by user
        if preferred_poi_names:
            try:
                from fuzzywuzzy import fuzz
                max_similarity = 0
                best_match = None
                for preferred in preferred_poi_names:
                    similarity = fuzz.ratio(poi_name.lower(), preferred.lower())
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_match = preferred
                
                if max_similarity >= 60:
                    current_score *= 2.0
                    is_preferred = True
            except ImportError:
                for preferred in preferred_poi_names:
                    if preferred.lower() in poi_name.lower() or poi_name.lower() in preferred.lower():
                        current_score *= 2.0
                        is_preferred = True
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
        
        # Layer 4: Behavioral Boost (NEW)
        behavior_boost = 0
        behavior_multiplier = 1.0
        
        if user_behavior:
            poi_place_id = poi.get("google_place_id")
            
            # Viewed: Weak signal (+3 points)
            if poi_place_id in viewed_ids:
                behavior_boost += 3
            
            # Collected: Medium signal (+20 points)
            if poi_place_id in collected_ids:
                behavior_boost += 20
            
            # In Saved Trips: Strong signal (×1.4 multiplier)
            if poi_place_id in trip_ids:
                behavior_multiplier = 1.4
        
        # Apply behavioral boosts
        current_score += behavior_boost
        current_score *= behavior_multiplier
        
        # Keep raw score (no normalization) - matches old implementation
        priority_score = current_score
        
        scored_pois.append({
            **poi,
            "priority_score": round(priority_score, 2),
            "is_preferred": is_preferred,
            "behavior_boost": behavior_boost if user_behavior else 0,
            "behavior_multiplier": behavior_multiplier if user_behavior else 1.0
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
            "state": poi.get("state"),
            "is_preferred": poi.get("is_preferred", False),
            "behavior_boost": poi.get("behavior_boost", 0),
            "behavior_multiplier": poi.get("behavior_multiplier", 1.0)
        }
        for poi in top_pois
    ]


def calculate_activity_mix(scored_pois: List[Dict[str, Any]]) -> Dict[str, float]:
    """Internal logic to calculate mix from all scored POIs."""
    category_counts = {k.lower(): 0 for k in INTEREST_CATEGORIES.keys()}
    total = len(scored_pois)
    
    if total == 0:
        return category_counts
    
    # Map categories based on INTEREST_CATEGORIES keys
    category_mapping = {k: k.lower() for k in INTEREST_CATEGORIES.keys()}
    
    for poi in scored_pois:
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
    all_priority_pois: List[Dict[str, Any]],
    activity_mix: Dict[str, float],
    user_preferences: List[str]
) -> Dict[str, Any]:
    """Internal logic to format output with all scored POIs."""
    preferences_str = ", ".join([p.lower() for p in user_preferences])
    top_categories = list(activity_mix.keys())[:3]
    categories_str = ", ".join(top_categories)
    
    summary = f"Prioritized based on user preferences for {preferences_str}. "
    summary += f"Recommended activity mix focuses on {categories_str}. "
    summary += f"Selected {len(all_priority_pois)} POIs optimized for {trip_duration_days}-day trip."
    
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
                "state": poi.get("state"),
                "is_preferred": poi.get("is_preferred", False)
            }
            for poi in all_priority_pois
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
    user_behavior: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Orchestrator function that calls other internal functions.
    Returns ALL scored POIs without limiting to top N.
    
    Args:
        user_behavior: Optional behavioral signals from Flutter app:
            - viewed_place_ids: POIs user viewed
            - collected_place_ids: POIs user bookmarked
            - trip_place_ids: POIs in user's saved trips
    """
    # Step 1: Load all POIs from state
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
    
    # Step 2: Calculate priority scores (includes geographic filtering + fuzzy matching for preferred POIs)
    scored_pois = calculate_priority_scores(
        pois=pois,
        user_preferences=user_preferences,
        number_of_travelers=number_of_travelers,
        travel_days=trip_duration_days,
        preferred_poi_names=preferred_poi_names,
        user_behavior=user_behavior
    )
    
    # Step 3: Calculate activity mix from all scored POIs
    activity_mix = calculate_activity_mix(scored_pois=scored_pois)
    
    # Step 4: Generate formatted output with all POIs
    output = generate_recommendation_output(
        destination_state=destination_state,
        trip_duration_days=trip_duration_days,
        all_priority_pois=scored_pois,
        activity_mix=activity_mix,
        user_preferences=user_preferences
    )
    
    # Step 6: Add behavior stats to output (for transparency)
    if user_behavior:
        output["behavior_stats"] = {
            "viewed_count": len(user_behavior.get("viewed_place_ids", [])),
            "collected_count": len(user_behavior.get("collected_place_ids", [])),
            "trip_count": len(user_behavior.get("trip_place_ids", []))
        }
    
    return output


def get_trending_pois_logic(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get trending POIs based on popularity score.
    Used for "For You" page when user has no behavioral data.
    
    Args:
        limit: Number of POIs to return (default 5)
    
    Returns:
        List of top trending POIs
    """
    supabase = get_supabase()
    
    # Query top POIs by popularity
    result = supabase.table("osm_pois").select(
        "google_place_id, name, state, lat, lon, popularity_score, "
        "google_rating, wikidata_sitelinks, google_types"
    ).eq("in_golden_list", True).gte(
        "popularity_score", 70
    ).order("popularity_score", desc=True).limit(limit * 2).execute()  # Get 2x for variety
    
    if not result.data:
        return []
    
    # Return top N with minimal formatting
    pois = []
    for poi in result.data[:limit]:
        pois.append({
            "google_place_id": poi.get("google_place_id"),
            "name": poi.get("name"),
            "state": poi.get("state"),
            "lat": poi.get("lat"),
            "lon": poi.get("lon"),
            "popularity_score": poi.get("popularity_score"),
            "google_rating": poi.get("google_rating")
        })
    
    return pois


def _generate_seed_for_recommendations(
    user_behavior: Optional[Dict[str, List[str]]] = None,
    rotation_hours: int = 6
) -> int:
    """
    Generate deterministic seed based on time window and user behavior.
    
    Args:
        user_behavior: Optional user signals for personalization
        rotation_hours: Hours per rotation window (default 6)
    
    Returns:
        Integer seed for random number generator
    """
    # Get current time window (rounds down to nearest rotation_hours)
    now = datetime.utcnow()
    time_window = now.replace(
        hour=(now.hour // rotation_hours) * rotation_hours,
        minute=0,
        second=0,
        microsecond=0
    )
    
    # Create base seed from time window
    time_seed = int(time_window.timestamp())
    
    # Add user behavior hash for personalization
    if user_behavior:
        behavior_str = "".join(sorted([
            *user_behavior.get("viewed_place_ids", []),
            *user_behavior.get("collected_place_ids", []),
            *user_behavior.get("trip_place_ids", [])
        ]))
        if behavior_str:
            behavior_hash = int(hashlib.md5(behavior_str.encode()).hexdigest()[:8], 16)
            return time_seed + behavior_hash
    
    return time_seed


def get_quick_recommendations_for_you(
    user_behavior: Optional[Dict[str, List[str]]] = None,
    user_preferences: Optional[List[str]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Fast personalized recommendations for "For You" page.
    Prioritizes FAMOUS POIs that match user preferences.
    
    **Scoring Strategy:**
    - Base: Popularity score (higher = more famous)
    - Preference match: ×1.8 boost if POI matches user interests
    - Quality: ×1.3 boost for highly-rated POIs (4.5+ rating)
    - Behavioral: Boost based on user viewing/collecting history
    - Selection: Random weighted sampling from top 50 candidates
    
    Args:
        user_behavior: Optional behavioral signals (viewed, collected, trips)
        user_preferences: Optional list of user interest categories for preference matching
        top_n: Number of recommendations (default 5)
    
    Returns:
        List of top N famous POIs matching preferences with weighted randomness
    """
    supabase = get_supabase()
    
    # Load FAMOUS golden POIs (higher threshold for quality)
    result = supabase.table("osm_pois").select(
        "google_place_id, name, state, lat, lon, popularity_score, "
        "google_rating, google_reviews, wikidata_sitelinks, google_types"
    ).eq("in_golden_list", True).filter(
        "popularity_score", "gte", 85  # Increased from 70 to 85 - only very famous POIs
    ).limit(200).execute()  # Consider top 200 golden POIs
    
    if not result.data:
        return []
    
    pois = result.data
    
    # Extract behavioral signals
    viewed_ids = set(user_behavior.get("viewed_place_ids", [])) if user_behavior else set()
    collected_ids = set(user_behavior.get("collected_place_ids", [])) if user_behavior else set()
    trip_ids = set(user_behavior.get("trip_place_ids", [])) if user_behavior else set()
    
    # Apply SMART SCORING with preference matching
    scored_pois = []
    
    for poi in pois:
        base_score = poi.get("popularity_score", 0)
        poi_id = poi.get("google_place_id")
        
        # Skip POIs with NULL or invalid popularity scores
        if base_score is None or base_score == 0:
            continue
        
        # Start with BASE POPULARITY (high weight for fame)
        score = float(base_score)
        
        # Layer 1: Preference Matching Boost (NEW)
        if user_preferences:
            google_types = poi.get("google_types") or []
            
            for preference in user_preferences:
                if preference in INTEREST_CATEGORIES:
                    relevant_types = INTEREST_CATEGORIES[preference]
                    for poi_type in google_types:
                        if poi_type in relevant_types:
                            score *= 1.8  # Strong boost for preference match
                            break
        
        # Layer 2: Quality Boost (reputation)
        google_rating = poi.get("google_rating", 0)
        google_reviews = poi.get("google_reviews", 0)
        
        if google_rating and google_rating >= 4.5 and google_reviews >= 100:
            score *= 1.3  # Boost highly-reviewed famous POIs
        
        # Layer 3: Behavioral Boost (personalization)
        if poi_id in trip_ids:
            score *= 1.5  # User actively used in trip
        elif poi_id in collected_ids:
            score *= 1.3  # User bookmarked
        elif poi_id in viewed_ids:
            score *= 1.1  # User viewed
        
        scored_pois.append({
            "google_place_id": poi_id,
            "name": poi.get("name"),
            "state": poi.get("state"),
            "lat": poi.get("lat"),
            "lon": poi.get("lon"),
            "score": round(score, 2),
            "popularity_score": base_score,
            "google_rating": google_rating
        })
    
    # Sort by score to identify top candidates
    scored_pois.sort(key=lambda x: x["score"], reverse=True)
    
    # Get top 50 candidates for sampling pool (only the most famous/relevant)
    candidate_pool_size = min(50, len(scored_pois))
    candidates = scored_pois[:candidate_pool_size]
    
    # If we have fewer candidates than requested, return all
    if len(candidates) <= top_n:
        return candidates
    
    # Extract scores for weighted sampling
    scores = [poi["score"] for poi in candidates]
    
    # Weighted random sampling from top 50 (truly random on each request)
    # Higher scores = higher selection probability
    selected_pois = random.choices(
        candidates,
        weights=scores,
        k=top_n
    )
    
    # Remove duplicates while preserving order (edge case)
    seen = set()
    unique_selected = []
    for poi in selected_pois:
        if poi["google_place_id"] not in seen:
            seen.add(poi["google_place_id"])
            unique_selected.append(poi)
    
    return unique_selected

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