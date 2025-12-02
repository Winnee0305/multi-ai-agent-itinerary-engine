from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from config.settings import settings
from config.prompts import PLANNER_AGENT_SYSTEM_PROMPT
from database.supabase_client import get_supabase
from tools.planner_tools import (
    get_poi_by_place_id_tool,
    calculate_distance_tool,
    get_pois_near_centroid_tool,
    cluster_pois_tool,
    generate_optimal_sequence_tool,
    plan_itinerary_tool # The main orchestrator tool
)

model = ChatGoogleGenerativeAI(
    model=settings.DEFAULT_LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE
)

# Define tools for planner agent
planner_tools = [
    get_poi_by_place_id_tool,
    calculate_distance_tool,
    get_pois_near_centroid_tool,
    cluster_pois_tool,
    generate_optimal_sequence_tool,
    plan_itinerary_tool
]

planner_agent = create_agent(
    model=model,
    tools=planner_tools,
    system_prompt=PLANNER_AGENT_SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)
