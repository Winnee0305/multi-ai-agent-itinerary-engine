from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from config.settings import settings
from config.prompts import PLANNER_AGENT_SYSTEM_PROMPT
from database.supabase_client import get_supabase


model = ChatGoogleGenerativeAI(
    model=settings.DEFAULT_LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE
)

supervisor_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=SUPERVISOR_AGENT_SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)