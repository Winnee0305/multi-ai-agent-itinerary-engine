"""
Recommender Agent: Calculates priority scores and returns top POIs
"""

from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import settings
from config.prompts import RECOMMENDER_AGENT_SYSTEM_PROMPT
from tools.supabase_tools import get_pois_by_filters, search_pois_by_name
from tools.priority_tools import calculate_priority_scores, get_interest_categories


class RecommenderAgent:
    """
    Agent that recommends POIs based on user preferences using priority scoring
    """
    
    def __init__(self, model_name: str = None):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name or settings.DEFAULT_LLM_MODEL,
            temperature=0.2
        )
        
        # Define tools for this agent
        self.tools = [
            get_pois_by_filters,
            search_pois_by_name,
            calculate_priority_scores,
            get_interest_categories
        ]
        
        # Create prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", RECOMMENDER_AGENT_SYSTEM_PROMPT),
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
            max_iterations=5
        )
    
    def recommend(
        self,
        user_context: Dict,
        top_n: int = None
    ) -> Dict:
        """
        Get POI recommendations based on user context
        
        Args:
            user_context: User travel context (from InfoAgent)
            top_n: Number of top POIs to return
        
        Returns:
            Dictionary with recommended_pois and reasoning
        """
        top_n = top_n or settings.TOP_N_RECOMMENDATIONS
        
        # Build input for agent
        input_text = f"""
        Recommend POIs for this travel context:
        
        Destination: {', '.join(user_context.get('destination_states', ['Malaysia']))}
        Duration: {user_context.get('travel_days', 5)} days
        Travelers: {user_context.get('number_of_travelers', 2)} people
        Interests: {', '.join(user_context.get('interests', ['Culture', 'Food']))}
        Preferred POIs: {', '.join(user_context.get('preferred_pois', []) or ['None specified'])}
        
        Steps:
        1. Query POIs from the database for the destination state(s)
        2. Calculate priority scores based on user context
        3. Return top {top_n} POIs with explanations
        
        Focus on POIs that:
        - Match user interests
        - Are appropriate for group size
        - Have good popularity and credibility
        - Include any user-specified preferred POIs
        """
        
        # Execute agent
        result = self.executor.invoke({"input": input_text})
        
        return {
            "recommendations": result.get("output"),
            "agent_steps": result.get("intermediate_steps")
        }
    
    def get_quick_recommendations(
        self,
        state: str,
        interests: List[str],
        travel_days: int = 5,
        travelers: int = 2,
        preferred_pois: List[str] = None,
        top_n: int = 20
    ) -> List[Dict]:
        """
        Direct recommendation without agent orchestration (faster)
        
        Args:
            state: Malaysian state
            interests: User interests
            travel_days: Trip duration
            travelers: Group size
            preferred_pois: Specific POIs to prioritize
            top_n: Number of results
        
        Returns:
            List of recommended POIs sorted by priority
        """
        # Get POIs from database
        pois = get_pois_by_filters.invoke({
            "state": state,
            "min_popularity": settings.MIN_POPULARITY_SCORE,
            "only_golden": True,
            "limit": 100  # Get more to have good selection for scoring
        })
        
        if not pois:
            print(f"No POIs found for state: {state}")
            return []
        
        # Calculate priority scores
        scored_pois = calculate_priority_scores.invoke({
            "pois": pois,
            "user_preferences": interests,
            "number_of_travelers": travelers,
            "travel_days": travel_days,
            "target_state": state,
            "preferred_pois": preferred_pois,
            "verbose": True
        })
        
        # Return top N
        return scored_pois[:top_n]
