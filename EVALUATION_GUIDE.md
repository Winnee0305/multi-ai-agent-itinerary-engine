# Evaluation Guide: Multi-AI Agent Itinerary Engine

## Overview

The `evaluation.py` script provides comprehensive evaluation and visualization of the Multi-AI Agent Itinerary Engine. It runs your AI agents with real queries and generates detailed performance reports and visualizations.

## Installation

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Required packages:
- `matplotlib` - for visualization
- `seaborn` - for enhanced plot styling
- `numpy` - for numerical computations
- `langchain` - for AI agent integration
- All packages in `requirements.txt`

## Quick Start

### Run with Default Settings

Generate a 3-day Penang trip itinerary and evaluation:

```bash
python evaluation.py
```

This will:
1. Query the AI agent with: *"Plan a 3-day food and culture trip to Penang for 2 people"*
2. Execute the full agent pipeline (Input Parser → Recommender → Planner → Formatter)
3. Measure latency and performance metrics
4. Generate 7 visualization charts
5. Create a detailed text report

### Use Sample Data (No Agent Execution)

If you want to test the visualization without running the agent:

```bash
python evaluation.py --sample
```

## Command-Line Options

### Basic Options

```bash
python evaluation.py --help
```

### Destination

Change the destination:

```bash
python evaluation.py --destination "Kuala Lumpur"
```

Supported Malaysian states: Johor, Kedah, Kelantan, Kuala Lumpur, Labuan, Melaka, Negeri Sembilan, Pahang, Penang, Perak, Perlis, Sabah, Sarawak, Selangor, Terengganu

### Trip Duration

Set number of days:

```bash
python evaluation.py --days 5
```

### Number of Travelers

Specify group size:

```bash
python evaluation.py --travelers 4
```

### Interest Categories

Select trip interests (comma-separated):

```bash
python evaluation.py --interests "food,culture,history"
```

Available categories:
- Food
- Culture
- History
- Nature
- Adventure
- Religion
- Entertainment
- Shopping
- Art
- Relaxation

### Custom Query

Provide a fully custom natural language query:

```bash
python evaluation.py --query "Plan a weekend adventure trip to Cameron Highlands for 3 people interested in hiking"
```

## Example Commands

### Kuala Lumpur Adventure Trip

```bash
python evaluation.py \
  --destination "Kuala Lumpur" \
  --days 4 \
  --travelers 2 \
  --interests "adventure,nature"
```

### Extended Sabah Exploration

```bash
python evaluation.py \
  --destination "Sabah" \
  --days 7 \
  --travelers 3 \
  --interests "nature,adventure,culture,history"
```

### Food-Focused Georgetown Tour

```bash
python evaluation.py \
  --query "Plan a 2-day food tour of Penang's Georgetown for 2 food enthusiasts, including hawker centers, street food, and upscale restaurants"
```

## Output Files

The evaluation script generates an `evaluation_results/` directory containing:

### Visualization Charts (PNG files @ 300 DPI)

1. **01_activity_distribution.png**
   - Bar chart of POI categories vs. user preferences
   - Shows alignment between recommendations and interests

2. **02_poi_rankings.png**
   - Horizontal bar chart of all selected POIs by priority score
   - Color-coded top 5 vs. remaining POIs

3. **03_geographic_clustering.png**
   - Map visualization of POIs by day
   - Shows daily clusters and geographic boundaries (radius circles)

4. **04_daily_distances.png**
   - Daily travel distances comparison
   - Cumulative distance within each day progression

5. **05_performance_metrics.png**
   - 4-panel performance dashboard:
     - Latency breakdown (pie chart)
     - Latency distribution by component
     - Scalability analysis (POI count vs. time)
     - Request type performance comparison

6. **06_optimization_comparison.png**
   - Naive vs. optimized routing distance
   - Improvement percentages

7. **07_query_performance.png**
   - Database query execution times
   - Spatial index efficiency

### Text Report

**evaluation_report.txt**

Contains:
- Trip summary (destination, duration, travelers, preferences)
- Activity distribution percentages with ASCII bars
- Detailed daily itineraries with POI descriptions
- Trip metrics (distances, latencies, optimization quality)
- Top 5 POIs with detailed metadata
- Performance summary

## Performance Metrics Explained

### Latency Breakdown

The system measures end-to-end latency across four components:

| Component | % of Total | Notes |
|-----------|-----------|-------|
| Input Parser (LLM) | ~48% | Natural language understanding using Gemini |
| Recommender (Database + Scoring) | ~12% | POI retrieval and priority scoring |
| Planner (Clustering + Sequencing) | ~8% | K-Means clustering and nearest-neighbor optimization |
| Response Formatter | ~4% | Formatting output for user |
| Network/Orchestration | ~28% | Graph execution overhead and network latency |

**Target P95 Latency**: < 5.2 seconds (acceptable for chat interfaces)

### Route Optimization Quality

The Planner Agent uses nearest-neighbor heuristic (O(n²)) to optimize daily visit sequences:

- **Approximation Ratio**: 8.8% above Traveling Salesman Problem (TSP) optimum
- **Why**: Greedy algorithm balances speed vs. optimality for interactive applications
- **Comparison**: Random ordering produces 15-20% longer paths

### Database Performance

PostGIS spatial queries on 8,000+ POIs:

- **State filtering**: ~45 ms
- **Radius search (50km)**: ~78 ms
- **Rating filter**: ~62 ms
- **Full scan**: ~124 ms

All queries complete < 125 ms, enabling sub-second recommendation times.

## Integration with Your System

To run evaluations programmatically:

```python
from evaluation import run_ai_agent_evaluation, generate_evaluation_report

# Run agent with custom query
analysis, latency = run_ai_agent_evaluation(
    user_query="Plan a 3-day trip to Penang for 2 people",
    thread_id="my-evaluation"
)

# Generate report
generate_evaluation_report(analysis, output_dir="my_results")

# Print summary
print_summary_statistics(analysis)
```

## Troubleshooting

### Agent Connection Error

**Error**: `Error running AI Agent: ...`

**Solution**: 
- Ensure supervisor graph is properly initialized
- Check database connection in `.env`
- Verify `agents/supervisor_graph.py` exists and is properly configured

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named '...'`

**Solution**:
```bash
pip install -r requirements.txt
```

### No Visualizations Generated

**Error**: Only text report generated, no PNG files

**Solution**:
- Ensure `matplotlib` backend is properly configured
- Check disk space in working directory
- Verify `evaluation_results/` directory is writable

### Database Query Timeout

**Error**: Spatial queries taking > 1 second

**Solution**:
- Check PostGIS indexes: `SELECT indexname FROM pg_indexes WHERE tablename='osm_pois';`
- Verify database connection speed
- Consider reducing POI dataset size for faster evaluation

## Interpreting Results

### Activity Distribution

**What it shows**: Percentage of recommended POIs in each category

**Interpretation**:
- High alignment with stated preferences = good recommendation quality
- Balanced distribution = diverse itinerary
- Any category > 30% = potential over-specialization

### Geographic Clustering

**What it shows**: Daily POI clusters and their radius

**Interpretation**:
- Smaller radius = more compact daily itinerary
- No overlapping clusters = efficient day-to-day routing
- Cluster radius should be < 10 km for urban destinations

### Optimization Quality

**What it shows**: Percentage improvement over naive random ordering

**Interpretation**:
- 5-15% improvement = good nearest-neighbor performance
- < 5% = POIs already naturally arranged
- > 20% = potential for more sophisticated algorithms (TSP solver)

## Advanced Usage

### Batch Evaluation

Compare multiple destinations:

```bash
#!/bin/bash
for destination in "Penang" "Kuala Lumpur" "Selangor" "Sabah"
do
    python evaluation.py --destination "$destination" --days 3
done
```

### Parameter Sweep

Evaluate performance across trip durations:

```bash
for days in 2 3 4 5 7
do
    python evaluation.py --days $days --output "results_${days}d"
done
```

### Custom Analysis

Write custom Python scripts using evaluation classes:

```python
from evaluation import TripdayAnalysis, DailyItinerary, POI

# Load your own trip data
analysis = TripdayAnalysis(...)

# Use analysis object with visualization functions
visualize_geographic_clustering(analysis)
```

## Citation

If using this evaluation framework in academic work, reference Section 5 of the system architecture document:

> "The Multi-AI Agent Itinerary Engine was evaluated using a comprehensive framework generating real itineraries for Malaysia destinations, with latency profiling (Section 5.7), optimization quality metrics (Section 5.5), and comparative analysis (Section 5.6)."

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Ensure AI agent system is properly configured
4. Review error messages in console output

---

**Last Updated**: December 18, 2025
