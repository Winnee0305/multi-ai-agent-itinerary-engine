"""
Info Agent: Extracts and structures user travel preferences
"""

from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from config.settings import settings
from config.prompts import INFO_AGENT_SYSTEM_PROMPT


class UserContext(BaseModel):
    """Structured user travel context"""
    destination_states: List[str] = Field(description="Malaysian states to visit")
    travel_days: int = Field(default=5, description="Trip duration in days")
    number_of_travelers: int = Field(default=2, description="Group size")
    interests: List[str] = Field(default=["Culture", "Food", "Nature"], description="User interests")
    preferred_pois: Optional[List[str]] = Field(default=None, description="Specific POIs mentioned")
    budget_level: Optional[str] = Field(default="medium", description="Budget: low/medium/high")
    travel_pace: Optional[str] = Field(default="moderate", description="Pace: relaxed/moderate/packed")
    constraints: Optional[List[str]] = Field(default=None, description="Special requirements or constraints")


class InfoAgent:
    """
    Agent that extracts structured travel information from user queries
    """
    
    def __init__(self, model_name: str = None):
        self.llm = ChatOpenAI(
            model=model_name or settings.DEFAULT_LLM_MODEL,
            temperature=0.1  # Low temperature for structured extraction
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=UserContext)
        
        # Create prompt with output format instructions
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INFO_AGENT_SYSTEM_PROMPT + "\n\n{format_instructions}"),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
        ])
    
    def extract_context(self, user_input: str, chat_history: List = None) -> UserContext:
        """
        Extract structured user context from natural language input
        
        Args:
            user_input: User's travel query
            chat_history: Optional conversation history
        
        Returns:
            UserContext object with extracted information
        """
        # Format the prompt with output instructions
        formatted_prompt = self.prompt.format_messages(
            format_instructions=self.output_parser.get_format_instructions(),
            input=user_input,
            chat_history=chat_history or []
        )
        
        # Get LLM response
        response = self.llm.invoke(formatted_prompt)
        
        # Parse into structured format
        try:
            context = self.output_parser.parse(response.content)
            return context
        except Exception as e:
            print(f"Error parsing user context: {e}")
            print(f"Raw response: {response.content}")
            # Return default context
            return UserContext(
                destination_states=["Penang"],
                travel_days=5,
                number_of_travelers=2,
                interests=["Culture", "Food", "Nature"]
            )
    
    def refine_context(
        self, 
        current_context: UserContext, 
        additional_input: str
    ) -> UserContext:
        """
        Refine existing context with additional user input
        
        Args:
            current_context: Current UserContext
            additional_input: New information from user
        
        Returns:
            Updated UserContext
        """
        # Create refinement prompt
        refinement_prompt = f"""
        Current travel context:
        {current_context.model_dump_json(indent=2)}
        
        User provided additional information:
        {additional_input}
        
        Update the context with the new information. Keep existing values unless explicitly changed.
        """
        
        return self.extract_context(refinement_prompt)
    
    def validate_context(self, context: UserContext) -> Dict[str, List[str]]:
        """
        Validate user context and return any warnings or missing information
        
        Args:
            context: UserContext to validate
        
        Returns:
            Dictionary with 'warnings' and 'missing' lists
        """
        warnings = []
        missing = []
        
        # Check for potential issues
        if context.travel_days > 14:
            warnings.append("Trip duration is quite long (>14 days). Consider breaking into multiple trips.")
        
        if context.number_of_travelers > 10:
            warnings.append("Large group (>10 people) may have difficulty at some venues.")
        
        if not context.destination_states:
            missing.append("No destination states specified")
        
        if context.travel_days < 1:
            warnings.append("Trip duration must be at least 1 day")
        
        return {
            "warnings": warnings,
            "missing": missing
        }
