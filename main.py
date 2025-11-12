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

@app.post("/recommend")
async def recommend(request: UserRequest):
    # 1. Get info for each POI
    info_list = [info_agent.fetch_info(poi, request.location, request.preferences) 
                 for poi in request.pois]
    # 2. Generate recommendations
    rec_list = rec_agent.recommend(info_list, request.preferences)
    # 3. Plan itinerary
    plan = planner_agent.plan(rec_list)
    # 4. Optimize route
    optimized = optimizer_agent.optimize(plan)
    return {"itinerary": optimized}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


# #uvicorn main:app --reload

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

    # test_recommendation()
    #Optionally start the FastAPI server as well
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    # ===== Run in terminal to start local server =====
    # uvicorn main:app --reload
