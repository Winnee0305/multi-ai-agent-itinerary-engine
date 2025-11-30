"""
Optimizer Agent: Optimizes routes and validates feasibility
"""

from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import settings
from config.prompts import OPTIMIZER_AGENT_SYSTEM_PROMPT
from tools.distance_tools import calculate_route_total_distance, calculate_travel_distance


class OptimizerAgent:
    """
    Agent that optimizes itinerary routes and validates feasibility
    """
    
    def __init__(self, model_name: str = None):
        self.llm = ChatOpenAI(
            model=model_name or settings.DEFAULT_LLM_MODEL,
            temperature=0.1  # Low temperature for optimization
        )
        
        # Define tools
        self.tools = [
            calculate_route_total_distance,
            calculate_travel_distance
        ]
        
        # Create prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZER_AGENT_SYSTEM_PROMPT),
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
            max_iterations=8
        )
    
    def optimize(
        self,
        draft_itinerary: Dict,
        user_context: Dict = None
    ) -> Dict:
        """
        Optimize draft itinerary for better route efficiency
        
        Args:
            draft_itinerary: Itinerary from PlannerAgent
            user_context: Optional user preferences
        
        Returns:
            Optimized itinerary with validation results
        """
        # Build input for agent
        input_text = f"""
        Optimize this draft itinerary:
        
        {self._format_itinerary_for_llm(draft_itinerary)}
        
        Tasks:
        1. VALIDATE FEASIBILITY:
           - Check total daily travel distances (should be < {settings.MAX_DAILY_TRAVEL_DISTANCE_KM}km)
           - Identify any excessive backtracking
           - Flag unrealistic time requirements
        
        2. OPTIMIZE ROUTES:
           - Reorder POIs within each day to minimize travel distance
           - Move POIs between days if needed for better flow
           - Ensure logical sequencing (e.g., morning temple, afternoon museum, evening food)
        
        3. PROVIDE IMPROVEMENTS:
           - List all optimizations made
           - Calculate distance savings
           - Explain routing decisions
        
        Return optimized itinerary with validation report.
        """
        
        # Execute agent
        result = self.executor.invoke({"input": input_text})
        
        return {
            "optimized_itinerary": result.get("output"),
            "optimization_steps": result.get("intermediate_steps")
        }
    
    def validate_daily_route(self, day_pois: List[Dict]) -> Dict:
        """
        Validate a single day's route
        
        Args:
            day_pois: List of POIs for one day in visit order
        
        Returns:
            Validation results with warnings and total distance
        """
        if len(day_pois) < 2:
            return {
                "valid": True,
                "total_distance_km": 0,
                "warnings": []
            }
        
        # Calculate total route distance
        poi_ids = [poi["id"] for poi in day_pois]
        route_info = calculate_route_total_distance.invoke({"poi_ids": poi_ids})
        
        total_km = route_info["total_distance_km"]
        warnings = []
        
        # Check distance constraints
        if total_km > settings.MAX_DAILY_TRAVEL_DISTANCE_KM:
            warnings.append(
                f"Total daily travel ({total_km}km) exceeds recommended maximum "
                f"({settings.MAX_DAILY_TRAVEL_DISTANCE_KM}km)"
            )
        
        # Check POI count
        if len(day_pois) > settings.MAX_POIS_PER_DAY:
            warnings.append(
                f"Too many POIs ({len(day_pois)}) for one day. "
                f"Recommended: {settings.MIN_POIS_PER_DAY}-{settings.MAX_POIS_PER_DAY}"
            )
        
        if len(day_pois) < settings.MIN_POIS_PER_DAY:
            warnings.append(
                f"Very few POIs ({len(day_pois)}) for one day. "
                f"Consider adding more attractions."
            )
        
        # Check for very long individual segments
        for segment in route_info["segments"]:
            if segment["distance_km"] > 20:
                warnings.append(
                    f"Long distance between {segment['from']} and {segment['to']} "
                    f"({segment['distance_km']}km)"
                )
        
        return {
            "valid": len(warnings) == 0,
            "total_distance_km": total_km,
            "warnings": warnings,
            "route_details": route_info["segments"]
        }
    
    def optimize_poi_order(self, pois: List[Dict]) -> List[Dict]:
        """
        Optimize POI visit order using nearest-neighbor heuristic
        
        Args:
            pois: List of POIs to reorder
        
        Returns:
            Reordered POI list with shorter total route
        """
        if len(pois) <= 2:
            return pois
        
        # Start with first POI (usually highest priority)
        optimized = [pois[0]]
        remaining = pois[1:].copy()
        
        # Nearest neighbor algorithm
        while remaining:
            current_poi = optimized[-1]
            
            # Find nearest POI
            nearest = None
            min_distance = float('inf')
            
            for poi in remaining:
                distance = calculate_travel_distance.invoke({
                    "from_lat": current_poi["lat"],
                    "from_lon": current_poi["lon"],
                    "to_lat": poi["lat"],
                    "to_lon": poi["lon"]
                })
                
                if distance < min_distance:
                    min_distance = distance
                    nearest = poi
            
            optimized.append(nearest)
            remaining.remove(nearest)
        
        return optimized
    
    def _format_itinerary_for_llm(self, itinerary: Dict) -> str:
        """Format itinerary for LLM consumption"""
        # This will depend on the structure returned by PlannerAgent
        # For now, a simple string representation
        return str(itinerary)
