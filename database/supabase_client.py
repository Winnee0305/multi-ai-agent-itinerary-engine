"""
Supabase client singleton for database connections
"""

from supabase import create_client, Client
from config.settings import settings


class SupabaseClient:
    """Singleton Supabase client"""
    
    _instance: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance"""
        if cls._instance is None:
            if not settings.SUPABASE_URL or not settings.SERVICE_ROLE_KEY:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Please set SUPABASE_URL and SERVICE_ROLE_KEY in .env file"
                )
            
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SERVICE_ROLE_KEY
            )
        
        return cls._instance


# Convenience function for direct access
def get_supabase() -> Client:
    """Get Supabase client instance"""
    return SupabaseClient.get_client()
