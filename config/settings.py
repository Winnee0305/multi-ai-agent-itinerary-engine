"""
Centralized configuration for the multi-agent itinerary system
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SERVICE_ROLE_KEY: str = os.getenv("SERVICE_ROLE_KEY", "")
    
    # OpenAI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gemini-2.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    
    # Google Places API (optional for real-time enrichment)
    GOOGLE_PLACES_API_KEY: Optional[str] = os.getenv("GOOGLE_PLACES_API_KEY")
    
    # LangSmith (optional for tracing)
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "itinerary-planner")
    
    # Application Defaults
    DEFAULT_TRAVEL_DAYS: int = 5
    DEFAULT_TRAVELERS: int = 2
    MAX_POIS_PER_DAY: int = 6
    MIN_POIS_PER_DAY: int = 3
    MAX_DAILY_TRAVEL_DISTANCE_KM: float = 50.0
    
    # POI Filtering
    MIN_POPULARITY_SCORE: int = 70
    TOP_N_RECOMMENDATIONS: int = 20
    
    # Distance Calculations
    DEFAULT_SEARCH_RADIUS_METERS: int = 5000
    MAX_SEARCH_RADIUS_METERS: int = 20000
    
    # Data Paths
    DATA_DIR: str = "data"
    POI_DATA_FILE: str = "malaysia_all_pois_google_enriched.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()


def validate_settings():
    """Validate that required settings are configured"""
    errors = []
    
    if not settings.SUPABASE_URL:
        errors.append("SUPABASE_URL not configured")
    
    if not settings.SERVICE_ROLE_KEY:
        errors.append("SERVICE_ROLE_KEY not configured")
    
    if not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not configured")
    
    if errors:
        raise ValueError(f"Missing required configuration: {', '.join(errors)}")
    
    return True