# Supervisor Agent - Multi-Agent Trip Planning System

## Architecture Overview

This system implements the **LangChain Supervisor Pattern** for coordinating specialized travel planning agents.

```
┌─────────────────────────────────────────────────────────┐
│                   SUPERVISOR AGENT                       │
│  (Coordinates workflow and combines results)             │
└─────────────────────────────────────────────────────────┘
                 │                    │
                 ▼                    ▼
    ┌────────────────────┐  ┌────────────────────┐
    │ RECOMMENDER AGENT  │  │  PLANNER AGENT     │
    │ (POI Selection)    │  │  (Route Planning)  │
    └────────────────────┘  └────────────────────┘
         │                         │
         ▼                         ▼
    [6 Tools]                 [8 Tools]
    - load_pois               - select_centroid
    - calculate_scores        - cluster_pois
    - get_top_pois           - generate_sequence
    - activity_mix           - calculate_distances
    - generate_output        - etc.
    - recommend_trip
```

## Why Supervisor Pattern?

### Benefits

1. **Separation of Concerns**: Each agent focuses on one domain
2. **Easier Debugging**: Issues isolated to specific agents
3. **Better Prompts**: Domain-specific instructions
4. **Scalability**: Easy to add new specialist agents
5. **Flexibility**: Can call agents individually or together

### Alternative: Single Mega-Agent

A single agent with all 14 tools would need to:

- Understand POI scoring AND route optimization
- Manage complex tool selection across domains
- Handle longer, more complex prompts
- Be harder to debug and improve

## Agents

### 1. Supervisor Agent

**Role**: Orchestrator and workflow coordinator

**Tools** (Wrapped Sub-Agents):

- `get_poi_recommendations` → Invokes Recommender Agent
- `plan_itinerary` → Invokes Planner Agent

**Responsibilities**:

- Parse user requests
- Decide which agents to call and in what order
- Combine outputs from sub-agents
- Present final results to user

**Example Flow**:

```
User: "Plan a 3-day trip to Penang for 2 people who love food"

Supervisor:
1. Calls get_poi_recommendations(...)
2. Gets 50 POIs with priority scores
3. Calls plan_itinerary(...)
4. Gets optimized 3-day route
5. Combines and presents results
```

---

### 2. Recommender Agent

**Role**: POI recommendation specialist

**Tools** (6 tools):

1. `load_pois_from_database` - Query Supabase
2. `calculate_priority_scores` - Apply user context
3. `get_top_priority_pois` - Extract top N
4. `calculate_activity_mix` - Analyze categories
5. `generate_recommendation_output` - Format results
6. `recommend_pois_for_trip` ⭐ - Complete workflow

**Scoring Algorithm**:

- Layer 0: Preferred POI Boost (2x)
- Layer 1: Interest Match Boost (1.5x)
- Layer 2: Group Safety Filter (0.8x penalty)
- Layer 3: Time Pressure Boost (1.2x)

**Output Format**:

```json
{
  "destination_state": "Penang",
  "trip_duration_days": 3,
  "top_priority_pois": [
    {
      "google_place_id": "ChIJ...",
      "name": "Kek Lok Si Temple",
      "priority_score": 0.92,
      "lat": 5.4001,
      "lon": 100.2733
    }
  ],
  "recommended_activity_mix": {
    "food": 0.4,
    "culture": 0.35,
    "shopping": 0.2
  },
  "summary_reasoning": "..."
}
```

---

### 3. Planner Agent

**Role**: Route optimization and itinerary planning

**Tools** (8 tools):

1. `select_best_centroid` - Choose anchor POI
2. `calculate_distances_from_centroid` - Batch distance calc
3. `cluster_pois_by_distance` - Group by proximity
4. `generate_optimal_sequence` - Nearest neighbor routing
5. `get_poi_by_place_id` - Fetch POI details
6. `get_pois_by_priority_list` - Batch fetch
7. `calculate_distance_between_pois` - Pairwise distance
8. `get_pois_near_centroid` - Spatial query

**Algorithm**:

1. Select centroid (highest priority from top 5)
2. Calculate distances to all POIs
3. Cluster: nearby (≤30km) vs far (>30km)
4. Generate sequence using nearest neighbor
5. Create day-by-day allocation

**Output Format**:

```json
{
  "centroid": {
    "google_place_id": "ChIJ...",
    "name": "George Town",
    "reason": "Highest priority score"
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
      "distance_from_previous_meters": 8500
    }
  ],
  "day_breakdown": {...}
}
```

## API Endpoints

### Main Endpoint: Supervisor

#### POST `/supervisor/chat`

Natural language trip planning (recommended).

**Request**:

```json
{
  "query": "Plan a 3-day trip to Penang for 2 people who love food and culture. Must visit Kek Lok Si Temple."
}
```

**Response**:

```json
{
  "success": true,
  "response": "Complete trip plan with recommendations and routing..."
}
```

#### POST `/supervisor/plan-trip`

Structured trip planning request.

**Request**:

```json
{
  "destination_state": "Penang",
  "user_preferences": ["Food", "Culture", "Art"],
  "number_of_travelers": 2,
  "trip_duration_days": 3,
  "preferred_poi_names": ["Kek Lok Si Temple"],
  "max_pois_per_day": 6
}
```

#### GET `/supervisor/capabilities`

View system architecture and capabilities.

---

### Sub-Agent Endpoints (Optional)

#### POST `/recommender/recommend`

Direct access to Recommender Agent.

#### POST `/planner/plan-itinerary`

Direct access to Planner Agent.

## Usage Examples

### Example 1: Complete Trip Planning

```python
import requests

response = requests.post("http://localhost:8000/supervisor/chat", json={
    "query": "Plan a 3-day trip to Penang for 2 people who love food and culture"
})

result = response.json()
print(result["response"])
```

### Example 2: Structured Request

```python
response = requests.post("http://localhost:8000/supervisor/plan-trip", json={
    "destination_state": "Kuala Lumpur",
    "user_preferences": ["Adventure", "Shopping", "Food"],
    "number_of_travelers": 5,
    "trip_duration_days": 4,
    "max_pois_per_day": 5
})
```

### Example 3: Just Recommendations

```python
response = requests.post("http://localhost:8000/supervisor/chat", json={
    "query": "Recommend POIs in Malacca for history lovers"
})
```

## Testing

### 1. Test Supervisor Agent

```bash
python test_supervisor_agent.py
```

### 2. Test via API

```bash
# Start server
uvicorn main:app --reload

# In another terminal
python test_supervisor_api.py
```

### 3. Interactive Docs

```
http://localhost:8000/docs
```

## Workflow Details

### Complete Trip Planning Flow

```
User Request
    ↓
Supervisor Agent
    ↓
┌───────────────────────────────────┐
│ Step 1: Get Recommendations       │
│ Tool: get_poi_recommendations     │
│   ↓                                │
│ Recommender Agent                 │
│   - Load POIs from DB             │
│   - Calculate priority scores     │
│   - Return top 50 POIs            │
│   - Generate activity mix         │
└───────────────────────────────────┘
    ↓
    Output: 50 priority-scored POIs
    ↓
┌───────────────────────────────────┐
│ Step 2: Plan Itinerary            │
│ Tool: plan_itinerary              │
│   ↓                                │
│ Planner Agent                     │
│   - Select centroid               │
│   - Calculate distances           │
│   - Cluster POIs                  │
│   - Generate sequence             │
│   - Create day-by-day plan        │
└───────────────────────────────────┘
    ↓
    Output: Optimized itinerary
    ↓
Supervisor combines results
    ↓
Present to user:
    - Trip overview
    - Recommended POIs
    - Day-by-day itinerary
    - Travel distances
    - Tips and insights
```

## Environment Variables

Required in `.env`:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SERVICE_ROLE_KEY=your-service-role-key

# Google Gemini
GOOGLE_API_KEY=your-google-api-key

# LangChain Model
DEFAULT_LLM_MODEL=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.7
```

## Database Requirements

**Table**: `osm_pois`

**Required Fields**:

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

**Required PostGIS Functions**:

- `calculate_distance(lat1, lon1, lat2, lon2)`
- `get_nearby_pois(center_lat, center_lon, radius_m, ...)`
- `get_pois_with_distances(poi_ids, center_lat, center_lon)`

## Extending the System

### Adding a New Agent

1. **Create the agent** (e.g., `agents/weather_agent.py`)
2. **Define its tools** (e.g., `tools/weather_tools.py`)
3. **Wrap as supervisor tool** in `tools/supervisor_tools.py`:

```python
@tool
def get_weather_forecast(request: str) -> str:
    """Get weather forecast for trip planning"""
    result = weather_agent.invoke(...)
    return result["messages"][-1].content
```

4. **Add to supervisor** in `agents/supervisor_agent.py`
5. **Update supervisor prompt** in `config/prompts.py`

## Best Practices

1. **Keep agents focused**: One domain per agent
2. **Clear tool descriptions**: Helps supervisor route correctly
3. **Structured outputs**: JSON format for agent-to-agent communication
4. **Error handling**: Each agent handles its own errors
5. **Logging**: Use LangSmith for debugging

## Troubleshooting

### Agent not being called

- Check supervisor prompt clarity
- Verify tool descriptions
- Review user request phrasing

### Wrong sequence

- Update supervisor workflow instructions
- Add explicit sequencing rules

### Sub-agent errors

- Test sub-agents individually first
- Check tool parameters
- Verify database connectivity

## Resources

- [LangChain Supervisor Pattern Docs](https://python.langchain.com/docs/concepts/multi_agent/)
- [LangChain Tools](https://python.langchain.com/docs/concepts/tools/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
