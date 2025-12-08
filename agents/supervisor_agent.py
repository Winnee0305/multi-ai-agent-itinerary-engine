"""
DEPRECATED: This file is deprecated as of December 4, 2025.

This file used the old LangChain agent pattern where sub-agents were wrapped as tools.
It has been replaced by agents/supervisor_graph.py which uses LangGraph nodes.

See LANGGRAPH_MIGRATION.md for details.

DO NOT USE THIS FILE. Import from agents.supervisor_graph instead:
    from agents.supervisor_graph import create_supervisor_graph

---

OLD IMPLEMENTATION (for reference only):
"""

# Old implementation kept for reference but should not be used
# from langchain.agents import create_agent
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.checkpoint.memory import InMemorySaver
# from config.settings import settings
# from config.prompts import SUPERVISOR_AGENT_SYSTEM_PROMPT
# 
# from tools.supervisor_tools import (
#     get_poi_recommendations,
#     plan_itinerary
# )
# 
# model = ChatGoogleGenerativeAI(
#     model=settings.DEFAULT_LLM_MODEL,
#     temperature=settings.LLM_TEMPERATURE
# )
# 
# # Supervisor only sees high-level tools (wrapped sub-agents)
# supervisor_tools = [
#     get_poi_recommendations,
#     plan_itinerary
# ]
# 
# supervisor_agent = create_agent(
#     model=model,
#     tools=supervisor_tools,
#     system_prompt=SUPERVISOR_AGENT_SYSTEM_PROMPT,
#     checkpointer=InMemorySaver()
# )

# Raise error if someone tries to import the old agent
class DeprecatedModuleError(Exception):
    pass

raise DeprecatedModuleError(
    "agents.supervisor_agent is deprecated. Use agents.supervisor_graph instead.\n"
    "Import: from agents.supervisor_graph import create_supervisor_graph\n"
    "See LANGGRAPH_MIGRATION.md for migration guide."
)