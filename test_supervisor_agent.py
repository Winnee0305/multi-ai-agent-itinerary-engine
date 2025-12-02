"""
Test script for Supervisor Agent
"""

from agents.supervisor_agent import supervisor_agent


def test_complete_trip_planning():
    """Test complete trip planning workflow"""
    print("\n" + "="*80)
    print("TEST 1: Complete Trip Planning (Penang)")
    print("="*80)
    
    query = """
    Plan a 3-day trip to Penang for 2 people.
    
    We love:
    - Food (especially local cuisine)
    - Culture and history
    - Street art
    
    We must visit Kek Lok Si Temple if possible.
    """
    
    print(f"\nUser Query:\n{query}")
    print("\n" + "-"*80)
    print("Supervisor Agent Processing...")
    print("-"*80 + "\n")
    
    # Stream the supervisor's response
    config = {"configurable": {"thread_id": "test-thread-1"}}
    for step in supervisor_agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        config = config
    ):
        for update in step.values():
            if "messages" in update:
                for msg in update["messages"]:
                    if hasattr(msg, "content"):
                        print(f"\n{msg.content}")
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            print(f"\n🔧 Tool: {tool_call['name']}")


def test_recommendations_only():
    """Test getting only recommendations"""
    print("\n" + "="*80)
    print("TEST 2: Recommendations Only (Kuala Lumpur)")
    print("="*80)
    
    query = """
    Recommend POIs in Kuala Lumpur for a family of 5 traveling for 4 days.
    
    Interests: Adventure, Shopping, Food
    We want about 30 recommendations.
    """
    
    print(f"\nUser Query:\n{query}")
    print("\n" + "-"*80)
    print("Supervisor Agent Processing...")
    print("-"*80 + "\n")
    
    config = {"configurable": {"thread_id": "test-thread-2"}}
    for step in supervisor_agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        config = config
    ):
        for update in step.values():
            if "messages" in update:
                for msg in update["messages"]:
                    if hasattr(msg, "content"):
                        print(f"\n{msg.content}")


def test_short_trip():
    """Test short trip planning"""
    print("\n" + "="*80)
    print("TEST 3: Short Trip Planning (Malacca - 2 days)")
    print("="*80)
    
    query = """
    I have only 2 days in Malacca. 
    Plan an itinerary for 3 people who are interested in history and food.
    We want to see the most important landmarks.
    """
    
    print(f"\nUser Query:\n{query}")
    print("\n" + "-"*80)
    print("Supervisor Agent Processing...")
    print("-"*80 + "\n")
    
    config = {"configurable": {"thread_id": "test-thread-3"}}
    for step in supervisor_agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        config = config
    ):
        for update in step.values():
            if "messages" in update:
                for msg in update["messages"]:
                    if hasattr(msg, "content"):
                        print(f"\n{msg.content}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SUPERVISOR AGENT TESTS")
    print("="*80)
    print("\nThe supervisor will coordinate Recommender and Planner agents")
    print("to create complete trip itineraries.")
    print("="*80)
    
    try:
        # Test 1: Complete trip planning
        test_complete_trip_planning()
        
        # Test 2: Recommendations only
        # test_recommendations_only()
        
        # Test 3: Short trip
        # test_short_trip()
        
        print("\n" + "="*80)
        print("✅ TESTS COMPLETED")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
