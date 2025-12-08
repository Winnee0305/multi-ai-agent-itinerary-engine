"""
Supervisor Graph - Main LangGraph orchestration for trip planning

This graph coordinates the entire trip planning workflow:
1. parse_input: Extract trip context from natural language
2. recommend: Generate POI recommendations
3. plan: Create optimized itinerary
4. format_response: Format final user-friendly output

Flow: START → parse_input → recommend → plan → format_response → END

Uses conditional routing based on state.next_step for error handling.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import TripPlannerState
from agents.input_parser import create_input_parser_node
from agents.recommender_agent import create_recommender_node
from agents.planner_agent import create_planner_node
from agents.response_formatter import create_response_formatter_node


def route_next_step(state: TripPlannerState) -> Literal["parse_input", "recommend", "plan", "format_response", "error", "__end__"]:
    """
    Conditional routing function based on state.next_step.
    
    This eliminates the need for an LLM-based supervisor to decide routing.
    Each node sets the next_step, and this function routes accordingly.
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name or END
    """
    next_step = state.get("next_step")
    
    if next_step == "recommend":
        return "recommend"
    elif next_step == "plan":
        return "plan"
    elif next_step == "format_response":
        return "format_response"
    elif next_step == "complete":
        return "__end__"
    elif next_step == "error":
        return "__end__"
    else:
        # Default: start with parsing
        return "parse_input"


def create_supervisor_graph(model):
    """
    Create the main supervisor graph for trip planning.
    
    Args:
        model: LangChain chat model (e.g., ChatGoogleGenerativeAI)
        
    Returns:
        Compiled LangGraph StateGraph with checkpointer for memory
    """
    
    # Create node functions
    input_parser_node = create_input_parser_node(model)
    recommender_node = create_recommender_node(model)
    planner_node = create_planner_node(model)
    response_formatter_node = create_response_formatter_node(model)
    
    # Initialize graph with state schema
    graph_builder = StateGraph(TripPlannerState)
    
    # Add nodes
    graph_builder.add_node("parse_input", input_parser_node)
    graph_builder.add_node("recommend", recommender_node)
    graph_builder.add_node("plan", planner_node)
    graph_builder.add_node("format_response", response_formatter_node)
    
    # Define edges
    # START → parse_input (always start with parsing)
    graph_builder.add_edge(START, "parse_input")
    
    # parse_input → conditional routing
    graph_builder.add_conditional_edges(
        "parse_input",
        route_next_step,
        {
            "recommend": "recommend",
            "__end__": END
        }
    )
    
    # recommend → conditional routing
    graph_builder.add_conditional_edges(
        "recommend",
        route_next_step,
        {
            "plan": "plan",
            "__end__": END
        }
    )
    
    # plan → conditional routing
    graph_builder.add_conditional_edges(
        "plan",
        route_next_step,
        {
            "format_response": "format_response",
            "__end__": END
        }
    )
    
    # format_response → conditional routing (should always go to END)
    graph_builder.add_conditional_edges(
        "format_response",
        route_next_step,
        {
            "__end__": END
        }
    )
    
    # Compile with checkpointer for conversation memory
    checkpointer = MemorySaver()
    graph = graph_builder.compile(checkpointer=checkpointer)
    
    return graph


def create_supervisor_graph_simple(model):
    """
    Create a simplified supervisor graph without response formatting.
    Useful for API responses where formatting is done client-side.
    
    Args:
        model: LangChain chat model
        
    Returns:
        Compiled LangGraph StateGraph
    """
    
    input_parser_node = create_input_parser_node(model)
    recommender_node = create_recommender_node(model)
    planner_node = create_planner_node(model)
    
    # Custom routing for simple graph (skips formatting)
    def route_next_step_simple(state: TripPlannerState) -> Literal["parse_input", "recommend", "plan", "__end__"]:
        """Route for simple graph - treats format_response as complete"""
        next_step = state.get("next_step")
        
        if next_step == "recommend":
            return "recommend"
        elif next_step == "plan":
            return "plan"
        elif next_step in ("format_response", "complete"):
            return "__end__"  # Skip formatting, go straight to end
        elif next_step == "error":
            return "__end__"
        else:
            return "parse_input"
    
    graph_builder = StateGraph(TripPlannerState)
    
    graph_builder.add_node("parse_input", input_parser_node)
    graph_builder.add_node("recommend", recommender_node)
    graph_builder.add_node("plan", planner_node)
    
    # Edges
    graph_builder.add_edge(START, "parse_input")
    
    graph_builder.add_conditional_edges(
        "parse_input",
        route_next_step_simple,
        {
            "recommend": "recommend",
            "__end__": END
        }
    )
    
    graph_builder.add_conditional_edges(
        "recommend",
        route_next_step_simple,
        {
            "plan": "plan",
            "__end__": END
        }
    )
    
    graph_builder.add_conditional_edges(
        "plan",
        route_next_step_simple,
        {
            "__end__": END
        }
    )
    
    checkpointer = MemorySaver()
    return graph_builder.compile(checkpointer=checkpointer)
