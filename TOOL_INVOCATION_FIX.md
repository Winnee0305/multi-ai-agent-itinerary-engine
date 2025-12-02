# Tool Architecture - StructuredTool Pattern

## Overview

This project uses **`StructuredTool.from_function()`** for programmatic tool orchestration, allowing direct function calls while maintaining LangChain tool compatibility.

## Why StructuredTool?

When orchestrating agents **programmatically** (not via LLM tool selection), using `StructuredTool.from_function()` is preferred over the `@tool` decorator because:

1. **Direct Invocation**: Tools can be called as regular functions: `get_poi_recommendations(request)`
2. **No .invoke() Required**: Cleaner code without wrapper invocation syntax
3. **LangChain Compatible**: Still compatible with agent tool binding
4. **Explicit Control**: Better for supervisor patterns with predetermined workflows

## Pattern Structure

### For Supervisor Tools (Sub-Agent Wrappers)

```python
from langchain.tools import StructuredTool

# Internal function - does the actual work
def _get_poi_recommendations(request: str) -> str:
    """Get personalized POI recommendations."""
    result = recommender_agent.invoke(...)
    return result["messages"][-1].content

# StructuredTool instance - exposed to supervisor
get_poi_recommendations = StructuredTool.from_function(
    func=_get_poi_recommendations,
    name="get_poi_recommendations",
    description="Detailed description for the agent..."
)
```

### For Regular Tools (Internal Helpers)

```python
# Internal helper (no decorator) - for tool-to-tool calls
def _load_pois_from_database(state, golden_only, min_popularity):
    """Internal helper - does the actual work"""
    supabase = get_supabase()
    # ... implementation ...
    return result.data

# Tool wrapper (with @tool) - for agent access
@tool
def load_pois_from_database(state, golden_only, min_popularity):
    """Load POIs from Supabase database."""
    return _load_pois_from_database(state, golden_only, min_popularity)
```

## Root Cause of Previous Error

**Error Message:** `'StructuredTool' object is not callable`

When you use the `@tool` decorator in LangChain, it creates a **`StructuredTool` object**, not a regular function.

- ✅ **Correct:** Agents can invoke tools using `.invoke({"param": value})`
- ❌ **Incorrect:** Tools calling other tools directly like regular functions: `calculate_distances_from_centroid(centroid, pois)`

### Problematic Code Locations

**In `tools/planner_tools.py`:**

- Line 283 in `cluster_pois_by_distance`: Calling `calculate_distances_from_centroid(...)` directly

**In `tools/recommender_tools.py`:**

- Line 342 in `recommend_pois_for_trip`: Calling `load_pois_from_database(...)` directly
- Line 347: Calling `calculate_priority_scores(...)` directly
- Line 395: Calling `get_top_priority_pois(...)` directly
- Line 398: Calling `calculate_activity_mix(...)` directly
- Line 401: Calling `generate_recommendation_output(...)` directly

## Solution: Internal Helper Pattern

Create **internal helper functions** (without `@tool` decorator) that contain the actual logic, and have the `@tool` wrappers call these helpers.

### Pattern Structure

```python
# ============================================================================
# INTERNAL HELPER FUNCTIONS (not exposed as tools)
# These are called by other tools internally
# ============================================================================

def _internal_helper(params):
    """Internal helper - does the actual work"""
    # ... implementation logic ...
    return result


# ============================================================================
# TOOL WRAPPERS (exposed to agents)
# These call the internal helper functions
# ============================================================================

@tool
def tool_wrapper(params):
    """Tool wrapper for agents - delegates to internal helper"""
    return _internal_helper(params)
```

### Benefits

1. **Tools can call helpers directly** - No need for `.invoke()` complexity
2. **Clean separation** - Logic in helpers, tool interface in wrappers
3. **Agent access maintained** - Agents still see and use the `@tool` decorated functions
4. **Reusability** - Other tools can call helpers without tool invocation overhead

## Files Fixed

### `tools/planner_tools.py`

**Internal Helpers Created:**

- `_get_poi_by_place_id(place_id)` - Get POI data from database
- `_calculate_distances_from_centroid(centroid_place_id, poi_place_ids)` - Calculate distances using PostGIS

**Tool Wrappers Updated:**

- `get_poi_by_place_id` → calls `_get_poi_by_place_id()`
- `calculate_distances_from_centroid` → calls `_calculate_distances_from_centroid()`

**Fixed Tool-to-Tool Calls:**

- `cluster_pois_by_distance` now calls `_calculate_distances_from_centroid()` instead of `calculate_distances_from_centroid()`

### `tools/recommender_tools.py`

**Internal Helpers Created:**

- `_load_pois_from_database(state, golden_only, min_popularity)` - Load POIs from Supabase
- `_calculate_priority_scores(pois, preferences, travelers, days, preferred_names)` - 4-layer scoring algorithm
- `_get_top_priority_pois(scored_pois, top_n)` - Extract top N POIs
- `_calculate_activity_mix(top_pois, scored_pois)` - Calculate category percentages
- `_generate_recommendation_output(state, days, pois, mix, preferences)` - Format final output

**Tool Wrappers Updated:**

- `load_pois_from_database` → calls `_load_pois_from_database()`
- `calculate_priority_scores` → calls `_calculate_priority_scores()`
- `get_top_priority_pois` → calls `_get_top_priority_pois()`
- `calculate_activity_mix` → calls `_calculate_activity_mix()`
- `generate_recommendation_output` → calls `_generate_recommendation_output()`

**Fixed Tool-to-Tool Calls:**

- `recommend_pois_for_trip` now calls all internal helpers (`_load_pois_from_database`, `_calculate_priority_scores`, `_get_top_priority_pois`, `_calculate_activity_mix`, `_generate_recommendation_output`)

## Verification

### Test the Fix

```bash
# Start the FastAPI server
python main.py

# Test the supervisor endpoint
curl -X POST http://localhost:8000/supervisor/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "destination_state": "Penang",
    "user_preferences": ["Food", "Culture"],
    "number_of_travelers": 2,
    "trip_duration_days": 3,
    "user_request": "Plan a 3-day food and culture trip to Penang for 2 people"
  }'
```

### Expected Behavior

- ✅ No more `'StructuredTool' object is not callable` errors
- ✅ Supervisor can invoke recommender and planner sub-agents successfully
- ✅ Each sub-agent can use its tools properly
- ✅ Complete trip planning workflow executes end-to-end

## Architecture Summary

```
Supervisor Agent (Programmatic Orchestration)
├── StructuredTool: get_poi_recommendations
│   └── Direct call: _get_poi_recommendations(request)
│       └── Invokes: recommender_agent.invoke(...)
│           └── Uses tools: @tool load_pois_from_database, calculate_priority_scores, etc.
│               └── Call helpers: _load_pois_from_database(), _calculate_priority_scores(), etc.
│
└── StructuredTool: plan_itinerary
    └── Direct call: _plan_itinerary(request)
        └── Invokes: planner_agent.invoke(...)
            └── Uses tools: @tool select_centroid_place, calculate_distances_from_centroid, etc.
                └── Call helpers: _select_centroid_place(), _calculate_distances_from_centroid(), etc.
```

## Key Differences

| Aspect         | @tool Decorator                      | StructuredTool.from_function()                |
| -------------- | ------------------------------------ | --------------------------------------------- |
| **Use Case**   | Sub-agent tools (for LLM selection)  | Supervisor tools (programmatic orchestration) |
| **Invocation** | Requires `.invoke({"param": value})` | Direct function call `func(param)`            |
| **Definition** | `@tool` above function               | Separate definition after function            |
| **Best For**   | Tools selected by LLM dynamically    | Predetermined workflow steps                  |

## Files Structure

### `tools/supervisor_tools.py` (StructuredTool Pattern)

- **Purpose**: Wrap sub-agents for programmatic supervisor orchestration
- **Pattern**: `StructuredTool.from_function()`
- **Tools**:
  - `get_poi_recommendations` - Wraps recommender_agent
  - `plan_itinerary` - Wraps planner_agent
- **Usage**: Supervisor calls these directly in predetermined workflow

### `tools/planner_tools.py` (@tool + Internal Helpers)

- **Purpose**: Distance calculations and route optimization
- **Pattern**: `@tool` decorators + internal `_helper()` functions
- **Why**: Planner agent needs LLM to select appropriate tools dynamically
- **Tools**: 8 tools for PostGIS queries, clustering, sequencing

### `tools/recommender_tools.py` (@tool + Internal Helpers)

- **Purpose**: POI loading and priority scoring
- **Pattern**: `@tool` decorators + internal `_helper()` functions
- **Why**: Recommender agent needs LLM to select appropriate tools dynamically
- **Tools**: 6 tools for database queries, scoring algorithms

## Key Takeaways

1. **Supervisor tools use `StructuredTool.from_function()`** - programmatic orchestration
2. **Sub-agent tools use `@tool` decorator** - LLM dynamic selection
3. **All tools use internal helpers** - enables tool-to-tool dependencies
4. **Two-tier architecture**: Supervisor (programmatic) → Sub-agents (dynamic tool selection)
5. **Clean separation**: Control flow vs. tool implementation

## Related Files

- `tools/planner_tools.py` - Route planning tools
- `tools/recommender_tools.py` - POI recommendation tools
- `tools/supervisor_tools.py` - High-level supervisor tools (wraps sub-agents)
- `agents/supervisor_agent.py` - Supervisor coordinator
- `agents/planner_agent.py` - Route planner sub-agent
- `agents/recommender_agent.py` - POI recommender sub-agent
