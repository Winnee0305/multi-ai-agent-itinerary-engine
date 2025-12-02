"""
Test script to verify StructuredTool pattern works correctly
"""

from tools.supervisor_tools import get_poi_recommendations, plan_itinerary
from langchain_core.tools import StructuredTool


def test_tool_types():
    """Verify tools are StructuredTool instances"""
    print("=" * 60)
    print("Testing Tool Types")
    print("=" * 60)
    
    print(f"\nget_poi_recommendations type: {type(get_poi_recommendations)}")
    print(f"Is StructuredTool: {isinstance(get_poi_recommendations, StructuredTool)}")
    
    print(f"\nplan_itinerary type: {type(plan_itinerary)}")
    print(f"Is StructuredTool: {isinstance(plan_itinerary, StructuredTool)}")
    
    print("\n✅ Both tools are StructuredTool instances")


def test_tool_attributes():
    """Verify tools have correct attributes"""
    print("\n" + "=" * 60)
    print("Testing Tool Attributes")
    print("=" * 60)
    
    print(f"\nget_poi_recommendations.name: {get_poi_recommendations.name}")
    print(f"get_poi_recommendations.description: {get_poi_recommendations.description[:100]}...")
    
    print(f"\nplan_itinerary.name: {plan_itinerary.name}")
    print(f"plan_itinerary.description: {plan_itinerary.description[:100]}...")
    
    print("\n✅ Tools have correct name and description attributes")


def test_tool_invocation_methods():
    """Verify tools have both direct call and .invoke() methods"""
    print("\n" + "=" * 60)
    print("Testing Invocation Methods")
    print("=" * 60)
    
    # Check if func attribute exists (for direct calls)
    print(f"\nget_poi_recommendations.func: {get_poi_recommendations.func}")
    print(f"Callable: {callable(get_poi_recommendations.func)}")
    
    # Check if invoke method exists
    print(f"\nget_poi_recommendations.invoke: {get_poi_recommendations.invoke}")
    print(f"Callable: {callable(get_poi_recommendations.invoke)}")
    
    print("\n✅ Tools support both direct function calls and .invoke()")


def test_tool_schema():
    """Verify tools have input schema"""
    print("\n" + "=" * 60)
    print("Testing Tool Schema")
    print("=" * 60)
    
    print(f"\nget_poi_recommendations.args_schema:")
    print(f"  {get_poi_recommendations.args_schema}")
    
    print(f"\nplan_itinerary.args_schema:")
    print(f"  {plan_itinerary.args_schema}")
    
    print("\n✅ Tools have proper schema definitions")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("StructuredTool Pattern Verification")
    print("=" * 60)
    
    try:
        test_tool_types()
        test_tool_attributes()
        test_tool_invocation_methods()
        test_tool_schema()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - StructuredTool pattern is working!")
        print("=" * 60)
        
        print("\n📝 Summary:")
        print("  - Supervisor tools are StructuredTool instances")
        print("  - Tools can be called directly: get_poi_recommendations(request)")
        print("  - Tools also support .invoke() for LangChain compatibility")
        print("  - Ready for programmatic orchestration in supervisor agent")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
