# Multi-AI-Agent Itinerary Engine

A sophisticated AI-powered travel itinerary planning system built with multi-agent architecture using LangGraph, LangChain, and Google's Gemini 2.5 Flash LLM. The system intelligently plans multi-day trips to Malaysia with geographically optimized routes and personalized recommendations.

## 🎯 System Overview

The Multi-AI-Agent Itinerary Engine is an intelligent travel planning assistant that can:

- **Plan Multi-Day Itineraries**: Create detailed day-by-day travel plans with optimized routes
- **Recommend POIs**: Suggest Points of Interest (temples, restaurants, natural sites, etc.) based on user preferences
- **Answer General Questions**: Provide information about Malaysian culture, history, food, and attractions
- **Optimize Routes**: Use geographic clustering (K-Means) to minimize travel distances and overnight transitions
- **Support Multiple Trip Types**: Full itineraries, POI suggestions, or general travel information

### Key Features

✨ **Three Request Types**:

- **Full Trip Planning**: Complete multi-day itinerary with day-by-day schedules
- **POI Suggestions**: Quick recommendations of top 5 places to visit
- **General Questions**: Information about Malaysian destinations and culture

🗺️ **Geographic Intelligence**:

- K-Means clustering for optimal geographic grouping
- PostGIS spatial queries for accurate distance calculations
- Support for all Malaysian states and regions
- Real-time POI enrichment with Google Places data

🤖 **Multi-Agent Architecture**:

- **Input Parser Agent**: Detects request type and extracts trip parameters
- **Recommender Agent**: Finds relevant POIs matching user preferences
- **Planner Agent**: Creates optimized itinerary sequences
- **Response Formatter**: Generates beautiful, user-friendly output

💾 **Memory & Persistence**:

- Conversation history tracking with LangGraph MemorySaver
- Session-based state management
- Multi-turn conversation support

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Server                        │
│              (main.py with CORS middleware)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌──────────────────────────────────────┐
        │    LangGraph Supervisor Graph        │
        │  (agents/supervisor_graph.py)        │
        └──────────────────────────────────────┘
                    ↓         ↓         ↓
        ┌───────────┴─────────┴────────┴────────┐
        │                                        │
    ┌───▼────┐  ┌──────────┐  ┌──────────┐  ┌──▼────────┐
    │ Parser │  │Recomm.  │  │ Planner  │  │ Formatter│
    │ Agent  │→ │ Agent   │→ │ Agent    │→ │  Agent   │
    └────────┘  └──────────┘  └──────────┘  └──────────┘
        ↓           ↓             ↓              ↓
    [Parsing]  [Scoring]     [Routing]     [Output]
        ↓           ↓             ↓              ↓
    ┌───────────────────────────────────────────────────┐
    │         Supabase PostgreSQL Database              │
    │  (POI Store, Geospatial Queries, History)        │
    └───────────────────────────────────────────────────┘
```

### Node-Based Flow

```
START
  ↓
[1] Parse Input (LLM parses user request)
  ├─→ Request Type Detection
  │   ├─ full_trip: Continue to recommend
  │   ├─ poi_suggestions: Recommend only (skip planner)
  │   └─ general_question: End with LLM answer
  ↓
[2] Recommend (Get POIs matching preferences)
  ├─ Query Supabase for relevant POIs
  ├─ Score based on priority and relevance
  └─ Return filtered results
  ↓
[3] Plan (Create optimized itinerary)
  ├─ Select centroid from top POIs
  ├─ K-Means clustering by geographic proximity
  ├─ Sequence within each day (nearest neighbor)
  └─ Calculate travel times and distances
  ↓
[4] Format Response (Generate user-friendly output)
  ├─ Create trip summary with metrics
  ├─ Generate day-by-day schedule
  └─ Include distance, duration, and activity mix
  ↓
END (Return to user)
```

## 🛠️ Technology Stack

### Core Framework

- **LangGraph**: Multi-agent orchestration and state management
- **LangChain**: Tool integration and memory management
- **Google Gemini 2.5 Flash**: LLM backbone with streaming support
- **FastAPI**: REST API server with async support

### Data & Geospatial

- **Supabase**: PostgreSQL database with PostGIS extension
- **PostGIS**: Spatial queries and distance calculations
- **scikit-learn**: K-Means clustering for geographic optimization
- **GeoPandas**: Geospatial data manipulation
- **Shapely**: Geometric operations

### Data Enrichment

- **Google Places API**: Real-time POI information
- **OSM (OpenStreetMap)**: Geographic boundaries and POI data
- **SPARQL**: Wikidata queries for enriched POI information

## 📁 Project Structure

```
multi-ai-agent-itinerary-engine/
├── agents/                      # Multi-agent orchestration
│   ├── state.py                # Unified TripPlannerState (TypedDict)
│   ├── input_parser.py          # Request parsing & type detection
│   ├── recommender_agent.py     # POI recommendation logic
│   ├── planner_agent.py         # Itinerary generation
│   ├── response_formatter.py    # Output formatting
│   ├── supervisor_agent.py      # Supervisor routing (deprecated)
│   └── supervisor_graph.py      # LangGraph main orchestration
│
├── tools/                        # Agent tools & utilities
│   ├── planner_tools.py         # Spatial operations, clustering
│   └── recommender_tools.py     # POI filtering & scoring
│
├── routers/                      # FastAPI route handlers
│   ├── supervisor.py            # Main chatbot endpoint
│   ├── recommender.py           # Direct recommendation API
│   └── planner.py               # Direct planning API
│
├── database/                     # Data layer
│   ├── supabase_client.py       # Supabase initialization
│   ├── schema.sql               # Database schema definition
│   ├── rpc_functions.sql        # PostGIS stored procedures
│   ├── seed_data.py             # Initial data loading
│   └── clean_and_recreate.sql   # Database reset utilities
│
├── config/                       # Configuration
│   ├── settings.py              # Environment & LLM settings
│   └── prompts.py               # LLM prompt templates
│
├── data/                         # Geospatial data
│   └── state_shape/             # Malaysia state boundaries
│       └── geoBoundaries-MYS-ADM1/  # GeoJSON files
│
├── preprocessing/               # Data preparation scripts
│   ├── osm_fetcher.py           # Fetch POI data from OSM
│   ├── osm_preprocessor.py      # Clean & normalize data
│   ├── pois_enrich.py           # Enrich with metadata
│   ├── pois_google_places_enricher.py  # Google Places integration
│   ├── pois_priority_scorer.py  # Calculate POI priorities
│   └── upload_pois.py           # Upload to Supabase
│
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
└── pyproject.toml              # Project configuration
```

## 📊 State Management

The system uses a unified `TripPlannerState` TypedDict that flows through all nodes:

```python
class TripPlannerState(TypedDict):
    # Conversation
    messages: list[BaseMessage]
  
    # Trip Parameters
    destination: Optional[str]
    preferences: Optional[list[str]]
    num_travelers: int
    trip_duration_days: int
    preferred_pois: Optional[list[str]]
  
    # Request Type Detection
    request_type: Optional[Literal["full_trip", "poi_suggestions", "general_question"]]
  
    # Results from agents
    recommendations: Optional[list[dict]]
    itinerary: Optional[dict]
  
    # Control Flow
    next_step: str
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+ with PostGIS extension
- Google Gemini API key
- Supabase account

### Installation

1. **Clone and setup**:

```bash
git clone <repository-url>
cd multi-ai-agent-itinerary-engine
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Configure environment**:
   Create `.env` file:

```env
supabase_SUPABASE_URL=https://your_password.supabase.co
SERVICE_ROLE_KEY=your_supabase_service_role_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_PLACES_API_KEY=your_google_places_api_key
```

4. **Initialize database**:

```bash
python database/seed_data.py
```

5. **Start server**:

```bash
run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

## 💡 Usage Examples

### Example 1: Full Trip Planning

**Request**:

```json
{
  "message": "Plan a 3-day trip to Penang. I love temples, food, and nature. There will be 2 of us."
}
```

**Response Flow**:

1. Parser detects: `request_type="full_trip"`, destination="Penang", duration=3 days
2. Recommender finds 50 relevant POIs (temples, restaurants, nature spots)
3. Planner creates optimized 3-day itinerary using K-Means clustering
4. Formatter generates day-by-day schedule with distances and times

**Output**: Day-by-day itinerary with morning/afternoon/evening activities, travel times, and distances.

### Example 2: POI Suggestions

**Request**:

```json
{
  "message": "Suggest the best temples to visit in Penang"
}
```

**Response Flow**:

1. Parser detects: `request_type="poi_suggestions"`, destination="Penang"
2. Recommender finds top temples
3. **Planner is skipped**
4. Formatter returns top 5 POIs in lightweight format

**Output**: 5 recommended temples with descriptions and distances.

### Example 3: General Question

**Request**:

```json
{
  "message": "Tell me about Malaysian food culture"
}
```

**Response Flow**:

1. Parser detects: `request_type="general_question"`
2. **All planning agents are skipped**
3. LLM provides direct answer

**Output**: Conversational response about Malaysian cuisine.

## 🔌 API Endpoints

### Supervisor Endpoint (Recommended)

**POST** `/supervisor/chat` - Main chatbot endpoint with intelligent routing

### Recommender Endpoint

**POST** `/recommender/recommend_pois` - Direct POI recommendation

### Planner Endpoint

**POST** `/planner/plan_itinerary` - Direct itinerary generation

### Health Check

**GET** `/health` - Server health status

See `/docs` for interactive API documentation.

## 🧠 Agent Specifications

### 1. Input Parser Agent

**Role**: Detects request intent and extracts parameters

**Inputs**:

- User message (natural language)

**Outputs**:

- Request type: full_trip | poi_suggestions | general_question
- Parsed parameters: destination, preferences, duration, travelers
- General answer (if applicable)

**Logic**: Uses LLM with structured output to classify requests and extract parameters.

### 2. Recommender Agent

**Role**: Finds relevant Points of Interest

**Inputs**:

- Destination and preferences
- Number of POIs needed (5 for suggestions, 50 for full trips)

**Outputs**:

- List of ranked POIs with metadata
- Priority scores based on relevance
- Categories and descriptions

**Logic**:

- Queries Supabase for matching POIs
- Scores based on preference match
- Filters by state/region
- Returns ranked results

### 3. Planner Agent

**Role**: Creates optimized multi-day itinerary

**Inputs**:

- POI list from recommender
- Trip duration in days
- Clustering strategy (K-Means or simple)

**Outputs**:

- Daily itineraries (day 1, day 2, etc.)
- Optimized sequences with distances
- Travel time estimates
- Activity mix per day

**Logic**:

- Selects geographic centroid from top POIs
- Uses K-Means clustering to group POIs by location
- Sequences within each cluster using nearest neighbor
- Calculates PostGIS distances between POIs

### 4. Response Formatter

**Role**: Generates user-friendly output

**Inputs**:

- Parsed trip context
- Recommendations or itinerary
- Request type

**Outputs**:

- Formatted text output with ASCII art
- Day-by-day schedule
- Summary statistics
- Activity mix visualization

## 🗄️ Database Schema

### Main Tables

**pois** (Points of Interest)

```sql
- id: UUID (Primary Key)
- google_place_id: VARCHAR (unique)
- name: VARCHAR
- description: TEXT
- category: VARCHAR (temple, restaurant, museum, etc.)
- lat: DECIMAL
- lon: DECIMAL
- state: VARCHAR (Penang, KL, Selangor, etc.)
- priority_score: FLOAT (0-100)
- metadata: JSONB (images, hours, phone, etc.)
```

**poi_visits** (Conversation History)

```sql
- id: UUID
- user_id: VARCHAR
- poi_id: UUID (FK to pois)
- visited_date: TIMESTAMP
- session_id: VARCHAR
```

### PostGIS Functions

- `calculate_distance()` - Compute distance between two coordinates
- `get_nearby_pois()` - Spatial query for nearby POIs
- `check_point_in_state()` - Check if coordinate is within state boundary

## 🔄 Data Flow Examples

### Trip Planning Flow

```
User Input: "Plan 3-day Penang trip"
    ↓
Parser → Destination: Penang, Duration: 3 days, Type: full_trip
    ↓
Recommender → [50 POIs matching preferences]
    ↓
Planner → K-Means clustering → 3 groups → Sequence each day
    ↓
Day 1: George Town → Penang Hill → Street Art
Day 2: Kek Lok Si → Botanical Garden → Temple
Day 3: Beach → Water Sports → Sunset
    ↓
Formatter → Beautiful formatted output with times & distances
    ↓
User Response
```

## 🎯 Request Type Detection Logic

The system classifies requests during input parsing:

| Type                 | Keywords                               | Behavior                             |
| -------------------- | -------------------------------------- | ------------------------------------ |
| `full_trip`        | "plan", "trip", "itinerary", "days"    | Full planning flow with all 4 agents |
| `poi_suggestions`  | "suggest", "recommend", "best places"  | Skip planner, return top 5 POIs      |
| `general_question` | Questions not related to trip planning | Skip agents, LLM answers directly    |

## 🔍 Key Algorithms

### K-Means Geographic Clustering

Clusters POIs geographically to create logical daily routes:

1. Extract coordinates from POIs
2. Run K-Means with k = trip_duration_days
3. Assign each POI to nearest centroid
4. Order clusters to minimize overnight transitions
5. Sequence POIs within each cluster using nearest neighbor

### Nearest Neighbor Sequencing

Optimizes POI visiting order within each day:

1. Start with highest-priority POI
2. Move to nearest unvisited POI
3. Repeat until all POIs visited
4. Calculate total distance and time

### Priority Scoring

Ranks POIs based on multiple factors:

- User preference match (0-30 points)
- Category relevance (0-30 points)
- Historical popularity (0-20 points)
- Visitor ratings (0-20 points)

## 📊 Evaluation & Testing

The system includes comprehensive testing and evaluation:

- **Unit Tests**: Individual agent and tool testing
- **Integration Tests**: Full workflow validation
- **Performance Evaluation**: Response time and accuracy metrics
- **User Testing**: Feedback on itinerary quality

Run evaluation:

```bash
python evaluation/evaluation.py
```

## 🚧 Extending the System

### Adding New POI Categories

1. Update preprocessing: `preprocessing/pois_google_places_enricher.py`
2. Add category keywords to detection logic
3. Re-run: `python preprocessing/upload_pois.py`

### Customizing Trip Parameters

Modify `agents/input_parser.py` to add new parameters:

- Budget constraints
- Mobility requirements
- Group composition preferences

### Changing Clustering Strategy

Update `tools/planner_tools.py`:

- Implement new clustering algorithms
- Set via `clustering_strategy` parameter

## 📚 Documentation

- [LangGraph Migration](LANGGRAPH_MIGRATION.md) - Architecture evolution
- [New Features Guide](NEW_FEATURES_GUIDE.md) - Multi-request-type support
- [Planner Tools](PLANNER_TOOLS_README.md) - Spatial operations reference
- [Multi-Day Implementation](MULTI_DAY_IMPLEMENTATION.md) - Clustering details

## 📝 License

This project is part of a Bachelor in Computer Science capstone project.

## 🙋 Support

For issues, questions, or contributions, please refer to the documentation files or contact the development team.
