"""
LangChain tools for PostGIS distance calculations
"""

from typing import List, Dict, Optional, Tuple
from langchain.tools import tool
from database.supabase_client import get_supabase
from config.settings import settings


@tool
def get_pois_near_location(
    lat: float,
    lon: float,
    radius_meters: int = 5000,
    min_popularity: int = 0,
    only_golden: bool = False,
    limit: int = 20
) -> List[Dict]:
    """
    Get POIs within a radius of a location, ordered by distance.
    Uses PostGIS ST_DWithin for efficient spatial query.
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_meters: Search radius in meters (default: 5000m = 5km)
        min_popularity: Minimum popularity score filter
        only_golden: If True, only return golden list POIs
        limit: Maximum number of POIs to return
    
    Returns:
        List of POIs with distance_meters field added
    """
    supabase = get_supabase()
    
    # Build RPC call for PostGIS query
    # Note: You need to create this RPC function in Supabase
    try:
        result = supabase.rpc(
            "get_nearby_pois",
            {
                "center_lat": lat,
                "center_lon": lon,
                "radius_m": radius_meters,
                "min_pop": min_popularity,
                "golden_only": only_golden,
                "max_results": limit
            }
        ).execute()
        
        return result.data
    except Exception as e:
        print(f"Error querying nearby POIs: {e}")
        print("Note: Make sure the 'get_nearby_pois' RPC function exists in Supabase")
        return []


@tool
def calculate_travel_distance(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float
) -> float:
    """
    Calculate straight-line distance between two points in meters using PostGIS.
    
    Args:
        from_lat: Starting point latitude
        from_lon: Starting point longitude
        to_lat: Destination point latitude
        to_lon: Destination point longitude
    
    Returns:
        Distance in meters (float)
    """
    supabase = get_supabase()
    
    try:
        result = supabase.rpc(
            "calculate_distance",
            {
                "lat1": from_lat,
                "lon1": from_lon,
                "lat2": to_lat,
                "lon2": to_lon
            }
        ).execute()
        
        return result.data
    except Exception as e:
        print(f"Error calculating distance: {e}")
        # Fallback to Haversine formula
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth's radius in meters
        
        lat1, lon1 = radians(from_lat), radians(from_lon)
        lat2, lon2 = radians(to_lat), radians(to_lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


@tool
def get_poi_distances_from_point(
    poi_ids: List[int],
    center_lat: float,
    center_lon: float
) -> List[Dict]:
    """
    Calculate distances from a center point to multiple POIs.
    
    Args:
        poi_ids: List of POI IDs to calculate distances for
        center_lat: Center point latitude
        center_lon: Center point longitude
    
    Returns:
        List of dicts with {poi_id, distance_meters}
    """
    supabase = get_supabase()
    
    # Get POI coordinates
    try:
        result = supabase.table("osm_pois").select("id, lat, lon").in_("id", poi_ids).execute()
        pois = result.data
        
        distances = []
        for poi in pois:
            distance = calculate_travel_distance.invoke({
                "from_lat": center_lat,
                "from_lon": center_lon,
                "to_lat": poi["lat"],
                "to_lon": poi["lon"]
            })
            
            distances.append({
                "poi_id": poi["id"],
                "distance_meters": distance,
                "distance_km": round(distance / 1000, 2)
            })
        
        # Sort by distance
        distances.sort(key=lambda x: x["distance_meters"])
        
        return distances
    except Exception as e:
        print(f"Error calculating POI distances: {e}")
        return []


@tool
def calculate_route_total_distance(poi_ids: List[int]) -> Dict:
    """
    Calculate total travel distance for a route visiting POIs in order.
    
    Args:
        poi_ids: List of POI IDs in visit order
    
    Returns:
        Dict with total_distance_meters, total_distance_km, and segment distances
    """
    supabase = get_supabase()
    
    if len(poi_ids) < 2:
        return {"total_distance_meters": 0, "total_distance_km": 0, "segments": []}
    
    try:
        # Get POI coordinates
        result = supabase.table("osm_pois").select("id, name, lat, lon").in_("id", poi_ids).execute()
        pois_data = {poi["id"]: poi for poi in result.data}
        
        # Maintain order from poi_ids
        ordered_pois = [pois_data[pid] for pid in poi_ids if pid in pois_data]
        
        segments = []
        total_distance = 0
        
        for i in range(len(ordered_pois) - 1):
            from_poi = ordered_pois[i]
            to_poi = ordered_pois[i + 1]
            
            distance = calculate_travel_distance.invoke({
                "from_lat": from_poi["lat"],
                "from_lon": from_poi["lon"],
                "to_lat": to_poi["lat"],
                "to_lon": to_poi["lon"]
            })
            
            total_distance += distance
            
            segments.append({
                "from": from_poi["name"],
                "to": to_poi["name"],
                "distance_meters": distance,
                "distance_km": round(distance / 1000, 2)
            })
        
        return {
            "total_distance_meters": total_distance,
            "total_distance_km": round(total_distance / 1000, 2),
            "segments": segments
        }
    except Exception as e:
        print(f"Error calculating route distance: {e}")
        return {"total_distance_meters": 0, "total_distance_km": 0, "segments": []}
