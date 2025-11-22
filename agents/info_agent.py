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
        """Fetches detailed POI info including location and user preferences."""
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

    def fetch_single_poi_info(self, poi_name: str) -> dict:
        """Fetches a short, standalone description for a single POI name."""
        prompt = (
            f"You are a travel guide AI. Write a brief, engaging 60–80 word description "
            f"about \"{poi_name}\" suitable for a travel mobile app. Describe what it is, "
            f"why it’s notable, and what visitors can experience. Keep it natural, factual, "
            f"and formatted as plain text (no lists, bullets, or headings)."
        )
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return {
            "poi": poi_name,
            "description": response.text
        }

    def discover_pois(self, location: str, preferences: dict = None) -> list[str]:
        """Discovers POIs based on location and preferences."""
        prompt = f"List the top 5-7 points of interest in {location}."
        if preferences:
            interest = preferences.get("interest_type")
            if interest:
                prompt += f" focusing on {interest}"
        prompt += " Return a comma-separated list of the names only."

        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        
        # Assuming the response is a comma-separated string of POI names
        poi_names = [poi.strip() for poi in response.text.split(',')]
        return poi_names

    def _make_prompt(self, poi_name: str, location: str, preferences: dict = None) -> str:
        """Prompt builder for detailed contextual info."""
        base = (
            f"You are a travel guide AI. Provide a concise and engaging description of "
            f"the point of interest \"{poi_name}\" located in {location}. Write a short "
            f"(50–80 words) description for this place to be displayed on a POI card. "
            f"Include key highlights, historical facts, and unique features. "
            f"The output should be in plain text format, without any bullet points or lists."
        )

        if preferences:
            interest = preferences.get("interest_type", "general")
            base += f" Focus on aspects that appeal to users interested in {interest}."

        base += " Make it sound natural and informative."
        return base
