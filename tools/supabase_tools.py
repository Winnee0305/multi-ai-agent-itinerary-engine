"""
LangChain tools for querying POIs from Supabase with filters
"""

from typing import List, Dict, Optional
from langchain.tools import tool
from database.supabase_client import get_supabase
from config.settings import settings


@tool
def get_pois_by_filters(
    state: Optional[str] = None,
    min_popularity: int = 0,
    only_golden: bool = True,
    limit: int = 50
) -> List[Dict]:
    """
    Query POIs from Supabase database with filters.
    
    Args:
        state: Malaysian state name (e.g., "Penang", "Kuala Lumpur", "Malacca")
        min_popularity: Minimum popularity score threshold (0-200)
        only_golden: If True, only return golden list POIs
        limit: Maximum number of POIs to return
    
    Returns:
        List of POI dictionaries with all enriched data
    """
    supabase = get_supabase()
    
    query = supabase.table("osm_pois").select("*")
    
    # Apply filters
    if state:
        query = query.eq("state", state)
    
    if only_golden:
        query = query.eq("in_golden_list", True)
    
    query = query.gte("popularity_score", min_popularity)
    query = query.order("popularity_score", desc=True)
    query = query.limit(limit)
    
    try:
        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Error querying POIs: {e}")
        return []


@tool
def get_poi_by_id(poi_id: int) -> Optional[Dict]:
    """
    Get a specific POI by its ID.
    
    Args:
        poi_id: The POI's unique identifier
    
    Returns:
        POI dictionary or None if not found
    """
    supabase = get_supabase()
    
    try:
        result = supabase.table("osm_pois").select("*").eq("id", poi_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error fetching POI {poi_id}: {e}")
        return None


@tool
def search_pois_by_name(
    search_term: str,
    state: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Search POIs by name using fuzzy text matching.
    
    Args:
        search_term: Name or partial name to search for
        state: Optional state filter
        limit: Maximum results to return
    
    Returns:
        List of matching POIs
    """
    supabase = get_supabase()
    
    query = supabase.table("osm_pois").select("*")
    
    # Use ilike for case-insensitive pattern matching
    query = query.ilike("name", f"%{search_term}%")
    
    if state:
        query = query.eq("state", state)
    
    query = query.order("popularity_score", desc=True)
    query = query.limit(limit)
    
    try:
        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Error searching POIs: {e}")
        return []


@tool
def get_pois_by_types(
    place_types: List[str],
    state: Optional[str] = None,
    min_popularity: int = 70,
    limit: int = 20
) -> List[Dict]:
    """
    Get POIs that match specific Google Places types.
    
    Args:
        place_types: List of Google Places types (e.g., ["museum", "art_gallery"])
        state: Optional state filter
        min_popularity: Minimum popularity score
        limit: Maximum results
    
    Returns:
        List of matching POIs
    """
    supabase = get_supabase()
    
    query = supabase.table("osm_pois").select("*")
    
    # Filter by types (check if any type in google_types array matches)
    # Note: This requires the @> operator in PostgreSQL (contains)
    query = query.filter("google_types", "cs", f"{{{','.join(place_types)}}}")
    
    if state:
        query = query.eq("state", state)
    
    query = query.gte("popularity_score", min_popularity)
    query = query.order("popularity_score", desc=True)
    query = query.limit(limit)
    
    try:
        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Error querying POIs by types: {e}")
        return []


@tool  
def get_all_states() -> List[str]:
    """
    Get list of all Malaysian states in the database.
    
    Returns:
        List of state names
    """
    supabase = get_supabase()
    
    try:
        result = supabase.table("osm_pois").select("state").execute()
        states = list(set(poi["state"] for poi in result.data if poi.get("state")))
        return sorted(states)
    except Exception as e:
        print(f"Error fetching states: {e}")
        return []
