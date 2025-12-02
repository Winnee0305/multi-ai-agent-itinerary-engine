"""
Tools for Planner Agent - Distance calculations and itinerary sequencing using PostGIS
"""

from langchain_core.tools import StructuredTool
from typing import List, Dict, Any, Optional
from database.supabase_client import get_supabase
import math

# ==============================================================================
# 1. HELPER FUNCTIONS (Pure Python)
# ==============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Returns distance in meters.
    """
    R = 6371000  # Radius of earth in meters
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# ==============================================================================
# 2. CORE LOGIC (Public Functions - No Decorators)
# ==============================================================================

def get_poi_by_place_id(google_place_id: str) -> Dict[str, Any]:
    """Internal logic to get POI details."""
    supabase = get_supabase()
    result = supabase.table("osm_pois").select("*").eq("google_place_id", google_place_id).execute()
    
    if result.data and len(result.data) > 0:
        return result.data[0]
    return {"error": f"POI not found for place_id: {google_place_id}"}


def get_pois_by_priority_list(priority_pois: List[Dict[str, Any]], limit: int = 50) -> List[Dict[str, Any]]:
    """Internal logic to fetch full details."""
    supabase = get_supabase()
    place_ids = [poi.get("google_place_id") for poi in priority_pois[:limit] if poi.get("google_place_id")]
    
    if not place_ids:
        return []
    
    result = supabase.table("osm_pois").select("*").in_("google_place_id", place_ids).execute()
    return result.data if result.data else []


def calculate_distance_between_pois(place_id_1: str, place_id_2: str) -> float:
    """Internal logic for single distance calc."""
    supabase = get_supabase()
    
    # Optimized: Fetch both in one query
    result = supabase.table("osm_pois").select("lat, lon").in_("google_place_id", [place_id_1, place_id_2]).execute()
    
    if not result.data or len(result.data) < 2:
        return -1.0
        
    # We don't know which order they came back in, but distance is symmetric
    p1 = result.data[0]
    p2 = result.data[1]
    
    return haversine_distance(p1['lat'], p1['lon'], p2['lat'], p2['lon'])


def get_pois_near_centroid(centroid_place_id: str, radius_meters: int = 50000, max_results: int = 50) -> List[Dict[str, Any]]:
    """Internal logic for radial search."""
    supabase = get_supabase()
    centroid = supabase.table("osm_pois").select("lat, lon").eq("google_place_id", centroid_place_id).execute()
    
    if not centroid.data:
        return []
    
    center_lat = centroid.data[0]["lat"]
    center_lon = centroid.data[0]["lon"]
    
    # Use PostGIS for the initial heavy filtering (finding neighbors)
    result = supabase.rpc("get_nearby_pois", {
        "center_lat": center_lat,
        "center_lon": center_lon,
        "radius_m": radius_meters,
        "min_pop": 50,
        "golden_only": False,
        "max_results": max_results
    }).execute()
    
    return result.data if result.data else []


def calculate_distances_from_centroid(centroid_place_id: str, poi_place_ids: List[str]) -> List[Dict[str, Any]]:
    """Internal logic for batch distance calc."""
    supabase = get_supabase()
    
    # 1. Get Centroid
    centroid = supabase.table("osm_pois").select("id, lat, lon").eq("google_place_id", centroid_place_id).execute()
    if not centroid.data:
        return []
    
    center_lat = centroid.data[0]["lat"]
    center_lon = centroid.data[0]["lon"]
    
    # 2. Get Targets
    pois = supabase.table("osm_pois").select("id, google_place_id, name, lat, lon").in_("google_place_id", poi_place_ids).execute()
    if not pois.data:
        return []
        
    results = []
    
    # 3. Calculate locally (Much faster than RPC for batch of 20-50)
    for poi in pois.data:
        dist = haversine_distance(center_lat, center_lon, poi['lat'], poi['lon'])
        results.append({
            "id": poi['id'],
            "google_place_id": poi['google_place_id'],
            "name": poi['name'],
            "distance_meters": dist
        })
        
    return results


def select_best_centroid(top_priority_pois: List[Dict[str, Any]], consider_top_n: int = 5) -> Dict[str, Any]:
    """Internal logic for centroid selection."""
    if not top_priority_pois:
        return {"error": "No POIs provided"}
    
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


def cluster_pois_by_distance(
    centroid_place_id: str,
    poi_list: List[Dict[str, Any]],
    max_distance_meters: int = 30000
) -> Dict[str, Any]:
    """Internal logic for clustering."""
    place_ids = [poi.get("google_place_id") for poi in poi_list if poi.get("google_place_id")]
    
    if not place_ids:
        return {"nearby": [], "far": []}
    
    # Call internal function
    distances = calculate_distances_from_centroid(centroid_place_id, place_ids)
    
    nearby = []
    far = []
    
    for dist_info in distances:
        item = {
            "google_place_id": dist_info["google_place_id"],
            "name": dist_info["name"],
            "distance_meters": dist_info["distance_meters"]
        }
        if dist_info["distance_meters"] <= max_distance_meters:
            nearby.append(item)
        else:
            far.append(item)
    
    nearby.sort(key=lambda x: x["distance_meters"])
    far.sort(key=lambda x: x["distance_meters"])
    
    return {
        "nearby": nearby,
        "far": far,
        "nearby_count": len(nearby),
        "far_count": len(far)
    }


def generate_optimal_sequence(poi_place_ids: List[str], start_place_id: str) -> List[Dict[str, Any]]:
    """Internal logic for sequencing (OPTIMIZED)."""
    supabase = get_supabase()
    
    if not poi_place_ids:
        return []
    
    # 1. Fetch ALL data in ONE network call
    all_place_ids = list(set([start_place_id] + poi_place_ids))
    pois = supabase.table("osm_pois").select("google_place_id, name, lat, lon").in_("google_place_id", all_place_ids).execute()
    
    if not pois.data:
        return []
    
    poi_map = {poi["google_place_id"]: poi for poi in pois.data}
    
    # 2. Sequencing logic (Pure Python, no network calls)
    sequence = []
    current_place_id = start_place_id
    remaining = set(poi_place_ids)
    # Remove start from remaining if it's there
    if start_place_id in remaining:
        remaining.remove(start_place_id)
        
    sequence_no = 1
    
    # Add start POI
    if current_place_id in poi_map:
        sequence.append({
            "google_place_id": current_place_id,
            "google_matched_name": poi_map[current_place_id]["name"],
            "sequence_no": sequence_no,
            "distance_from_previous_meters": 0
        })
        sequence_no += 1
    
    while remaining:
        current_poi = poi_map.get(current_place_id)
        if not current_poi:
            break
        
        current_lat, current_lon = current_poi["lat"], current_poi["lon"]
        
        min_distance = float('inf')
        nearest_place_id = None
        
        # Calculate distance to all remaining neighbors in MEMORY
        for place_id in remaining:
            poi = poi_map.get(place_id)
            if not poi:
                continue
            
            # Use local haversine function
            distance = haversine_distance(
                current_lat, current_lon, 
                poi["lat"], poi["lon"]
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_place_id = place_id
        
        if nearest_place_id:
            sequence.append({
                "google_place_id": nearest_place_id,
                "google_matched_name": poi_map[nearest_place_id]["name"],
                "sequence_no": sequence_no,
                "distance_from_previous_meters": round(min_distance, 2)
            })
            sequence_no += 1
            remaining.remove(nearest_place_id)
            current_place_id = nearest_place_id
        else:
            break
            
    return sequence


def plan_itinerary_logic(
    priority_pois: List[Dict[str, Any]],
    max_pois_per_day: int = 6,
    max_distance_threshold: int = 30000
) -> Dict[str, Any]:
    """
    Orchestrator logic for planning.
    Combines centroid selection, clustering, and sequencing.
    """
    # 1. Select Centroid
    centroid_info = select_best_centroid(priority_pois)
    if "error" in centroid_info:
        return {"error": "Could not select centroid"}
        
    centroid_id = centroid_info["google_place_id"]
    
    # 2. Cluster
    clusters = cluster_pois_by_distance(centroid_id, priority_pois, max_distance_threshold)
    
    # 3. Sequence (Focus on 'nearby' cluster for now)
    target_pois = [p["google_place_id"] for p in clusters["nearby"]]
    
    # Remove centroid from target list to avoid duplication if it's in there
    if centroid_id in target_pois:
        target_pois.remove(centroid_id)
        
    sequence = generate_optimal_sequence(target_pois, centroid_id)
    
    return {
        "centroid": centroid_info,
        "clusters": clusters,
        "optimized_sequence": sequence,
        "total_pois": len(sequence)
    }

# ==============================================================================
# 3. EXPORTED TOOLS (Wrappers)
# ==============================================================================

get_poi_by_place_id_tool = StructuredTool.from_function(
    func=get_poi_by_place_id,
    name="get_poi_by_place_id",
    description="Get POI details by place ID."
)

get_pois_by_priority_list_tool = StructuredTool.from_function(
    func=get_pois_by_priority_list,
    name="get_pois_by_priority_list",
    description="Fetch full POI details for a list of priority-scored POIs."
)

calculate_distance_tool = StructuredTool.from_function(
    func=calculate_distance_between_pois,
    name="calculate_distance_between_pois",
    description="Calculate distance in meters between two POIs."
)

get_pois_near_centroid_tool = StructuredTool.from_function(
    func=get_pois_near_centroid,
    name="get_pois_near_centroid",
    description="Get POIs near a centroid POI."
)

select_best_centroid_tool = StructuredTool.from_function(
    func=select_best_centroid,
    name="select_best_centroid",
    description="Select the best centroid from top priority POIs."
)

cluster_pois_tool = StructuredTool.from_function(
    func=cluster_pois_by_distance,
    name="cluster_pois_by_distance",
    description="Cluster POIs based on distance from centroid."
)

generate_optimal_sequence_tool = StructuredTool.from_function(
    func=generate_optimal_sequence,
    name="generate_optimal_sequence",
    description="Generate optimal visit sequence using nearest neighbor algorithm."
)

# Main orchestrator tool
plan_itinerary_tool = StructuredTool.from_function(
    func=plan_itinerary_logic,
    name="plan_itinerary_logic",
    description="Complete workflow: Selects centroid, clusters POIs, and sequences them."
)