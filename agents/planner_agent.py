"""
Planner Agent: Selects centroid and builds day-by-day itinerary
"""

from typing import List, Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import settings
from config.prompts import PLANNER_AGENT_SYSTEM_PROMPT
from tools.distance_tools import (
    get_pois_near_location,
    calculate_travel_distance,
    get_poi_distances_from_point,
    calculate_route_total_distance
)


class PlannerAgent:
    """
    Agent that builds day-by-day itinerary using centroid selection and spatial queries
    """
    
    def __init__(self, model_name: str = None):
        self.llm = ChatOpenAI(
            model=model_name or settings.DEFAULT_LLM_MODEL,
            temperature=0.3  # Slightly higher for creative planning
        )
        
        # Define tools
        self.tools = [
            get_pois_near_location,
            calculate_travel_distance,
            get_poi_distances_from_point,
            calculate_route_total_distance
        ]
        
        # Create prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10
        )
    
    def create_itinerary(
        self,
        recommended_pois: List[Dict],
        travel_days: int,
        user_context: Dict = None
    ) -> Dict:
        """
        Create day-by-day itinerary from recommended POIs
        
        Args:
            recommended_pois: POIs sorted by priority score (from RecommenderAgent)
            travel_days: Number of days for the trip
            user_context: Optional additional context
        
        Returns:
            Dictionary with itinerary structure, centroid info, and reasoning
        """
        # Build input for agent
        poi_summary = self._format_pois_for_llm(recommended_pois[:10])
        
        input_text = f"""
        Create a {travel_days}-day itinerary from these recommended POIs:
        
        {poi_summary}
        
        Instructions:
        1. SELECT CENTROID: Choose the best centroid POI from the top 5
           - Consider: high priority score, central location, nearby attractions
           - Explain your choice
        
        2. FIND NEARBY POIS: Use tools to find POIs within 5-10km of centroid
           - Query for nearby POIs using get_pois_near_location
           - Check distances using calculate_travel_distance
        
        3. BUILD DAILY ROUTES: Group POIs into {travel_days} days
           - {settings.MIN_POIS_PER_DAY}-{settings.MAX_POIS_PER_DAY} POIs per day
           - Minimize travel distances (keep nearby POIs together)
           - Avoid backtracking
        
        4. STRUCTURE OUTPUT: For each day provide:
           - Morning/Afternoon/Evening activities
           - Travel distances between POIs
           - Brief justification for grouping
        
        Return a structured itinerary in JSON format.
        """
        
        # Execute agent
        result = self.executor.invoke({"input": input_text})
        
        return {
            "itinerary": result.get("output"),
            "reasoning": result.get("intermediate_steps")
        }
    
    def select_centroid(
        self,
        top_pois: List[Dict],
        consider_top_n: int = 5
    ) -> Tuple[Dict, str]:
        """
        Select the best centroid POI from top recommendations
        
        Args:
            top_pois: POIs sorted by priority
            consider_top_n: Consider top N POIs for centroid selection
        
        Returns:
            Tuple of (centroid_poi, reasoning)
        """
        candidates = top_pois[:consider_top_n]
        
        # Simple heuristic: highest priority POI
        # Can be enhanced with centrality calculations
        centroid = candidates[0]
        
        reasoning = f"""
        Selected '{centroid['name']}' as centroid because:
        - Highest priority score: {centroid.get('priority_score', 0)}
        - Location: {centroid.get('state')}
        - This will serve as the anchor point for finding nearby attractions
        """
        
        return centroid, reasoning
    
    def build_daily_routes(
        self,
        pois: List[Dict],
        travel_days: int,
        centroid: Dict
    ) -> List[Dict]:
        """
        Build day-by-day routes from POI list
        
        Args:
            pois: List of POIs to include
            travel_days: Number of days
            centroid: Centroid POI
        
        Returns:
            List of daily itineraries
        """
        # Calculate distances from centroid
        poi_ids = [poi["id"] for poi in pois]
        distances = get_poi_distances_from_point.invoke({
            "poi_ids": poi_ids,
            "center_lat": centroid["lat"],
            "center_lon": centroid["lon"]
        })
        
        # Sort POIs by distance from centroid
        distance_map = {d["poi_id"]: d["distance_meters"] for d in distances}
        sorted_pois = sorted(pois, key=lambda p: distance_map.get(p["id"], float('inf')))
        
        # Distribute POIs across days
        pois_per_day = max(settings.MIN_POIS_PER_DAY, len(sorted_pois) // travel_days)
        
        daily_routes = []
        for day in range(travel_days):
            start_idx = day * pois_per_day
            end_idx = start_idx + pois_per_day
            day_pois = sorted_pois[start_idx:end_idx]
            
            if day_pois:
                daily_routes.append({
                    "day": day + 1,
                    "pois": day_pois,
                    "total_pois": len(day_pois)
                })
        
        return daily_routes
    
    def _format_pois_for_llm(self, pois: List[Dict]) -> str:
        """Format POIs for LLM consumption"""
        lines = []
        for i, poi in enumerate(pois, 1):
            priority = poi.get('priority_score', 0)
            name = poi.get('name', 'Unknown')
            state = poi.get('state', 'Unknown')
            lat = poi.get('lat', 0)
            lon = poi.get('lon', 0)
            
            lines.append(
                f"{i}. {name}\n"
                f"   Priority: {priority} | State: {state}\n"
                f"   Coordinates: ({lat:.4f}, {lon:.4f})"
            )
        
        return "\n\n".join(lines)
