#!/usr/bin/env python3
"""
Quick Examples: Running Evaluations with Different Parameters

This file demonstrates various ways to use the evaluation.py script.
Run any of these commands from the project root directory.
"""

# ============================================================================
# EXAMPLE 1: Default Evaluation
# ============================================================================
# Generates a 3-day Penang trip for 2 people interested in food & culture
# 
# Command:
#   python evaluation.py
#
# What happens:
#   1. AI agent processes: "Plan a 3-day food and culture trip to Penang for 2 people"
#   2. Input Parser extracts trip parameters
#   3. Recommender loads and scores POIs
#   4. Planner clusters POIs by day and optimizes routes
#   5. Response Formatter generates output
#   6. Evaluation framework generates 7 visualization charts + text report
#


# ============================================================================
# EXAMPLE 2: Multi-Day Adventure Trip
# ============================================================================
# 5-day adventure and nature trip to Sabah for 3 travelers
#
# Command:
#   python evaluation.py \
#     --destination "Sabah" \
#     --days 5 \
#     --travelers 3 \
#     --interests "adventure,nature"
#
# Expected results:
#   - POIs heavily weighted toward outdoor activities (trekking, diving, hiking)
#   - Geographic clustering across Sabah (Kota Kinabalu, Sandakan, Tawau)
#   - Higher daily distances due to geographic spread
#


# ============================================================================
# EXAMPLE 3: Food & Culture Focused
# ============================================================================
# Short 2-day food tour of Georgetown, Penang
#
# Command:
#   python evaluation.py \
#     --query "Plan a 2-day food and culture tour of Georgetown Penang for 2 people, including hawker centers and restaurants"
#
# Expected results:
#   - >40% of POIs categorized as "Food"
#   - Tight geographic clustering (Georgetown historic district)
#   - Minimal daily distances (<10 km)
#


# ============================================================================
# EXAMPLE 4: Extended History & Heritage Tour
# ============================================================================
# 7-day comprehensive history trip across multiple regions
#
# Command:
#   python evaluation.py \
#     --destination "Selangor" \
#     --days 7 \
#     --travelers 4 \
#     --interests "history,culture,religion,art"
#
# Expected results:
#   - Balanced distribution across heritage categories
#   - Geographically spread itinerary (Kuala Lumpur, Selangor, surrounding areas)
#   - Good mix of museums, temples, historical sites
#


# ============================================================================
# EXAMPLE 5: Quick POI Suggestions (Skip Planning)
# ============================================================================
# Just get recommendations without itinerary planning
#
# Command:
#   python evaluation.py \
#     --query "What are the best cultural attractions in Melaka?" \
#     --sample
#
# Note: Using --sample for fast execution without agent
#
# Expected results:
#   - Only Input Parser + Recommender execute
#   - Planner is skipped (40% latency reduction)
#   - Top-5 POI list with descriptions
#


# ============================================================================
# EXAMPLE 6: Compare Different Destinations
# ============================================================================
# Generate evaluations for multiple Malaysian states
#
# Script:
import subprocess
import os

destinations = ["Penang", "Kuala Lumpur", "Sabah", "Melaka", "Cameron Highlands"]
base_cmd = "python evaluation.py --destination '{}' --days 3"

for dest in destinations:
    cmd = base_cmd.format(dest)
    # Uncomment to run:
    # result = subprocess.run(cmd, shell=True)
    print(f"# Run evaluation for {dest}:")
    print(f"  {cmd}\n")


# ============================================================================
# EXAMPLE 7: Performance Benchmarking
# ============================================================================
# Test system performance with varying trip durations
#
# Commands:
#   python evaluation.py --days 2 --interests "food"
#   python evaluation.py --days 4 --interests "food"
#   python evaluation.py --days 7 --interests "food"
#
# Compare latency and clustering complexity
#


# ============================================================================
# EXAMPLE 8: Using Sample Data (for testing/demos)
# ============================================================================
# Generate evaluation using hardcoded sample data (no agent execution)
#
# Command:
#   python evaluation.py --sample
#
# Use cases:
#   - Quick testing of visualization generation
#   - Demo without full agent execution
#   - Baseline comparison
#


# ============================================================================
# EXAMPLE 9: Programmatic Usage
# ============================================================================
# Use evaluation framework in your own Python code
#
# Code:

from evaluation import run_ai_agent_evaluation, generate_evaluation_report, print_summary_statistics

# Run agent with custom query
query = "Plan a 3-day adventure and nature trip to Pahang for 2 people"
analysis, latency = run_ai_agent_evaluation(
    user_query=query,
    thread_id="custom-evaluation-session"
)

# Print summary
print_summary_statistics(analysis)

# Generate full report
generate_evaluation_report(analysis, output_dir="custom_results")


# ============================================================================
# EXAMPLE 10: Batch Processing with Error Handling
# ============================================================================
# Process multiple evaluations with graceful error handling
#
# Code:

from evaluation import run_ai_agent_evaluation, get_sample_penang_data, generate_evaluation_report

test_queries = [
    "3-day food trip to Penang for 2 people",
    "5-day adventure trip to Sabah for 3 people",
    "2-day cultural heritage tour of Melaka for 2 people",
]

for idx, query in enumerate(test_queries, 1):
    try:
        print(f"\n[{idx}/{len(test_queries)}] Evaluating: {query}")
        
        analysis, latency = run_ai_agent_evaluation(
            user_query=query,
            thread_id=f"batch-eval-{idx}"
        )
        
        # Generate report in numbered directories
        output_dir = f"evaluation_results_batch_{idx:02d}"
        generate_evaluation_report(analysis, output_dir=output_dir)
        
        print(f"✓ Completed in {latency:.1f}s")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        # Fall back to sample data
        print(f"  Using sample data instead...")
        analysis = get_sample_penang_data()
        generate_evaluation_report(analysis, output_dir=f"evaluation_results_sample_{idx:02d}")


# ============================================================================
# EXAMPLE 11: Comparative Analysis
# ============================================================================
# Compare evaluation results across different parameters
#
# Script:

from evaluation import run_ai_agent_evaluation, print_summary_statistics

# Test different trip durations with same destination/preferences
test_configs = [
    {"destination": "Penang", "days": 2, "interests": "food,culture"},
    {"destination": "Penang", "days": 3, "interests": "food,culture"},
    {"destination": "Penang", "days": 5, "interests": "food,culture"},
]

results = {}

for config in test_configs:
    query = f"Plan a {config['days']}-day {config['interests']} trip to {config['destination']} for 2 people"
    
    try:
        analysis, latency = run_ai_agent_evaluation(user_query=query)
        results[f"{config['days']}d"] = {
            "analysis": analysis,
            "latency": latency,
            "total_pois": analysis.total_pois_selected,
            "total_distance": analysis.total_trip_distance
        }
    except:
        print(f"Skipped {config['days']} day evaluation")

# Compare results
print("\n" + "="*70)
print("COMPARISON: Impact of Trip Duration")
print("="*70)
for duration, data in results.items():
    print(f"\n{duration} Trip:")
    print(f"  POIs: {data['total_pois']}")
    print(f"  Total Distance: {data['total_distance']:.1f} km")
    print(f"  Latency: {data['latency']:.1f}s")


# ============================================================================
# OUTPUT INTERPRETATION GUIDE
# ============================================================================

"""
After running evaluations, interpret the generated visualizations:

1. ACTIVITY DISTRIBUTION (01_activity_distribution.png)
   - HIGH PREFERENCE MATCH (>50% in stated categories)
     → Good recommendation quality
   
   - LOW PREFERENCE MATCH (<30% in stated categories)
     → Recommender needs parameter tuning
   
   - BALANCED DISTRIBUTION (no category >35%)
     → Good diversity

2. POI RANKINGS (02_poi_rankings.png)
   - Top 5 POIs should include user-specified preferences
   - Score range of 100-200 indicates high-confidence rankings
   - Scores <80 indicate lower-quality POIs

3. GEOGRAPHIC CLUSTERING (03_geographic_clustering.png)
   - Non-overlapping daily clusters = efficient routing
   - Cluster radius <8km = tight geographic coherence
   - Balanced POI counts per day = balanced workload

4. DAILY DISTANCES (04_daily_distances.png)
   - Similar daily distances = consistent pacing
   - Distances < 20km = urban destination
   - Distances 20-50km = regional destination
   - Distances > 50km = extensive coverage

5. PERFORMANCE METRICS (05_performance_metrics.png)
   - LLM dominance (>40%) = semantic extraction bottleneck
   - P95 <5s = suitable for chat interfaces
   - Linear scalability = good algorithmic efficiency

6. OPTIMIZATION QUALITY (06_optimization_comparison.png)
   - 5-15% improvement = effective nearest-neighbor
   - < 5% = limited routing benefit
   - > 20% = potential for advanced optimization

7. DATABASE PERFORMANCE (07_query_performance.png)
   - All queries <150ms = healthy database performance
   - Radius search < 100ms = good spatial index
   - Scale linear with result count = efficient queries
"""


# ============================================================================
# TIPS FOR BEST RESULTS
# ============================================================================

"""
1. NATURALISTIC QUERIES
   ✓ "3-day food trip to Penang for 2 people"
   ✗ "destination=Penang, days=3, food"

2. SPECIFIC INTERESTS
   ✓ "adventure and nature activities"
   ✗ "fun stuff"

3. REALISTIC CONSTRAINTS
   ✓ "5-day trip for family of 4"
   ✗ "cover all of Malaysia in 2 days"

4. FOLLOW-UP REFINEMENTS
   ✓ "Make it 4 days instead"
   ✓ "Add more cultural attractions"
   ✗ Rerunning with completely different query (loses context)

5. DOCUMENTATION
   - Save interesting outputs for comparison
   - Note latency measurements across different parameters
   - Track optimization quality improvements
"""
