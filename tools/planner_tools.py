"""
Tools for Planner Agent - Distance calculations and itinerary sequencing using PostGIS
"""

from langchain_core.tools import StructuredTool
from typing import List, Dict, Any, Optional
from database.supabase_client import get_supabase
import math
import random
from datetime import datetime

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

def _generate_seed_for_sequencing(rotation_hours: int = 6) -> int:
    """
    Generate a deterministic seed based on time windows for sequence randomization.
    Same seed within rotation_hours window for consistency, changes after.
    
    Args:
        rotation_hours: Duration of time window in hours (default 6)
        
    Returns:
        Integer seed for random number generation
    """
    now = datetime.utcnow()
    time_window = now.replace(
        hour=(now.hour // rotation_hours) * rotation_hours,
        minute=0,
        second=0,
        microsecond=0
    )
    return int(time_window.timestamp())

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


# K-Means clustering functions removed - now using anchor-based clustering only


def sequence_pois_within_cluster(
    pois: List[Dict[str, Any]],
    start_poi: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Sequence POIs within a cluster using nearest neighbor.
    Randomly selects start point for variety (different on every generation).
    """
    if not pois:
        return []
    
    if start_poi is None:
        # Randomly select starting POI (unique each time)
        start_idx = random.randint(0, len(pois) - 1)
        start_poi = pois[start_idx]
    
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


def identify_anchors(priority_pois: List[Dict[str, Any]]) -> tuple:
    """
    Separate preferred POIs (anchors) from regular POIs.
    
    Args:
        priority_pois: All POIs with is_preferred flags
    
    Returns:
        (anchors, regular_pois)
    """
    anchors = [poi for poi in priority_pois if poi.get("is_preferred", False)]
    regular = [poi for poi in priority_pois if not poi.get("is_preferred", False)]
    
    return anchors, regular


def cluster_anchors_by_proximity(
    anchors: List[Dict[str, Any]],
    proximity_threshold_meters: int = 30000
) -> List[List[Dict[str, Any]]]:
    """
    Group anchors that are geographically close.
    
    Algorithm:
    1. Start with first anchor as cluster seed
    2. Add nearby anchors (< threshold) to same cluster
    3. Distant anchors start new clusters
    4. Use greedy agglomerative approach
    
    Args:
        anchors: List of preferred POIs
        proximity_threshold_meters: Distance threshold (default 30km)
    
    Returns:
        List of anchor clusters (each cluster = 1 day skeleton)
    """
    if not anchors:
        return []
    
    clusters = []
    remaining = anchors.copy()
    
    while remaining:
        # Start new cluster with first remaining anchor
        current_cluster = [remaining.pop(0)]
        
        # Find all nearby anchors
        i = 0
        while i < len(remaining):
            anchor = remaining[i]
            
            # Check distance to any POI in current cluster
            is_nearby = False
            for cluster_poi in current_cluster:
                dist = haversine_distance(
                    anchor["lat"], anchor["lon"],
                    cluster_poi["lat"], cluster_poi["lon"]
                )
                if dist <= proximity_threshold_meters:
                    is_nearby = True
                    break
            
            if is_nearby:
                current_cluster.append(remaining.pop(i))
                # Don't increment i, we removed an element
            else:
                i += 1
        
        clusters.append(current_cluster)
    
    return clusters


def map_anchor_clusters_to_days(
    anchor_clusters: List[List[Dict]],
    trip_duration_days: int,
    max_pois_per_day: int
) -> Dict[int, Dict]:
    """
    Assign anchor clusters to specific days.
    
    Strategy:
    - If anchors < days: Spread them out, leave flexible days
    - If anchors == days: 1 anchor cluster per day
    - If anchors > days: Priority merge of nearby clusters
    
    Returns:
        {day_num: {"anchors": [...], "capacity": remaining_slots}}
    """
    day_assignments = {}
    num_clusters = len(anchor_clusters)
    
    if num_clusters == 0:
        # No anchors, all days flexible
        for day in range(1, trip_duration_days + 1):
            day_assignments[day] = {"anchors": [], "capacity": max_pois_per_day}
    
    elif num_clusters <= trip_duration_days:
        # Distribute anchor clusters across days
        for day_num, cluster in enumerate(anchor_clusters, start=1):
            day_assignments[day_num] = {
                "anchors": cluster,
                "capacity": max(0, max_pois_per_day - len(cluster))
            }
        
        # Fill remaining days as flexible
        for day in range(num_clusters + 1, trip_duration_days + 1):
            day_assignments[day] = {"anchors": [], "capacity": max_pois_per_day}
    
    else:
        # More anchor clusters than days - distribute across available days
        # Strategy: Put multiple small clusters on same day
        for day_num in range(1, trip_duration_days + 1):
            day_assignments[day_num] = {"anchors": [], "capacity": max_pois_per_day}
        
        # Distribute clusters across days
        for idx, cluster in enumerate(anchor_clusters):
            day_num = (idx % trip_duration_days) + 1
            day_assignments[day_num]["anchors"].extend(cluster)
            day_assignments[day_num]["capacity"] = max(
                0, 
                max_pois_per_day - len(day_assignments[day_num]["anchors"])
            )
    
    return day_assignments


def fill_days_with_nearby_pois(
    day_assignments: Dict[int, Dict],
    regular_pois: List[Dict[str, Any]],
    max_distance_from_anchor: int = 50000
) -> Dict[int, List[Dict]]:
    """
    Fill remaining slots in each day with nearby high-priority POIs.
    
    Algorithm:
    1. For each day with capacity:
       - Calculate centroid of day's anchors
       - Find regular POIs within max_distance
       - Sort by priority score
       - Fill remaining slots
    
    Returns:
        {day_num: [all_pois_for_day]}
    """
    daily_pois = {}
    used_pois = set()
    
    # Calculate total capacity needed across all days
    total_days = len(day_assignments)
    total_capacity_needed = sum(d["capacity"] for d in day_assignments.values())
    
    for day_num in sorted(day_assignments.keys()):
        day_info = day_assignments[day_num]
        anchors = day_info["anchors"]
        capacity = day_info["capacity"]
        
        # Start with anchors
        day_pois = anchors.copy()
        
        if capacity > 0 and regular_pois:
            # Calculate day centroid
            if anchors:
                # Day has anchors - find POIs near the anchors
                centroid_lat = sum(p["lat"] for p in anchors) / len(anchors)
                centroid_lon = sum(p["lon"] for p in anchors) / len(anchors)
                use_distance_filter = True
            else:
                # Flexible day (no anchors) - use highest priority remaining POIs regardless of distance
                use_distance_filter = False
                centroid_lat = 0
                centroid_lon = 0
            
            # Find candidate POIs
            candidates = []
            for poi in regular_pois:
                if poi["google_place_id"] in used_pois:
                    continue
                
                if use_distance_filter:
                    # For days with anchors, enforce proximity requirement
                    dist = haversine_distance(
                        centroid_lat, centroid_lon,
                        poi["lat"], poi["lon"]
                    )
                    
                    if dist <= max_distance_from_anchor:
                        candidates.append({
                            "poi": poi,
                            "distance": dist,
                            "priority": poi.get("priority_score", 0)
                        })
                else:
                    # For flexible days, include all remaining POIs
                    candidates.append({
                        "poi": poi,
                        "distance": 0,  # Distance not relevant for flexible days
                        "priority": poi.get("priority_score", 0)
                    })
            
            # Sort by priority (higher is better)
            candidates.sort(key=lambda x: x["priority"], reverse=True)
            
            # Calculate remaining days and adjust selection strategy
            remaining_days = total_days - day_num + 1
            remaining_unused = len([p for p in regular_pois if p["google_place_id"] not in used_pois])
            
            # If running low on POIs, be more conservative with selection
            if remaining_unused < remaining_days * 3:  # Less than 3 POIs per remaining day
                # Take top priority POIs deterministically to ensure coverage
                selected = candidates[:capacity]
            else:
                # Randomly select from top candidates for variety
                # Take from top 2x capacity (or all if fewer available)
                top_candidates = candidates[:min(len(candidates), capacity * 2)]
                
                # Randomly sample 'capacity' POIs from top candidates
                if len(top_candidates) > capacity:
                    selected = random.sample(top_candidates, capacity)
                else:
                    selected = top_candidates
            
            # Fill remaining slots
            for candidate in selected:
                day_pois.append(candidate["poi"])
                used_pois.add(candidate["poi"]["google_place_id"])
        
        daily_pois[day_num] = day_pois
    
    return daily_pois


def sequence_daily_pois(
    daily_pois: Dict[int, List[Dict]],
    prev_day_end_poi: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Apply nearest-neighbor sequencing within each day.
    
    Args:
        daily_pois: Dict mapping day number to list of POIs
        prev_day_end_poi: Last POI from previous execution (for continuity)
    
    Returns:
        daily_itineraries with same structure as current format
    """
    daily_itineraries = []
    prev_day_last_poi = prev_day_end_poi
    
    for day_num in sorted(daily_pois.keys()):
        pois = daily_pois[day_num]
        
        if not pois:
            daily_itineraries.append({
                "day": day_num,
                "pois": [],
                "total_pois": 0,
                "total_distance_meters": 0,
                "message": "Flexible day - relax or revisit favorites"
            })
            continue
        
        # Use random start point for variety
        # Allow random selection from all POIs for maximum variety
        start_poi = None
        
        # Sequence using nearest neighbor
        sequenced = sequence_pois_within_cluster(pois, start_poi)
        
        # Calculate stats
        total_distance = sum(
            poi.get("distance_from_previous_meters", 0)
            for poi in sequenced
        )
        
        # Calculate overnight transition if not first day
        overnight_transition = None
        if prev_day_last_poi is not None and sequenced:
            transition_dist = haversine_distance(
                prev_day_last_poi["lat"], prev_day_last_poi["lon"],
                sequenced[0]["lat"], sequenced[0]["lon"]
            )
            overnight_transition = {
                "from_poi": prev_day_last_poi.get("name", "Unknown"),
                "to_poi": sequenced[0].get("name", "Unknown"),
                "distance_meters": round(transition_dist, 2)
            }
        
        daily_itineraries.append({
            "day": day_num,
            "pois": sequenced,
            "total_pois": len(sequenced),
            "total_distance_meters": round(total_distance, 2),
            "overnight_transition": overnight_transition
        })
        
        # Update for next iteration
        if sequenced:
            prev_day_last_poi = sequenced[-1]
    
    return daily_itineraries


def plan_itinerary_anchor_based(
    priority_pois: List[Dict[str, Any]],
    trip_duration_days: int = 1,
    max_pois_per_day: int = 6,
    anchor_proximity_threshold: int = 30000,
    poi_search_radius: int = 50000
) -> Dict[str, Any]:
    """
    Anchor-based itinerary planning - preferred POIs define the trip skeleton.
    
    Workflow:
    1. Identify anchors (preferred POIs)
    2. Cluster anchors by geographic proximity
    3. Assign anchor clusters to days
    4. Fill days with nearby regular POIs
    5. Sequence each day's POIs using nearest neighbor
    
    Args:
        priority_pois: All POIs with is_preferred flags and priority scores
        trip_duration_days: Number of days for the trip
        max_pois_per_day: Maximum POIs per day
        anchor_proximity_threshold: Distance to group anchors (meters, default 30km)
        poi_search_radius: Max distance to search for fill POIs (meters, default 50km)
    
    Returns:
        Dict with daily_itineraries, trip_summary, and metadata
    """
    # Step 1: Identify anchors
    anchors, regular_pois = identify_anchors(priority_pois)
    
    # Step 2: Cluster anchors by proximity
    anchor_clusters = cluster_anchors_by_proximity(
        anchors, 
        anchor_proximity_threshold
    )
    
    # Step 3: Map anchor clusters to days
    day_assignments = map_anchor_clusters_to_days(
        anchor_clusters,
        trip_duration_days,
        max_pois_per_day
    )
    
    # Step 4: Fill days with nearby regular POIs
    daily_pois = fill_days_with_nearby_pois(
        day_assignments,
        regular_pois,
        poi_search_radius
    )
    
    # Step 5: Sequence each day's POIs
    daily_itineraries = sequence_daily_pois(daily_pois)
    
    # Step 6: Calculate summary stats
    total_pois = sum(day["total_pois"] for day in daily_itineraries)
    total_distance = sum(day["total_distance_meters"] for day in daily_itineraries)
    
    included_preferred_count = sum(
        1 for day in daily_itineraries 
        for poi in day["pois"] 
        if poi.get("is_preferred", False)
    )
    
    # Determine centroid (first anchor or highest priority POI)
    centroid_poi = anchors[0] if anchors else (priority_pois[0] if priority_pois else None)
    
    centroid = {
        "google_place_id": centroid_poi.get("google_place_id", ""),
        "name": centroid_poi.get("name", "Unknown"),
        "priority_score": centroid_poi.get("priority_score", 0),
        "lat": centroid_poi.get("lat", 0),
        "lon": centroid_poi.get("lon", 0),
        "reason": "Primary anchor (preferred POI)" if anchors else "Highest priority POI"
    } if centroid_poi else {"error": "No POIs available"}
    
    return {
        "trip_duration_days": trip_duration_days,
        "centroid": centroid,
        "daily_itineraries": daily_itineraries,
        "trip_summary": {
            "total_pois": total_pois,
            "total_days": trip_duration_days,
            "total_distance_meters": round(total_distance, 2),
            "avg_pois_per_day": round(total_pois / trip_duration_days, 1) if trip_duration_days > 0 else 0,
            "avg_distance_per_day_meters": round(total_distance / trip_duration_days, 2) if trip_duration_days > 0 else 0,
            "preferred_pois_requested": len(anchors),
            "preferred_pois_included": included_preferred_count,
            "anchor_clusters": len(anchor_clusters)
        },
        "clustering_strategy_used": "anchor_based",
        "clusters": {"anchor_clusters": len(anchor_clusters), "days_with_anchors": len([d for d in day_assignments.values() if d["anchors"]])}
    }


def plan_itinerary_logic(
    priority_pois: List[Dict[str, Any]],
    trip_duration_days: int = 1,
    max_pois_per_day: int = 6,
    anchor_proximity_threshold: int = 30000,
    poi_search_radius: int = 50000
) -> Dict[str, Any]:
    """
    Main orchestrator for itinerary planning using anchor-based strategy.
    
    Always uses anchor-based clustering for optimal results:
    - Preferred POIs (anchors) define the trip skeleton
    - Regular POIs fill remaining slots
    - Geographic clustering ensures efficient routing
    
    Args:
        priority_pois: List of POIs with priority scores and is_preferred flags
        trip_duration_days: Number of days for the trip
        max_pois_per_day: Maximum POIs to visit per day
        anchor_proximity_threshold: Distance to group anchors (meters, default 30km)
        poi_search_radius: Max distance to search for fill POIs (meters, default 50km)
    
    Returns:
        Dict with daily_itineraries, trip_summary, and metadata
    """
    if not priority_pois:
        return {"error": "No POIs available for planning"}
    
    # Always use anchor-based clustering
    return plan_itinerary_anchor_based(
        priority_pois=priority_pois,
        trip_duration_days=trip_duration_days,
        max_pois_per_day=max_pois_per_day,
        anchor_proximity_threshold=anchor_proximity_threshold,
        poi_search_radius=poi_search_radius
    )

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
    description="[DEPRECATED] Select the best centroid from top priority POIs. Use plan_itinerary_logic instead."
)

cluster_pois_tool = StructuredTool.from_function(
    func=cluster_pois_by_distance,
    name="cluster_pois_by_distance",
    description="[DEPRECATED] Cluster POIs based on distance from centroid. Use plan_itinerary_logic instead."
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


# ==============================================================================
# 7. PACKING LIST GENERATION
# ==============================================================================

def analyze_trip_context(daily_itineraries: List[Dict], destination_state: str) -> Dict:
    """
    Analyze itinerary to extract trip context for packing list generation.
    
    Args:
        daily_itineraries: List of daily plans with POIs
        destination_state: Malaysian state name
        
    Returns:
        Dict with activities, categories, climate, and special requirements
    """
    activities = set()
    categories = set()
    special_requirements = set()
    poi_names = []
    
    # Extract from POIs
    for day in daily_itineraries:
        for poi in day.get("pois", []):
            poi_name = poi.get("name", "").lower()
            poi_names.append(poi.get("name", ""))
            category = poi.get("category", "").lower()
            categories.add(category)
            
            # Infer activities from POI names and categories
            if any(keyword in poi_name for keyword in ["gunung", "mountain", "hill", "peak", "trail", "trek"]):
                activities.add("hiking")
                activities.add("nature_walks")
            if any(keyword in poi_name for keyword in ["park", "garden", "forest", "nature", "jungle"]):
                activities.add("nature_walks")
            if any(keyword in poi_name for keyword in ["beach", "island", "pulau", "pantai", "sea"]):
                activities.add("swimming")
                activities.add("beach_activities")
            if any(keyword in poi_name for keyword in ["temple", "mosque", "church", "masjid", "kuil"]):
                activities.add("temple_visits")
                special_requirements.add("modest_clothing")
            if any(keyword in poi_name for keyword in ["theme park", "skyworlds", "legoland", "sunway"]):
                activities.add("theme_parks")
            if any(keyword in poi_name for keyword in ["mall", "shopping", "market", "bazaar"]):
                activities.add("shopping")
            if any(keyword in poi_name for keyword in ["cave", "gua"]):
                activities.add("cave_exploration")
            if any(keyword in poi_name for keyword in ["waterfall", "air terjun"]):
                activities.add("waterfall_visits")
    
    # Infer climate
    climate = infer_climate(destination_state, poi_names)
    
    return {
        "activities": sorted(list(activities)),
        "categories": sorted(list(categories)),
        "special_requirements": sorted(list(special_requirements)),
        "climate": climate,
        "poi_names": poi_names[:10]  # First 10 for context
    }


def infer_climate(state: str, poi_names: List[str]) -> str:
    """
    Infer climate based on state and POI names.
    
    Args:
        state: Malaysian state name
        poi_names: List of POI names for context
        
    Returns:
        Climate type string
    """
    poi_text = " ".join(poi_names).lower()
    
    # Check for highland indicators
    highland_keywords = ["cameron", "genting", "fraser", "highland", "bukit tinggi"]
    is_highland = any(keyword in poi_text for keyword in highland_keywords)
    
    # State-based climate
    highland_states = ["Pahang", "Perak"]
    coastal_states = ["Penang", "Kedah", "Terengganu", "Kelantan", "Johor", "Melaka"]
    
    if state in highland_states and is_highland:
        return "highland_cool"
    elif state in coastal_states or "beach" in poi_text or "island" in poi_text:
        return "coastal_hot"
    else:
        return "tropical_warm"


def generate_packing_list_with_llm(
    trip_context: Dict,
    trip_duration_days: int,
    destination_state: str,
    model
) -> Dict:
    """
    Use LLM to generate smart packing list based on trip context.
    
    Args:
        trip_context: Analysis of trip activities and requirements
        trip_duration_days: Number of days
        destination_state: Malaysian state
        model: ChatGoogleGenerativeAI instance (injected from caller)
        
    Returns:
        Dict with categories and smart_tips
    """
    from langchain_core.messages import HumanMessage
    import json
    import re
    
    # Climate descriptions
    climate_descriptions = {
        "highland_cool": "Cool highland climate (15-25°C), potential rain, cooler evenings. Pack layers and light jacket.",
        "coastal_hot": "Hot & humid coastal climate (28-35°C), high UV exposure, beach weather. Pack light, breathable clothing.",
        "tropical_warm": "Warm tropical climate (25-32°C), humid with occasional rain. Pack light, quick-dry clothing."
    }
    
    climate_desc = climate_descriptions.get(trip_context["climate"], "Tropical climate")
    activities_str = ", ".join(trip_context["activities"]) if trip_context["activities"] else "general sightseeing"
    special_req_str = ", ".join(trip_context["special_requirements"]) if trip_context["special_requirements"] else "None"
    poi_context = ", ".join(trip_context["poi_names"][:5]) if trip_context["poi_names"] else "various attractions"
    
    prompt = f"""You are a travel packing expert for Malaysia tourism.

Generate a comprehensive, categorized packing list for this trip:

TRIP DETAILS:
- Destination: {destination_state}, Malaysia
- Duration: {trip_duration_days} days
- Climate: {climate_desc}
- Activities: {activities_str}
- Key POIs: {poi_context}
- Special Requirements: {special_req_str}

INSTRUCTIONS:
1. Create 8 categories: Clothing, Footwear, Activity Gear, Electronics, Health & Safety, Documents, Toiletries, Miscellaneous
2. For each item, provide:
   - Specific item name (be practical and specific to Malaysia/activities)
   - Quantity (number or null if variable)
   - Reason (relate to specific activities/climate/POIs)
   - Priority: "essential" (must have), "recommended" (should have), "optional" (nice to have), or "required" (cultural/legal necessity)
3. Adjust quantities based on {trip_duration_days}-day duration
4. Add 3-5 practical smart tips based on the specific activities and destination
5. Consider Malaysian context: tropical climate, multicultural, religious sites, outdoor activities

Return ONLY valid JSON with this exact structure (no markdown, no code blocks):
{{
  "categories": [
    {{
      "name": "Clothing",
      "icon": "👕",
      "items": [
        {{"item": "T-shirts (breathable)", "quantity": 5, "reason": "Daily wear for activities", "priority": "essential"}},
        {{"item": "Light jacket", "quantity": 1, "reason": "Cool highland evenings", "priority": "essential"}}
      ]
    }},
    {{
      "name": "Footwear",
      "icon": "👟",
      "items": [
        {{"item": "Hiking shoes", "quantity": 1, "reason": "Mountain trails", "priority": "essential"}}
      ]
    }},
    {{
      "name": "Activity Gear",
      "icon": "🎒",
      "items": []
    }},
    {{
      "name": "Electronics",
      "icon": "📱",
      "items": []
    }},
    {{
      "name": "Health & Safety",
      "icon": "💊",
      "items": []
    }},
    {{
      "name": "Documents",
      "icon": "📄",
      "items": []
    }},
    {{
      "name": "Toiletries",
      "icon": "🧴",
      "items": []
    }},
    {{
      "name": "Miscellaneous",
      "icon": "🎫",
      "items": []
    }}
  ],
  "smart_tips": ["tip1", "tip2", "tip3"]
}}

IMPORTANT: Return pure JSON only, no markdown formatting, no ```json blocks."""
    
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # Try direct JSON parse first
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # Fallback: extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                return result
            
            # Last attempt: find JSON object in content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            
            raise ValueError(f"Failed to parse LLM response as JSON: {content[:200]}")
            
    except Exception as e:
        # Return fallback structure
        print(f"Error generating packing list: {str(e)}")
        return {
            "categories": [
                {
                    "name": "Clothing",
                    "icon": "👕",
                    "items": [
                        {"item": "T-shirts", "quantity": trip_duration_days, "reason": "Daily wear", "priority": "essential"},
                        {"item": "Comfortable pants", "quantity": 2, "reason": "General activities", "priority": "essential"}
                    ]
                }
            ],
            "smart_tips": ["Pack light and comfortable clothing", "Bring rain protection", "Stay hydrated"]
        }