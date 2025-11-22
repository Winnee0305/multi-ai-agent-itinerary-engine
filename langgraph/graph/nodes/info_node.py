from typing import List, Dict

try:
    # Prefer the higher-level InfoAgent if present in the repo
    from agents.info_agent import InfoAgent
    _info_agent = InfoAgent()
except Exception:
    _info_agent = None

from llm.hf_llm import get_llm, _FallbackLLM

_llm = get_llm()
_llm_fallback = _FallbackLLM()


def info_node(state):
    if not state.pois and _info_agent is not None:
        print(f"No POIs provided for {state.location}. Discovering POIs...")
        state.pois = _info_agent.discover_pois(state.location, state.preferences)

    poi_descriptions: List[Dict] = []

    for poi in state.pois:
        if _info_agent is not None:
            # Use the InfoAgent implementation
            info = _info_agent.fetch_single_poi_info(poi)
            desc = info.get("description") if isinstance(info, dict) else str(info)
        else:
            prompt = (
                f"You are a travel guide. Write a concise 50-80 word description for "
                f"{poi} in {state.location}. Focus on accuracy, history, highlights. "
                f"No bullet points, plain text only."
            )
            desc = _llm.invoke(prompt)

        poi_descriptions.append({"poi": poi, "description": desc})

    return {"info_results": poi_descriptions}
