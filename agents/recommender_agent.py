from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from config.settings import settings
from config.prompts import RECOMMENDER_AGENT_SYSTEM_PROMPT

from tools.recommender_tools import (
    load_pois_tool,
    calculate_priority_scores_tool,
    get_top_priority_pois_tool,
    calculate_activity_mix_tool,
    generate_recommendation_output_tool,
    recommend_pois_for_trip_tool
)

model = ChatGoogleGenerativeAI(
    model=settings.DEFAULT_LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE
)

recommender_tools = [
    load_pois_tool,
    calculate_priority_scores_tool,
    get_top_priority_pois_tool,
    calculate_activity_mix_tool,
    generate_recommendation_output_tool,
    recommend_pois_for_trip_tool
]

recommender_agent = create_agent(
    model=model,
    tools=recommender_tools,
    system_prompt=RECOMMENDER_AGENT_SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)