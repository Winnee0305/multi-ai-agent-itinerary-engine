from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()
# print("API KEY: ", os.getenv("GEMINI_API_KEY"))

from agents.info_agent import InfoAgent
from agents.recommender_agent import RecommenderAgent
from agents.planner_agent import PlannerAgent
from agents.optimizer_agent import OptimizerAgent

app = FastAPI()

info_agent = InfoAgent()
rec_agent = RecommenderAgent()
planner_agent = PlannerAgent()
optimizer_agent = OptimizerAgent()

class UserRequest(BaseModel):
    preferences: Dict
    pois: List[str]        # list of POI names
    location: str

@app.post("/getDescription")
async def describe(request: UserRequest):
    desc = info_agent.fetch_single_poi_info(request.pois[0])
    return desc["description"]

def test_recommendation():
    # Example test data
    test_request = UserRequest(
        preferences={"interest_type": "architecture"},
        pois=["stadthuys"],
        location="melacca"
    )

    # 1. Get info for each POI
    info_list = [info_agent.fetch_info(poi, test_request.location, test_request.preferences)
                 for poi in test_request.pois]
    print("InfoAgent results:")
    for info in info_list:
        print(info["description"])
        print("-" * 50)

    # 2. Generate recommendations
    rec_list = rec_agent.recommend(info_list, test_request.preferences)
    print("RecommenderAgent results:", rec_list)

    # 3. Plan itinerary
    plan = planner_agent.plan(rec_list)
    print("PlannerAgent results:", plan)

    # 4. Optimize route
    optimized = optimizer_agent.optimize(plan)
    print("OptimizerAgent results:", optimized)


# Run test when file is executed directly
if __name__ == "__main__":

    test_recommendation()
    #Optionally start the FastAPI server as well
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    # ===== Run in terminal to start local server =====
    # uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    # ===== Access API documentation =====
    # http://127.0.0.1:8000/docs#/default/describe_getDescription_post


