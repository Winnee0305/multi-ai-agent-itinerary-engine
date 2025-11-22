from fastapi import FastAPI
from pydantic import BaseModel
from graph.graph import build_graph

app = FastAPI()
workflow = build_graph()

class UserRequest(BaseModel):
    preferences: dict
    pois: list[str]
    location: str

@app.post("/itinerary")
async def run_pipeline(req: UserRequest):
    initial = {
        "preferences": req.preferences,
        "location": req.location,
        "pois": req.pois,
    }

    result = workflow.invoke(initial)
    return result["optimized"]

    # ===== Run in terminal to start local server =====
    ## At langgraph/ directory run:
    # uvicorn api.main:app --reload
    # ===== Access API documentation =====
    # http://127.0.0.1:8000/docs#/default/run_pipeline_itinerary_post


    # ===== If address in use =====
    # lsof -i :8000
    # kill -9 $(lsof -t -i:8000)


# try thi
{
  "preferences": { "interest_type": "architecture" },
  "pois": ["Stadthuys", "Jonker Street"],
  "location": "Melacca"
}
