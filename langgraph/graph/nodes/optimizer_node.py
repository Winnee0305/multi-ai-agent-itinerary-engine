from typing import List, Dict

try:
    from agents.optimizer_agent import OptimizerAgent
    _optimizer = OptimizerAgent()
except Exception:
    _optimizer = None

from llm.hf_llm import get_llm, _FallbackLLM
_llm = get_llm()
_llm_fallback = _FallbackLLM()


def optimizer_node(state):
    if _optimizer is not None:
        opt = _optimizer.optimize(state.plan)
    else:
        prompt = (
            f"Optimize this itinerary for minimum travel time between stops. "
            f"Reorder only if necessary. Keep same POIs.\n\n"
            f"{state.plan}\n\n"
            f"Return optimized JSON itinerary."
        )
        opt = _llm.invoke(prompt)

    return {"optimized": opt}
