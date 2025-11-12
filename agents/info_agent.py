# old import (causing error)
# from google import genai

# new correct import:
from google import genai
from google.genai import types

import os

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable")

client = genai.Client(api_key=api_key)

class InfoAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    def fetch_info(self, poi_name: str, location: str, preferences: dict = None) -> dict:
        prompt = self._make_prompt(poi_name, location, preferences)
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return {
            "poi": poi_name,
            "location": location,
            "description": response.text
        }

    def _make_prompt(self, poi_name: str, location: str, preferences: dict = None) -> str:
        # Updated prompt engineering
        base = (
            f"You are a travel guide AI. Provide a concise and engaging description of "
            f"the point of interest \"{poi_name}\" located in {location}. Write a short "
            f"(50-80 words) description for this place to be displayed on a poi card. "
            f"Include key highlights, historical facts, and unique features."
            f"The output should be in string text format, without any bullet points, lists or other formatting."
        )

        if preferences:
            interest = preferences.get("interest_type", "general")
            base += f" Focus on aspects that appeal to users interested in {interest}."

        base += " Make it sound natural and informative."

        return base
