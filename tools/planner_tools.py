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


def extract_coordinates(pois: List[Dict[str, Any]]) -> tuple:
    """
    Extract lat/lon coordinates from POI list.
    Returns: (coords_array, poi_map)
    """
    import numpy as np
    
    coords = []
    poi_map = {}
    
    for idx, poi in enumerate(pois):
        lat = poi.get("lat")
        lon = poi.get("lon")
        
        if lat is not None and lon is not None:
            coords.append([lat, lon])
            poi_map[idx] = poi
    
    return np.array(coords), poi_map


def split_into_days_simple(
    sequence: List[Dict[str, Any]],
    trip_duration_days: int,
    max_pois_per_day: int
) -> List[Dict[str, Any]]:
    """
    Split sequence into daily chunks (simple equal distribution).
    Fallback when k-means fails or for single-day trips.
    """
    daily_itineraries = []
    
    for day_num in range(1, trip_duration_days + 1):
        start_idx = (day_num - 1) * max_pois_per_day
        end_idx = start_idx + max_pois_per_day
        
        day_pois = sequence[start_idx:end_idx]
        
        if not day_pois:
            # Empty day
            daily_itineraries.append({
                "day": day_num,
                "pois": [],
                "total_pois": 0,
                "total_distance_meters": 0,
                "message": "Flexible day - relax or revisit favorites"
            })
            continue
        
        # Renumber sequences within each day
        for seq_num, poi in enumerate(day_pois, start=1):
            poi["sequence_no"] = seq_num
        
        # Calculate total distance
        total_distance = sum(
            poi.get("distance_from_previous_meters", 0) 
            for poi in day_pois
        )
        
        daily_itineraries.append({
            "day": day_num,
            "pois": day_pois,
            "total_pois": len(day_pois),
            "total_distance_meters": round(total_distance, 2)
        })
    
    return daily_itineraries


def cluster_pois_kmeans(
    pois: List[Dict[str, Any]],
    n_clusters: int
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Cluster POIs geographically using K-Means.
    
    Args:
        pois: List of POIs with lat/lon
        n_clusters: Number of clusters (= trip_duration_days)
    
    Returns:
        Dict mapping cluster_id to list of POIs
    """
    from sklearn.cluster import KMeans
    import numpy as np
    
    if len(pois) < n_clusters:
        # Not enough POIs for clustering
        return {0: pois}  # Return all in one cluster
    
    # Extract coordinates
    coords, poi_map = extract_coordinates(pois)
    
    if len(coords) == 0:
        return {0: pois}
    
    # Run K-Means
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )
    
    cluster_labels = kmeans.fit_predict(coords)
    
    # Group POIs by cluster
    clustered_pois = {i: [] for i in range(n_clusters)}
    
    for idx, cluster_id in enumerate(cluster_labels):
        if idx in poi_map:
            clustered_pois[cluster_id].append(poi_map[idx])
    
    return clustered_pois


def order_clusters_by_proximity(
    clustered_pois: Dict[int, List[Dict]],
    start_cluster_id: int = 0
) -> List[int]:
    """
    Order clusters to minimize overnight transitions.
    Uses cluster centroids to determine order.
    
    Returns: Ordered list of cluster IDs
    """
    if len(clustered_pois) <= 1:
        return list(clustered_pois.keys())
    
    # Calculate centroid for each cluster
    centroids = {}
    for cluster_id, pois in clustered_pois.items():
        if not pois:
            continue
        avg_lat = sum(p.get("lat", 0) for p in pois) / len(pois)
        avg_lon = sum(p.get("lon", 0) for p in pois) / len(pois)
        centroids[cluster_id] = (avg_lat, avg_lon)
    
    # Greedy nearest cluster ordering
    ordered = [start_cluster_id]
    remaining = set(centroids.keys()) - {start_cluster_id}
    
    current_centroid = centroids[start_cluster_id]
    
    while remaining:
        # Find nearest cluster
        min_dist = float('inf')
        nearest_cluster = None
        
        for cluster_id in remaining:
            centroid = centroids[cluster_id]
            dist = haversine_distance(
                current_centroid[0], current_centroid[1],
                centroid[0], centroid[1]
            )
            if dist < min_dist:
                min_dist = dist
                nearest_cluster = cluster_id
        
        if nearest_cluster is not None:
            ordered.append(nearest_cluster)
            remaining.remove(nearest_cluster)
            current_centroid = centroids[nearest_cluster]
        else:
            break
    
    # Add any remaining clusters
    ordered.extend(remaining)
    
    return ordered


def sequence_pois_within_cluster(
    pois: List[Dict[str, Any]],
    start_poi: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Sequence POIs within a cluster using nearest neighbor.
    Similar to generate_optimal_sequence but works with POI objects.
    """
    if not pois:
        return []
    
    if start_poi is None:
        start_poi = pois[0]
    
    sequence = [start_poi]
    remaining = [p for p in pois if p != start_poi]
    
    sequence_no = 1
    start_poi["sequence_no"] = sequence_no
    start_poi["distance_from_previous_meters"] = 0
    
    current_poi = start_poi
    
    while remaining:
        # Find nearest POI
        min_dist = float('inf')
        nearest_poi = None
        
        for poi in remaining:
            dist = haversine_distance(
                current_poi["lat"], current_poi["lon"],
                poi["lat"], poi["lon"]
            )
            if dist < min_dist:
                min_dist = dist
                nearest_poi = poi
        
        if nearest_poi:
            sequence_no += 1
            nearest_poi["sequence_no"] = sequence_no
            nearest_poi["distance_from_previous_meters"] = round(min_dist, 2)
            sequence.append(nearest_poi)
            remaining.remove(nearest_poi)
            current_poi = nearest_poi
        else:
            break
    
    return sequence


def split_into_days_kmeans(
    sequence: List[Dict[str, Any]],
    trip_duration_days: int,
    max_pois_per_day: int
) -> List[Dict[str, Any]]:
    """
    Split sequence into daily itineraries using K-Means geographic clustering.
    
    Algorithm:
    1. Cluster POIs geographically into K groups (K = trip_duration_days)
    2. Order clusters to minimize overnight transitions
    3. Sequence POIs within each cluster using nearest neighbor
    4. Balance cluster sizes if needed
    """
    if trip_duration_days == 1:
        # Single day trip - no clustering needed
        return split_into_days_simple(sequence, 1, max_pois_per_day)
    
    if len(sequence) < trip_duration_days:
        # Not enough POIs for clustering
        return split_into_days_simple(sequence, trip_duration_days, max_pois_per_day)
    
    try:
        # Step 1: Cluster POIs
        clustered_pois = cluster_pois_kmeans(sequence, trip_duration_days)
        
        # Step 2: Order clusters
        ordered_cluster_ids = order_clusters_by_proximity(clustered_pois)
        
        # Step 3: Create daily itineraries
        daily_itineraries = []
        prev_day_end_poi = None
        
        for day_num, cluster_id in enumerate(ordered_cluster_ids, start=1):
            cluster_pois = clustered_pois[cluster_id]
            
            if not cluster_pois:
                daily_itineraries.append({
                    "day": day_num,
                    "pois": [],
                    "total_pois": 0,
                    "total_distance_meters": 0,
                    "message": "Flexible day"
                })
                continue
            
            # Determine starting POI for this day
            if prev_day_end_poi is not None:
                # Find closest POI to previous day's end
                min_dist = float('inf')
                start_poi = cluster_pois[0]
                
                for poi in cluster_pois:
                    dist = haversine_distance(
                        prev_day_end_poi["lat"], prev_day_end_poi["lon"],
                        poi["lat"], poi["lon"]
                    )
                    if dist < min_dist:
                        min_dist = dist
                        start_poi = poi
            else:
                start_poi = cluster_pois[0]
            
            # Sequence POIs within cluster
            day_sequence = sequence_pois_within_cluster(cluster_pois, start_poi)
            
            # Limit to max_pois_per_day
            day_sequence = day_sequence[:max_pois_per_day]
            
            # Calculate total distance
            total_distance = sum(
                poi.get("distance_from_previous_meters", 0)
                for poi in day_sequence
            )
            
            # Calculate overnight transition if not first day
            overnight_transition = None
            if prev_day_end_poi is not None and day_sequence:
                transition_dist = haversine_distance(
                    prev_day_end_poi["lat"], prev_day_end_poi["lon"],
                    day_sequence[0]["lat"], day_sequence[0]["lon"]
                )
                overnight_transition = {
                    "from_poi": prev_day_end_poi.get("google_matched_name") or prev_day_end_poi.get("name", "Unknown"),
                    "to_poi": day_sequence[0].get("google_matched_name") or day_sequence[0].get("name", "Unknown"),
                    "distance_meters": round(transition_dist, 2)
                }
            
            daily_itineraries.append({
                "day": day_num,
                "pois": day_sequence,
                "total_pois": len(day_sequence),
                "total_distance_meters": round(total_distance, 2),
                "overnight_transition": overnight_transition
            })
            
            # Update for next iteration
            if day_sequence:
                prev_day_end_poi = day_sequence[-1]
        
        return daily_itineraries
    
    except Exception as e:
        # Fallback to simple splitting if k-means fails
        print(f"K-Means clustering failed: {e}. Falling back to simple split.")
        return split_into_days_simple(sequence, trip_duration_days, max_pois_per_day)


def plan_itinerary_logic(
    priority_pois: List[Dict[str, Any]],
    trip_duration_days: int = 1,
    max_pois_per_day: int = 6,
    max_distance_threshold: int = 30000,
    clustering_strategy: str = "kmeans"
) -> Dict[str, Any]:
    """
    Orchestrator logic for planning with multi-day support.
    
    Args:
        priority_pois: List of POIs sorted by priority score
        trip_duration_days: Number of days for the trip
        max_pois_per_day: Maximum POIs to visit per day
        max_distance_threshold: Distance threshold for clustering (meters)
        clustering_strategy: "simple" | "kmeans" - Day splitting strategy
    
    Returns:
        Dict with daily_itineraries, trip_summary, and metadata
    """
    # 1. Select Centroid
    centroid_info = select_best_centroid(priority_pois)
    if "error" in centroid_info:
        return {"error": "Could not select centroid"}
        
    centroid_id = centroid_info["google_place_id"]
    
    # 2. Cluster by distance (nearby vs far)
    clusters = cluster_pois_by_distance(centroid_id, priority_pois, max_distance_threshold)
    
    # 3. Limit to realistic number of POIs
    max_total_pois = trip_duration_days * max_pois_per_day
    target_pois = [p["google_place_id"] for p in clusters["nearby"][:max_total_pois]]
    
    # Remove centroid from target list to avoid duplication
    if centroid_id in target_pois:
        target_pois.remove(centroid_id)
    
    # 4. Generate initial sequence (nearest neighbor)
    sequence = generate_optimal_sequence(target_pois, centroid_id)
    
    # 5. Split into daily itineraries
    if clustering_strategy == "kmeans":
        daily_itineraries = split_into_days_kmeans(
            sequence, trip_duration_days, max_pois_per_day
        )
    else:  # "simple"
        daily_itineraries = split_into_days_simple(
            sequence, trip_duration_days, max_pois_per_day
        )
    
    # 6. Calculate trip summary
    total_pois = sum(day["total_pois"] for day in daily_itineraries)
    total_distance = sum(day["total_distance_meters"] for day in daily_itineraries)
    
    return {
        "trip_duration_days": trip_duration_days,
        "centroid": centroid_info,
        "daily_itineraries": daily_itineraries,
        "trip_summary": {
            "total_pois": total_pois,
            "total_days": trip_duration_days,
            "total_distance_meters": round(total_distance, 2),
            "avg_pois_per_day": round(total_pois / trip_duration_days, 1) if trip_duration_days > 0 else 0,
            "avg_distance_per_day_meters": round(total_distance / trip_duration_days, 2) if trip_duration_days > 0 else 0
        },
        "clustering_strategy_used": clustering_strategy,
        "clusters": clusters  # Keep for debugging
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