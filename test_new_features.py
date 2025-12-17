#!/usr/bin/env python3
"""
Test the new features:
1. General chatbot for out-of-scope questions
2. POI suggestions mode
"""

import os
import sys
from typing import Optional

# Configure settings
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from langchain_google_genai import ChatGoogleGenerativeAI
from agents.supervisor_graph import create_supervisor_graph
from agents.state import TripPlannerState


def test_general_question():
    """Test 1: General question (out of scope)"""
    print("\n" + "="*60)
    print("TEST 1: General Question (Cultural)")
    print("="*60)
    
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    graph = create_supervisor_graph(model)
    
    # Test question: General cultural question (no trip planning)
    user_message = "Tell me about Malaysian food culture and what makes it unique"
    
    print(f"\nUser: {user_message}")
    print("\nProcessing...")
    
    config = {"configurable": {"thread_id": "general_question_test"}}
    
    try:
        result = graph.invoke(
            {
                "messages": [],
                "destination_state": None,
                "user_preferences": [],
                "trip_duration_days": 0,
                "next_step": None
            },
            config=config,
            input={"type": "human", "content": user_message}
        )
        
        # Extract and print the response
        if result.get("messages"):
            final_message = result["messages"][-1]
            print(f"\nAssistant: {final_message.content}")
            print(f"\nRequest Type Detected: {result.get('request_type', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_poi_suggestions():
    """Test 2: POI suggestions mode"""
    print("\n" + "="*60)
    print("TEST 2: POI Suggestions Mode")
    print("="*60)
    
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    graph = create_supervisor_graph(model)
    
    # Test question: User asking for suggestions
    user_message = "Suggest some temples and cultural sites in Penang"
    
    print(f"\nUser: {user_message}")
    print("\nProcessing...")
    
    config = {"configurable": {"thread_id": "poi_suggestions_test"}}
    
    try:
        result = graph.invoke(
            {
                "messages": [],
                "destination_state": None,
                "user_preferences": [],
                "trip_duration_days": 0,
                "next_step": None
            },
            config=config,
            input={"type": "human", "content": user_message}
        )
        
        # Extract and print the response
        if result.get("messages"):
            final_message = result["messages"][-1]
            print(f"\nAssistant:\n{final_message.content}")
            print(f"\nRequest Type Detected: {result.get('request_type', 'N/A')}")
            print(f"Number of POIs to Show: {result.get('num_pois', 'N/A')}")
            
            if result.get("top_priority_pois"):
                print(f"\nFound {len(result['top_priority_pois'])} POIs")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_full_trip_planning():
    """Test 3: Full trip planning (baseline test)"""
    print("\n" + "="*60)
    print("TEST 3: Full Trip Planning (Baseline)")
    print("="*60)
    
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    graph = create_supervisor_graph(model)
    
    # Test question: Full trip planning request
    user_message = "Plan a 3-day trip to Malacca. I'm interested in history and food."
    
    print(f"\nUser: {user_message}")
    print("\nProcessing...")
    
    config = {"configurable": {"thread_id": "full_trip_test"}}
    
    try:
        result = graph.invoke(
            {
                "messages": [],
                "destination_state": None,
                "user_preferences": [],
                "trip_duration_days": 0,
                "next_step": None
            },
            config=config,
            input={"type": "human", "content": user_message}
        )
        
        # Extract and print the response
        if result.get("messages"):
            final_message = result["messages"][-1]
            print(f"\nAssistant:\n{final_message.content[:500]}...")  # Show first 500 chars
            print(f"\nRequest Type Detected: {result.get('request_type', 'N/A')}")
            print(f"Trip Duration: {result.get('trip_duration_days', 'N/A')} days")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nTesting New Features Implementation")
    print("=" * 60)
    
    try:
        # Test 1: General question
        test_general_question()
        
        # Test 2: POI suggestions
        test_poi_suggestions()
        
        # Test 3: Full trip (baseline)
        test_full_trip_planning()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"Test suite error: {e}")
        import traceback
        traceback.print_exc()
