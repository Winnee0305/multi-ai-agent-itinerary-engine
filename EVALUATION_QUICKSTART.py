#!/usr/bin/env python3
"""
Quick Start Guide: Running Evaluations

This script demonstrates the most common evaluation use cases.
"""

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║         MULTI-AI AGENT ITINERARY ENGINE - EVALUATION QUICK START             ║
╚══════════════════════════════════════════════════════════════════════════════╝

📌 WHAT'S NEW:
  • evaluation.py now runs YOUR ACTUAL AI AGENTS (not hardcoded sample data)
  • Generates real trip plans and measures actual performance metrics
  • Supports flexible CLI parameters for any Malaysian destination
  • Visualizes results with 7 comprehensive charts + detailed text report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 QUICK START (Choose One):

1️⃣  DEFAULT EVALUATION (Recommended for first run)
   $ python evaluation.py
   
   ✓ Runs: "Plan a 3-day food and culture trip to Penang for 2 people"
   ✓ Executes: Input Parser → Recommender → Planner → Formatter
   ✓ Output: evaluation_results/ with 7 PNG charts + text report
   ✓ Time: ~5-10 seconds

2️⃣  FAST TEST (Using sample data, no agent execution)
   $ python evaluation.py --sample
   
   ✓ No agent execution (instant visualization generation)
   ✓ Good for testing the evaluation framework
   ✓ Time: <2 seconds

3️⃣  CUSTOM DESTINATION
   $ python evaluation.py --destination "Kuala Lumpur" --days 5
   
   ✓ Runs evaluation for your chosen destination
   ✓ Supports: Penang, Kuala Lumpur, Sabah, Melaka, Johor, etc.
   ✓ Time: ~5-10 seconds per destination

4️⃣  CUSTOM INTERESTS
   $ python evaluation.py --interests "adventure,nature,hiking"
   
   ✓ Focus on specific activity categories
   ✓ Available: food, culture, adventure, nature, history, religion, etc.

5️⃣  CUSTOM QUERY
   $ python evaluation.py --query "Plan a 2-day hiking trip to Cameron Highlands for 3 people"
   
   ✓ Fully natural language query
   ✓ Maximum flexibility

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 WHAT YOU'LL GET:

evaluation_results/
├── 01_activity_distribution.png    ← % of POIs by category
├── 02_poi_rankings.png              ← Top POIs with priority scores
├── 03_geographic_clustering.png     ← Map of daily clusters
├── 04_daily_distances.png           ← Travel distances by day
├── 05_performance_metrics.png       ← Latency breakdown & scalability
├── 06_optimization_comparison.png   ← Naive vs. optimized routing
├── 07_query_performance.png         ← Database query benchmarks
└── evaluation_report.txt            ← Detailed text report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 DOCUMENTATION:

  • EVALUATION_GUIDE.md
    → Complete user guide with all options
    → Troubleshooting and interpretation
    
  • EVALUATION_EXAMPLES.md
    → 11 practical examples with expected outputs
    → Batch processing and advanced usage
    
  • EVALUATION_REFACTORING_SUMMARY.md
    → Technical details of how it works
    → Architecture and data flow diagrams

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  REQUIREMENTS:

  Run once (if not done):
  $ pip install -r requirements.txt

  Required packages:
  • matplotlib (for visualizations)
  • seaborn (for enhanced styling)
  • numpy (for numerical computations)
  • langchain (for agent integration)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDED WORKFLOW:

Step 1: Quick Test
  $ python evaluation.py --sample
  → Verify visualizations are generated correctly

Step 2: Real Evaluation
  $ python evaluation.py
  → Run default Penang 3-day trip evaluation

Step 3: Explore Destinations
  $ python evaluation.py --destination "Sabah" --days 5
  → Test different destinations

Step 4: Compare Results
  → Check evaluation_results/ folders
  → Interpret charts and metrics
  → Review evaluation_report.txt

Step 5: Batch Evaluation (Optional)
  $ for dest in Penang KualaLumpur Melaka; do
      python evaluation.py --destination "$dest"
    done

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 COMMAND REFERENCE:

  Basic:
    python evaluation.py                    # Default: 3-day Penang trip
    python evaluation.py --help             # Show all options
    python evaluation.py --sample           # Use sample data (fast)

  Customization:
    python evaluation.py --destination X   # Change destination
    python evaluation.py --days N           # Change duration
    python evaluation.py --travelers N      # Change group size
    python evaluation.py --interests A,B,C  # Change interests
    python evaluation.py --query "..."      # Custom natural language

  Examples:
    python evaluation.py --days 5
    python evaluation.py --destination "Kuala Lumpur" --days 4
    python evaluation.py --interests "adventure,nature,hiking"
    python evaluation.py --query "2-day food tour of Georgetown"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ TROUBLESHOOTING:

  ❌ "Agent execution failed"
     ✓ Check .env file has SUPABASE_URL and SERVICE_ROLE_KEY
     ✓ Verify database connection is working
     ✓ Try with --sample to test visualization separately

  ❌ "No PNG files generated"
     ✓ Check matplotlib backend: python -m matplotlib
     ✓ Ensure evaluation_results/ directory is writable
     ✓ Check disk space in working directory

  ❌ "ModuleNotFoundError"
     ✓ Run: pip install -r requirements.txt
     ✓ Verify all dependencies installed: pip list

  ❌ "Destination not found"
     ✓ Valid Malaysian states: Penang, Kuala Lumpur, Selangor, Sabah,
       Sarawak, Johor, Melaka, Pahang, Kedah, Perak, Terengganu, Kelantan,
       Perlis, Negeri Sembilan, Labuan

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 INTERPRETING RESULTS:

  Activity Distribution (Chart 1):
    → High % in stated interests = good recommendation quality
    → Balanced distribution = diverse itinerary

  POI Rankings (Chart 2):
    → Top POIs should match your interests
    → Scores typically 100-180

  Geographic Clustering (Chart 3):
    → Tight clusters = efficient daily routing
    → No overlaps = well-separated days

  Daily Distances (Chart 4):
    → 10-20 km/day = compact urban destination
    → 20-50 km/day = regional destination
    → >50 km/day = extensive coverage

  Performance Metrics (Chart 5):
    → P95 latency <5s = good performance
    → LLM dominance normal (AI inference is slow)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TIPS FOR BEST RESULTS:

  ✓ Use natural language queries: "3-day food trip to Penang"
  ✗ Avoid structured format: "destination=Penang, days=3"

  ✓ Be specific: "adventure and nature activities"
  ✗ Vague: "fun things"

  ✓ Realistic constraints: "5-day trip for family of 4"
  ✗ Unrealistic: "see all of Malaysia in 2 days"

  ✓ Follow-up refinements: "Make it 4 days instead"
  ✗ Completely different query (loses context)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎓 FOR ACADEMIC USE:

  Reference in your thesis/documentation:
  
  "The Multi-AI Agent Itinerary Engine was evaluated using a comprehensive
   framework that generates real itineraries through the full agent pipeline,
   measuring latency, optimization quality, and recommendation alignment.
   Evaluations were conducted across multiple Malaysian destinations with
   varying trip durations and user preferences."

  Export results for figures:
  → PNG files are production-ready (300 DPI) for inclusion in papers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ READY TO START?

  Run your first evaluation now:

    python evaluation.py

  Expected output in evaluation_results/:
    ✓ 7 PNG visualization charts
    ✓ 1 detailed text report
    ✓ Console summary with key metrics

╚══════════════════════════════════════════════════════════════════════════════╝
    """)
