# Setup Guide

## Step-by-Step Implementation Guide

### Phase 1: Environment Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Create .env File

Create `.env` in the project root:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SERVICE_ROLE_KEY=your-service-role-key

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key
DEFAULT_LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.2

# Optional: Google Places API (for real-time enrichment)
GOOGLE_PLACES_API_KEY=your-google-places-key

# Optional: LangSmith (for debugging/tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=itinerary-planner
```

### Phase 2: Database Setup

#### 1. Create Supabase Project

- Go to https://supabase.com
- Create new project
- Copy URL and Service Role Key to `.env`

#### 2. Enable PostGIS Extension

In Supabase SQL Editor, run:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

#### 3. Create Database Schema

Run `database/schema.sql` in Supabase SQL Editor

This creates:

- `osm_pois` table with all enriched fields
- PostGIS geography column for spatial queries
- Indexes for performance
- Helper functions and views

#### 4. Create RPC Functions

Run `database/rpc_functions.sql` in Supabase SQL Editor

This creates:

- `get_nearby_pois()` - Find POIs within radius
- `calculate_distance()` - Calculate distances
- `get_pois_with_distances()` - Batch distance calculations

#### 5. Upload POI Data

```bash
python database/seed_data.py
```

This uploads POIs from `data/malaysia_all_pois_google_enriched.json`

**Expected output:**

```
📂 Loading POIs from: data/malaysia_all_pois_google_enriched.json
✅ Loaded 1234 POIs
================================================================================
UPLOADING 1234 POIs TO SUPABASE
================================================================================
[1/3] Uploading 500 POIs...
  ✅ Batch 1 uploaded successfully
...
✅ All POIs uploaded successfully!
```

### Phase 3: Test Each Component

#### Test 1: Configuration

```python
from config.settings import settings, validate_settings

validate_settings()
print(f"✅ Supabase URL: {settings.SUPABASE_URL}")
print(f"✅ LLM Model: {settings.DEFAULT_LLM_MODEL}")
```

#### Test 2: Database Connection

```python
from database.supabase_client import get_supabase

supabase = get_supabase()
result = supabase.table("osm_pois").select("name, state").limit(5).execute()
print(f"✅ Found {len(result.data)} POIs")
for poi in result.data:
    print(f"  - {poi['name']} ({poi['state']})")
```

#### Test 3: Supabase Tools

```python
from tools.supabase_tools import get_pois_by_filters

pois = get_pois_by_filters.invoke({
    "state": "Penang",
    "min_popularity": 70,
    "only_golden": True,
    "limit": 10
})

print(f"✅ Found {len(pois)} POIs in Penang")
for poi in pois[:3]:
    print(f"  - {poi['name']} (Score: {poi['popularity_score']})")
```

#### Test 4: Distance Tools

```python
from tools.distance_tools import calculate_travel_distance

# Distance between two POIs in Penang
distance = calculate_travel_distance.invoke({
    "from_lat": 5.4164,
    "from_lon": 100.3327,
    "to_lat": 5.3547,
    "to_lon": 100.3020
})

print(f"✅ Distance: {distance:.2f} meters ({distance/1000:.2f} km)")
```

#### Test 5: Priority Scoring

```python
from tools.priority_tools import calculate_priority_scores
from tools.supabase_tools import get_pois_by_filters

# Get some POIs
pois = get_pois_by_filters.invoke({
    "state": "Penang",
    "limit": 20
})

# Calculate priority scores
scored_pois = calculate_priority_scores.invoke({
    "pois": pois,
    "user_preferences": ["Culture", "Art", "Food"],
    "number_of_travelers": 4,
    "travel_days": 5,
    "verbose": True
})

print(f"✅ Scored {len(scored_pois)} POIs")
for poi in scored_pois[:3]:
    print(f"  - {poi['name']}: Priority {poi['priority_score']}")
```

#### Test 6: Info Agent

```python
from agents.info_agent import InfoAgent

agent = InfoAgent()
context = agent.extract_context(
    "I want to visit Penang for 5 days with my family of 4. We love art and food."
)

print(f"✅ Extracted context:")
print(f"  - States: {context.destination_states}")
print(f"  - Days: {context.travel_days}")
print(f"  - Travelers: {context.number_of_travelers}")
print(f"  - Interests: {context.interests}")
```

#### Test 7: Recommender Agent

```python
from agents.recommender_agent import RecommenderAgent

agent = RecommenderAgent()
recommendations = agent.get_quick_recommendations(
    state="Penang",
    interests=["Culture", "Art", "Food"],
    travel_days=5,
    travelers=4,
    top_n=10
)

print(f"✅ Got {len(recommendations)} recommendations")
for poi in recommendations[:5]:
    print(f"  - {poi['name']}: {poi['priority_score']}")
```

### Phase 4: Run Full Pipeline

#### Run Main Script

```bash
python main.py
```

**Expected output:**

```
================================================================================
🔍 STEP 1: EXTRACTING USER PREFERENCES
================================================================================
✅ User Context Extracted (2.34s):
  • Destination: Penang
  • Duration: 5 days
  • Travelers: 4 people
  • Interests: Art, Culture, Food

================================================================================
🎯 STEP 2: GETTING POI RECOMMENDATIONS
================================================================================
✅ Found 20 Recommended POIs (1.56s)

Top 5 POIs:
  1. Penang Street Art - Priority: 156.5
  2. Khoo Kongsi - Priority: 145.2
  ...

================================================================================
📅 STEP 3: CREATING ITINERARY PLAN
================================================================================
✅ Itinerary Created (3.12s)

📍 Centroid: Penang Street Art
   Selected 'Penang Street Art' as centroid because:
   - Highest priority score: 156.5
   ...

📅 5 Days Planned:
   Day 1: 4 POIs
   Day 2: 4 POIs
   ...

================================================================================
⚡ STEP 4: OPTIMIZING ROUTES
================================================================================
✅ Optimization Complete (2.45s)
✅ No validation issues found!

================================================================================
✅ ITINERARY GENERATION COMPLETE!
================================================================================

📊 Execution Summary:
   • Total steps: 4
   • Total time: 9.47s
   • POIs recommended: 20
   • Days planned: 5

💾 Full itinerary saved to: generated_itinerary.json
```

### Phase 5: Troubleshooting

#### Common Issues

**1. Import errors for langchain**

```bash
pip install --upgrade langchain langchain-openai langchain-community
```

**2. Supabase connection error**

Check `.env` file has correct credentials:

```python
from config.settings import settings
print(settings.SUPABASE_URL)
print(settings.SERVICE_ROLE_KEY[:10] + "...")
```

**3. No POIs found**

Verify data upload:

```python
from database.supabase_client import get_supabase
supabase = get_supabase()
count = supabase.table("osm_pois").select("id", count="exact").execute()
print(f"Total POIs: {count.count}")
```

**4. OpenAI API errors**

Check API key:

```python
from config.settings import settings
print(f"API Key: {settings.OPENAI_API_KEY[:10]}...")
```

**5. PostGIS functions not found**

Re-run `database/rpc_functions.sql` in Supabase SQL Editor

### Phase 6: Customization

#### Change LLM Model

In `.env`:

```env
DEFAULT_LLM_MODEL=gpt-3.5-turbo  # Faster, cheaper
# or
DEFAULT_LLM_MODEL=gpt-4o         # Better quality
```

#### Adjust Scoring Weights

Edit `preprocessing/pois_priority_scorer.py`:

```python
# Line 108: Interest boost
INTEREST_MULTIPLIER = 1.5  # Change to 2.0 for stronger boost

# Line 143: Group safety penalty
SAFETY_PENALTY = 0.8  # Change to 0.7 for stronger penalty
```

#### Modify Daily POI Limits

In `config/settings.py`:

```python
MAX_POIS_PER_DAY: int = 6  # Change to 8 for more packed days
MIN_POIS_PER_DAY: int = 3  # Change to 4 for minimum
```

## Next Steps

1. ✅ Set up Supabase database
2. ✅ Upload POI data
3. ✅ Test individual components
4. ✅ Run full pipeline
5. 🔄 Customize for your needs
6. 🚀 Build web interface (optional)
7. 📊 Add analytics and logging
8. 🌐 Deploy to production
