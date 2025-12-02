"""
Test script for Recommender Agent API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_get_interest_categories():
    """Test getting available interest categories"""
    print("\n" + "="*80)
    print("TEST 1: Get Interest Categories")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/recommender/interest-categories")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"Available categories: {result['categories']}")
        print(f"\nCategory details:")
        for cat, types in result['category_details'].items():
            print(f"  {cat}: {', '.join(types[:3])}...")
    else:
        print(f"❌ Error: {response.text}")


def test_get_available_states():
    """Test getting available states"""
    print("\n" + "="*80)
    print("TEST 2: Get Available States")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/recommender/states")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"Available states ({result['count']}): {result['states']}")
    else:
        print(f"❌ Error: {response.text}")


def test_load_pois():
    """Test loading POIs from database"""
    print("\n" + "="*80)
    print("TEST 3: Load POIs from Database")
    print("="*80)
    
    payload = {
        "state": "Penang",
        "golden_only": True,
        "min_popularity": 70
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/recommender/load-pois", json=payload)
    
    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"Found {result['count']} POIs")
        
        # Show first 3 POIs
        if result['pois']:
            print(f"\nFirst 3 POIs:")
            for poi in result['pois'][:3]:
                print(f"  - {poi.get('name')} (Pop: {poi.get('popularity_score')}, State: {poi.get('state')})")
    else:
        print(f"❌ Error: {response.text}")


def test_get_recommendations():
    """Test complete recommendation workflow"""
    print("\n" + "="*80)
    print("TEST 4: Get Trip Recommendations (Complete Workflow)")
    print("="*80)
    
    payload = {
        "destination_state": "Penang",
        "user_preferences": ["Food", "Culture", "Art"],
        "number_of_travelers": 2,
        "trip_duration_days": 3,
        "preferred_poi_names": ["Kek Lok Si", "Penang Hill"],
        "top_n": 20
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/recommender/recommend", json=payload)
    
    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"\nDestination: {result['destination_state']}")
        print(f"Trip Duration: {result['trip_duration_days']} days")
        print(f"\nTop 10 Priority POIs:")
        
        for i, poi in enumerate(result['top_priority_pois'][:10], 1):
            print(f"  {i:2}. {poi['name']:40} | Priority: {poi['priority_score']:.2f} | {poi.get('state', 'N/A')}")
        
        print(f"\n📊 Recommended Activity Mix:")
        for activity, percentage in result['recommended_activity_mix'].items():
            bar = "█" * int(percentage * 50)
            print(f"  {activity:15} {percentage:4.0%} {bar}")
        
        print(f"\n💡 Reasoning: {result['summary_reasoning']}")
        
        # Save output
        with open("test_recommendation_output.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Full output saved to test_recommendation_output.json")
        
    else:
        print(f"❌ Error: {response.text}")


def test_kuala_lumpur_recommendations():
    """Test recommendations for Kuala Lumpur"""
    print("\n" + "="*80)
    print("TEST 5: Kuala Lumpur Family Trip (5 travelers, 4 days)")
    print("="*80)
    
    payload = {
        "destination_state": "Kuala Lumpur",
        "user_preferences": ["Adventure", "Shopping", "Food"],
        "number_of_travelers": 5,
        "trip_duration_days": 4,
        "preferred_poi_names": None,
        "top_n": 30
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/recommender/recommend", json=payload)
    
    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success!")
        print(f"\nTop 10 Priority POIs:")
        
        for i, poi in enumerate(result['top_priority_pois'][:10], 1):
            print(f"  {i:2}. {poi['name']:40} | Priority: {poi['priority_score']:.2f}")
        
        print(f"\n📊 Activity Mix: {result['recommended_activity_mix']}")
        
    else:
        print(f"❌ Error: {response.text}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RECOMMENDER AGENT API TESTS")
    print("="*80)
    print("Make sure the API server is running: uvicorn main:app --reload")
    print("="*80)
    
    try:
        # Test API is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API server not responding. Please start it with: uvicorn main:app --reload")
            return
        
        # Run tests
        test_get_interest_categories()
        test_get_available_states()
        test_load_pois()
        test_get_recommendations()
        test_kuala_lumpur_recommendations()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API server.")
        print("Please start the server with: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
