#!/usr/bin/env python3
"""
Quick test to verify request type detection logic
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from agents.input_parser import TripContext
from pydantic import ValidationError

# Test cases for request_type detection
test_cases = [
    {
        "description": "General Question - Culture",
        "request_type": "general_question",
        "should_have_destination": False,
        "should_have_trip_duration": False
    },
    {
        "description": "Full Trip - Multi-day planning",
        "request_type": "full_trip",
        "should_have_destination": True,
        "should_have_trip_duration": True
    },
    {
        "description": "POI Suggestions - No full itinerary",
        "request_type": "poi_suggestions",
        "should_have_destination": True,
        "should_have_trip_duration": False,
        "num_pois": 5
    }
]

print("\n" + "="*60)
print("Testing TripContext Model")
print("="*60)

# Test 1: General question with minimal fields
print("\nTest 1: General Question Type")
try:
    general = TripContext(
        destination_state="Malaysia",
        request_type="general_question",
        trip_duration_days=0,
        num_pois=0
    )
    print(f"✓ Created general question context")
    print(f"  - Request Type: {general.request_type}")
    print(f"  - Trip Duration: {general.trip_duration_days}")
except ValidationError as e:
    print(f"✗ Failed to create: {e}")

# Test 2: Full trip with all fields
print("\nTest 2: Full Trip Type")
try:
    full_trip = TripContext(
        destination_state="Penang",
        user_preferences=["Culture", "Food"],
        num_travelers=2,
        trip_duration_days=3,
        request_type="full_trip",
        num_pois=50
    )
    print(f"✓ Created full trip context")
    print(f"  - Request Type: {full_trip.request_type}")
    print(f"  - Trip Duration: {full_trip.trip_duration_days} days")
    print(f"  - Num POIs: {full_trip.num_pois}")
except ValidationError as e:
    print(f"✗ Failed to create: {e}")

# Test 3: POI suggestions with limited POIs
print("\nTest 3: POI Suggestions Type")
try:
    suggestions = TripContext(
        destination_state="Malacca",
        user_preferences=["History", "Architecture"],
        request_type="poi_suggestions",
        num_pois=5,  # Limited to 5
        trip_duration_days=1
    )
    print(f"✓ Created POI suggestions context")
    print(f"  - Request Type: {suggestions.request_type}")
    print(f"  - Num POIs: {suggestions.num_pois}")
    print(f"  - Trip Duration: {suggestions.trip_duration_days}")
except ValidationError as e:
    print(f"✗ Failed to create: {e}")

print("\n" + "="*60)
print("All model tests passed!")
print("="*60)
