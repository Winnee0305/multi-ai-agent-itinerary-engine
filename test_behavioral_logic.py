"""
Simplified test for behavioral layer - standalone version
Tests the scoring logic without needing database imports
"""

# Copy the core scoring logic here for testing
def test_behavioral_scoring():
    """Test the behavioral boost calculations"""
    
    # Simulate a POI with base score
    base_score = 100.0
    poi_place_id = "ChIJabc123"
    
    print("=== Behavioral Scoring Tests ===\n")
    
    # Test 1: No behavioral data
    print("Test 1: No behavioral data")
    print(f"  Base score: {base_score}")
    user_behavior = None
    if user_behavior:
        pass  # No boost
    final_score = base_score
    print(f"  Final score: {final_score}")
    print(f"  Expected: {base_score} (no change)\n")
    
    # Test 2: Viewed POI (+3 points)
    print("Test 2: POI was viewed")
    print(f"  Base score: {base_score}")
    user_behavior = {"viewed_place_ids": ["ChIJabc123"]}
    viewed_ids = set(user_behavior.get("viewed_place_ids", []))
    
    behavior_boost = 0
    behavior_multiplier = 1.0
    if poi_place_id in viewed_ids:
        behavior_boost += 3
    
    current_score = base_score + behavior_boost
    current_score *= behavior_multiplier
    
    print(f"  Behavior boost: +{behavior_boost}")
    print(f"  Behavior multiplier: ×{behavior_multiplier}")
    print(f"  Final score: {current_score}")
    print(f"  Expected: {base_score + 3}\n")
    
    # Test 3: Collected POI (+20 points)
    print("Test 3: POI was collected/bookmarked")
    print(f"  Base score: {base_score}")
    user_behavior = {"collected_place_ids": ["ChIJabc123"]}
    collected_ids = set(user_behavior.get("collected_place_ids", []))
    
    behavior_boost = 0
    behavior_multiplier = 1.0
    if poi_place_id in collected_ids:
        behavior_boost += 20
    
    current_score = base_score + behavior_boost
    current_score *= behavior_multiplier
    
    print(f"  Behavior boost: +{behavior_boost}")
    print(f"  Behavior multiplier: ×{behavior_multiplier}")
    print(f"  Final score: {current_score}")
    print(f"  Expected: {base_score + 20}\n")
    
    # Test 4: In trip (×1.4 multiplier)
    print("Test 4: POI in user's saved trips")
    print(f"  Base score: {base_score}")
    user_behavior = {"trip_place_ids": ["ChIJabc123"]}
    trip_ids = set(user_behavior.get("trip_place_ids", []))
    
    behavior_boost = 0
    behavior_multiplier = 1.0
    if poi_place_id in trip_ids:
        behavior_multiplier = 1.4
    
    current_score = base_score + behavior_boost
    current_score *= behavior_multiplier
    
    print(f"  Behavior boost: +{behavior_boost}")
    print(f"  Behavior multiplier: ×{behavior_multiplier}")
    print(f"  Final score: {current_score}")
    print(f"  Expected: {base_score * 1.4}\n")
    
    # Test 5: All signals combined (viewed + collected + in trip)
    print("Test 5: POI has ALL behavioral signals")
    print(f"  Base score: {base_score}")
    user_behavior = {
        "viewed_place_ids": ["ChIJabc123"],
        "collected_place_ids": ["ChIJabc123"],
        "trip_place_ids": ["ChIJabc123"]
    }
    viewed_ids = set(user_behavior.get("viewed_place_ids", []))
    collected_ids = set(user_behavior.get("collected_place_ids", []))
    trip_ids = set(user_behavior.get("trip_place_ids", []))
    
    behavior_boost = 0
    behavior_multiplier = 1.0
    
    if poi_place_id in viewed_ids:
        behavior_boost += 3
    if poi_place_id in collected_ids:
        behavior_boost += 20
    if poi_place_id in trip_ids:
        behavior_multiplier = 1.4
    
    current_score = base_score + behavior_boost
    current_score *= behavior_multiplier
    
    print(f"  Behavior boost: +{behavior_boost} (3 viewed + 20 collected)")
    print(f"  Behavior multiplier: ×{behavior_multiplier}")
    print(f"  Final score: {current_score}")
    expected = (base_score + 23) * 1.4
    print(f"  Expected: ({base_score} + 23) × 1.4 = {expected}\n")
    
    # Test 6: Different POI IDs (no match)
    print("Test 6: POI not in user behavior (different IDs)")
    print(f"  Base score: {base_score}")
    user_behavior = {
        "viewed_place_ids": ["ChIJxyz999"],  # Different ID
        "collected_place_ids": ["ChIJlmn888"],
        "trip_place_ids": ["ChIJdef777"]
    }
    viewed_ids = set(user_behavior.get("viewed_place_ids", []))
    collected_ids = set(user_behavior.get("collected_place_ids", []))
    trip_ids = set(user_behavior.get("trip_place_ids", []))
    
    behavior_boost = 0
    behavior_multiplier = 1.0
    
    if poi_place_id in viewed_ids:
        behavior_boost += 3
    if poi_place_id in collected_ids:
        behavior_boost += 20
    if poi_place_id in trip_ids:
        behavior_multiplier = 1.4
    
    current_score = base_score + behavior_boost
    current_score *= behavior_multiplier
    
    print(f"  Behavior boost: +{behavior_boost}")
    print(f"  Behavior multiplier: ×{behavior_multiplier}")
    print(f"  Final score: {current_score}")
    print(f"  Expected: {base_score} (no boost, POI not in behavior data)\n")
    
    print("=== All tests completed ===")

if __name__ == "__main__":
    test_behavioral_scoring()
