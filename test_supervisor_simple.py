"""
Simple test for refactored Supervisor Agent
"""

from agents.supervisor_agent import supervisor_agent


def test_basic_invoke():
    """Test basic invoke method"""
    print("=" * 80)
    print("Testing Supervisor Agent - Invoke Method")
    print("=" * 80)
    
    query = """
    Plan a 2-day trip to Penang for 2 people.
    Interests: Food, Culture
    """
    
    print(f"\nQuery: {query}\n")
    print("-" * 80)
    
    try:
        result = supervisor_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        print("\n✅ Invoke successful!")
        print("\nResult structure:", type(result))
        print("\nMessages:", len(result.get("messages", [])))
        
        if "messages" in result:
            final_message = result["messages"][-1]
            print(f"\nFinal response preview:")
            print(final_message.get("content", str(final_message))[:500])
            print("...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_basic_stream():
    """Test basic stream method"""
    print("\n" + "=" * 80)
    print("Testing Supervisor Agent - Stream Method")
    print("=" * 80)
    
    query = """
    Recommend POIs in Kuala Lumpur for 3 days.
    Interests: Shopping, Food
    """
    
    print(f"\nQuery: {query}\n")
    print("-" * 80)
    
    try:
        step_count = 0
        for step in supervisor_agent.stream({
            "messages": [{"role": "user", "content": query}]
        }):
            step_count += 1
            print(f"\n📦 Step {step_count}:")
            for key, value in step.items():
                print(f"  {key}: {type(value)}")
                if isinstance(value, dict) and "messages" in value:
                    for msg in value["messages"]:
                        content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
                        print(f"    → {content[:100]}...")
        
        print(f"\n✅ Stream successful! {step_count} steps completed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SUPERVISOR AGENT - SIMPLE TESTS")
    print("=" * 80)
    print("\nThis tests the refactored supervisor with direct orchestration")
    print("(No LLM tool selection, just sequential workflow)")
    print("=" * 80 + "\n")
    
    # Test invoke
    test_basic_invoke()
    
    # Test stream
    # test_basic_stream()
    
    print("\n" + "=" * 80)
    print("Tests completed")
    print("=" * 80 + "\n")
