"""
Test script for the mobile-optimized /supervisor/plan-trip/mobile endpoint.

This endpoint returns lightweight data structure with:
- Google Place IDs
- Sequence numbers (1-N across entire trip)
- Day assignments

Perfect for mobile app consumption.

Run this after starting the FastAPI server with: uvicorn main:app --reload
"""

import requests
import json

# API endpoint
url = "http://localhost:8000/supervisor/plan-trip/mobile"

# Test payload
payload = {
    "destination_state": "Penang",
    "max_pois_per_day": 6,
    "number_of_travelers": 2,
    "preferred_poi_names": [
        "Kek Lok Si Temple",
        "Penang Hill"
    ],
    "trip_duration_days": 3,
    "user_preferences": [
        "Food",
        "Culture",
        "Art"
    ]
}

print("=" * 80)
print("TESTING MOBILE ENDPOINT: /supervisor/plan-trip/mobile")
print("=" * 80)
print(f"\nURL: {url}")
print(f"\nPayload:")
print(json.dumps(payload, indent=2))
print("\nSending request...\n")

try:
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS! Mobile endpoint is working correctly.")
        print("=" * 80)
        
        # Show trip summary
        print("\n📋 TRIP SUMMARY:")
        print(json.dumps(data["trip_summary"], indent=2))
        
        # Show POI sequence (first 5 and last 5)
        print(f"\n🗺️  POI SEQUENCE ({data['total_pois']} total POIs):")
        pois = data["pois_sequence"]
        
        print("\nFirst 5 POIs:")
        for poi in pois[:5]:
            print(f"  [{poi['sequence_number']}] Day {poi['day']}: {poi['name']}")
            print(f"      google_place_id: {poi['google_place_id']}")
        
        if len(pois) > 10:
            print("\n  ...")
            print(f"\n  ({len(pois) - 10} POIs omitted)")
            print("\n  ...")
        
        print("\nLast 5 POIs:")
        for poi in pois[-5:]:
            print(f"  [{poi['sequence_number']}] Day {poi['day']}: {poi['name']}")
            print(f"      google_place_id: {poi['google_place_id']}")
        
        # Show metrics
        print(f"\n📊 METRICS:")
        print(f"  Total POIs: {data['total_pois']}")
        print(f"  Total Distance: {data['total_distance_km']} km")
        
        # Show POI distribution by day
        day_counts = {}
        for poi in pois:
            day = poi['day']
            day_counts[day] = day_counts.get(day, 0) + 1
        
        print(f"\n📅 POI DISTRIBUTION:")
        for day in sorted(day_counts.keys()):
            print(f"  Day {day}: {day_counts[day]} POIs")
        
        # Validate sequence numbers
        print(f"\n✅ VALIDATION:")
        sequence_numbers = [poi['sequence_number'] for poi in pois]
        expected_sequence = list(range(1, len(pois) + 1))
        
        if sequence_numbers == expected_sequence:
            print("  ✓ Sequence numbers are continuous (1 to N)")
        else:
            print("  ✗ WARNING: Sequence numbers have gaps or duplicates!")
        
        # Check for missing Google Place IDs
        missing_ids = [poi for poi in pois if poi['google_place_id'].startswith('unknown_')]
        if missing_ids:
            print(f"  ⚠️  WARNING: {len(missing_ids)} POIs missing Google Place IDs")
            for poi in missing_ids[:3]:
                print(f"      - {poi['name']} (sequence {poi['sequence_number']})")
        else:
            print("  ✓ All POIs have valid Google Place IDs")
        
        # Response size comparison
        response_size = len(response.content)
        print(f"\n📦 RESPONSE SIZE:")
        print(f"  Mobile endpoint: {response_size:,} bytes ({response_size/1024:.1f} KB)")
        print(f"  (Much smaller than full /plan-trip endpoint)")
        
        # Example usage for mobile app
        print("\n" + "=" * 80)
        print("📱 MOBILE APP USAGE EXAMPLE:")
        print("=" * 80)
        print("""
// 1. Fetch itinerary from this endpoint
const itinerary = await fetch('/supervisor/plan-trip/mobile', {
  method: 'POST',
  body: JSON.stringify(tripRequest)
}).then(r => r.json());

// 2. Loop through POIs in sequence
itinerary.pois_sequence.forEach(poi => {
  console.log(`Stop ${poi.sequence_number} on Day ${poi.day}`);
  
  // 3. Fetch full POI details from Google Places API
  const details = await googlePlaces.getDetails({
    placeId: poi.google_place_id,
    fields: ['name', 'photos', 'rating', 'formatted_address']
  });
  
  // 4. Display POI card in app
  renderPOICard(poi.sequence_number, details);
});
        """)
        
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to API. Make sure the server is running:")
    print("   uvicorn main:app --reload")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
