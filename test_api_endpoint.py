"""
Test script to verify the /supervisor/plan-trip endpoint works correctly.
Run this after starting the FastAPI server with: uvicorn main:app --reload
"""

import requests
import json

# API endpoint
url = "http://localhost:8000/supervisor/plan-trip"

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

print("Testing /supervisor/plan-trip endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...\n")

try:
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! API endpoint is working correctly.")
        
        # Show summary
        data = response.json()
        if data.get("success"):
            print("\n=== TRIP SUMMARY ===")
            print(f"Destination: {data['trip_context']['destination_state']}")
            print(f"Duration: {data['trip_context']['trip_duration_days']} days")
            print(f"Travelers: {data['trip_context']['num_travelers']}")
            print(f"POIs Found: {len(data['recommendations']['top_priority_pois'])}")
            
            if data.get('itinerary'):
                itinerary = data['itinerary']
                print(f"Itinerary Created: Yes ({itinerary.get('total_pois', 0)} POIs, {itinerary.get('total_distance_km', 0):.1f} km)")
    else:
        print(f"\n❌ ERROR: {response.json()}")
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to API. Make sure the server is running:")
    print("   uvicorn main:app --reload")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
