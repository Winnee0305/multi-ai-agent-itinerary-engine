from langgraph.graph import StateGraph

from graph.state import TravelState
from graph.nodes.info_node import info_node
from graph.nodes.recommender_node import recommender_node
from graph.nodes.planner_node import planner_node
from graph.nodes.optimizer_node import optimizer_node

def build_graph():
    g = StateGraph(TravelState)

    g.add_node("info", info_node)
    g.add_node("recommend", recommender_node)
    g.add_node("plan", planner_node)
    g.add_node("optimize", optimizer_node)

    g.set_entry_point("info")
    g.add_edge("info", "recommend")
    g.add_edge("recommend", "plan")
    g.add_edge("plan", "optimize")

    return g.compile()
