from typing import List, Dict

try:
    from agents.recommender_agent import RecommenderAgent
    _recommender = RecommenderAgent()
except Exception:
    _recommender = None

from llm.hf_llm import get_llm, _FallbackLLM
_llm = get_llm()
_llm_fallback = _FallbackLLM()


def recommender_node(state):
    interest = state.preferences.get("interest_type", "general")

    if _recommender is not None:
        # Let the project-level agent implement recommendation logic
        recs = _recommender.recommend(state.info_results, state.preferences)
        # Normalise into expected structure if necessary
        recommendations = [
            {"poi": r.get("poi", r.get("name")), "description": r.get("description"), "scored_info": r.get("scored_info", {})}
            for r in recs
        ]
    else:
        recommendations: List[Dict] = []
        for item in state.info_results:
            score_prompt = (
                f"Given this POI description:\n\n{item['description']}\n\n"
                f"Rate how suitable this place is for someone interested in {interest}. "
                f"Give a score 1-10 and one-sentence reason. Output JSON with keys "
                f"'score' and 'reason'."
            )
            resp = _llm.invoke(score_prompt)
            recommendations.append({
                "poi": item["poi"],
                "description": item["description"],
                "scored_info": resp,
            })

        # simple ordering
        try:
            recommendations.sort(key=lambda x: int(x["scored_info"]["score"]), reverse=True)
        except Exception:
            pass

    return {"recommendations": recommendations}
