# Behavioral Layer Implementation - Summary

## Overview

Successfully implemented a behavioral scoring system that personalizes POI recommendations based on user interaction history from the Flutter mobile app.

## Architecture

### Data Flow

```
Flutter App → FastAPI Endpoint → Orchestrator → Scoring Function → Scored POIs
```

1. **Flutter App** collects user behavior:

   - `viewed_place_ids`: POIs the user has viewed
   - `collected_place_ids`: POIs the user has bookmarked/saved
   - `trip_place_ids`: POIs that appear in user's saved trips

2. **API Endpoint** (`routers/recommender.py`):

   - Receives `UserBehavior` Pydantic model
   - Converts to dict format
   - Passes to orchestrator function

3. **Orchestrator** (`recommend_pois_for_trip_logic`):

   - Receives `user_behavior` dict
   - Passes to scoring function
   - Adds `behavior_stats` to output for transparency

4. **Scoring Function** (`calculate_priority_scores`):
   - Extracts behavioral signals (viewed/collected/trip sets)
   - Applies Layer 4 behavioral boosts
   - Includes boost values in POI output

## Scoring Layers

### Layer 0: Preferred POI Match

- **Trigger**: POI name matches user's preferred_poi_names list
- **Effect**: `current_score *= 2.0`

### Layer 1: Interest Category Match

- **Trigger**: POI's google_types match user's interest preferences
- **Effect**: `current_score *= 1.5`

### Layer 2: Group Safety

- **Trigger**: Number of travelers > 2
- **Effect**: `current_score *= 0.8` (reduce priority for crowded group trips)

### Layer 3: Time Pressure Landmarks

- **Trigger**: Trip duration < 3 days AND POI is landmark
- **Effect**: `current_score *= 1.2`

### Layer 4: Behavioral Boost (NEW)

- **Viewed POI**: `behavior_boost += 3` (weak signal - user just looked)
- **Collected POI**: `behavior_boost += 20` (medium signal - user bookmarked)
- **In Trip POI**: `behavior_multiplier = 1.4` (strong signal - user actively used)

**Application Order**:

```python
current_score += behavior_boost  # Add points first
current_score *= behavior_multiplier  # Then multiply
```

**Example**: POI with all 3 signals

- Base score: 100
- After boost: 100 + 3 + 20 = 123
- After multiplier: 123 × 1.4 = 172.2

## Implementation Details

### File Changes

#### 1. `tools/recommender_tools.py`

**Function: `calculate_priority_scores()`**

```python
def calculate_priority_scores(
    pois: List[Dict[str, Any]],
    user_preferences: List[str],
    number_of_travelers: int,
    travel_days: int,
    preferred_poi_names: Optional[List[str]] = None,
    user_behavior: Optional[Dict[str, List[str]]] = None  # NEW PARAMETER
) -> List[Dict[str, Any]]:
```

**Behavioral Signal Extraction**:

```python
# Extract sets for O(1) lookup
viewed_ids = set(user_behavior.get("viewed_place_ids", [])) if user_behavior else set()
collected_ids = set(user_behavior.get("collected_place_ids", [])) if user_behavior else set()
trip_ids = set(user_behavior.get("trip_place_ids", [])) if user_behavior else set()
```

**Layer 4 Scoring Logic**:

```python
# Initialize
behavior_boost = 0
behavior_multiplier = 1.0

# Apply boosts
if user_behavior:
    if poi_place_id in viewed_ids:
        behavior_boost += 3
    if poi_place_id in collected_ids:
        behavior_boost += 20
    if poi_place_id in trip_ids:
        behavior_multiplier = 1.4

# Apply to score
current_score += behavior_boost
current_score *= behavior_multiplier
```

**POI Output Enhancement**:

```python
scored_pois.append({
    **poi,
    "priority_score": round(priority_score, 2),
    "behavior_boost": behavior_boost if user_behavior else 0,
    "behavior_multiplier": behavior_multiplier if user_behavior else 1.0
})
```

**Function: `get_top_priority_pois()`**

- Added `behavior_boost` and `behavior_multiplier` to output dict

**Function: `recommend_pois_for_trip_logic()`**

- Added `user_behavior` parameter
- Passes to `calculate_priority_scores()`
- Adds `behavior_stats` to output:

```python
if user_behavior:
    output["behavior_stats"] = {
        "viewed_count": len(user_behavior.get("viewed_place_ids", [])),
        "collected_count": len(user_behavior.get("collected_place_ids", [])),
        "trip_count": len(user_behavior.get("trip_place_ids", []))
    }
```

#### 2. `routers/recommender.py`

**New Pydantic Model**:

```python
class UserBehavior(BaseModel):
    """User behavioral signals from Flutter app"""
    viewed_place_ids: List[str] = Field(default=[], description="POIs user has viewed")
    collected_place_ids: List[str] = Field(default=[], description="POIs user has bookmarked/collected")
    trip_place_ids: List[str] = Field(default=[], description="POIs in user's saved trips")
```

**Updated Request Model**:

```python
class RecommendationRequest(BaseModel):
    # ... existing fields ...
    user_behavior: Optional[UserBehavior] = Field(default=None, description="User behavioral signals")
```

**Endpoint Handler**:

```python
@router.post("/recommend")
async def get_recommendations(request: RecommendationRequest):
    # Convert Pydantic model to dict
    user_behavior_dict = None
    if request.user_behavior:
        user_behavior_dict = {
            "viewed_place_ids": request.user_behavior.viewed_place_ids,
            "collected_place_ids": request.user_behavior.collected_place_ids,
            "trip_place_ids": request.user_behavior.trip_place_ids
        }

    # Pass to orchestrator
    result = recommend_pois_for_trip_logic(
        # ... other params ...
        user_behavior=user_behavior_dict,
        top_n=request.top_n
    )
```

## API Usage Example

### Request Format

```json
POST /recommender/recommend
{
  "destination_state": "Penang",
  "user_preferences": ["Food", "Culture", "Art"],
  "number_of_travelers": 2,
  "trip_duration_days": 3,
  "preferred_poi_names": ["Kek Lok Si Temple"],
  "user_behavior": {
    "viewed_place_ids": ["ChIJabc123", "ChIJdef456"],
    "collected_place_ids": ["ChIJghi789"],
    "trip_place_ids": ["ChIJjkl012"]
  },
  "top_n": 50
}
```

### Response Format

```json
{
  "success": true,
  "destination_state": "Penang",
  "trip_duration_days": 3,
  "top_priority_pois": [
    {
      "google_place_id": "ChIJabc123",
      "name": "Kek Lok Si Temple",
      "priority_score": 245.8,
      "lat": 5.4,
      "lon": 100.27,
      "state": "Penang",
      "behavior_boost": 20,
      "behavior_multiplier": 1.0
    }
  ],
  "recommended_activity_mix": {
    "culture": 0.35,
    "food": 0.4,
    "nature": 0.25
  },
  "behavior_stats": {
    "viewed_count": 2,
    "collected_count": 1,
    "trip_count": 1
  }
}
```

## Flutter Integration Pattern

### Step 1: Collect User Behavior

```dart
class UserBehaviorService {
  // Track when user views a POI
  void trackView(String placeId) {
    // Save to local storage (SharedPreferences, Hive, SQLite)
    viewedPlaceIds.add(placeId);
  }

  // Track when user bookmarks a POI
  void trackCollection(String placeId) {
    collectedPlaceIds.add(placeId);
  }

  // Extract POIs from saved trips
  List<String> getTripPlaceIds() {
    return savedTrips
        .expand((trip) => trip.pois)
        .map((poi) => poi.placeId)
        .toSet()
        .toList();
  }

  // Build behavior payload for API
  Map<String, dynamic> getBehaviorPayload() {
    return {
      "viewed_place_ids": viewedPlaceIds.toList(),
      "collected_place_ids": collectedPlaceIds.toList(),
      "trip_place_ids": getTripPlaceIds()
    };
  }
}
```

### Step 2: Call Recommendation API

```dart
Future<RecommendationResponse> getRecommendations({
  required String destinationState,
  required List<String> userPreferences,
  required int numberOfTravelers,
  required int tripDurationDays,
  List<String>? preferredPoiNames,
  int topN = 50,
}) async {
  final userBehavior = userBehaviorService.getBehaviorPayload();

  final response = await http.post(
    Uri.parse('$apiUrl/recommender/recommend'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'destination_state': destinationState,
      'user_preferences': userPreferences,
      'number_of_travelers': numberOfTravelers,
      'trip_duration_days': tripDurationDays,
      'preferred_poi_names': preferredPoiNames,
      'user_behavior': userBehavior,  // Include behavioral signals
      'top_n': topN,
    }),
  );

  return RecommendationResponse.fromJson(jsonDecode(response.body));
}
```

## Key Benefits

### 1. Personalization Without Complexity

- No backend database for user behavior
- Flutter handles all data storage locally
- API stateless - just processes provided signals

### 2. Privacy-Friendly

- User data stays on device
- Only sent when making recommendation request
- No persistent tracking on server

### 3. Transparent Scoring

- Each POI shows `behavior_boost` and `behavior_multiplier`
- Output includes `behavior_stats` summary
- Easy to debug and explain to users

### 4. Performance

- Set-based lookups: O(1) for behavior checks
- No database queries for behavior data
- Minimal impact on scoring performance

### 5. Flexible Weights

- Easy to adjust boost values:
  - Viewed: 3 points (can increase if valuable signal)
  - Collected: 20 points (strong intent signal)
  - Trip: 1.4× multiplier (proven preference)

## Testing

### Standalone Logic Test

Run `test_behavioral_logic.py` to verify:

- No behavior: No boost applied
- Viewed: +3 points
- Collected: +20 points
- In trip: ×1.4 multiplier
- Combined: +23 points, then ×1.4
- Different IDs: No boost

### Integration Test

Run actual API request with sample behavior data:

```bash
curl -X POST http://localhost:8000/recommender/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "destination_state": "Penang",
    "user_preferences": ["Food"],
    "number_of_travelers": 2,
    "trip_duration_days": 3,
    "user_behavior": {
      "viewed_place_ids": ["ChIJabc123"],
      "collected_place_ids": ["ChIJdef456"],
      "trip_place_ids": ["ChIJghi789"]
    }
  }'
```

## Future Enhancements

### Short Term

1. **Time Decay**: Reduce boost for old interactions

   ```python
   days_ago = (now - view_date).days
   time_weight = max(0, 1 - (days_ago / 30))  # Decay over 30 days
   behavior_boost *= time_weight
   ```

2. **Frequency Weighting**: Multiple views = stronger signal
   ```python
   view_count = viewed_counts.get(poi_place_id, 0)
   behavior_boost += min(view_count * 2, 10)  # Cap at 10 points
   ```

### Long Term

1. **Category Affinity**: Learn preferred POI types from history
2. **Collaborative Filtering**: "Users who liked X also liked Y"
3. **Contextual Boost**: Time of day, season, weather-aware recommendations

## Notes

- **Not Collaborative Filtering**: This is content-based + behavioral filtering

  - Collaborative: "Users similar to you liked X"
  - This approach: "You interacted with X, so boost X"

- **Scalability**: Current approach works well for:

  - Up to ~1000 POIs per request
  - Up to ~500 behavioral signals per user
  - Single-user context (no cross-user data needed)

- **Maintenance**: Update boost weights based on:
  - User feedback (A/B testing)
  - Conversion rates (viewed → collected → trip)
  - Feature usage analytics from Flutter
