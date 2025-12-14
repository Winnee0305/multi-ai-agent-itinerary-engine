"""
Test script to verify preferred POI fix

This tests that preferred_poi_names are properly passed through the system
without being lost in LLM translation.

Run with: python test_preferred_poi_fix.py
(Make sure server is running: uvicorn main:app --reload)
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_lavender_garden():
    """Test with Lavender garden in Pahang"""
    print("="*80)
    print("TEST: Preferred POI - Lavender Garden")
    print("="*80)
    
    payload = {
        "destination_state": "Pahang",
        "max_pois_per_day": 4,
        "number_of_travelers": 2,
        "preferred_poi_names": ["Lavender garden"],
        "trip_duration_days": 7,
        "user_preferences": ["Food", "Culture", "Art", "Entertainment"]
    }
    
    print("\n📤 Sending request...")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/supervisor/plan-trip/mobile",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n✅ Response received!")
        print(f"\n📊 Trip Summary:")
        print(f"  Destination: {data['trip_summary']['destination']}")
        print(f"  Days: {data['trip_summary']['duration_days']}")
        print(f"  Total POIs: {data['total_pois']}")
        print(f"  Clustering: {data['clustering_strategy']}")
        print(f"  ⭐ Preferred POIs Requested: {data['trip_summary']['preferred_pois_requested']}")
        print(f"  ⭐ Preferred POIs Included: {data['trip_summary']['preferred_pois_included']}")
        
        # Check for preferred POIs
        preferred_pois = [poi for poi in data['pois_sequence'] if poi['is_preferred']]
        
        if preferred_pois:
            print(f"\n✨ Found {len(preferred_pois)} preferred POI(s):")
            for poi in preferred_pois:
                print(f"  ⭐ {poi['name']} (Day {poi['day']}, Seq #{poi['sequence_number']})")
        else:
            print("\n❌ NO PREFERRED POIs FOUND!")
            print("This indicates the fix didn't work or Lavender garden doesn't exist in database.")
        
        # Show first 5 POIs
        print(f"\n📍 First 5 POIs in sequence:")
        for poi in data['pois_sequence'][:5]:
            marker = "⭐" if poi['is_preferred'] else "  "
            print(f"  {marker} #{poi['sequence_number']} (Day {poi['day']}): {poi['name']}")
        
        # Validation
        print("\n🔍 Validation:")
        if data['trip_summary']['preferred_pois_requested'] > 0:
            print("  ✅ System recognized preferred POI request")
        else:
            print("  ❌ System did NOT recognize preferred POI request")
        
        if data['trip_summary']['preferred_pois_included'] > 0:
            print("  ✅ Preferred POI included in itinerary")
        else:
            print("  ❌ Preferred POI NOT included in itinerary")
        
        inclusion_rate = (data['trip_summary']['preferred_pois_included'] / 
                         max(data['trip_summary']['preferred_pois_requested'], 1)) * 100
        print(f"  📈 Inclusion Rate: {inclusion_rate:.0f}%")
        
        if inclusion_rate == 100:
            print("\n🎉 SUCCESS! Preferred POIs working correctly!")
        else:
            print("\n⚠️  WARNING! Preferred POIs not fully included!")
        
    else:
        print(f"\n❌ Request failed with status {response.status_code}")
        print(f"Response: {response.text}")


def test_cameron_highlands():
    """Test with Cameron Highlands"""
    print("\n" + "="*80)
    print("TEST: Preferred POI - Cameron Highlands")
    print("="*80)
    
    payload = {
        "destination_state": "Pahang",
        "max_pois_per_day": 5,
        "number_of_travelers": 2,
        "preferred_poi_names": ["Cameron Highlands"],
        "trip_duration_days": 5,
        "user_preferences": ["Nature", "Culture", "Food"]
    }
    
    print("\n📤 Sending request...")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/supervisor/plan-trip/mobile",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n✅ Response received!")
        print(f"  ⭐ Preferred POIs Requested: {data['trip_summary']['preferred_pois_requested']}")
        print(f"  ⭐ Preferred POIs Included: {data['trip_summary']['preferred_pois_included']}")
        
        preferred_pois = [poi for poi in data['pois_sequence'] if poi['is_preferred']]
        
        if preferred_pois:
            print(f"\n✨ Found {len(preferred_pois)} preferred POI(s):")
            for poi in preferred_pois:
                print(f"  ⭐ {poi['name']}")
        else:
            print("\n❌ NO PREFERRED POIs FOUND!")
        
    else:
        print(f"\n❌ Request failed with status {response.status_code}")


def test_multiple_preferred_pois():
    """Test with multiple preferred POIs"""
    print("\n" + "="*80)
    print("TEST: Multiple Preferred POIs")
    print("="*80)
    
    payload = {
        "destination_state": "Pahang",
        "max_pois_per_day": 5,
        "number_of_travelers": 2,
        "preferred_poi_names": ["Genting Highlands", "Cameron Highlands", "Lavender garden"],
        "trip_duration_days": 7,
        "user_preferences": ["Nature", "Entertainment", "Food"]
    }
    
    print("\n📤 Sending request...")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/supervisor/plan-trip/mobile",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n✅ Response received!")
        print(f"  ⭐ Preferred POIs Requested: {data['trip_summary']['preferred_pois_requested']}")
        print(f"  ⭐ Preferred POIs Included: {data['trip_summary']['preferred_pois_included']}")
        
        preferred_pois = [poi for poi in data['pois_sequence'] if poi['is_preferred']]
        
        print(f"\n✨ Found {len(preferred_pois)} preferred POI(s):")
        for poi in preferred_pois:
            print(f"  ⭐ {poi['name']} (Day {poi['day']})")
        
        inclusion_rate = (data['trip_summary']['preferred_pois_included'] / 
                         max(data['trip_summary']['preferred_pois_requested'], 1)) * 100
        print(f"\n📈 Inclusion Rate: {inclusion_rate:.0f}%")
        
    else:
        print(f"\n❌ Request failed with status {response.status_code}")


if __name__ == "__main__":
    print("\n🧪 PREFERRED POI FIX VERIFICATION TESTS")
    print("Make sure server is running: uvicorn main:app --reload\n")
    
    try:
        test_lavender_garden()
        test_cameron_highlands()
        test_multiple_preferred_pois()
        
        print("\n" + "="*80)
        print("✅ All tests completed!")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server!")
        print("Please start the server with: uvicorn main:app --reload\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
