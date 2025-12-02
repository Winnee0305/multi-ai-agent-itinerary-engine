from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from config.settings import settings
from config.prompts import SUPERVISOR_AGENT_SYSTEM_PROMPT

from tools.supervisor_tools import (
    get_poi_recommendations,
    plan_itinerary
)

model = ChatGoogleGenerativeAI(
    model=settings.DEFAULT_LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE
)

# Supervisor only sees high-level tools (wrapped sub-agents)
supervisor_tools = [
    get_poi_recommendations,
    plan_itinerary
]

supervisor_agent = create_agent(
    model=model,
    tools=supervisor_tools,
    system_prompt=SUPERVISOR_AGENT_SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)