# Planner Agent Tools - Documentation

## Overview

The Planner Agent uses **PostGIS spatial queries** to calculate distances and generate optimal itinerary sequences. The tools work together to:

1. **Select a centroid** from top priority POIs
2. **Calculate distances** using PostGIS
3. **Cluster POIs** based on proximity
4. **Generate optimal sequences** using nearest neighbor algorithm

## Tools Available

### 1. `get_poi_by_place_id(google_place_id)`

Get full POI details from Supabase.

**Input:**

- `google_place_id`: Google Place ID

**Output:**

```python
{
    "id": 123,
    "name": "George Town",
    "lat": 5.4164,
    "lon": 100.3327,
    "google_place_id": "ChIJ...",
    "state": "Penang",
    ...
}
```

### 2. `calculate_distance_between_pois(place_id_1, place_id_2)`

Calculate distance in meters between two POIs using PostGIS.

**Input:**

- `place_id_1`: First POI's Google Place ID
- `place_id_2`: Second POI's Google Place ID

**Output:**

```python
12500.45  # Distance in meters
```

### 3. `get_pois_near_centroid(centroid_place_id, radius_meters, max_results)`

Find POIs within a radius of the centroid using PostGIS spatial query.

**Input:**

- `centroid_place_id`: Centroid's Google Place ID
- `radius_meters`: Search radius (default: 50000 = 50km)
- `max_results`: Max POIs to return (default: 50)

**Output:**

```python
[
    {
        "id": 123,
        "name": "Nearby POI",
        "distance_meters": 5000.0,
        "google_place_id": "ChIJ...",
        ...
    }
]
```

### 4. `calculate_distances_from_centroid(centroid_place_id, poi_place_ids)`

Calculate distances from centroid to multiple POIs.

**Input:**

- `centroid_place_id`: Centroid's Google Place ID
- `poi_place_ids`: List of Google Place IDs

**Output:**

```python
[
    {
        "google_place_id": "ChIJ...",
        "name": "POI Name",
        "distance_meters": 3500.0
    }
]
```

### 5. `select_best_centroid(top_priority_pois, consider_top_n)`

Select the best centroid from top N priority POIs.

**Input:**

- `top_priority_pois`: List of POIs with `priority_score`
- `consider_top_n`: Consider top N POIs (default: 5)

**Output:**

```python
{
    "google_place_id": "ChIJ...",
    "name": "George Town",
    "priority_score": 95,
    "lat": 5.4164,
    "lon": 100.3327,
    "reason": "Highest priority score among top 5 POIs"
}
```

### 6. `cluster_pois_by_distance(centroid_place_id, poi_list, max_distance_meters)`

Cluster POIs into "nearby" and "far" based on distance from centroid.

**Input:**

- `centroid_place_id`: Centroid's Google Place ID
- `poi_list`: List of POIs to cluster
- `max_distance_meters`: Distance threshold (default: 30000 = 30km)

**Output:**

```python
{
    "nearby": [
        {"google_place_id": "...", "name": "Close POI", "distance_meters": 5000}
    ],
    "far": [
        {"google_place_id": "...", "name": "Far POI", "distance_meters": 45000}
    ],
    "nearby_count": 15,
    "far_count": 10
}
```

### 7. `generate_optimal_sequence(poi_place_ids, start_place_id)`

Generate optimal visit sequence using **nearest neighbor algorithm**.

**Input:**

- `poi_place_ids`: List of Google Place IDs to visit
- `start_place_id`: Starting POI (centroid)

**Output:**

```python
[
    {
        "google_place_id": "ChIJ...",
        "google_matched_name": "George Town",
        "sequence_no": 1
    },
    {
        "google_place_id": "ChIJ...",
        "google_matched_name": "Penang Hill",
        "sequence_no": 2,
        "distance_from_previous_meters": 8500.0
    }
]
```

## Complete Workflow Example

```python
from agents.tools import (
    select_best_centroid,
    calculate_distances_from_centroid,
    cluster_pois_by_distance,
    generate_optimal_sequence
)

# Step 1: Get priority POIs from Recommender Agent
priority_pois = [...]  # From recommender agent

# Step 2: Select centroid from top 5
centroid = select_best_centroid.invoke({
    "top_priority_pois": priority_pois,
    "consider_top_n": 5
})

# Step 3: Calculate distances from centroid to top 50 POIs
top_50_place_ids = [poi["google_place_id"] for poi in priority_pois[:50]]
distances = calculate_distances_from_centroid.invoke({
    "centroid_place_id": centroid["google_place_id"],
    "poi_place_ids": top_50_place_ids
})

# Step 4: Cluster POIs (nearby vs far)
clusters = cluster_pois_by_distance.invoke({
    "centroid_place_id": centroid["google_place_id"],
    "poi_list": priority_pois[:50],
    "max_distance_meters": 30000  # 30km
})

# Step 5: Select nearby POIs to visit
nearby_place_ids = [poi["google_place_id"] for poi in clusters["nearby"][:5]]

# Step 6: Generate optimal sequence
sequence = generate_optimal_sequence.invoke({
    "poi_place_ids": nearby_place_ids,
    "start_place_id": centroid["google_place_id"]
})

# Result: Sequenced itinerary
for item in sequence:
    print(f"{item['sequence_no']}. {item['google_matched_name']}")
```

## PostGIS Requirements

The tools use these PostGIS RPC functions (must be deployed to Supabase):

1. **`calculate_distance(lat1, lon1, lat2, lon2)`**

   - Calculates distance between two points in meters

2. **`get_nearby_pois(center_lat, center_lon, radius_m, ...)`**

   - Finds POIs within radius using spatial index

3. **`get_pois_with_distances(poi_ids, center_lat, center_lon)`**
   - Calculates distances from center to multiple POIs

See `database/rpc_functions.sql` for the SQL definitions.

## Setup Instructions

### 1. Deploy PostGIS Functions

```sql
-- Run in Supabase SQL Editor
-- Copy from database/rpc_functions.sql
```

### 2. Configure Environment

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SERVICE_ROLE_KEY=your_service_role_key
```

### 3. Test the Tools

```bash
python test_planner_tools.py
```

### 4. Run Example Workflow

```bash
python example_planner_usage.py
```

## Algorithm Details

### Centroid Selection

- **Strategy**: Select POI with highest priority score from top 5
- **Rationale**: Highest priority = most relevant to user preferences

### Clustering

- **Method**: Distance-based clustering from centroid
- **Threshold**: 30km (configurable)
- **Purpose**: Separate feasible POIs from outliers

### Sequence Optimization

- **Algorithm**: Greedy nearest neighbor
- **Starting point**: Centroid
- **Next POI**: Closest unvisited POI from current position
- **Complexity**: O(n²) where n = number of POIs

### Distance Calculations

- **Method**: PostGIS `ST_Distance` with geography type
- **Accuracy**: Meters on Earth's surface (WGS84)
- **Performance**: Uses spatial index (GIST) for fast queries

## Output Format

All tools return standard Python dictionaries that can be:

- Serialized to JSON
- Passed between agents
- Stored in database
- Returned via API

**Example Itinerary Output:**

```json
{
  "centroid": {
    "google_place_id": "ChIJ...",
    "google_matched_name": "George Town",
    "sequence_no": 1
  },
  "sequence": [
    {
      "google_place_id": "ChIJ...",
      "google_matched_name": "George Town",
      "sequence_no": 1
    },
    {
      "google_place_id": "ChIJ...",
      "google_matched_name": "Penang Hill",
      "sequence_no": 2,
      "distance_from_previous_meters": 8500.0
    }
  ],
  "total_distance_km": 45.2
}
```

## Integration with Other Agents

### From Recommender Agent

Receives: List of POIs with `priority_score`, `google_place_id`, `name`

### To Optimizer Agent

Sends: Sequenced itinerary with distances

## Performance Considerations

- **PostGIS queries**: Fast with spatial index (sub-second)
- **Nearest neighbor**: O(n²) - keep POI count reasonable (<100)
- **Batch calculations**: Use `calculate_distances_from_centroid` instead of individual calls

## Error Handling

Tools return:

- Valid data on success
- `{"error": "message"}` on failure
- Empty lists `[]` when no results found
- `-1.0` for invalid distance calculations

## Next Steps

1. Test with your actual Supabase data
2. Adjust clustering threshold (30km) based on your regions
3. Implement multi-day splitting logic
4. Add time constraints (opening hours, travel time)
5. Consider traffic/public transport in distance calculations

## Questions?

See:

- `test_planner_tools.py` - Individual tool tests
- `example_planner_usage.py` - Complete workflow example
- `database/rpc_functions.sql` - PostGIS function definitions
