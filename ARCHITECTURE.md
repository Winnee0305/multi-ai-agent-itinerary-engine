# Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                      (Natural Language Query)                    │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ITINERARY ORCHESTRATOR                         │
│                  (Multi-Agent Coordinator)                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Info Agent   │  │  Recommender  │  │  Planner      │
│               │→ │  Agent        │→ │  Agent        │
└───────────────┘  └───────────────┘  └───────────────┘
                                                │
                                                ▼
                                      ┌───────────────┐
                                      │  Optimizer    │
                                      │  Agent        │
                                      └───────────────┘
                                                │
                                                ▼
                                      Final Itinerary
```

## 📊 Data Flow

### Phase 1: Information Extraction

```
User Input: "5-day trip to Penang, love food and culture"
            ↓
    ┌─────────────┐
    │ Info Agent  │  (LLM: GPT-4)
    └─────────────┘
            ↓
UserContext {
    destination_states: ["Penang"]
    travel_days: 5
    interests: ["Food", "Culture"]
    number_of_travelers: 2
}
```

### Phase 2: POI Recommendation

```
UserContext
    ↓
┌──────────────────┐
│ Recommender      │
│ Agent            │  Uses Tools:
│                  │  • get_pois_by_filters
│                  │  • calculate_priority_scores
└──────────────────┘
    ↓
    │ Database Query (Supabase)
    │ SELECT * FROM osm_pois WHERE state='Penang'...
    ↓
┌──────────────────┐
│ Priority Scorer  │  Applies Rules:
│                  │  • Interest Match (×1.5)
│                  │  • Group Safety (×0.8)
│                  │  • Time Pressure (×1.2)
│                  │  • Preferred POIs (×2.0)
└──────────────────┘
    ↓
Top 20 POIs (sorted by priority_score)
```

### Phase 3: Itinerary Planning

```
Top 20 POIs
    ↓
┌──────────────────┐
│ Planner Agent    │  Uses Tools:
│                  │  • get_pois_near_location
│                  │  • calculate_travel_distance
└──────────────────┘
    ↓
    │ 1. Select Centroid (Top 5 → Pick 1)
    │ 2. PostGIS Query: Find POIs within 5km
    │    SELECT * WHERE ST_DWithin(geom, centroid, 5000)
    │ 3. Group by proximity into days
    ↓
Draft Itinerary {
    centroid: "Penang Street Art"
    daily_routes: [
        Day 1: [POI1, POI2, POI3, POI4]
        Day 2: [POI5, POI6, POI7, POI8]
        ...
    ]
}
```

### Phase 4: Route Optimization

```
Draft Itinerary
    ↓
┌──────────────────┐
│ Optimizer Agent  │  Uses Tools:
│                  │  • calculate_route_total_distance
│                  │  • validate_daily_route
└──────────────────┘
    ↓
    │ For each day:
    │ 1. Validate total distance < 50km
    │ 2. Optimize POI order (nearest-neighbor)
    │ 3. Check feasibility
    ↓
Final Optimized Itinerary + Validation Report
```

## 🔧 Component Details

### 1. Tools Layer

**Supabase Tools** (Database Queries)

```python
get_pois_by_filters(state, min_popularity, only_golden, limit)
    ↓ SQL Query
    SELECT * FROM osm_pois
    WHERE state = ? AND popularity_score >= ?
    ORDER BY popularity_score DESC
    LIMIT ?
```

**Distance Tools** (PostGIS Spatial Queries)

```python
get_pois_near_location(lat, lon, radius_meters)
    ↓ RPC Call
    SELECT * FROM get_nearby_pois(5.4164, 100.3327, 5000)
    ↓ PostGIS Function
    ST_DWithin(geom, ST_MakePoint(lon, lat)::geography, radius)
```

**Priority Tools** (Scoring Logic)

```python
calculate_priority_scores(pois, preferences, travelers, days)
    ↓ Uses PriorityScorer
    For each POI:
        base_score = popularity_score
        score × 1.5 if interest match
        score × 0.8 if unsafe for group
        score × 1.2 if landmark on short trip
        score × 2.0 if user-preferred
```

### 2. Agent Layer

**Info Agent** (Structured Extraction)

```
Input: Natural language
    ↓ LLM Prompt
    System: "Extract travel preferences..."
    Output Format: UserContext Pydantic model
    ↓ Validation
    Pydantic validates all fields
    ↓
Output: Structured UserContext
```

**Recommender Agent** (POI Selection)

```
Input: UserContext
    ↓ Tool Call 1
    pois = get_pois_by_filters.invoke(...)
    ↓ Tool Call 2
    scored_pois = calculate_priority_scores.invoke(...)
    ↓
Output: Top N POIs (sorted)
```

**Planner Agent** (Itinerary Building)

```
Input: Recommended POIs
    ↓ Logic
    1. Select centroid (highest priority in top 5)
    2. Find nearby POIs (PostGIS query)
    3. Distribute across days
    ↓
Output: Draft daily itinerary
```

**Optimizer Agent** (Route Refinement)

```
Input: Draft itinerary
    ↓ For each day
    1. Validate distance constraints
    2. Reorder POIs (nearest-neighbor)
    3. Calculate travel distances
    ↓
Output: Optimized itinerary + report
```

### 3. Orchestrator Layer

**State Management**

```python
ItineraryState {
    user_query: str
    user_context: Dict
    recommended_pois: List[Dict]
    draft_itinerary: Dict
    final_itinerary: Dict
    current_step: str
}
```

**Execution History**

```python
PipelineHistory {
    steps: [
        AgentStep(agent="InfoAgent", time=2.3s, success=True),
        AgentStep(agent="RecommenderAgent", time=1.5s, success=True),
        AgentStep(agent="PlannerAgent", time=3.1s, success=True),
        AgentStep(agent="OptimizerAgent", time=2.4s, success=True)
    ],
    total_time: 9.3s
}
```

## 🗄️ Database Schema

```sql
osm_pois
├── id (BIGINT, PK)
├── name (TEXT)
├── lat, lon (DOUBLE PRECISION)
├── geom (GEOGRAPHY) ← PostGIS column
├── state (TEXT)
├── wikidata_sitelinks (INTEGER)
├── in_golden_list (BOOLEAN)
├── popularity_score (INTEGER)
├── google_rating (REAL)
├── google_reviews (INTEGER)
├── google_place_id (TEXT)
└── google_types (TEXT[])

Indexes:
• idx_osm_pois_geom (GIST) ← Spatial index
• idx_osm_pois_state
• idx_osm_pois_popularity
• idx_osm_pois_golden
```

## 🎯 Key Design Decisions

### Why Multi-Agent?

1. **Separation of Concerns**: Each agent has one clear job
2. **LLM Token Efficiency**: Smaller, focused prompts vs one huge prompt
3. **Debuggability**: Can test/fix each agent independently
4. **Flexibility**: Easy to swap LLM models per agent
5. **Parallel Execution**: Could run agents in parallel (future)

### Why PostGIS?

1. **Efficient Spatial Queries**: Find nearby POIs in milliseconds
2. **Accurate Distances**: Geography-aware calculations
3. **Scalability**: Handles millions of POIs
4. **Standard SQL**: No custom geo libraries needed

### Why LangChain Tools?

1. **LLM Awareness**: Tools have natural language descriptions
2. **Type Safety**: Pydantic validation on inputs/outputs
3. **Observability**: Built-in logging and tracing
4. **Composability**: Easily add new tools to agents

## 📈 Performance Characteristics

**Expected Execution Times:**

- Info Agent: 1-3 seconds (LLM call)
- Recommender Agent: 1-2 seconds (DB query + scoring)
- Planner Agent: 2-4 seconds (PostGIS queries + logic)
- Optimizer Agent: 2-3 seconds (distance calculations)

**Total Pipeline: 6-12 seconds**

**Optimization Opportunities:**

1. Cache POI queries by state
2. Batch PostGIS distance calculations
3. Use faster LLM (GPT-3.5) for non-critical agents
4. Parallel tool execution in agents
5. Database query result caching

## 🔐 Security Considerations

- **Environment Variables**: All secrets in `.env` (not committed)
- **Service Role Key**: Needed for RLS bypass (use with caution)
- **API Rate Limiting**: OpenAI has built-in rate limits
- **Input Validation**: Pydantic models validate all inputs
- **SQL Injection**: Parameterized queries only (no string interpolation)

## 🚀 Scalability Path

1. **Horizontal Scaling**: Deploy multiple orchestrator instances
2. **Caching Layer**: Redis for POI queries
3. **Async Agents**: Use async/await for I/O operations
4. **Message Queue**: RabbitMQ for agent communication
5. **Load Balancer**: Distribute requests across instances
