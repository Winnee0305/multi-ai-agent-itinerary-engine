from typing import Callable, Dict, List, Type, Any, Set, Optional
from collections import deque


class StateGraph:
	"""Minimal state graph builder used by the example pipeline.

	Usage:
	  g = StateGraph(StateModel)
	  g.add_node("name", node_fn)
	  g.add_edge("name", "next")
	  g.set_entry_point("name")
	  workflow = g.compile()
	  state = workflow.invoke(initial_dict)
	"""

	def __init__(self, state_model: Type[Any]):
		self.state_model = state_model
		self.nodes: Dict[str, Callable[[Any], Any]] = {}
		self.edges: Dict[str, List[str]] = {}
		self.entry_point: Optional[str] = None

	def add_node(self, name: str, fn: Callable[[Any], Any]) -> None:
		self.nodes[name] = fn
		self.edges.setdefault(name, [])

	def add_edge(self, src: str, dst: str) -> None:
		self.edges.setdefault(src, []).append(dst)

	def set_entry_point(self, name: str) -> None:
		self.entry_point = name

	def compile(self) -> "Workflow":
		return Workflow(self.nodes, self.edges, self.entry_point, self.state_model)


class Workflow:
	def __init__(self, nodes: Dict[str, Callable], edges: Dict[str, List[str]], entry_point: Optional[str], state_model: Type[Any]):
		self.nodes = nodes
		self.edges = edges
		self.entry_point = entry_point
		self.state_model = state_model

	def invoke(self, initial_state: Any) -> Any:
		# Build pydantic model instance if a dict was provided
		if isinstance(initial_state, dict):
			state = self.state_model(**initial_state)
		else:
			state = initial_state

		if self.entry_point is None:
			raise RuntimeError("Entry point not set on StateGraph")

		visited: Set[str] = set()
		q = deque([self.entry_point])

		while q:
			node = q.popleft()
			if node in visited:
				continue
			visited.add(node)

			fn = self.nodes.get(node)
			if fn is None:
				continue

			# Node functions are expected to accept and return the state
			state = fn(state)

			for nbr in self.edges.get(node, []):
				if nbr not in visited:
					q.append(nbr)

		return state

