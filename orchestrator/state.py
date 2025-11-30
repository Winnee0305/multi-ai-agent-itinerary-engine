"""
Shared state management for multi-agent orchestration
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ItineraryState(BaseModel):
    """
    Shared state that flows through the multi-agent pipeline
    """
    
    # Original user input
    user_query: str = Field(description="Original user query")
    
    # Info Agent output
    user_context: Optional[Dict] = Field(default=None, description="Extracted user context")
    
    # Recommender Agent output
    recommended_pois: Optional[List[Dict]] = Field(default=None, description="Recommended POIs with priority scores")
    recommendation_count: int = Field(default=0, description="Number of POIs recommended")
    
    # Planner Agent output
    centroid_poi: Optional[Dict] = Field(default=None, description="Selected centroid POI")
    centroid_reasoning: Optional[str] = Field(default=None, description="Centroid selection reasoning")
    draft_itinerary: Optional[Dict] = Field(default=None, description="Draft day-by-day itinerary")
    
    # Optimizer Agent output
    final_itinerary: Optional[Dict] = Field(default=None, description="Optimized final itinerary")
    optimization_report: Optional[Dict] = Field(default=None, description="Optimization changes and validation")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    current_step: str = Field(default="info", description="Current pipeline step")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    
    class Config:
        arbitrary_types_allowed = True


class AgentStep(BaseModel):
    """
    Record of a single agent's execution
    """
    agent_name: str
    input_data: Dict
    output_data: Dict
    execution_time_seconds: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PipelineHistory(BaseModel):
    """
    Complete history of the multi-agent pipeline execution
    """
    state: ItineraryState
    steps: List[AgentStep] = Field(default_factory=list)
    total_execution_time: float = 0.0
    
    def add_step(self, step: AgentStep):
        """Add an agent execution step to history"""
        self.steps.append(step)
        self.total_execution_time += step.execution_time_seconds
    
    def get_step_by_agent(self, agent_name: str) -> Optional[AgentStep]:
        """Get execution step for a specific agent"""
        for step in self.steps:
            if step.agent_name == agent_name:
                return step
        return None
    
    def summary(self) -> Dict:
        """Get summary of pipeline execution"""
        return {
            "total_steps": len(self.steps),
            "successful_steps": sum(1 for s in self.steps if s.success),
            "failed_steps": sum(1 for s in self.steps if not s.success),
            "total_time_seconds": self.total_execution_time,
            "agents_executed": [s.agent_name for s in self.steps],
            "final_state": self.state.current_step
        }
