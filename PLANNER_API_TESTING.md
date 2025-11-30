# Testing Planner Agent API

## Quick Start

### 1. Start the API Server

```bash
python test_planner_api.py
```

You should see:

```
🗺️  PLANNER AGENT TEST API
================================================================================

📍 Server: http://localhost:8001
📚 Docs: http://localhost:8001/docs

Available Endpoints:
  • POST /planner/select-centroid - Select best centroid
  • POST /planner/calculate-distance - Distance between 2 POIs
  • POST /planner/cluster-pois - Cluster by distance
  • POST /planner/generate-sequence - Optimal sequence
  • POST /planner/plan-itinerary - Complete workflow ⭐
  • GET /planner/nearby-pois/{place_id} - Find nearby POIs
```

### 2. Open Interactive Docs

Go to: **http://localhost:8001/docs**

You'll see a beautiful Swagger UI with all endpoints ready to test!

### 3. Run Automated Tests

```bash
python test_planner_api_calls.py
```

## API Endpoints

### 1. **Select Centroid** (POST /planner/select-centroid)

Select the best centroid from top priority POIs.

**Request:**

```json
{
  "priority_pois": [
    {
      "google_place_id": "ChIJ123",
      "name": "George Town",
      "priority_score": 95.5,
      "lat": 5.4164,
      "lon": 100.3327,
      "state": "Penang"
    }
  ],
  "consider_top_n": 5
}
```

**Response:**

```json
{
  "success": true,
  "centroid": {
    "google_place_id": "ChIJ123",
    "name": "George Town",
    "priority_score": 95.5,
    "reason": "Highest priority score among top 5 POIs"
  }
}
```

### 2. **Calculate Distance** (POST /planner/calculate-distance)

Calculate distance between two POIs using PostGIS.

**Request:**

```json
{
  "place_id_1": "ChIJ123",
  "place_id_2": "ChIJ456"
}
```

**Response:**

```json
{
  "success": true,
  "distance_meters": 8500.0,
  "distance_km": 8.5
}
```

### 3. **Cluster POIs** (POST /planner/cluster-pois)

Cluster POIs into nearby and far based on distance threshold.

**Request:**

```json
{
  "centroid_place_id": "ChIJ123",
  "poi_list": [
    { "google_place_id": "ChIJ456", "name": "POI 1" },
    { "google_place_id": "ChIJ789", "name": "POI 2" }
  ],
  "max_distance_meters": 30000
}
```

**Response:**

```json
{
  "success": true,
  "clusters": {
    "nearby": [...],
    "far": [...],
    "nearby_count": 15,
    "far_count": 5
  }
}
```

### 4. **Generate Sequence** (POST /planner/generate-sequence)

Generate optimal visit sequence using nearest neighbor.

**Request:**

```json
{
  "start_place_id": "ChIJ123",
  "poi_place_ids": ["ChIJ456", "ChIJ789", "ChIJ012"]
}
```

**Response:**

```json
{
  "success": true,
  "sequence": [
    {
      "google_place_id": "ChIJ123",
      "google_matched_name": "George Town",
      "sequence_no": 1
    },
    {
      "google_place_id": "ChIJ456",
      "google_matched_name": "Penang Hill",
      "sequence_no": 2,
      "distance_from_previous_meters": 8500.0
    }
  ],
  "summary": {
    "total_pois": 4,
    "total_distance_meters": 25000,
    "total_distance_km": 25.0
  }
}
```

### 5. **Plan Itinerary** ⭐ (POST /planner/plan-itinerary)

**Complete workflow** - Does everything in one call:

- Selects centroid from top 5
- Calculates distances to top 50 POIs
- Clusters POIs (nearby vs far)
- Generates optimal sequence

**Request:**

```json
{
  "priority_pois": [
    {
      "google_place_id": "ChIJ123",
      "name": "George Town",
      "priority_score": 95.5,
      "lat": 5.4164,
      "lon": 100.3327
    }
    // ... more POIs
  ],
  "max_pois_per_day": 6,
  "max_distance_meters": 30000
}
```

**Response:**

```json
{
  "success": true,
  "centroid": {
    "google_place_id": "ChIJ123",
    "name": "George Town",
    "priority_score": 95.5
  },
  "sequence": [
    {
      "google_place_id": "ChIJ123",
      "google_matched_name": "George Town",
      "sequence_no": 1
    },
    {
      "google_place_id": "ChIJ456",
      "google_matched_name": "Penang Hill",
      "sequence_no": 2,
      "distance_from_previous_meters": 8500.0
    }
  ],
  "clusters": {
    "nearby_count": 15,
    "far_count": 10
  },
  "summary": {
    "total_pois": 6,
    "total_distance_km": 25.5
  }
}
```

### 6. **Find Nearby POIs** (GET /planner/nearby-pois/{place_id})

Find POIs within a radius using PostGIS.

**Request:**

```
GET /planner/nearby-pois/ChIJ123?radius_meters=50000&max_results=20
```

**Response:**

```json
{
  "success": true,
  "center_place_id": "ChIJ123",
  "radius_km": 50,
  "pois": [
    {
      "id": 456,
      "name": "Nearby POI",
      "distance_meters": 5000.0,
      "google_place_id": "ChIJ456"
    }
  ],
  "count": 20
}
```

## Testing with cURL

```bash
# 1. Select Centroid
curl -X POST "http://localhost:8001/planner/select-centroid" \
  -H "Content-Type: application/json" \
  -d '{
    "priority_pois": [
      {
        "google_place_id": "ChIJ123",
        "name": "George Town",
        "priority_score": 95.5,
        "lat": 5.4164,
        "lon": 100.3327
      }
    ],
    "consider_top_n": 5
  }'

# 2. Plan Complete Itinerary
curl -X POST "http://localhost:8001/planner/plan-itinerary" \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

## Testing with Python

```python
import requests

# Plan complete itinerary
response = requests.post("http://localhost:8001/planner/plan-itinerary", json={
    "priority_pois": [
        {
            "google_place_id": "ChIJ123",
            "name": "George Town",
            "priority_score": 95.5,
            "lat": 5.4164,
            "lon": 100.3327
        }
    ],
    "max_pois_per_day": 6,
    "max_distance_meters": 30000
})

result = response.json()
print(f"Centroid: {result['centroid']['name']}")
print(f"Total POIs: {result['summary']['total_pois']}")
print(f"Total Distance: {result['summary']['total_distance_km']} km")
```

## Notes

⚠️ **Important**: Some endpoints require **real Google Place IDs** from your Supabase database to work properly:

- `calculate-distance`
- `generate-sequence`
- `nearby-pois`

The `select-centroid` and `plan-itinerary` endpoints work with any data for testing the logic.

## Next Steps

1. Test with mock data using the interactive docs
2. Update test scripts with real `google_place_id` values from your database
3. Test complete workflow with real POI data
4. Integrate with your recommender agent output

Happy testing! 🚀
