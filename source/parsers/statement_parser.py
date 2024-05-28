import re
from typing import Tuple, List
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
class StatementParser:

    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph

    def extract_fluents(self, statement: str) -> List[str]:
        fluents = re.findall(r'~?\b\w+', statement)
        fluents = [fluent.strip().lstrip('~') for fluent in fluents if fluent.strip() not in ["and", "or", "implies", "iff", "(", ")"]]
        return fluents

    def evaluate_formula(self, formula: str, state: StateNode) -> bool:
        for fluent, value in state.fluents.items():
            formula = formula.replace(f"~{fluent}", str(not value))
            formula = formula.replace(fluent, str(value))

        formula = formula.replace("iff", "==") 
        formula = f"({formula})"
        return eval(formula)

    def parse_initially(self, statement: str) -> None:
        initial_logic = statement.split("initially ")[1]
        fluents = self.extract_fluents(initial_logic)
        
        for fluent in fluents:
            self.transition_graph.add_fluent(fluent)
        
        for state in self.transition_graph.generate_all_states():
            if self.evaluate_formula(initial_logic, state):
                self.transition_graph.add_possible_initial_state(state)

    def parse_causes(self, statement: str) -> None:

        action, effect = statement.split(" causes ")
        
        effect_formula = effect.split(" if ")[0].strip()
        effect_fluents = self.extract_fluents(effect_formula)
        
        precondition_formula = effect.split(" if ")[1] if " if " in effect else ""
        precondition_fluents = self.extract_fluents(precondition_formula)

        for fluent in effect_fluents + precondition_fluents:
            self.transition_graph.add_fluent(fluent)

        all_states = self.transition_graph.generate_all_states()
        for from_state in all_states:
            for to_state in all_states:
                if (self.evaluate_formula(precondition_formula, from_state) or not precondition_formula) and self.evaluate_formula(effect_formula, to_state):
                    self.transition_graph.add_state(from_state)
                    self.transition_graph.add_state(to_state)
                    self.transition_graph.add_edge(from_state, action, to_state)

    def parse_releases(self, statement: str) -> None:
        action, effect = statement.split(" releases ")
        
        effect_formula = effect.split(" if ")[0].strip()
        effect_fluents = self.extract_fluents(effect_formula)
        
        precondition_formula = effect.split(" if ")[1] if " if " in effect else ""
        precondition_fluents = self.extract_fluents(precondition_formula)

        for fluent in effect_fluents + precondition_fluents:
            self.transition_graph.add_fluent(fluent)

        all_states = self.transition_graph.generate_all_states()
        for from_state in all_states:
            if self.evaluate_formula(precondition_formula, from_state):
                self.transition_graph.add_state(state)
                to_state = StateNode(state.fluents.copy())
                for fluent in effect_fluents:
                    to_state.fluents[fluent] = not from_state.fluents[fluent]
                self.transition_graph.add_edge(from_state, action, to_state)

    def parse_duration(self, statement: str) -> None:
        action, duration = statement.split(" lasts ")
        for i, edge in enumerate(self.transition_graph.edges):
            if edge.action == action.strip() and edge.source != edge.target:
                edge.add_duration(int(duration))
                self.transition_graph.edges[i] = edge

    def parse_statement(self, statement: str) -> None:
        if statement.startswith("initially"):
            self.parse_initially(statement)
        elif "causes" in statement:
            self.parse_causes(statement)
        elif "releases" in statement:
            self.parse_releases(statement)
        elif "lasts" in statement:
            self.parse_duration(statement)

        self.transition_graph.update_states_with_new_fluents()