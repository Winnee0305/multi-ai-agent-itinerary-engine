# New Features Implementation Guide

## Overview

Two major features have been added to the chatbot:

1. **General Chatbot for Out-of-Scope Questions** - Handles questions about Malaysian culture, history, food, etc.
2. **POI Suggestions Mode** - Returns 5 POI recommendations instead of full itinerary when user asks for suggestions

## Architecture

### Request Type Detection

The system now classifies user requests into three types during the input parsing phase:

```
request_type: Literal["full_trip", "poi_suggestions", "general_question"]
```

#### Classification Logic (in `input_parser.py`)

```python
- 'full_trip': User is planning a multi-day trip
  Keywords: "plan", "trip", "itinerary", "days", duration mentioned
  
- 'poi_suggestions': User wants POI recommendations (no full itinerary)
  Keywords: "suggest", "recommend", "what to visit", "best places"
  Result: Return 5 POIs only, skip itinerary generation
  
- 'general_question': User asks about culture, history, food, etc.
  NOT related to trip planning
  Result: Skip planning, answer with general LLM response
```

## Flow Changes

### Original Flow (Full Trip Planning)
```
START → parse_input → recommend → plan → format_response → END
```

### New Flow (POI Suggestions)
```
START → parse_input → recommend → [SKIP plan] → format_response → END
        (request_type="poi_suggestions")
```

### New Flow (General Question)
```
START → parse_input → [SKIP recommend/plan] → END
        (request_type="general_question")
        Returns: General LLM response about Malaysia
```

## Implementation Details

### 1. State Schema Update (`agents/state.py`)

Added new field to `TripPlannerState`:
```python
request_type: Optional[Literal["full_trip", "poi_suggestions", "general_question"]]
```

### 2. Input Parser (`agents/input_parser.py`)

**Enhanced Detection:**
- Detects request type during LLM parsing
- For general questions: Returns early with LLM response
- For POI suggestions: Sets `num_pois=5` and `trip_duration_days=1`
- For full trip: Continues normal flow

**Key Changes:**
```python
# For general questions
if request_type == "general_question":
    general_response = model.invoke([HumanMessage(content=general_answer_prompt)])
    return {
        "messages": [AIMessage(content=general_response.content)],
        "next_step": "complete"  # Skip planning
    }

# For POI suggestions
if request_type == "poi_suggestions":
    parsed_context.num_pois = 5
    parsed_context.trip_duration_days = 1
```

### 3. Supervisor Graph (`agents/supervisor_graph.py`)

**Enhanced Routing:**
- Detects `request_type` in routing function
- Skips planner for POI suggestions (goes to formatter)
- Routes complete requests to END

```python
elif next_step == "plan":
    # Skip planning for POI suggestions - go straight to formatting
    if request_type == "poi_suggestions":
        return "format_response"
    return "plan"

elif next_step == "complete":
    return "__end__"  # End for general questions
```

### 4. Recommender Agent (`agents/recommender_agent.py`)

**Updated:**
- Preserves `request_type` through state
- Returns results regardless of request type

### 5. Planner Agent (`agents/planner_agent.py`)

**Updated:**
- Preserves `request_type` through state
- Skipped entirely for POI suggestions

### 6. Response Formatter (`agents/response_formatter.py`)

**New Logic:**
- Detects `request_type` in formatting node
- Returns different formats based on type

**For POI Suggestions (5 POIs only):**
```markdown
🎯 Recommended Places in [State]

Based on your interests: [Preferences]

1. **[POI Name]**
   *Category: [Type]*
   [Description first 150 chars]...

2. **[POI Name]**
   ...

---
Want a full itinerary? Just tell me your trip duration and travel dates!
```

**For Full Trip:**
- Returns original format with day-by-day itinerary

## Testing

### Test File: `test_request_types.py`

Validates the TripContext model with different request types:
```bash
python3 test_request_types.py
```

Expected output:
```
✓ Created general question context
✓ Created full trip context  
✓ Created POI suggestions context
```

### Test File: `test_new_features.py` (LLM-based integration tests)

Tests the full graph with three scenarios:
1. General question (culture)
2. POI suggestions request
3. Full trip planning (baseline)

**Note:** Requires Google Gemini API key

```bash
export GOOGLE_API_KEY="your_key_here"
python3 test_new_features.py
```

## Usage Examples

### Example 1: General Question

**User Input:**
> "Tell me about Malaysian food culture and what makes it unique"

**System Response:**
- Detects: `request_type="general_question"`
- Skips: Input parsing, recommendation, planning
- Returns: Direct LLM response about Malaysian food

### Example 2: POI Suggestions

**User Input:**
> "Suggest some temples and cultural sites in Penang"

**System Response:**
- Detects: `request_type="poi_suggestions"`
- Extracts: `destination_state="Penang"`, `user_preferences=["Culture"]`
- Sets: `num_pois=5`, `trip_duration_days=1`
- Skips: Itinerary generation
- Returns: Top 5 cultural POIs in Penang

### Example 3: Full Trip (No Change)

**User Input:**
> "Plan a 3-day trip to Malacca for 2 people. We like history and food."

**System Response:**
- Detects: `request_type="full_trip"`
- Continues: Normal flow through all agents
- Returns: Complete 3-day itinerary

## State Propagation

The `request_type` is now preserved through all nodes:

```
parse_input  → request_type="poi_suggestions"
    ↓
recommend    → request_type="poi_suggestions" (preserved)
    ↓
[SKIP plan]  → goes to format_response
    ↓
format_response → Detects request_type, formats 5 POIs only
    ↓
END
```

## Configuration

### Keywords for Request Type Detection

The LLM uses these guidelines for detection:

**Full Trip Keywords:**
- "plan", "trip", "itinerary", "days", "duration mentioned"

**POI Suggestions Keywords:**
- "suggest", "recommend", "what to visit", "best places"

**General Question Keywords:**
- Questions about culture, history, food culture, customs, etc. without trip context

## Future Enhancements

1. **Confidence Scoring**: Add confidence scores to request type detection
2. **Clarification Prompts**: Ask user to clarify if request type is ambiguous
3. **Chaining Requests**: Allow "suggest 5 POIs" → "expand to 3-day itinerary"
4. **Caching**: Cache general question responses

## Troubleshooting

### Issue: Request classified as wrong type

**Solution:** Update the detection keywords in `input_parser.py` prompt section

### Issue: General responses not helpful

**Solution:** Modify the `general_answer_prompt` in `input_parser.py` to provide more context

### Issue: POI suggestions showing too many/too few

**Solution:** Adjust `num_pois=5` in the POI suggestions branch

## Files Modified

- ✅ `agents/state.py` - Added `request_type` field
- ✅ `agents/input_parser.py` - Enhanced detection logic + general Q&A
- ✅ `agents/supervisor_graph.py` - Updated routing for new types
- ✅ `agents/recommender_agent.py` - Preserve `request_type`
- ✅ `agents/planner_agent.py` - Preserve `request_type`
- ✅ `agents/response_formatter.py` - Different formats per request type
- ✅ `test_request_types.py` - Model validation tests (NEW)
- ✅ `test_new_features.py` - Integration tests (UPDATED)
