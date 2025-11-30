"""
Main entry point for the Multi-Agent Itinerary Planning System
"""

from orchestrator.itinerary_orchestrator import ItineraryOrchestrator
from config.settings import settings, validate_settings
import json


def main():
    """Run the itinerary planner with a sample query"""
    
    # Validate configuration
    try:
        validate_settings()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease set up your .env file with:")
        print("  - SUPABASE_URL")
        print("  - SERVICE_ROLE_KEY")
        print("  - OPENAI_API_KEY")
        return
    
    # Create orchestrator
    print("\n🚀 Initializing Multi-Agent Itinerary Planner...\n")
    orchestrator = ItineraryOrchestrator()
    
    # Example query
    user_query = """
    I'm planning a 5-day trip to Penang with my family (4 people).
    We love art, culture, and food. We'd like to visit Penang Street Art and Khoo Kongsi.
    We prefer a moderate pace and are interested in historical landmarks too.
    """
    
    print(f"User Query: {user_query.strip()}")
    
    # Generate itinerary
    try:
        result = orchestrator.generate_itinerary(user_query, verbose=True)
        
        # Print final itinerary
        print("\n" + "="*80)
        print("📋 FINAL ITINERARY")
        print("="*80)
        
        itinerary = result["itinerary"]
        
        # Print centroid
        print(f"\n📍 Trip Anchor Point: {itinerary['centroid']['name']}")
        print(f"   {itinerary.get('centroid_reasoning', '').strip()}")
        
        # Print daily routes
        print(f"\n📅 {itinerary['total_days']}-Day Itinerary:\n")
        
        for day_route in itinerary['daily_routes']:
            print(f"Day {day_route['day']}")
            print("-" * 40)
            
            for i, poi in enumerate(day_route['pois'], 1):
                print(f"  {i}. {poi['name']}")
                print(f"     Priority Score: {poi.get('priority_score', 0)}")
                if poi.get('google_rating'):
                    print(f"     Google: {poi['google_rating']}⭐ ({poi.get('google_reviews', 0)} reviews)")
                print()
            
            # Print validation
            validation = day_route.get('validation', {})
            if validation:
                print(f"  📏 Total Travel: {validation.get('total_distance_km', 0)}km")
                if validation.get('warnings'):
                    print(f"  ⚠️  Warnings: {len(validation['warnings'])}")
            print()
        
        # Print optimization report
        opt_report = itinerary.get('optimization_report', {})
        if opt_report.get('warnings'):
            print("\n⚠️  Optimization Warnings:")
            for warning in opt_report['warnings']:
                print(f"   • {warning}")
        
        # Save to file
        output_file = "generated_itinerary.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Full itinerary saved to: {output_file}")
        
        # Print execution summary
        summary = result['execution_summary']
        print(f"\n⏱️  Execution Time: {summary['total_time_seconds']:.2f}s")
        print(f"✅ Pipeline: {' → '.join(summary['agents_executed'])}")
        
    except Exception as e:
        print(f"\n❌ Error generating itinerary: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
