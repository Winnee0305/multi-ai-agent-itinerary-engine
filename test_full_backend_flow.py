"""
Comprehensive Backend Flow Test Script

Tests the complete multi-ai-agent itinerary engine flow through FastAPI endpoints:
1. Info Agent - Get state information
2. Recommender Agent - Get recommendations with preferred POIs
3. Planner Agent - Plan multi-day itinerary with anchor-based clustering
4. Optimizer Agent - Optimize sequences
5. Supervisor Graph - End-to-end flow
6. Mobile Endpoint - Mobile-optimized format

Run this after starting the server with:
    uvicorn main:app --reload

Usage:
    python test_full_backend_flow.py
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test Colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_json(data: Dict[Any, Any], indent: int = 2):
    """Print formatted JSON."""
    print(f"{Colors.OKBLUE}{json.dumps(data, indent=indent)}{Colors.ENDC}")


def test_info_agent():
    """Test Info Agent endpoint."""
    print_section("TEST 1: Info Agent - State Information")
    
    try:
        response = requests.post(
            f"{BASE_URL}/info/state-info",
            json={"state_name": "Pahang"},
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Info Agent returned state info for Pahang")
            print_info(f"Capital: {data.get('capital', 'N/A')}")
            print_info(f"Population: {data.get('population', 'N/A'):,}")
            print_info(f"Description: {data.get('description', 'N/A')[:100]}...")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_recommender_agent():
    """Test Recommender Agent with preferred POIs."""
    print_section("TEST 2: Recommender Agent - POI Recommendations")
    
    payload = {
        "user_input": "I want to visit Genting Highlands and Cameron Highlands in Pahang",
        "user_state": "Pahang",
        "trip_duration_days": 5,
        "preferences": {
            "interests": ["nature", "highlands", "scenic_views"],
            "budget": "medium"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/recommender/recommend-pois",
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get("recommendations", [])
            
            print_success(f"Got {len(recommendations)} recommendations")
            
            # Check for preferred POIs
            preferred_count = sum(1 for poi in recommendations if poi.get("is_preferred", False))
            print_info(f"Preferred POIs: {preferred_count}")
            
            # Show top 5 POIs
            print_info("\nTop 5 POIs:")
            for i, poi in enumerate(recommendations[:5], 1):
                is_preferred = "⭐" if poi.get("is_preferred", False) else "  "
                print(f"  {is_preferred} {i}. {poi.get('name')} (Score: {poi.get('priority_score', 0):.1f})")
            
            return recommendations
        else:
            print_error(f"Failed with status {response.status_code}")
            return []
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return []


def test_planner_agent(recommendations: list):
    """Test Planner Agent with anchor-based clustering."""
    print_section("TEST 3: Planner Agent - Multi-Day Itinerary Planning")
    
    if not recommendations:
        print_error("No recommendations to plan with")
        return None
    
    # Use top 30 recommendations
    top_pois = recommendations[:30]
    
    payload = {
        "priority_pois": top_pois,
        "trip_duration_days": 5,
        "max_pois_per_day": 5,
        "anchor_proximity_threshold": 30000,  # 30km
        "poi_search_radius": 50000  # 50km
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/planner/plan-itinerary",
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print_success("Itinerary planned successfully")
            
            trip_summary = data.get("trip_summary", {})
            print_info(f"Total Days: {trip_summary.get('total_days', 0)}")
            print_info(f"Total POIs: {trip_summary.get('total_pois', 0)}")
            print_info(f"Total Distance: {trip_summary.get('total_distance_meters', 0)/1000:.1f} km")
            print_info(f"Clustering Strategy: {data.get('clustering_strategy_used', 'N/A')}")
            print_info(f"Preferred POIs Requested: {trip_summary.get('preferred_pois_requested', 0)}")
            print_info(f"Preferred POIs Included: {trip_summary.get('preferred_pois_included', 0)}")
            
            # Show daily breakdown
            print_info("\nDaily Breakdown:")
            daily_itineraries = data.get("daily_itineraries", [])
            for day in daily_itineraries:
                day_num = day.get("day", 0)
                pois_count = day.get("total_pois", 0)
                distance = day.get("total_distance_meters", 0) / 1000
                
                print(f"  Day {day_num}: {pois_count} POIs, {distance:.1f} km")
                
                # Show POIs with preferred markers
                for poi in day.get("pois", [])[:3]:  # First 3 POIs per day
                    is_preferred = "⭐" if poi.get("is_preferred", False) else "  "
                    name = poi.get("google_matched_name") or poi.get("name", "Unknown")
                    print(f"    {is_preferred} {name}")
                
                if len(day.get("pois", [])) > 3:
                    print(f"    ... and {len(day.get('pois', [])) - 3} more")
            
            return data
        else:
            print_error(f"Failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


def test_supervisor_graph():
    """Test Supervisor Graph end-to-end flow."""
    print_section("TEST 4: Supervisor Graph - Complete Trip Planning")
    
    payload = {
        "user_input": "Plan a 5-day trip to Pahang visiting Genting Highlands and Cameron Highlands",
        "user_state": "Pahang",
        "trip_duration_days": 5,
        "preferences": {
            "interests": ["nature", "highlands", "theme_parks"],
            "budget": "medium"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/supervisor/plan-trip",
            json=payload,
            headers=HEADERS,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print_success("Supervisor graph completed successfully")
            
            # Show state transitions
            state_history = data.get("state_history", [])
            print_info(f"\nState Transitions ({len(state_history)} states):")
            for i, state in enumerate(state_history, 1):
                print(f"  {i}. {state}")
            
            # Show itinerary summary
            itinerary = data.get("itinerary", {})
            if itinerary:
                trip_summary = itinerary.get("trip_summary", {})
                print_info(f"\nTrip Summary:")
                print_info(f"  Total POIs: {trip_summary.get('total_pois', 0)}")
                print_info(f"  Total Days: {trip_summary.get('total_days', 0)}")
                print_info(f"  Total Distance: {trip_summary.get('total_distance_meters', 0)/1000:.1f} km")
                print_info(f"  Preferred POIs: {trip_summary.get('preferred_pois_included', 0)}/{trip_summary.get('preferred_pois_requested', 0)}")
            
            return data
        else:
            print_error(f"Failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


def test_mobile_endpoint():
    """Test Mobile endpoint with preferred POIs."""
    print_section("TEST 5: Mobile Endpoint - Optimized Format")
    
    payload = {
        "user_input": "Plan a 5-day trip to Pahang with Genting Highlands and Cameron Highlands",
        "user_state": "Pahang",
        "trip_duration_days": 5,
        "preferences": {
            "interests": ["nature", "highlands"],
            "budget": "medium"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/supervisor/plan-trip/mobile",
            json=payload,
            headers=HEADERS,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print_success("Mobile endpoint returned optimized format")
            
            # Show POI sequence
            pois = data.get("pois", [])
            print_info(f"Total POIs: {len(pois)}")
            
            # Show first 5 POIs with details
            print_info("\nFirst 5 POIs:")
            for poi in pois[:5]:
                seq = poi.get("sequence_number", 0)
                day = poi.get("day", 0)
                name = poi.get("name", "Unknown")
                is_preferred = "⭐" if poi.get("is_preferred", False) else "  "
                distance = poi.get("distance_from_previous_meters", 0) / 1000
                
                print(f"  {is_preferred} #{seq} (Day {day}): {name} [{distance:.1f} km]")
            
            # Show summary
            summary = data.get("summary", {})
            print_info(f"\nSummary:")
            print_info(f"  Total POIs: {summary.get('total_pois', 0)}")
            print_info(f"  Total Days: {summary.get('total_days', 0)}")
            print_info(f"  Total Distance: {summary.get('total_distance_km', 0):.1f} km")
            print_info(f"  Clustering Strategy: {data.get('clustering_strategy', 'N/A')}")
            print_info(f"  Preferred POIs: {summary.get('preferred_pois_included', 0)}/{summary.get('preferred_pois_requested', 0)}")
            
            return data
        else:
            print_error(f"Failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


def test_for_you_recommendations():
    """Test For You page recommendations with randomness."""
    print_section("TEST 6: For You Recommendations - Randomness & Variety")
    
    payload = {
        "user_state": "Pahang",
        "user_id": "test_user_123",
        "limit": 10
    }
    
    try:
        # Call endpoint twice to verify randomness
        print_info("Fetching recommendations (Call 1)...")
        response1 = requests.post(
            f"{BASE_URL}/recommender/for-you",
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        print_info("Fetching recommendations (Call 2)...")
        response2 = requests.post(
            f"{BASE_URL}/recommender/for-you",
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            recs1 = data1.get("recommendations", [])
            recs2 = data2.get("recommendations", [])
            
            # Check for variety
            ids1 = set(poi["google_place_id"] for poi in recs1)
            ids2 = set(poi["google_place_id"] for poi in recs2)
            
            overlap = len(ids1 & ids2)
            unique1 = len(ids1 - ids2)
            unique2 = len(ids2 - ids1)
            
            print_success(f"Got {len(recs1)} recommendations in each call")
            print_info(f"Overlap: {overlap} POIs")
            print_info(f"Unique to Call 1: {unique1} POIs")
            print_info(f"Unique to Call 2: {unique2} POIs")
            print_info(f"Variety Score: {(unique1 + unique2)/(len(recs1) + len(recs2))*100:.1f}%")
            
            if overlap < len(recs1):
                print_success("✓ Randomness verified - different POIs in each call")
            else:
                print_error("✗ No randomness detected - identical POIs")
            
            return True
        else:
            print_error("Failed to get recommendations")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_packing_list():
    """Test Packing List Generation for mobile."""
    print_section("TEST 7: Packing List - Smart Recommendations")
    
    # Sample itinerary data
    payload = {
        "daily_itineraries": [
            {
                "day": 1,
                "pois": [
                    {"name": "Lavender Garden Cameron", "category": "nature"},
                    {"name": "Gunung Brinchang", "category": "hiking"},
                    {"name": "Sam Poh Temple", "category": "religious"}
                ]
            },
            {
                "day": 2,
                "pois": [
                    {"name": "Genting SkyWorlds Theme Park", "category": "entertainment"},
                    {"name": "Chin Swee Caves Temple", "category": "religious"}
                ]
            }
        ],
        "trip_duration_days": 5,
        "destination_state": "Pahang"
    }
    
    try:
        print_info("Sending packing list request...")
        print_json(payload)
        
        response = requests.post(
            f"{BASE_URL}/supervisor/generate-packing-list/mobile",
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Packing list generated successfully!")
            
            # Display trip summary
            trip_summary = data.get("trip_summary", {})
            print(f"\n{Colors.BOLD}Trip Analysis:{Colors.ENDC}")
            print(f"  Destination: {trip_summary.get('destination')}")
            print(f"  Duration: {trip_summary.get('duration_days')} days")
            print(f"  Activities: {', '.join(trip_summary.get('activities', []))}")
            print(f"  Climate: {trip_summary.get('climate')}")
            
            # Display packing categories
            categories = data.get("categories", [])
            print(f"\n{Colors.BOLD}Packing Categories ({len(categories)}):{Colors.ENDC}")
            
            for category in categories:
                items = category.get("items", [])
                if items:  # Only show categories with items
                    print(f"\n{category['icon']} {Colors.OKCYAN}{category['name']}{Colors.ENDC} ({len(items)} items):")
                    for item in items[:3]:  # Show first 3 items per category
                        priority = item['priority'].upper()
                        color = Colors.FAIL if priority == "ESSENTIAL" else Colors.WARNING if priority == "RECOMMENDED" else Colors.OKBLUE
                        print(f"  {color}[{priority}]{Colors.ENDC} {item['item']}")
                        print(f"    → {item['reason']}")
            
            # Display smart tips
            tips = data.get("smart_tips", [])
            if tips:
                print(f"\n{Colors.BOLD}💡 Smart Tips:{Colors.ENDC}")
                for i, tip in enumerate(tips, 1):
                    print(f"  {i}. {tip}")
            
            print_success(f"✓ Generated {len(categories)} categories with smart recommendations")
            return True
            
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def run_all_tests():
    """Run all backend tests."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║                  MULTI-AI-AGENT ITINERARY ENGINE TEST SUITE                   ║")
    print("║                          Comprehensive Backend Flow                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    print_info(f"Testing server at: {BASE_URL}")
    print_info("Make sure the server is running with: uvicorn main:app --reload\n")
    
    results = {
        "info_agent": False,
        "recommender_agent": False,
        "planner_agent": False,
        "supervisor_graph": False,
        "mobile_endpoint": False,
        "for_you_recommendations": False,
        "packing_list": False
    }
    
    # Test 1: Info Agent
    results["info_agent"] = test_info_agent()
    
    # Test 2: Recommender Agent
    recommendations = test_recommender_agent()
    results["recommender_agent"] = len(recommendations) > 0
    
    # Test 3: Planner Agent
    if recommendations:
        itinerary = test_planner_agent(recommendations)
        results["planner_agent"] = itinerary is not None
    
    # Test 4: Supervisor Graph
    results["supervisor_graph"] = test_supervisor_graph() is not None
    
    # Test 5: Mobile Endpoint
    mobile_result = test_mobile_endpoint()
    results["mobile_endpoint"] = mobile_result is not None
    
    # Test 6: For You Recommendations
    results["for_you_recommendations"] = test_for_you_recommendations()
    
    # Test 7: Packing List
    results["packing_list"] = test_packing_list()
    
    # Final Summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        color = Colors.OKGREEN if passed else Colors.FAIL
        print(f"{color}{test_name.replace('_', ' ').title()}: {status}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Results: {passed_tests}/{total_tests} tests passed{Colors.ENDC}")
    
    if failed_tests == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  {failed_tests} test(s) failed{Colors.ENDC}")
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


if __name__ == "__main__":
    run_all_tests()
