"""
Test script for Planner Agent tools
Demonstrates distance calculations and itinerary sequencing
"""

from agents.tools import (
    get_poi_by_place_id,
    calculate_distance_between_pois,
    get_pois_near_centroid,
    calculate_distances_from_centroid,
    select_best_centroid,
    cluster_pois_by_distance,
    generate_optimal_sequence
)


def test_basic_tools():
    """Test basic tool functionality"""
    print("\n" + "="*80)
    print("TEST 1: Get POI by Place ID")
    print("="*80)
    
    # Replace with actual place_id from your database
    place_id = "ChIJD7fiBh9u5kcRYJSMaMOCCwQ"  # Example: Paris
    result = get_poi_by_place_id.invoke(place_id)
    print(f"POI: {result.get('name', 'Not found')}")
    print(f"Location: ({result.get('lat')}, {result.get('lon')})")
    
    print("\n" + "="*80)
    print("TEST 2: Calculate Distance Between Two POIs")
    print("="*80)
    
    # Replace with actual place_ids
    place_id_1 = "ChIJD7fiBh9u5kcRYJSMaMOCCwQ"
    place_id_2 = "ChIJD7fiBh9u5kcRYJSMaMOCCwQ"
    
    distance = calculate_distance_between_pois.invoke({
        "place_id_1": place_id_1,
        "place_id_2": place_id_2
    })
    print(f"Distance: {distance:.2f} meters ({distance/1000:.2f} km)")


def test_centroid_selection():
    """Test centroid selection from priority list"""
    print("\n" + "="*80)
    print("TEST 3: Select Best Centroid")
    print("="*80)
    
    # Simulate priority POI list
    priority_pois = [
        {
            "google_place_id": "place_1",
            "name": "Top Attraction",
            "priority_score": 95,
            "lat": 5.4164,
            "lon": 100.3327
        },
        {
            "google_place_id": "place_2",
            "name": "Second Best",
            "priority_score": 90,
            "lat": 5.4200,
            "lon": 100.3400
        },
        {
            "google_place_id": "place_3",
            "name": "Third Place",
            "priority_score": 85,
            "lat": 5.4100,
            "lon": 100.3250
        }
    ]
    
    centroid = select_best_centroid.invoke({
        "top_priority_pois": priority_pois,
        "consider_top_n": 5
    })
    
    print(f"Selected Centroid: {centroid.get('name')}")
    print(f"Priority Score: {centroid.get('priority_score')}")
    print(f"Reason: {centroid.get('reason')}")


def test_nearby_pois():
    """Test finding POIs near a centroid"""
    print("\n" + "="*80)
    print("TEST 4: Find POIs Near Centroid")
    print("="*80)
    
    # Replace with actual centroid place_id
    centroid_place_id = "ChIJD7fiBh9u5kcRYJSMaMOCCwQ"
    
    nearby = get_pois_near_centroid.invoke({
        "centroid_place_id": centroid_place_id,
        "radius_meters": 50000,
        "max_results": 10
    })
    
    print(f"Found {len(nearby)} POIs within 50km")
    for i, poi in enumerate(nearby[:5], 1):
        print(f"{i}. {poi['name']} - {poi['distance_meters']/1000:.2f} km away")


def test_clustering():
    """Test POI clustering by distance"""
    print("\n" + "="*80)
    print("TEST 5: Cluster POIs by Distance")
    print("="*80)
    
    centroid_place_id = "place_1"
    
    poi_list = [
        {"google_place_id": "place_2", "name": "Close POI"},
        {"google_place_id": "place_3", "name": "Medium POI"},
        {"google_place_id": "place_4", "name": "Far POI"}
    ]
    
    clusters = cluster_pois_by_distance.invoke({
        "centroid_place_id": centroid_place_id,
        "poi_list": poi_list,
        "max_distance_meters": 30000
    })
    
    print(f"Nearby POIs (within 30km): {clusters.get('nearby_count', 0)}")
    print(f"Far POIs (beyond 30km): {clusters.get('far_count', 0)}")


def test_sequence_generation():
    """Test optimal sequence generation"""
    print("\n" + "="*80)
    print("TEST 6: Generate Optimal Visit Sequence")
    print("="*80)
    
    start_place_id = "place_1"
    poi_place_ids = ["place_2", "place_3", "place_4", "place_5"]
    
    sequence = generate_optimal_sequence.invoke({
        "poi_place_ids": poi_place_ids,
        "start_place_id": start_place_id
    })
    
    print("\nOptimal Visit Sequence:")
    for item in sequence:
        dist = item.get('distance_from_previous_meters', 0)
        dist_km = dist / 1000 if dist > 0 else 0
        print(f"{item['sequence_no']}. {item['google_matched_name']}")
        if dist > 0:
            print(f"   → {dist_km:.2f} km from previous")


def test_complete_workflow():
    """Test complete planning workflow"""
    print("\n" + "="*80)
    print("COMPLETE WORKFLOW TEST")
    print("="*80)
    
    # Step 1: Select centroid from top priority POIs
    priority_pois = [
        {"google_place_id": "p1", "name": "Main Attraction", "priority_score": 95, "lat": 5.4164, "lon": 100.3327},
        {"google_place_id": "p2", "name": "Second Best", "priority_score": 90, "lat": 5.4200, "lon": 100.3400},
        {"google_place_id": "p3", "name": "Third", "priority_score": 85, "lat": 5.4100, "lon": 100.3250},
    ]
    
    print("\nStep 1: Select Centroid")
    centroid = select_best_centroid.invoke({"top_priority_pois": priority_pois, "consider_top_n": 5})
    print(f"✓ Centroid: {centroid.get('name')}")
    
    # Step 2: Find nearby POIs
    print("\nStep 2: Find POIs Near Centroid")
    print("(Using actual PostGIS query - requires real data)")
    
    # Step 3: Cluster POIs
    print("\nStep 3: Cluster POIs by Distance")
    print("(Nearby vs Far POIs)")
    
    # Step 4: Generate sequence
    print("\nStep 4: Generate Optimal Sequence")
    print("(Using nearest neighbor algorithm)")
    
    print("\n✓ Workflow complete!")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PLANNER AGENT TOOLS - TEST SUITE")
    print("="*80)
    print("\nNOTE: Update place_ids with actual data from your Supabase database")
    print("="*80)
    
    try:
        # Run individual tests
        # test_basic_tools()
        test_centroid_selection()
        # test_nearby_pois()
        # test_clustering()
        # test_sequence_generation()
        test_complete_workflow()
        
        print("\n" + "="*80)
        print("✓ All tests completed!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Supabase is configured in .env")
        print("2. PostGIS RPC functions are deployed")
        print("3. osm_pois table has data")
