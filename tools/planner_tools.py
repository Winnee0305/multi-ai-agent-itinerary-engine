"""
Tools for Planner Agent - Distance calculations and itinerary sequencing using PostGIS
"""

from langchain.tools import tool
from typing import List, Dict, Any
from database.supabase_client import get_supabase


@tool
def get_poi_by_place_id(google_place_id: str) -> Dict[str, Any]:
    """
    Get POI details from Supabase by Google Place ID.
    
    Args:
        google_place_id: Google Place ID of the POI
        
    Returns:
        Dictionary with POI details (id, name, lat, lon, google_place_id, etc.)
    """
    supabase = get_supabase()
    
    result = supabase.table("osm_pois").select("*").eq("google_place_id", google_place_id).execute()
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    else:
        return {"error": f"POI not found for place_id: {google_place_id}"}


@tool
def get_pois_by_priority_list(priority_pois: List[Dict[str, Any]], limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch full POI details from Supabase for a list of priority-scored POIs.
    
    Args:
        priority_pois: List of POIs with priority_score and google_place_id
        limit: Maximum number of POIs to return
        
    Returns:
        List of POI dictionaries with full details from database
    """
    supabase = get_supabase()
    
    # Extract place IDs
    place_ids = [poi.get("google_place_id") for poi in priority_pois[:limit] if poi.get("google_place_id")]
    
    if not place_ids:
        return []
    
    result = supabase.table("osm_pois").select("*").in_("google_place_id", place_ids).execute()
    
    return result.data if result.data else []


@tool
def calculate_distance_between_pois(place_id_1: str, place_id_2: str) -> float:
    """
    Calculate distance in meters between two POIs using PostGIS.
    
    Args:
        place_id_1: Google Place ID of first POI
        place_id_2: Google Place ID of second POI
        
    Returns:
        Distance in meters
    """
    supabase = get_supabase()
    
    # Get coordinates for both POIs
    poi1 = supabase.table("osm_pois").select("lat, lon").eq("google_place_id", place_id_1).execute()
    poi2 = supabase.table("osm_pois").select("lat, lon").eq("google_place_id", place_id_2).execute()
    
    if not poi1.data or not poi2.data:
        return -1.0
    
    lat1, lon1 = poi1.data[0]["lat"], poi1.data[0]["lon"]
    lat2, lon2 = poi2.data[0]["lat"], poi2.data[0]["lon"]
    
    # Use PostGIS RPC function
    result = supabase.rpc("calculate_distance", {
        "lat1": lat1,
        "lon1": lon1,
        "lat2": lat2,
        "lon2": lon2
    }).execute()
    
    return result.data if result.data else -1.0


@tool
def get_pois_near_centroid(centroid_place_id: str, radius_meters: int = 50000, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Get POIs near a centroid POI using PostGIS spatial query.
    
    Args:
        centroid_place_id: Google Place ID of centroid POI
        radius_meters: Search radius in meters (default 50km)
        max_results: Maximum number of results
        
    Returns:
        List of nearby POIs with distance_meters field
    """
    supabase = get_supabase()
    
    # Get centroid coordinates
    centroid = supabase.table("osm_pois").select("lat, lon").eq("google_place_id", centroid_place_id).execute()
    
    if not centroid.data:
        return []
    
    center_lat = centroid.data[0]["lat"]
    center_lon = centroid.data[0]["lon"]
    
    # Use PostGIS RPC function to find nearby POIs
    result = supabase.rpc("get_nearby_pois", {
        "center_lat": center_lat,
        "center_lon": center_lon,
        "radius_m": radius_meters,
        "min_pop": 50,
        "golden_only": False,
        "max_results": max_results
    }).execute()
    
    return result.data if result.data else []


@tool
def calculate_distances_from_centroid(centroid_place_id: str, poi_place_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Calculate distances from centroid to multiple POIs.
    
    Args:
        centroid_place_id: Google Place ID of centroid
        poi_place_ids: List of Google Place IDs to calculate distances to
        
    Returns:
        List of dictionaries with {google_place_id, name, distance_meters}
    """
    supabase = get_supabase()
    
    # Get centroid coordinates
    centroid = supabase.table("osm_pois").select("id, lat, lon").eq("google_place_id", centroid_place_id).execute()
    
    if not centroid.data:
        return []
    
    center_lat = centroid.data[0]["lat"]
    center_lon = centroid.data[0]["lon"]
    
    # Get POI IDs from place_ids
    pois = supabase.table("osm_pois").select("id, google_place_id, name").in_("google_place_id", poi_place_ids).execute()
    
    if not pois.data:
        return []
    
    poi_ids = [poi["id"] for poi in pois.data]
    
    # Use PostGIS RPC function
    result = supabase.rpc("get_pois_with_distances", {
        "poi_ids": poi_ids,
        "center_lat": center_lat,
        "center_lon": center_lon
    }).execute()
    
    if not result.data:
        return []
    
    # Add google_place_id to results
    place_id_map = {poi["id"]: poi["google_place_id"] for poi in pois.data}
    
    for item in result.data:
        item["google_place_id"] = place_id_map.get(item["id"])
    
    return result.data


@tool
def select_best_centroid(top_priority_pois: List[Dict[str, Any]], consider_top_n: int = 5) -> Dict[str, Any]:
    """
    Select the best centroid from top N priority POIs.
    Simply returns the highest priority POI as centroid.
    
    Args:
        top_priority_pois: List of POIs sorted by priority_score
        consider_top_n: Consider top N POIs (default 5)
        
    Returns:
        Best centroid POI with reason
    """
    if not top_priority_pois:
        return {"error": "No POIs provided"}
    
    # Simple strategy: pick the highest priority POI
    candidates = top_priority_pois[:consider_top_n]
    centroid = candidates[0]
    
    return {
        "google_place_id": centroid.get("google_place_id"),
        "name": centroid.get("name"),
        "priority_score": centroid.get("priority_score"),
        "lat": centroid.get("lat"),
        "lon": centroid.get("lon"),
        "reason": f"Highest priority score among top {consider_top_n} POIs"
    }


@tool
def cluster_pois_by_distance(
    centroid_place_id: str,
    poi_list: List[Dict[str, Any]],
    max_distance_meters: int = 30000
) -> Dict[str, Any]:
    """
    Cluster POIs based on distance from centroid.
    
    Args:
        centroid_place_id: Google Place ID of centroid
        poi_list: List of POIs with google_place_id
        max_distance_meters: Maximum distance for clustering (default 30km)
        
    Returns:
        Dictionary with 'nearby' and 'far' POI lists
    """
    place_ids = [poi.get("google_place_id") for poi in poi_list if poi.get("google_place_id")]
    
    if not place_ids:
        return {"nearby": [], "far": []}
    
    # Calculate distances
    distances = calculate_distances_from_centroid(centroid_place_id, place_ids)
    
    nearby = []
    far = []
    
    for dist_info in distances:
        if dist_info["distance_meters"] <= max_distance_meters:
            nearby.append({
                "google_place_id": dist_info["google_place_id"],
                "name": dist_info["name"],
                "distance_meters": dist_info["distance_meters"]
            })
        else:
            far.append({
                "google_place_id": dist_info["google_place_id"],
                "name": dist_info["name"],
                "distance_meters": dist_info["distance_meters"]
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x["distance_meters"])
    far.sort(key=lambda x: x["distance_meters"])
    
    return {
        "nearby": nearby,
        "far": far,
        "nearby_count": len(nearby),
        "far_count": len(far)
    }


@tool
def generate_optimal_sequence(poi_place_ids: List[str], start_place_id: str) -> List[Dict[str, Any]]:
    """
    Generate optimal visit sequence using nearest neighbor algorithm.
    
    Args:
        poi_place_ids: List of Google Place IDs to sequence
        start_place_id: Starting POI (centroid)
        
    Returns:
        List of POIs in optimal sequence with {google_place_id, google_matched_name, sequence_no}
    """
    supabase = get_supabase()
    
    if not poi_place_ids:
        return []
    
    # Get full POI details
    all_place_ids = [start_place_id] + poi_place_ids
    pois = supabase.table("osm_pois").select("google_place_id, name, lat, lon").in_("google_place_id", all_place_ids).execute()
    
    if not pois.data:
        return []
    
    # Create lookup map
    poi_map = {poi["google_place_id"]: poi for poi in pois.data}
    
    # Nearest neighbor sequencing
    sequence = []
    current_place_id = start_place_id
    remaining = set(poi_place_ids)
    sequence_no = 1
    
    # Add start POI
    if current_place_id in poi_map:
        sequence.append({
            "google_place_id": current_place_id,
            "google_matched_name": poi_map[current_place_id]["name"],
            "sequence_no": sequence_no
        })
        sequence_no += 1
    
    # Greedy nearest neighbor
    while remaining:
        current_poi = poi_map.get(current_place_id)
        if not current_poi:
            break
        
        current_lat, current_lon = current_poi["lat"], current_poi["lon"]
        
        # Find nearest unvisited POI
        min_distance = float('inf')
        nearest_place_id = None
        
        for place_id in remaining:
            poi = poi_map.get(place_id)
            if not poi:
                continue
            
            # Calculate distance using PostGIS
            result = supabase.rpc("calculate_distance", {
                "lat1": current_lat,
                "lon1": current_lon,
                "lat2": poi["lat"],
                "lon2": poi["lon"]
            }).execute()
            
            distance = result.data if result.data else float('inf')
            
            if distance < min_distance:
                min_distance = distance
                nearest_place_id = place_id
        
        if nearest_place_id:
            sequence.append({
                "google_place_id": nearest_place_id,
                "google_matched_name": poi_map[nearest_place_id]["name"],
                "sequence_no": sequence_no,
                "distance_from_previous_meters": min_distance
            })
            sequence_no += 1
            remaining.remove(nearest_place_id)
            current_place_id = nearest_place_id
        else:
            break
    
    return sequence


