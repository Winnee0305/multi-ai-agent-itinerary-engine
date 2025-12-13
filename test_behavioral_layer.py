"""
Test behavioral layer implementation
"""

from tools.recommender_tools import calculate_priority_scores

# Mock POIs for testing
mock_pois = [
    {
        "google_place_id": "ChIJabc123",
        "name": "Kek Lok Si Temple",
        "state": "Penang",
        "google_types": ["tourist_attraction", "place_of_worship"],
        "popularity_score": 90,
        "is_golden_list": True,
        "lat": 5.4,
        "lon": 100.27
    },
    {
        "google_place_id": "ChIJdef456",
        "name": "Penang Hill",
        "state": "Penang",
        "google_types": ["tourist_attraction", "point_of_interest"],
        "popularity_score": 85,
        "is_golden_list": True,
        "lat": 5.42,
        "lon": 100.26
    },
    {
        "google_place_id": "ChIJghi789",
        "name": "Gurney Drive",
        "state": "Penang",
        "google_types": ["restaurant", "food"],
        "popularity_score": 75,
        "is_golden_list": True,
        "lat": 5.43,
        "lon": 100.31
    },
    {
        "google_place_id": "ChIJjkl012",
        "name": "Street Art Georgetown",
        "state": "Penang",
        "google_types": ["tourist_attraction", "art_gallery"],
        "popularity_score": 80,
        "is_golden_list": True,
        "lat": 5.41,
        "lon": 100.33
    }
]

# Test case 1: No behavioral data
print("=== Test 1: No behavioral data ===")
scored = calculate_priority_scores(
    pois=mock_pois,
    user_preferences=["Culture", "Food"],
    number_of_travelers=2,
    travel_days=3,
    preferred_poi_names=None,
    user_behavior=None
)

for poi in scored:
    print(f"{poi['name']}: score={poi['priority_score']}, boost={poi['behavior_boost']}, multiplier={poi['behavior_multiplier']}")

print("\n=== Test 2: With behavioral data ===")
# Test case 2: With behavioral signals
user_behavior = {
    "viewed_place_ids": ["ChIJabc123", "ChIJdef456"],  # Viewed 2 POIs
    "collected_place_ids": ["ChIJghi789"],  # Collected 1 POI
    "trip_place_ids": ["ChIJjkl012"]  # In 1 trip
}

scored = calculate_priority_scores(
    pois=mock_pois,
    user_preferences=["Culture", "Food"],
    number_of_travelers=2,
    travel_days=3,
    preferred_poi_names=None,
    user_behavior=user_behavior
)

print("\nUser behavior:")
print(f"  Viewed: {user_behavior['viewed_place_ids']}")
print(f"  Collected: {user_behavior['collected_place_ids']}")
print(f"  In trips: {user_behavior['trip_place_ids']}")

print("\nScored POIs:")
for poi in scored:
    boost_info = ""
    if poi['behavior_boost'] > 0:
        boost_info += f" (+{poi['behavior_boost']} boost)"
    if poi['behavior_multiplier'] > 1.0:
        boost_info += f" (×{poi['behavior_multiplier']} multiplier)"
    
    print(f"{poi['name']}: score={poi['priority_score']}{boost_info}")

print("\n=== Test 3: Multiple signals on same POI ===")
# Test case 3: POI that is viewed AND collected AND in trip
user_behavior_multiple = {
    "viewed_place_ids": ["ChIJabc123"],
    "collected_place_ids": ["ChIJabc123"],
    "trip_place_ids": ["ChIJabc123"]
}

scored = calculate_priority_scores(
    pois=mock_pois,
    user_preferences=["Culture"],
    number_of_travelers=2,
    travel_days=3,
    preferred_poi_names=None,
    user_behavior=user_behavior_multiple
)

kek_lok_si = next(p for p in scored if p['google_place_id'] == 'ChIJabc123')
print(f"\n{kek_lok_si['name']} (viewed + collected + in trip):")
print(f"  Final score: {kek_lok_si['priority_score']}")
print(f"  Behavior boost: +{kek_lok_si['behavior_boost']} (3 viewed + 20 collected)")
print(f"  Behavior multiplier: ×{kek_lok_si['behavior_multiplier']} (in trips)")
print(f"  Expected boost calculation: base_score + 23 points, then × 1.4")
