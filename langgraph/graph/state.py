from typing import List, Dict, Optional
from pydantic import BaseModel

class TravelState(BaseModel):
    preferences: Dict
    location: str
    pois: List[str]

    info_results: Optional[List[Dict]] = None
    recommendations: Optional[List[Dict]] = None
    plan: Optional[Dict] = None
    optimized: Optional[Dict] = None
