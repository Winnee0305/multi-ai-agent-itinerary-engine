"""
Example: Using Planner Agent to generate sequenced itinerary
"""

from agents.tools import (
    select_best_centroid,
    calculate_distances_from_centroid,
    cluster_pois_by_distance,
    generate_optimal_sequence
)


def plan_itinerary_simple(priority_pois_list, max_pois_per_day=6):
    """
    Simple itinerary planner using the tools.
    
    Args:
        priority_pois_list: List of POIs sorted by priority_score with google_place_id
        max_pois_per_day: Maximum POIs to visit per day
        
    Returns:
        Dictionary with sequenced itinerary
    """
    
    print("\n" + "="*80)
    print("ITINERARY PLANNING - STEP BY STEP")
    print("="*80)
    
    # Step 1: Select centroid from top 5 priority POIs
    print("\nStep 1: Selecting centroid from top 5 priority POIs...")
    centroid = select_best_centroid.invoke({
        "top_priority_pois": priority_pois_list,
        "consider_top_n": 5
    })
    print(f"✓ Centroid selected: {centroid.get('name')}")
    print(f"  Reason: {centroid.get('reason')}")
    
    centroid_place_id = centroid.get("google_place_id")
    
    # Step 2: Get top 50 POIs from priority list
    top_50_pois = priority_pois_list[:50]
    print(f"\nStep 2: Working with top {len(top_50_pois)} priority POIs...")
    
    # Step 3: Calculate distances from centroid
    print("\nStep 3: Calculating distances from centroid...")
    poi_place_ids = [poi.get("google_place_id") for poi in top_50_pois if poi.get("google_place_id")]
    
    distances = calculate_distances_from_centroid.invoke({
        "centroid_place_id": centroid_place_id,
        "poi_place_ids": poi_place_ids
    })
    print(f"✓ Calculated distances for {len(distances)} POIs")
    
    # Step 4: Cluster POIs by distance (within 30km is "nearby")
    print("\nStep 4: Clustering POIs by distance...")
    clusters = cluster_pois_by_distance.invoke({
        "centroid_place_id": centroid_place_id,
        "poi_list": top_50_pois,
        "max_distance_meters": 30000  # 30km radius
    })
    
    nearby_count = clusters.get("nearby_count", 0)
    far_count = clusters.get("far_count", 0)
    print(f"✓ Nearby POIs (≤30km): {nearby_count}")
    print(f"✓ Far POIs (>30km): {far_count}")
    
    # Step 5: Select POIs to visit (prioritize nearby ones)
    nearby_pois = clusters.get("nearby", [])
    selected_place_ids = [poi["google_place_id"] for poi in nearby_pois[:max_pois_per_day-1]]
    
    print(f"\nStep 5: Selected {len(selected_place_ids)} POIs to visit (excluding centroid)")
    
    # Step 6: Generate optimal sequence using nearest neighbor
    print("\nStep 6: Generating optimal visit sequence...")
    sequence = generate_optimal_sequence.invoke({
        "poi_place_ids": selected_place_ids,
        "start_place_id": centroid_place_id
    })
    
    print(f"✓ Sequence generated with {len(sequence)} POIs")
    
    # Display the sequence
    print("\n" + "="*80)
    print("FINAL ITINERARY SEQUENCE")
    print("="*80)
    
    total_distance = 0
    for item in sequence:
        print(f"\n{item['sequence_no']}. {item['google_matched_name']}")
        print(f"   Google Place ID: {item['google_place_id']}")
        
        if 'distance_from_previous_meters' in item:
            dist_km = item['distance_from_previous_meters'] / 1000
            total_distance += item['distance_from_previous_meters']
            print(f"   → Travel {dist_km:.2f} km from previous POI")
    
    print(f"\n{'='*80}")
    print(f"Total Travel Distance: {total_distance/1000:.2f} km")
    print(f"{'='*80}")
    
    return {
        "centroid": centroid,
        "sequence": sequence,
        "total_distance_km": total_distance / 1000,
        "nearby_pois_count": nearby_count,
        "far_pois_count": far_count
    }


# Example usage with mock data
if __name__ == "__main__":
    # Mock priority POIs (replace with actual data from your recommender agent)
    mock_priority_pois = [
        {
            "google_place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
            "name": "George Town",
            "priority_score": 95,
            "lat": 5.4164,
            "lon": 100.3327,
            "state": "Penang"
        },
        {
            "google_place_id": "ChIJ_-vKub175kcROF1v2eC35_k",
            "name": "Penang Hill",
            "priority_score": 90,
            "lat": 5.4200,
            "lon": 100.2700,
            "state": "Penang"
        },
        {
            "google_place_id": "ChIJfauPtb175kcR8J3v2eC35_k",
            "name": "Kek Lok Si Temple",
            "priority_score": 88,
            "lat": 5.3985,
            "lon": 100.2736,
            "state": "Penang"
        },
        # Add more POIs here...
    ]
    
    print("\n🗺️  ITINERARY PLANNER - DEMO")
    print("="*80)
    print("This demonstrates how the planner agent tools work together")
    print("Update with real data from your Supabase database")
    print("="*80)
    
    try:
        result = plan_itinerary_simple(mock_priority_pois, max_pois_per_day=6)
        
        print("\n✓ Itinerary planning complete!")
        print(f"\nSummary:")
        print(f"  • Centroid: {result['centroid']['name']}")
        print(f"  • POIs to visit: {len(result['sequence'])}")
        print(f"  • Total distance: {result['total_distance_km']:.2f} km")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. SUPABASE_URL and SERVICE_ROLE_KEY are set in .env")
        print("2. PostGIS RPC functions are deployed (see database/rpc_functions.sql)")
        print("3. osm_pois table exists and has data")
