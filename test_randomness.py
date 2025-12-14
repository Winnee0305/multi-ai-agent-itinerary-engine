"""
Test script to verify random sequencing is working correctly.
This will test:
1. Same time window produces same sequence (deterministic)
2. Sequences vary across different POIs
3. Randomness doesn't break preferred POI handling
"""

import sys
from tools.planner_tools import sequence_pois_within_cluster, _generate_seed_for_sequencing

def test_sequence_randomness():
    """Test that sequences have controlled randomness."""
    print("\n" + "="*80)
    print("TESTING RANDOM SEQUENCE START POINT")
    print("="*80 + "\n")
    
    # Mock POI data
    test_pois = [
        {"name": "POI A", "lat": 3.1390, "lon": 101.6869, "priority_score": 5.0, "is_preferred": False},
        {"name": "POI B", "lat": 3.1400, "lon": 101.6880, "priority_score": 4.5, "is_preferred": False},
        {"name": "POI C", "lat": 3.1410, "lon": 101.6890, "priority_score": 4.0, "is_preferred": False},
        {"name": "POI D", "lat": 3.1420, "lon": 101.6900, "priority_score": 3.5, "is_preferred": False},
        {"name": "POI E", "lat": 3.1430, "lon": 101.6910, "priority_score": 3.0, "is_preferred": False},
    ]
    
    # Test 1: Multiple runs in same time window should produce same sequence
    print("Test 1: Determinism within time window")
    print("-" * 40)
    
    seed = _generate_seed_for_sequencing()
    print(f"Current seed: {seed}")
    
    sequences = []
    for i in range(3):
        # Create fresh copies to avoid mutation
        pois_copy = [p.copy() for p in test_pois]
        seq = sequence_pois_within_cluster(pois_copy)
        seq_names = [p["name"] for p in seq]
        sequences.append(seq_names)
        print(f"Run {i+1}: {' → '.join(seq_names)}")
    
    # Check if all sequences are identical
    if all(s == sequences[0] for s in sequences):
        print("✓ PASS: All sequences identical within time window\n")
    else:
        print("✗ FAIL: Sequences differ within same time window\n")
    
    # Test 2: Verify sequence starts at different points
    print("\nTest 2: Starting point varies")
    print("-" * 40)
    start_poi = sequences[0][0]
    print(f"Sequence starts with: {start_poi}")
    
    if start_poi != "POI A":
        print(f"✓ PASS: Starting point is randomized (not always POI A)\n")
    else:
        print(f"⚠ Note: Currently starts with POI A (may be random, may not be)\n")
    
    # Test 3: Verify sequence_no and distances are assigned
    print("\nTest 3: Verify sequence metadata")
    print("-" * 40)
    pois_copy = [p.copy() for p in test_pois]
    seq = sequence_pois_within_cluster(pois_copy)
    
    for poi in seq:
        seq_no = poi.get("sequence_no", "MISSING")
        dist = poi.get("distance_from_previous_meters", "MISSING")
        print(f"{poi['name']}: seq={seq_no}, dist={dist}m")
    
    has_metadata = all("sequence_no" in p and "distance_from_previous_meters" in p for p in seq)
    if has_metadata:
        print("✓ PASS: All POIs have sequence metadata\n")
    else:
        print("✗ FAIL: Missing sequence metadata\n")
    
    # Test 4: Test with preferred POI as start
    print("\nTest 4: Explicit start_poi parameter")
    print("-" * 40)
    
    preferred_poi = test_pois[2].copy()  # POI C
    pois_copy = [p.copy() for p in test_pois]
    
    seq = sequence_pois_within_cluster(pois_copy, start_poi=preferred_poi)
    seq_names = [p["name"] for p in seq]
    print(f"Forced start with POI C: {' → '.join(seq_names)}")
    
    if seq_names[0] == "POI C":
        print("✓ PASS: Explicit start_poi parameter respected\n")
    else:
        print("✗ FAIL: start_poi parameter ignored\n")
    
    print("="*80)
    print("RANDOMNESS TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        test_sequence_randomness()
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
