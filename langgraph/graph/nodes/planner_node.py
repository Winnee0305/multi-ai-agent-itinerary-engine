from typing import List, Dict

try:
    from agents.planner_agent import PlannerAgent
    _planner = PlannerAgent()
except Exception:
    _planner = None

from llm.hf_llm import get_llm, _FallbackLLM
_llm = get_llm()
_llm_fallback = _FallbackLLM()


def planner_node(state):
    top_pois = [rec["poi"] for rec in state.recommendations[:5]]

    if _planner is not None:
        plan = _planner.plan(state.recommendations, state.location)
    else:
        prompt = (
            f"Create a half-day itinerary for these POIs in {state.location}:\n"
            f"{top_pois}\n\n"
            f"Return JSON with a list of steps, each having 'poi', 'time', 'activity'."
        )

        plan = _llm.invoke(prompt)

    return {"plan": plan}
