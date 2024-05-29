from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from typing import List, Tuple


class QueryParser:
    def __init__(self, graph: TransitionGraph):
        self.graph = graph

    def parse_query(self, query: str) -> bool:
        if "necessary" in query or "possibly" in query:
            if "after" in query:
                return self.parse_value_query(query)
            elif "with time" in query:
                return self.parse_executability_time_query(query)
            else:
                return self.parse_executability_query(query)
        else:
            raise ValueError("Invalid query format.")

    def parse_value_query(self, query: str) -> bool:
        necessity, formula, _, actions, _, condition = query.split("  ")
        return self.check_query(necessity, actions.split(","), condition, formula)

    def parse_executability_query(self, query: str) -> bool:
        necessity, _, actions, _, condition = query.split("  ")
        return self.check_query(necessity, actions.split(","), condition)

    def parse_executability_time_query(self, query: str) -> bool:
        necessity, _, actions, _, time_str, _, condition = query.split("  ")
        time_limit = int(time_str.split(" ")[0])
        return self.check_query(necessity, actions.split(","), condition, time_limit=time_limit)

    def check_query(self, necessity: str, actions: List[str], condition: str, formula: str = None, time_limit: int = None) -> bool:
        for state in self.graph.states:
            if self.check_condition(state, condition):
                current_state = state
                total_time = 0
                for action in actions:
                    next_state, duration = self.get_next_state(current_state, action)
                    if next_state is None or (time_limit is not None and total_time + duration > time_limit):
                        return False if necessity == "necessary" else True
                    current_state = next_state
                    total_time += duration
                if formula is not None:
                    if necessity == "necessary":
                        if not self.check_condition(current_state, formula):
                            return False
                    else:
                        if self.check_condition(current_state, formula):
                            return True
        return True if necessity == "necessary" else False

    def check_condition(self, state: StateNode, condition: str) -> bool:
        return all(fluent in state.label for fluent in condition.split(" and "))

    def get_next_state(self, state: StateNode, action: str) -> Tuple[StateNode, int]:
        for edge in self.graph.edges:
            if edge.source == state and edge.action == action:
                return edge.target, edge.duration
        return None, 0