# Behavioral Scoring Quick Reference

## Scoring Weights

| Signal Type   | Effect          | Strength | Notes                            |
| ------------- | --------------- | -------- | -------------------------------- |
| **Viewed**    | +3 points       | Weak     | User just looked, low intent     |
| **Collected** | +20 points      | Medium   | User bookmarked, moderate intent |
| **In Trip**   | ×1.4 multiplier | Strong   | User actively used, high intent  |

## Score Calculation Formula

```
Base Score = popularity_score + preference_match + group_adjustment + time_adjustment

Layer 4 (Behavioral):
  behavior_boost = 0
  behavior_multiplier = 1.0

  if viewed: behavior_boost += 3
  if collected: behavior_boost += 20
  if in_trip: behavior_multiplier = 1.4

Final Score = (Base Score + behavior_boost) × behavior_multiplier
```

## Examples

### Example 1: No Behavior

```
Base Score: 100
Viewed: No
Collected: No
In Trip: No
---
behavior_boost = 0
behavior_multiplier = 1.0
Final Score = (100 + 0) × 1.0 = 100
```

### Example 2: Viewed Only

```
Base Score: 100
Viewed: Yes (+3)
Collected: No
In Trip: No
---
behavior_boost = 3
behavior_multiplier = 1.0
Final Score = (100 + 3) × 1.0 = 103
```

### Example 3: Collected Only

```
Base Score: 100
Viewed: No
Collected: Yes (+20)
In Trip: No
---
behavior_boost = 20
behavior_multiplier = 1.0
Final Score = (100 + 20) × 1.0 = 120
```

### Example 4: In Trip Only

```
Base Score: 100
Viewed: No
Collected: No
In Trip: Yes (×1.4)
---
behavior_boost = 0
behavior_multiplier = 1.4
Final Score = (100 + 0) × 1.4 = 140
```

### Example 5: All Signals

```
Base Score: 100
Viewed: Yes (+3)
Collected: Yes (+20)
In Trip: Yes (×1.4)
---
behavior_boost = 3 + 20 = 23
behavior_multiplier = 1.4
Final Score = (100 + 23) × 1.4 = 172.2
```

## Data Structure

### Input (from Flutter)

```json
{
  "user_behavior": {
    "viewed_place_ids": ["ChIJabc123", "ChIJdef456"],
    "collected_place_ids": ["ChIJghi789"],
    "trip_place_ids": ["ChIJjkl012", "ChIJmno345"]
  }
}
```

### Output (in POI)

```json
{
  "google_place_id": "ChIJabc123",
  "name": "Kek Lok Si Temple",
  "priority_score": 172.2,
  "behavior_boost": 23,
  "behavior_multiplier": 1.4,
  "lat": 5.4,
  "lon": 100.27,
  "state": "Penang"
}
```

### Output (behavior_stats)

```json
{
  "behavior_stats": {
    "viewed_count": 2,
    "collected_count": 1,
    "trip_count": 2
  }
}
```

## Signal Strength Rationale

### Why Viewed = 3?

- **Weak Signal**: User might just be browsing
- Low commitment action (single tap)
- Many false positives (accidental views)
- Small boost to avoid noise

### Why Collected = 20?

- **Medium Signal**: User actively bookmarked
- Requires intentional action (tap + confirm)
- Shows planning intent
- Significant boost for curation signal

### Why Trip = 1.4?

- **Strong Signal**: User built itinerary with POI
- Highest commitment level
- Proven preference (used in real trip)
- Multiplicative to amplify already-high scores

### Why Multiply Instead of Add for Trips?

```
Scenario: POI with low base score but in trip
  Option A (additive): 30 + 50 = 80
  Option B (multiplicative): 30 × 1.4 = 42

Scenario: POI with high base score and in trip
  Option A (additive): 150 + 50 = 200
  Option B (multiplicative): 150 × 1.4 = 210
```

Multiplicative approach:

- ✅ Amplifies already-good POIs (wanted behavior)
- ✅ Doesn't over-boost poor POIs
- ✅ Scales with base score quality
- ✅ Reflects "confidence boost" rather than fixed value

## Flutter Implementation Checklist

- [ ] Create `UserBehaviorService` class
- [ ] Track POI views in `onTap` handlers
- [ ] Track collections in bookmark button handler
- [ ] Extract place_ids from saved trips
- [ ] Build behavior payload method
- [ ] Pass behavior to recommendation API
- [ ] Display behavior_boost in POI cards (optional)
- [ ] Add behavior_stats to debug view (optional)

## API Integration Checklist

- [x] Add `user_behavior` parameter to `calculate_priority_scores()`
- [x] Extract behavioral signals (viewed/collected/trip sets)
- [x] Implement Layer 4 scoring logic
- [x] Add `behavior_boost` and `behavior_multiplier` to POI output
- [x] Add `behavior_stats` to final response
- [x] Update `UserBehavior` Pydantic model
- [x] Update `RecommendationRequest` to accept behavior
- [x] Convert Pydantic model to dict in endpoint handler
- [x] Pass behavior through orchestrator
- [ ] Test with sample behavioral data
- [ ] Document in API docs (Swagger)

## Performance Considerations

### Time Complexity

- Behavioral signal extraction: O(n) where n = total signals
- Lookup per POI: O(1) with set membership check
- Overall: O(m) where m = number of POIs to score

### Memory Usage

- Viewed set: ~8 bytes × viewed_count
- Collected set: ~8 bytes × collected_count
- Trip set: ~8 bytes × trip_count
- Example: 100 + 50 + 30 signals = ~1.44 KB

### Scalability

- **Current**: Works well for:

  - Up to 200 behavioral signals per user
  - Up to 1000 POIs per recommendation request
  - ~5ms additional latency

- **If Needed**: Optimization strategies:
  - Limit behavioral signals to recent 6 months
  - Cap at 500 most recent signals
  - Pre-filter POIs before scoring

## Debugging Tips

### Check if Behavior is Passed

```python
# In calculate_priority_scores()
print(f"User behavior: {user_behavior}")
print(f"Viewed IDs: {len(viewed_ids)} items")
```

### Verify Scoring Logic

```python
# After Layer 4
print(f"POI: {poi['name']}")
print(f"  Base: {base_score}")
print(f"  Boost: +{behavior_boost}")
print(f"  Multiplier: ×{behavior_multiplier}")
print(f"  Final: {current_score}")
```

### Check Output Format

```python
# In endpoint handler
print(f"Behavior stats: {result.get('behavior_stats')}")
for poi in result['top_priority_pois'][:3]:
    print(f"{poi['name']}: boost={poi['behavior_boost']}")
```

## Common Issues

### Issue: Boost not applied

**Cause**: POI place_id doesn't match behavior place_ids
**Fix**: Verify place_id format consistency (with/without "ChIJ" prefix)

### Issue: All boosts are 0

**Cause**: `user_behavior` is None or empty
**Fix**: Check Flutter is sending data, API is parsing correctly

### Issue: Boost too aggressive

**Cause**: Weights might be too high for your use case
**Fix**: Tune constants in `calculate_priority_scores()`

- Reduce viewed from 3 → 1
- Reduce collected from 20 → 10
- Reduce trip from 1.4 → 1.2

### Issue: Performance degradation

**Cause**: Too many behavioral signals
**Fix**: Limit to most recent N signals in Flutter before sending
