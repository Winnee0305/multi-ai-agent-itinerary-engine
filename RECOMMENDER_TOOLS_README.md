# Recommender Agent Tools

## Overview

The Recommender Agent loads POIs from Supabase and calculates priority scores based on user preferences, generating personalized trip recommendations.

## Tools

### 1. `load_pois_from_database`

Load POIs from Supabase with filters.

**Parameters:**

- `state` (Optional[str]): Filter by state name (e.g., "Penang", "Kuala Lumpur")
- `golden_only` (bool): If True, only return golden list POIs (default: True)
- `min_popularity` (int): Minimum popularity score threshold (default: 50)

**Returns:** List of POI dictionaries

**Example:**

```python
pois = load_pois_from_database.invoke({
    "state": "Penang",
    "golden_only": True,
    "min_popularity": 70
})
```

---

### 2. `calculate_priority_scores`

Calculate priority scores for POIs based on user context.

**Parameters:**

- `pois` (List[Dict]): List of POI dictionaries from database
- `user_preferences` (List[str]): User interest categories (e.g., ["Food", "Culture"])
- `number_of_travelers` (int): Number of people traveling
- `travel_days` (int): Trip duration in days
- `preferred_poi_names` (Optional[List[str]]): Specific POI names user wants to visit

**Scoring Algorithm:**

1. **Preferred POI Boost** (2x): POIs matching user's preferred names
2. **Interest Match Boost** (1.5x): POIs matching user's interest categories
3. **Group Safety Filter** (0.8x penalty): Low reviews/sitelinks for groups >2
4. **Time Pressure Boost** (1.2x): Landmarks with high sitelinks for trips <3 days

**Returns:** List of POIs with `priority_score` field (0.0 to 1.0), sorted by priority

---

### 3. `get_top_priority_pois`

Extract top N POIs from scored list.

**Parameters:**

- `scored_pois` (List[Dict]): POIs with priority_score field
- `top_n` (int): Number of top POIs to return (default: 50)

**Returns:** Simplified POI list with essential fields

---

### 4. `calculate_activity_mix`

Calculate recommended activity mix percentages.

**Parameters:**

- `top_pois` (List[Dict]): Top priority POIs
- `scored_pois` (List[Dict]): All scored POIs with full data

**Returns:** Dictionary with activity categories and percentages

**Example Output:**

```json
{
  "food": 0.4,
  "culture": 0.35,
  "shopping": 0.2,
  "nature": 0.05
}
```

---

### 5. `generate_recommendation_output`

Format final recommendation output.

**Returns:** Complete recommendation in standardized format

---

### 6. `recommend_pois_for_trip` ⭐

**Main tool** - Complete recommendation workflow.

**Parameters:**

- `destination_state` (str): Target state
- `user_preferences` (List[str]): Interest categories
- `number_of_travelers` (int): Group size
- `trip_duration_days` (int): Trip duration
- `preferred_poi_names` (Optional[List[str]]): Specific POIs
- `top_n` (int): Number of top POIs (default: 50)

**Returns:** Complete recommendation output

**Example:**

```python
result = recommend_pois_for_trip.invoke({
    "destination_state": "Penang",
    "user_preferences": ["Food", "Culture", "Art"],
    "number_of_travelers": 2,
    "trip_duration_days": 3,
    "preferred_poi_names": ["Kek Lok Si Temple"],
    "top_n": 50
})
```

**Output Format:**

```json
{
  "destination_state": "Penang",
  "trip_duration_days": 3,
  "top_priority_pois": [
    {
      "google_place_id": "ChIJ123...",
      "name": "Kek Lok Si Temple",
      "priority_score": 0.92,
      "lat": 5.4001,
      "lon": 100.2733,
      "state": "Penang"
    }
  ],
  "recommended_activity_mix": {
    "food": 0.4,
    "culture": 0.35,
    "shopping": 0.2,
    "nature": 0.05
  },
  "summary_reasoning": "Prioritized based on user preferences..."
}
```

## Interest Categories

Available user preference categories:

- **Art**: art_gallery, museum, painter, art_studio, craft
- **Culture**: museum, art_gallery, cultural_center, library, historical_landmark
- **Adventure**: amusement_park, theme_park, water_park, zoo, aquarium, park
- **Nature**: park, natural_feature, hiking_area, beach, waterfall, mountain
- **Food**: restaurant, cafe, food, bar, bakery, meal_takeaway
- **Shopping**: shopping_mall, department_store, store, market, supermarket
- **History**: historical_landmark, museum, monument, heritage, archaeological_site
- **Religion**: place_of_worship, church, mosque, temple, hindu_temple
- **Entertainment**: night_club, bar, movie_theater, casino, amusement_park
- **Relaxation**: spa, beauty_salon, park, beach, resort, tourist_attraction

## API Endpoints

### POST `/recommender/recommend`

Get complete trip recommendations (main endpoint).

**Request:**

```json
{
  "destination_state": "Penang",
  "user_preferences": ["Food", "Culture", "Art"],
  "number_of_travelers": 2,
  "trip_duration_days": 3,
  "preferred_poi_names": ["Kek Lok Si Temple", "Penang Hill"],
  "top_n": 50
}
```

### POST `/recommender/load-pois`

Load POIs from database with filters.

### GET `/recommender/states`

Get list of available states.

### GET `/recommender/interest-categories`

Get available interest categories.

## Testing

### 1. Start API Server

```bash
uvicorn main:app --reload
```

### 2. Run Tests

```bash
python test_recommender_api.py
```

### 3. Interactive Docs

Open http://localhost:8000/docs

## Integration with Planner

The recommender output is designed to feed directly into the planner agent:

```python
# 1. Get recommendations
recommendation = recommend_pois_for_trip.invoke({...})

# 2. Feed to planner
planner_result = plan_itinerary.invoke({
    "priority_pois": recommendation["top_priority_pois"],
    "max_pois_per_day": 6,
    "max_distance_meters": 30000
})
```

The `top_priority_pois` format matches exactly what the planner expects!

## Database Requirements

**Table:** `osm_pois`

**Required Fields:**

- `google_place_id` (text)
- `name` (text)
- `state` (text)
- `lat` (float)
- `lon` (float)
- `popularity_score` (int)
- `in_golden_list` (boolean)
- `google_types` (text[])
- `google_reviews` (int)
- `wikidata_sitelinks` (int)

## Example Usage

```python
from tools.recommender_tools import recommend_pois_for_trip

# Get recommendations for Penang trip
result = recommend_pois_for_trip.invoke({
    "destination_state": "Penang",
    "user_preferences": ["Food", "Culture", "Art"],
    "number_of_travelers": 2,
    "trip_duration_days": 3,
    "preferred_poi_names": ["Kek Lok Si Temple"],
    "top_n": 50
})

print(f"Found {len(result['top_priority_pois'])} POIs")
print(f"Activity mix: {result['recommended_activity_mix']}")

# Top 5 POIs
for poi in result['top_priority_pois'][:5]:
    print(f"{poi['name']}: {poi['priority_score']}")
```
