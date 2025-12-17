"""
Input Parser Node - Extracts structured trip context from natural language

This node uses the LLM to parse user requests and extract:
- Destination state
- User preferences/interests
- Number of travelers
- Trip duration
- Specific POI requests
- Number of POIs to recommend
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from agents.state import TripPlannerState


class TripContext(BaseModel):
    """Structured trip context extracted from natural language"""
    destination_state: str = Field(
        description="Malaysian state (e.g., 'Penang', 'Kuala Lumpur', 'Malacca', 'Pahang')"
    )
    user_preferences: list[str] = Field(
        default=["Culture", "Food", "Nature"],
        description="User interests from: Art, Culture, Adventure, Nature, Food, Shopping, History, Religion, Entertainment, Relaxation"
    )
    num_travelers: int = Field(
        default=2,
        description="Number of travelers in the group"
    )
    trip_duration_days: int = Field(
        default=3,
        description="Number of days for the trip"
    )
    preferred_pois: list[str] | None = Field(
        default=None,
        description="Specific POI names the user wants to visit (optional)"
    )
    num_pois: int = Field(
        default=50,
        description="Number of POI recommendations to generate"
    )
    request_type: str = Field(
        default="full_trip",
        description="Type of request: 'full_trip', 'poi_suggestions', or 'general_question'"
    )


def create_input_parser_node(model):
    """
    Create the input parser node function.
    
    Args:
        model: LangChain chat model (e.g., ChatGoogleGenerativeAI)
    
    Returns:
        Node function that parses user input into structured trip context
    """
    
    parser = JsonOutputParser(pydantic_object=TripContext)
    
    def parse_input_node(state: TripPlannerState) -> Dict[str, Any]:
        """
        Parse natural language user request into structured trip context.
        
        Args:
            state: Current graph state with messages
            
        Returns:
            Dictionary with extracted trip context and next_step
        """
        
        # Get the latest user message
        user_message = None
        for msg in reversed(state["messages"]):
            if msg.type == "human":
                user_message = msg
                break
        
        if not user_message:
            return {
                "next_step": "error",
                "error_message": "No user message found in conversation"
            }
        
        # Create parsing prompt (use HumanMessage instead of SystemMessage for Gemini)
        parsing_prompt = f"""You are a travel planning assistant for Malaysia tourism.

Extract structured information from the user's request and return ONLY valid JSON.

{parser.get_format_instructions()}

IMPORTANT: Detect the request type:
- 'full_trip': User is planning a multi-day trip (mentions duration, destination)
- 'poi_suggestions': User just wants POI suggestions/recommendations (no trip duration)
- 'general_question': User asks about culture, history, etc. NOT trip planning

Guidelines:
1. For destination_state, use the official Malaysian state name (e.g., "Penang", "Kuala Lumpur", "Malacca")
2. For user_preferences, choose from: Art, Culture, Adventure, Nature, Food, Shopping, History, Religion, Entertainment, Relaxation
3. For request_type:
   - If "plan", "trip", "itinerary", "days", or duration mentioned → 'full_trip'
   - If "suggest", "recommend", "what to visit", "best places" → 'poi_suggestions'
   - If asking about culture, history, food culture, etc. without trip context → 'general_question'
4. If information is missing, use defaults:
   - num_travelers: 2
   - trip_duration_days: 3 (but set to 1 for poi_suggestions)
   - user_preferences: ["Culture", "Food", "Nature"]
   - num_pois: 50 (but set to 5 for poi_suggestions)
5. Extract specific POI names if mentioned

User request: {user_message.content}

Return ONLY the JSON object, no other text."""
        
        try:
            # Invoke LLM to parse (use HumanMessage for Gemini compatibility)
            response = model.invoke([HumanMessage(content=parsing_prompt)])
            parsed_dict = parser.parse(response.content)
            
            # Convert dict to TripContext for attribute access
            parsed_context = TripContext(**parsed_dict)
            
            # Handle different request types
            request_type = parsed_context.request_type
            
            # If it's a general question, skip the planning flow
            if request_type == "general_question":
                # Use LLM to answer general questions
                general_answer_prompt = f"""You are a helpful travel information assistant for Malaysia.
Answer the user's question about Malaysian culture, history, food, customs, etc.
Be friendly, informative, and relevant to Malaysia tourism.

User question: {user_message.content}

Provide a helpful, conversational answer."""
                
                general_response = model.invoke([HumanMessage(content=general_answer_prompt)])
                return {
                    "messages": [AIMessage(content=general_response.content)],
                    "next_step": "complete"  # Skip planning, go straight to complete
                }
            
            # For POI suggestions, limit to 5 POIs
            if request_type == "poi_suggestions":
                parsed_context.num_pois = 5
                parsed_context.trip_duration_days = 1
            
            # Create confirmation message
            preferences_str = ", ".join(parsed_context.user_preferences)
            
            if request_type == "poi_suggestions":
                confirmation = f"Finding the best {parsed_context.num_pois} POIs in {parsed_context.destination_state} for you. Interests: {preferences_str}."
            else:
                confirmation = f"Planning a {parsed_context.trip_duration_days}-day trip to {parsed_context.destination_state} for {parsed_context.num_travelers} traveler(s). Interests: {preferences_str}."
            
            if parsed_context.preferred_pois:
                confirmation += f" Must-visit POIs: {', '.join(parsed_context.preferred_pois)}."
            
            # Return state updates
            return {
                "messages": [AIMessage(content=confirmation)],
                "destination_state": parsed_context.destination_state,
                "user_preferences": parsed_context.user_preferences,
                "num_travelers": parsed_context.num_travelers,
                "trip_duration_days": parsed_context.trip_duration_days,
                "preferred_pois": parsed_context.preferred_pois,
                "num_pois": parsed_context.num_pois,
                "request_type": request_type,
                "next_step": "recommend"
            }
            
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Sorry, I couldn't understand your request. Error: {str(e)}")],
                "next_step": "error",
                "error_message": f"Failed to parse input: {str(e)}"
            }
    
    return parse_input_node
