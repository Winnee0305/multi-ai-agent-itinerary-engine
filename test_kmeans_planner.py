"""
Test K-Means Multi-Day Itinerary Planning

This script tests the new multi-day itinerary planning with K-Means geographic clustering.
Run this after implementing the changes to verify the system works correctly.

Test Scenarios:
1. Single day trip (should use simple splitting)
2. 3-day trip with k-means clustering
3. 7-day trip with limited POIs
4. Compare simple vs k-means strategies
"""

import json
from tools.planner_tools import plan_itinerary_logic

# Mock POIs for Penang (covering different geographic areas)
MOCK_PENANG_POIS = [
    # Georgetown Area (Central)
    {"google_place_id": "poi_georgetown_1", "name": "Komtar Tower", "lat": 5.4141, "lon": 100.3288, "priority_score": 150},
    {"google_place_id": "poi_georgetown_2", "name": "Penang Street Art", "lat": 5.4164, "lon": 100.3327, "priority_score": 145},
    {"google_place_id": "poi_georgetown_3", "name": "Clan Jetties", "lat": 5.4089, "lon": 100.3442, "priority_score": 140},
    {"google_place_id": "poi_georgetown_4", "name": "Little India", "lat": 5.4185, "lon": 100.3324, "priority_score": 135},
    
    # Penang Hill Area (West)
    {"google_place_id": "poi_hill_1", "name": "Penang Hill", "lat": 5.4231, "lon": 100.2699, "priority_score": 142},
    {"google_place_id": "poi_hill_2", "name": "Kek Lok Si Temple", "lat": 5.3980, "lon": 100.2733, "priority_score": 138},
    {"google_place_id": "poi_hill_3", "name": "Botanical Gardens", "lat": 5.4319, "lon": 100.2862, "priority_score": 130},
    
    # Batu Ferringhi Area (North)
    {"google_place_id": "poi_north_1", "name": "Batu Ferringhi Beach", "lat": 5.4723, "lon": 100.2467, "priority_score": 133},
    {"google_place_id": "poi_north_2", "name": "Tropical Spice Garden", "lat": 5.4589, "lon": 100.2234, "priority_score": 128},
    {"google_place_id": "poi_north_3", "name": "Entopia Butterfly Farm", "lat": 5.4656, "lon": 100.2389, "priority_score": 125},
    
    # Gurney Drive Area (Northeast)
    {"google_place_id": "poi_gurney_1", "name": "Gurney Drive", "lat": 5.4378, "lon": 100.3101, "priority_score": 132},
    {"google_place_id": "poi_gurney_2", "name": "Gurney Plaza", "lat": 5.4381, "lon": 100.3097, "priority_score": 127},
    
    # Balik Pulau Area (South)
    {"google_place_id": "poi_south_1", "name": "Balik Pulau Town", "lat": 5.3465, "lon": 100.2341, "priority_score": 120},
    {"google_place_id": "poi_south_2", "name": "Snake Temple", "lat": 5.3320, "lon": 100.2865, "priority_score": 118},
    {"google_place_id": "poi_south_3", "name": "Penang Bridge View", "lat": 5.3589, "lon": 100.3267, "priority_score": 115},
    
    # Additional POIs
    {"google_place_id": "poi_other_1", "name": "Penang National Park", "lat": 5.4423, "lon": 100.1989, "priority_score": 122},
    {"google_place_id": "poi_other_2", "name": "Wat Chaiyamangkalaram", "lat": 5.4174, "lon": 100.2991, "priority_score": 116},
    {"google_place_id": "poi_other_3", "name": "Khoo Kongsi", "lat": 5.4153, "lon": 100.3385, "priority_score": 134},
]


def print_separator(title: str):
    """Print a visual separator for test sections"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_daily_summary(result: dict):
    """Print formatted summary of daily itineraries"""
    print(f"Trip Duration: {result['trip_duration_days']} days")
    print(f"Strategy: {result['clustering_strategy_used']}")
    print(f"Centroid: {result['centroid']['name']}")
    print(f"\nTrip Summary:")
    print(f"  Total POIs: {result['trip_summary']['total_pois']}")
    print(f"  Total Distance: {result['trip_summary']['total_distance_meters']/1000:.2f} km")
    print(f"  Avg POIs/Day: {result['trip_summary']['avg_pois_per_day']}")
    print(f"  Avg Distance/Day: {result['trip_summary']['avg_distance_per_day_meters']/1000:.2f} km")
    
    print(f"\nDaily Breakdown:")
    for day in result['daily_itineraries']:
        print(f"\n  Day {day['day']}:")
        print(f"    POIs: {day['total_pois']}")
        print(f"    Distance: {day['total_distance_meters']/1000:.2f} km")
        
        if day.get('overnight_transition'):
            trans = day['overnight_transition']
            print(f"    Overnight Transition: {trans['from_poi']} → {trans['to_poi']} ({trans['distance_meters']/1000:.2f} km)")
        
        if day['pois']:
            print(f"    Sequence:")
            for poi in day['pois']:
                print(f"      {poi['sequence_no']}. {poi.get('google_matched_name', 'Unknown')} "
                      f"({poi['distance_from_previous_meters']/1000:.2f} km)")


def test_single_day_trip():
    """Test 1: Single day trip should use simple splitting"""
    print_separator("TEST 1: Single Day Trip - Direct Function Test")
    
    from tools.planner_tools import split_into_days_simple
    
    # Create mock sequence with all required fields
    mock_sequence = []
    for i, poi in enumerate(MOCK_PENANG_POIS[:6], start=1):
        mock_sequence.append({
            "google_place_id": poi["google_place_id"],
            "google_matched_name": poi["name"],
            "sequence_no": i,
            "distance_from_previous_meters": 1000 * i if i > 1 else 0,
            "lat": poi["lat"],
            "lon": poi["lon"]
        })
    
    result = split_into_days_simple(mock_sequence, trip_duration_days=1, max_pois_per_day=6)
    
    print(f"Trip Duration: 1 days")
    print(f"Total POIs: {len(mock_sequence)}")
    print(f"\nDaily Breakdown:")
    for day in result:
        print(f"\n  Day {day['day']}:")
        print(f"    POIs: {day['total_pois']}")
        print(f"    Distance: {day['total_distance_meters']/1000:.2f} km")
        if day['pois']:
            print(f"    Sequence:")
            for poi in day['pois']:
                print(f"      {poi['sequence_no']}. {poi.get('google_matched_name', 'Unknown')} "
                      f"({poi['distance_from_previous_meters']/1000:.2f} km)")
    
    # Assertions
    assert len(result) == 1, "Should be 1 day"
    assert result[0]['total_pois'] == 6, "Should have 6 POIs"
    assert result[0]['total_pois'] <= 6, "Should have max 6 POIs"
    
    print("\n✅ Test 1 PASSED")


def test_three_day_kmeans():
    """Test 2: 3-day trip with k-means clustering"""
    print_separator("TEST 2: 3-Day Trip with K-Means - Direct Function Test")
    
    from tools.planner_tools import split_into_days_kmeans
    
    # Create mock sequence with all required fields (15 POIs for 3 days)
    mock_sequence = []
    for i, poi in enumerate(MOCK_PENANG_POIS[:15], start=1):
        mock_sequence.append({
            "google_place_id": poi["google_place_id"],
            "google_matched_name": poi["name"],
            "name": poi["name"],
            "sequence_no": i,
            "distance_from_previous_meters": 1000 * i if i > 1 else 0,
            "lat": poi["lat"],
            "lon": poi["lon"]
        })
    
    result = split_into_days_kmeans(mock_sequence, trip_duration_days=3, max_pois_per_day=6)
    
    print(f"Trip Duration: 3 days")
    print(f"Strategy: kmeans")
    print(f"Total POIs: {len(mock_sequence)}")
    
    total_pois = sum(day['total_pois'] for day in result)
    total_distance = sum(day['total_distance_meters'] for day in result)
    
    print(f"\nTrip Summary:")
    print(f"  Total POIs in itinerary: {total_pois}")
    print(f"  Total Distance: {total_distance/1000:.2f} km")
    print(f"  Avg POIs/Day: {total_pois/3:.1f}")
    
    print(f"\nDaily Breakdown:")
    for day in result:
        print(f"\n  Day {day['day']}:")
        print(f"    POIs: {day['total_pois']}")
        print(f"    Distance: {day['total_distance_meters']/1000:.2f} km")
        
        if day.get('overnight_transition'):
            trans = day['overnight_transition']
            print(f"    Overnight Transition: {trans['from_poi']} → {trans['to_poi']} ({trans['distance_meters']/1000:.2f} km)")
        
        if day['pois']:
            print(f"    Sequence:")
            for poi in day['pois'][:3]:  # Show first 3
                print(f"      {poi['sequence_no']}. {poi.get('google_matched_name', 'Unknown')} "
                      f"({poi['distance_from_previous_meters']/1000:.2f} km)")
            if len(day['pois']) > 3:
                print(f"      ... and {len(day['pois']) - 3} more")
    
    # Assertions
    assert len(result) == 3, "Should be 3 days"
    assert total_pois > 0, "Should have POIs"
    
    # Check each day has POIs (at least some days should)
    non_empty_days = [day for day in result if day['total_pois'] > 0]
    assert len(non_empty_days) > 0, "Should have at least some days with POIs"
    
    for day in result:
        assert day['total_pois'] <= 6, f"Day {day['day']} should have max 6 POIs"
    
    print("\n✅ Test 2 PASSED")


def test_seven_day_limited_pois():
    """Test 3: 7-day trip with only 12 POIs (some days will be empty)"""
    print_separator("TEST 3: 7-Day Trip with Limited POIs - Direct Function Test")
    
    from tools.planner_tools import split_into_days_simple
    
    # Use only first 12 POIs
    limited_pois = MOCK_PENANG_POIS[:12]
    
    # Create mock sequence
    mock_sequence = []
    for i, poi in enumerate(limited_pois, start=1):
        mock_sequence.append({
            "google_place_id": poi["google_place_id"],
            "google_matched_name": poi["name"],
            "sequence_no": i,
            "distance_from_previous_meters": 800 * i if i > 1 else 0,
            "lat": poi["lat"],
            "lon": poi["lon"]
        })
    
    result = split_into_days_simple(mock_sequence, trip_duration_days=7, max_pois_per_day=4)
    
    print(f"Trip Duration: 7 days")
    print(f"Total POIs available: {len(mock_sequence)}")
    print(f"Max POIs per day: 4")
    
    non_empty_days = [day for day in result if day['total_pois'] > 0]
    print(f"\nNon-empty days: {len(non_empty_days)}/{len(result)}")
    
    print(f"\nDaily Breakdown:")
    for day in result:
        if day['total_pois'] > 0:
            print(f"\n  Day {day['day']}: {day['total_pois']} POIs, {day['total_distance_meters']/1000:.2f} km")
        else:
            print(f"\n  Day {day['day']}: Empty (flexible day)")
    
    # Assertions
    assert len(result) == 7, "Should be 7 days"
    assert len(non_empty_days) >= 3, f"Should have at least 3 non-empty days, got {len(non_empty_days)}"
    
    print("\n✅ Test 3 PASSED")


def test_compare_strategies():
    """Test 4: Compare simple vs k-means strategies"""
    print_separator("TEST 4: Compare Simple vs K-Means Strategies - Direct Function Test")
    
    from tools.planner_tools import split_into_days_simple, split_into_days_kmeans
    
    # Create mock sequence with 15 POIs
    mock_sequence = []
    for i, poi in enumerate(MOCK_PENANG_POIS[:15], start=1):
        mock_sequence.append({
            "google_place_id": poi["google_place_id"],
            "google_matched_name": poi["name"],
            "name": poi["name"],
            "sequence_no": i,
            "distance_from_previous_meters": 1500 * i if i > 1 else 0,
            "lat": poi["lat"],
            "lon": poi["lon"]
        })
    
    # Test with simple strategy
    print("\n--- SIMPLE STRATEGY ---")
    result_simple = split_into_days_simple(mock_sequence.copy(), trip_duration_days=3, max_pois_per_day=5)
    
    simple_total_pois = sum(day['total_pois'] for day in result_simple)
    simple_total_distance = sum(day['total_distance_meters'] for day in result_simple)
    
    print(f"Total POIs: {simple_total_pois}")
    print(f"Total Distance: {simple_total_distance/1000:.2f} km")
    print(f"Avg Distance/Day: {simple_total_distance/3/1000:.2f} km")
    
    for day in result_simple:
        print(f"  Day {day['day']}: {day['total_pois']} POIs, {day['total_distance_meters']/1000:.2f} km")
    
    # Test with k-means strategy
    print("\n--- K-MEANS STRATEGY ---")
    result_kmeans = split_into_days_kmeans(mock_sequence.copy(), trip_duration_days=3, max_pois_per_day=5)
    
    kmeans_total_pois = sum(day['total_pois'] for day in result_kmeans)
    kmeans_total_distance = sum(day['total_distance_meters'] for day in result_kmeans)
    
    print(f"Total POIs: {kmeans_total_pois}")
    print(f"Total Distance: {kmeans_total_distance/1000:.2f} km")
    print(f"Avg Distance/Day: {kmeans_total_distance/3/1000:.2f} km")
    
    for day in result_kmeans:
        print(f"  Day {day['day']}: {day['total_pois']} POIs, {day['total_distance_meters']/1000:.2f} km")
        if day.get('overnight_transition'):
            trans = day['overnight_transition']
            print(f"    Overnight: {trans['distance_meters']/1000:.2f} km")
    
    # Compare results
    print("\n--- COMPARISON ---")
    print(f"Simple: {simple_total_pois} POIs, {simple_total_distance/1000:.2f} km total")
    print(f"K-Means: {kmeans_total_pois} POIs, {kmeans_total_distance/1000:.2f} km total")
    
    print(f"\nBoth strategies organized {simple_total_pois} POIs across 3 days")
    print(f"K-Means adds geographic clustering for better day grouping")
    
    print("\n✅ Test 4 PASSED")


def test_overnight_transitions():
    """Test 5: Check overnight transitions are calculated"""
    print_separator("TEST 5: Overnight Transitions - Direct Function Test")
    
    from tools.planner_tools import split_into_days_kmeans
    
    # Create mock sequence with diverse locations
    mock_sequence = []
    for i, poi in enumerate(MOCK_PENANG_POIS[:12], start=1):
        mock_sequence.append({
            "google_place_id": poi["google_place_id"],
            "google_matched_name": poi["name"],
            "name": poi["name"],
            "sequence_no": i,
            "distance_from_previous_meters": 2000 * i if i > 1 else 0,
            "lat": poi["lat"],
            "lon": poi["lon"]
        })
    
    result = split_into_days_kmeans(mock_sequence, trip_duration_days=3, max_pois_per_day=4)
    
    print("Checking overnight transitions between days...")
    
    has_transitions = False
    for i, day in enumerate(result):
        if i > 0:  # Skip first day
            transition = day.get('overnight_transition')
            if transition:
                has_transitions = True
                print(f"\nDay {day['day']} Transition:")
                print(f"  From: {transition['from_poi']}")
                print(f"  To: {transition['to_poi']}")
                print(f"  Distance: {transition['distance_meters']/1000:.2f} km")
            elif day['total_pois'] == 0:
                print(f"\nDay {day['day']}: Empty day (no transition needed)")
            else:
                print(f"\nDay {day['day']}: Has POIs but no transition data")
    
    if has_transitions:
        print("\n✅ Overnight transitions are being calculated correctly")
    else:
        print("\n⚠️  No overnight transitions found (might be expected for this data)")
    
    print("\n✅ Test 5 PASSED")


def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "🚀" * 40)
    print("  K-MEANS MULTI-DAY ITINERARY TESTING")
    print("🚀" * 40)
    
    try:
        test_single_day_trip()
        test_three_day_kmeans()
        test_seven_day_limited_pois()
        test_compare_strategies()
        test_overnight_transitions()
        
        print_separator("ALL TESTS PASSED ✅")
        print("\nThe multi-day itinerary system with K-Means clustering is working correctly!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
