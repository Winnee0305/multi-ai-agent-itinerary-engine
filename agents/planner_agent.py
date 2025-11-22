from typing import List, Dict
import os
import json
from google import genai

# Configure the client
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable")

client = genai.Client(api_key=api_key)

class PlannerAgent:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name

    def plan(self, recommendations: List[Dict], location: str) -> List[Dict]:
        top_pois = [rec["poi"] for rec in recommendations[:5]]
        
        prompt = (
            f"Create a half-day itinerary for these POIs in {location}:\n"
            f"{top_pois}\n\n"
            f"Return a JSON object with a single key 'steps', which is a list of objects. "
            f"Each object in the list should have the keys 'poi', 'time', and 'activity'."
        )

        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )

        try:
            # The response might be a JSON string, so we need to parse it.
            plan_data = json.loads(response.text)
            return plan_data
        except (json.JSONDecodeError, TypeError):
            # Handle cases where the response is not valid JSON or not a string
            return {"error": "Failed to generate a valid plan.", "raw_response": response.text}

