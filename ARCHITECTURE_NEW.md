# LangGraph Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH SUPERVISOR GRAPH                    │
│                   (Deterministic State-Based Flow)               │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  User Input  │
│ (Natural     │
│  Language)   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  START                                                        │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  NODE: Input Parser                                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ • LLM extracts structured data from NL query           │  │
│  │ • Outputs: destination, preferences, travelers, days   │  │
│  │ • Sets next_step = "recommend"                         │  │
│  └────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CONDITIONAL EDGE: route_next_step()                         │
│  if next_step == "recommend" → go to Recommender            │
│  if next_step == "error" → go to END                         │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  NODE: Recommender                                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ • Direct call: recommend_pois_for_trip_logic()         │  │
│  │ • Load POIs from Supabase                              │  │
│  │ • Calculate priority scores (contextual boosts)        │  │
│  │ • Generate activity mix                                │  │
│  │ • Outputs: top_priority_pois, activity_mix             │  │
│  │ • Sets next_step = "plan"                              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CONDITIONAL EDGE: route_next_step()                         │
│  if next_step == "plan" → go to Planner                     │
│  if next_step == "error" → go to END                         │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  NODE: Planner                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ • Direct calls:                                        │  │
│  │   - select_best_centroid()                             │  │
│  │   - cluster_pois_by_distance() (30km threshold)        │  │
│  │   - generate_optimal_sequence() (nearest-neighbor)     │  │
│  │   - split_sequence_into_days()                         │  │
│  │ • Outputs: itinerary, centroid, optimized_sequence     │  │
│  │ • Sets next_step = "format_response"                   │  │
│  └────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CONDITIONAL EDGE: route_next_step()                         │
│  if next_step == "format_response" → go to Formatter        │
│  if next_step == "error" → go to END                         │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  NODE: Response Formatter                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ • Formats trip overview                                │  │
│  │ • Lists top POIs with priority scores                  │  │
│  │ • Visualizes activity mix (ASCII bars)                 │  │
│  │ • Displays day-by-day itinerary with distances         │  │
│  │ • Outputs: formatted user-friendly text               │  │
│  │ • Sets next_step = "complete"                          │  │
│  └────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  CONDITIONAL EDGE: route_next_step()                         │
│  if next_step == "complete" → go to END                     │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  END                                                          │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│   Response   │
│ (Formatted   │
│  Itinerary)  │
└──────────────┘
```

## State Flow

```
TripPlannerState = {
    # Conversation
    messages: [HumanMessage, AIMessage, ...]

    # User Context (from Input Parser)
    destination_state: "Penang"
    user_preferences: ["Food", "Culture"]
    num_travelers: 2
    trip_duration_days: 3
    preferred_pois: ["Kek Lok Si Temple"]
    num_pois: 50

    # Recommender Output
    recommendations: {...}
    top_priority_pois: [{...}, {...}, ...]
    activity_mix: {"food": 0.22, "culture": 0.09, ...}

    # Planner Output
    itinerary: {...}
    centroid: {...}
    optimized_sequence: [{...}, {...}, ...]

    # Control Flow
    next_step: "recommend" | "plan" | "format_response" | "complete" | "error"
    error_message: null | "error details"
}
```

## Key Differences from Old Architecture

### Old (LangChain Agent Pattern)

```
Supervisor Agent (LLM)
    ├─ Tool: get_poi_recommendations
    │    └─ Recommender Agent (LLM)
    │         └─ Tools: load_pois, calculate_scores, ...
    │
    └─ Tool: plan_itinerary
         └─ Planner Agent (LLM)
              └─ Tools: select_centroid, cluster, sequence, ...

❌ Multiple LLM calls for routing
❌ String-based communication between agents
❌ Non-deterministic flow (LLM decides)
❌ Hard to trace and debug
```

### New (LangGraph Node Pattern)

```
Graph (Deterministic)
    ├─ Input Parser (LLM for parsing only)
    ├─ Recommender (Direct function calls)
    ├─ Planner (Direct function calls)
    └─ Formatter (Text formatting only)

✅ One LLM call for parsing
✅ Typed state object
✅ Deterministic routing (state-based)
✅ Clear node boundaries in traces
```

## Routing Logic

```python
def route_next_step(state: TripPlannerState) -> str:
    """Pure Python routing - no LLM needed"""
    next_step = state.get("next_step")

    if next_step == "recommend":
        return "recommend"  # Go to Recommender node
    elif next_step == "plan":
        return "plan"  # Go to Planner node
    elif next_step == "format_response":
        return "format_response"  # Go to Formatter node
    elif next_step in ("complete", "error"):
        return "__end__"  # Stop execution
    else:
        return "parse_input"  # Default: start with parsing
```

## Memory & Persistence

```
MemorySaver (In-Memory Checkpointer)
    └─ Stores state after each node
    └─ Enables conversation continuity
    └─ Accessible via thread_id

config = {
    "configurable": {
        "thread_id": "user_123"  # Unique per user session
    }
}
```

## API Integration

```
FastAPI Router
    ├─ POST /supervisor/chat
    │    └─ Uses create_supervisor_graph()
    │         (with formatting)
    │
    └─ POST /supervisor/plan-trip
         └─ Uses create_supervisor_graph_simple()
              (without formatting, returns JSON)
```

## Error Handling

```
Any node can set:
    next_step = "error"
    error_message = "Detailed error info"

Routing will send to END immediately.
Final state will contain error details.
```

---

**This architecture is**:

- 🚀 **Faster**: Direct function calls instead of nested agent invocations
- 🎯 **Deterministic**: State-based routing, no LLM guessing
- 🔍 **Observable**: Clear node boundaries in LangSmith traces
- 🛡️ **Reliable**: Explicit error handling with state fields
- 🧹 **Maintainable**: Simple Python functions, not complex prompts
