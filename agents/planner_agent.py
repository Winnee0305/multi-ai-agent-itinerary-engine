from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from config.settings import settings
from config.prompts import PLANNER_AGENT_SYSTEM_PROMPT
from database.supabase_client import get_supabase
from tools.planner_tools import (
    get_poi_by_place_id,
    get_pois_by_priority_list,
    calculate_distance_between_pois,
    get_pois_near_centroid,
    calculate_distances_from_centroid,
    select_best_centroid,
    cluster_pois_by_distance,
    generate_optimal_sequence
)

model = ChatGoogleGenerativeAI(
    model=settings.DEFAULT_LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE
)

# Define tools for planner agent
planner_tools = [
    get_poi_by_place_id,
    get_pois_by_priority_list,
    calculate_distance_between_pois,
    get_pois_near_centroid,
    calculate_distances_from_centroid,
    select_best_centroid,
    cluster_pois_by_distance,
    generate_optimal_sequence
]

planner_agent = create_agent(
    model=model,
    tools=planner_tools,
    system_prompt=PLANNER_AGENT_SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)
