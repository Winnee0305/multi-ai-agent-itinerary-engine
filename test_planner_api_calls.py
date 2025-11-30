"""
Test the Planner API endpoints
Run the API first: python test_planner_api.py
Then run this: python test_planner_api_calls.py
"""

import requests
import json

BASE_URL = "http://localhost:8001"


def test_select_centroid():
    """Test centroid selection"""
    print("\n" + "="*80)
    print("TEST 1: Select Centroid")
    print("="*80)
    
    payload = {
        "priority_pois": [
            {
                "google_place_id": "ChIJ_abc123",
                "name": "George Town",
                "priority_score": 95.5,
                "lat": 5.4164,
                "lon": 100.3327,
                "state": "Penang"
            },
            {
                "google_place_id": "ChIJ_def456",
                "name": "Penang Hill",
                "priority_score": 90.0,
                "lat": 5.4200,
                "lon": 100.2700,
                "state": "Penang"
            },
            {
                "google_place_id": "ChIJ_ghi789",
                "name": "Kek Lok Si",
                "priority_score": 88.0,
                "lat": 5.3985,
                "lon": 100.2736,
                "state": "Penang"
            }
        ],
        "consider_top_n": 5
    }
    
    response = requests.post(f"{BASE_URL}/planner/select-centroid", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Success!")
        print(f"Centroid: {result['centroid']['name']}")
        print(f"Priority Score: {result['centroid']['priority_score']}")
        print(f"Reason: {result['centroid']['reason']}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
    
    return response.json() if response.status_code == 200 else None


def test_calculate_distance():
    """Test distance calculation"""
    print("\n" + "="*80)
    print("TEST 2: Calculate Distance Between POIs")
    print("="*80)
    
    # Note: These need to be real place_ids from your database
    payload = {
        "place_id_1": "ChIJ_abc123",
        "place_id_2": "ChIJ_def456"
    }
    
    response = requests.post(f"{BASE_URL}/planner/calculate-distance", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Success!")
        print(f"Distance: {result['distance_meters']:.2f} meters")
        print(f"Distance: {result['distance_km']} km")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def test_generate_sequence():
    """Test sequence generation"""
    print("\n" + "="*80)
    print("TEST 3: Generate Optimal Sequence")
    print("="*80)
    
    payload = {
        "start_place_id": "ChIJ_abc123",
        "poi_place_ids": [
            "ChIJ_def456",
            "ChIJ_ghi789",
            "ChIJ_jkl012"
        ]
    }
    
    response = requests.post(f"{BASE_URL}/planner/generate-sequence", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Success!")
        print(f"Total POIs: {result['summary']['total_pois']}")
        print(f"Total Distance: {result['summary']['total_distance_km']} km")
        print("\nSequence:")
        for item in result['sequence']:
            print(f"  {item['sequence_no']}. {item['google_matched_name']}")
            if 'distance_from_previous_meters' in item:
                dist_km = item['distance_from_previous_meters'] / 1000
                print(f"     → {dist_km:.2f} km from previous")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def test_plan_itinerary():
    """Test complete itinerary planning workflow"""
    print("\n" + "="*80)
    print("TEST 4: Complete Itinerary Planning (Full Workflow)")
    print("="*80)
    
    # Sample priority POIs list
    priority_pois = []
    for i in range(20):
        priority_pois.append({
            "google_place_id": f"ChIJ_poi_{i}",
            "name": f"POI {i+1}",
            "priority_score": 95 - i,
            "lat": 5.4164 + (i * 0.01),
            "lon": 100.3327 + (i * 0.01),
            "state": "Penang"
        })
    
    payload = {
        "priority_pois": priority_pois,
        "max_pois_per_day": 6,
        "max_distance_meters": 30000
    }
    
    response = requests.post(f"{BASE_URL}/planner/plan-itinerary", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Success!")
        print(f"\nCentroid: {result['centroid']['name']}")
        print(f"Priority Score: {result['centroid']['priority_score']}")
        
        print(f"\nClusters:")
        print(f"  • Nearby POIs: {result['clusters']['nearby_count']}")
        print(f"  • Far POIs: {result['clusters']['far_count']}")
        
        print(f"\nItinerary Summary:")
        print(f"  • Total POIs in sequence: {result['summary']['total_pois']}")
        print(f"  • Total distance: {result['summary']['total_distance_km']} km")
        
        print(f"\nSequence:")
        for item in result['sequence']:
            print(f"  {item['sequence_no']}. {item['google_matched_name']}")
            print(f"     Place ID: {item['google_place_id']}")
            if 'distance_from_previous_meters' in item:
                dist_km = item['distance_from_previous_meters'] / 1000
                print(f"     → {dist_km:.2f} km from previous POI")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def test_nearby_pois():
    """Test finding nearby POIs"""
    print("\n" + "="*80)
    print("TEST 5: Find Nearby POIs")
    print("="*80)
    
    # Note: Use a real place_id from your database
    place_id = "ChIJ_abc123"
    
    response = requests.get(
        f"{BASE_URL}/planner/nearby-pois/{place_id}",
        params={
            "radius_meters": 50000,
            "max_results": 10
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Success!")
        print(f"Center: {result['center_place_id']}")
        print(f"Radius: {result['radius_km']} km")
        print(f"Found: {result['count']} POIs")
        
        if result['pois']:
            print("\nNearby POIs:")
            for poi in result['pois'][:5]:
                print(f"  • {poi.get('name', 'Unknown')}")
                print(f"    Distance: {poi.get('distance_meters', 0)/1000:.2f} km")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def main():
    print("\n" + "="*80)
    print("🧪 PLANNER API TEST SUITE")
    print("="*80)
    print("\nMake sure the API is running: python test_planner_api.py")
    print("="*80)
    
    try:
        # Test health
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("\n✓ API is online!")
        else:
            print("\n✗ API not responding")
            return
        
        # Run tests
        test_select_centroid()
        # test_calculate_distance()  # Requires real place_ids in DB
        # test_generate_sequence()     # Requires real place_ids in DB
        test_plan_itinerary()
        # test_nearby_pois()           # Requires real place_ids in DB
        
        print("\n" + "="*80)
        print("✓ Tests completed!")
        print("="*80)
        print("\nNOTE: Some tests are commented out because they require")
        print("real Google Place IDs from your Supabase database.")
        print("\nTo test with real data:")
        print("1. Update place_ids with actual values from your database")
        print("2. Uncomment the tests")
        print("3. Run again")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API!")
        print("Start the API with: python test_planner_api.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
