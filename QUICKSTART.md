# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment (1 min)

Create `.env` file in project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SERVICE_ROLE_KEY=your-service-role-key-here
OPENAI_API_KEY=sk-your-openai-api-key-here
DEFAULT_LLM_MODEL=gpt-4o
```

### Step 3: Set Up Supabase Database (2 mins)

1. Go to your Supabase project → SQL Editor
2. Copy and run `database/schema.sql` (creates tables)
3. Copy and run `database/rpc_functions.sql` (creates PostGIS functions)

### Step 4: Upload POI Data (1 min)

```bash
python database/seed_data.py
```

Expected output:

```
✅ Loaded 1234 POIs
[1/3] Uploading 500 POIs...
  ✅ Batch 1 uploaded successfully
...
✅ All POIs uploaded successfully!
```

### Step 5: Run the System! (30 sec)

```bash
python main.py
```

You should see:

```
🚀 Initializing Multi-Agent Itinerary Planner...
================================================================================
🔍 STEP 1: EXTRACTING USER PREFERENCES
================================================================================
✅ User Context Extracted (2.34s):
  • Destination: Penang
  • Duration: 5 days
  • Travelers: 4 people
  • Interests: Art, Culture, Food
...
================================================================================
✅ ITINERARY GENERATION COMPLETE!
================================================================================
💾 Full itinerary saved to: generated_itinerary.json
```

## 🧪 Quick Test

Test individual components:

### Test Database Connection

```python
python -c "from database import get_supabase; s = get_supabase(); print('✅ Connected to Supabase')"
```

### Test Priority Scoring

```python
from tools.priority_tools import calculate_priority_scores
from tools.supabase_tools import get_pois_by_filters

pois = get_pois_by_filters.invoke({"state": "Penang", "limit": 10})
scored = calculate_priority_scores.invoke({
    "pois": pois,
    "user_preferences": ["Culture", "Food"],
    "number_of_travelers": 2,
    "travel_days": 5
})

print(f"✅ Scored {len(scored)} POIs")
for poi in scored[:3]:
    print(f"  - {poi['name']}: {poi['priority_score']}")
```

### Test Full Orchestrator

```python
from orchestrator import ItineraryOrchestrator

orchestrator = ItineraryOrchestrator()
result = orchestrator.generate_itinerary(
    "Plan a 3-day trip to Penang. I love food and culture.",
    verbose=True
)

print(result["itinerary"]["centroid"]["name"])
```

## 📚 Learn More

- **Full Setup Guide**: See `SETUP_GUIDE.md`
- **Architecture Details**: See `README.md`
- **Code Changes**: See `REFACTORING_SUMMARY.md`

## 🆘 Getting Help

### Common Issues

**Import Errors**

```bash
pip install --upgrade langchain langchain-openai pydantic supabase
```

**No POIs Found**

- Check if data upload completed successfully
- Verify table exists: Check Supabase dashboard → Table Editor

**OpenAI Errors**

- Verify API key in `.env`
- Check billing: https://platform.openai.com/account/billing

**PostGIS Errors**

- Re-run `database/rpc_functions.sql`
- Enable PostGIS: `CREATE EXTENSION IF NOT EXISTS postgis;`

### Test Checklist

- [ ] Dependencies installed
- [ ] `.env` file created with all keys
- [ ] Database schema created
- [ ] RPC functions created
- [ ] POI data uploaded (check Supabase dashboard)
- [ ] Can import modules: `from agents import InfoAgent`
- [ ] Main script runs: `python main.py`

## 🎯 What You Can Do Now

### 1. Customize Queries

```python
orchestrator = ItineraryOrchestrator()

# Different destinations
result = orchestrator.generate_itinerary("5 days in Malacca for history lovers")

# Different group sizes
result = orchestrator.generate_itinerary("Solo trip to Kuala Lumpur, 3 days, love art")

# Specific POIs
result = orchestrator.generate_itinerary(
    "Family trip to Penang. Must visit Penang Street Art and Khoo Kongsi. 4 people, 5 days."
)
```

### 2. Access Individual Agents

```python
from agents import InfoAgent, RecommenderAgent

# Extract context only
info_agent = InfoAgent()
context = info_agent.extract_context("Weekend trip to Penang")
print(context.destination_states)
print(context.travel_days)

# Get recommendations only
recommender = RecommenderAgent()
pois = recommender.get_quick_recommendations(
    state="Penang",
    interests=["Food", "Culture"],
    travel_days=3,
    travelers=2
)
print(f"Found {len(pois)} recommendations")
```

### 3. Modify Scoring

Edit `preprocessing/pois_priority_scorer.py`:

```python
# Line 108 - Boost interest matches more
INTEREST_MULTIPLIER = 2.0  # Was 1.5

# Line 143 - Stronger safety penalty
SAFETY_PENALTY = 0.7  # Was 0.8

# Line 173 - Bigger landmark boost
LANDMARK_MULTIPLIER = 1.5  # Was 1.2
```

Then re-run:

```bash
python main.py
```

## 🎉 You're Ready!

The system is now set up and ready to generate itineraries. Start experimenting with different queries!

For detailed customization and advanced features, see `SETUP_GUIDE.md`.
