"""
Test script for the new LangGraph-based supervisor graph.

This script demonstrates the complete trip planning workflow:
1. User provides natural language request
2. Graph parses input and extracts trip context
3. Recommender generates POI recommendations
4. Planner creates optimized itinerary
5. Formatter produces user-friendly output

Run with: python test_graph.py
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agents.supervisor_graph import create_supervisor_graph
from config.settings import settings


def test_trip_planning_graph():
    """Test the complete trip planning graph with a sample query."""
    
    print("=" * 80)
    print("TESTING LANGGRAPH TRIP PLANNER")
    print("=" * 80)
    print()
    
    # Initialize model
    print("Initializing Gemini model...")
    model = ChatGoogleGenerativeAI(
        model=settings.DEFAULT_LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE
    )
    
    # Create graph
    print("Creating supervisor graph...")
    graph = create_supervisor_graph(model)
    
    # Configuration with thread ID for memory
    config = {
        "configurable": {
            "thread_id": "test_trip_123"
        }
    }
    
    # Test queries
    test_queries = [
        "Plan a 3-day food and culture trip to Penang for 2 people",
        "I want a 4-day adventure and nature trip to Pahang for a family of 5",
        "Create a 2-day cultural itinerary for Malacca, must include A Famosa and Jonker Street"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print()
        print("=" * 80)
        print(f"TEST QUERY {i}: {query}")
        print("=" * 80)
        print()
        
        # Stream execution
        print("🚀 Starting graph execution...\n")
        
        try:
            for event in graph.stream(
                {"messages": [HumanMessage(content=query)]},
                config={
                    "configurable": {
                        "thread_id": f"test_trip_{i}"
                    }
                },
                stream_mode="values"
            ):
                # Print latest AI message
                if event.get("messages"):
                    latest_message = event["messages"][-1]
                    if latest_message.type == "ai":
                        print(f"📨 {latest_message.content}\n")
                        print("-" * 80)
                        print()
            
            print("✅ Graph execution completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during graph execution: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Only run first test to save time
        print("\n🛑 Stopping after first test. Remove this break to test all queries.")
        break


def test_simple_graph():
    """Test with a simple workflow to debug."""
    
    print("=" * 80)
    print("TESTING SIMPLE WORKFLOW")
    print("=" * 80)
    
    model = ChatGoogleGenerativeAI(
        model=settings.DEFAULT_LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE
    )
    
    graph = create_supervisor_graph(model)
    
    query = "Plan a 3-day trip to Penang for 2 people who love food and culture"
    
    print(f"\nQuery: {query}\n")
    
    result = graph.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"configurable": {"thread_id": "simple_test"}}
    )
    
    print("\n=== FINAL STATE ===")
    print(f"Destination: {result.get('destination_state')}")
    print(f"Duration: {result.get('trip_duration_days')} days")
    print(f"Travelers: {result.get('num_travelers')}")
    print(f"Preferences: {result.get('user_preferences')}")
    print(f"POIs found: {len(result.get('top_priority_pois', []))}")
    print(f"Itinerary created: {result.get('itinerary') is not None}")
    
    if result.get("messages"):
        print("\n=== FINAL MESSAGE ===")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    import sys
    
    # Choose test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        test_simple_graph()
    else:
        test_trip_planning_graph()
