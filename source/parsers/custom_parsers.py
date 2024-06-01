import re

from abc import ABC, abstractmethod
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from source.parsers.logical_formula_parser import LogicalFormulaParser
from typing import List, Dict, Tuple


class CustomParser(ABC):
    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph
        self.logical_formula_parser = LogicalFormulaParser()
        self.statements = []

    @abstractmethod
    def extract_fluents(self, statement: str) -> List[str]:
        pass

    @abstractmethod
    def parse(self, statement: str, *args, **kwargs) -> None:
        pass

    def get_transition_graph(self) -> TransitionGraph:
        return self.transition_graph

    def evaluate_formula(self, formula: str, state: StateNode) -> bool:
        def replace_fluents_with_values(formula: str, state: StateNode) -> str:
            for fluent, value in state.fluents.items():
                formula = formula.replace(f"~{fluent}", str(not value))
                formula = formula.replace(f"{fluent}",str(value))
            return formula

        for logical_statement in self.logical_formula_parser.extract_logical_statements(formula):
            formula = replace_fluents_with_values(logical_statement, state)
            if eval(formula):
                return True
        return False

    def precondition_met(self, state: StateNode, precondition: str) -> bool:
        return self.evaluate_formula(precondition, state) or not precondition


class InitiallyParser(CustomParser):

    def get_initial_logic(self, statement: str) -> str:
        return statement.split("initially")[1].strip()

    def extract_fluents(self, statement: str) -> List[str]:
        formula = self.get_initial_logic(statement)
        return self.logical_formula_parser.extract_fluents(formula)
    
    def parse(self, statement: str) -> None:
        initial_logic = self.get_initial_logic(statement)
        for state in self.transition_graph.generate_all_states():
            if self.evaluate_formula(initial_logic, state):
                self.transition_graph.add_possible_initial_state(state)


class CausesParser(CustomParser):
    
    def get_action_effect_and_precondition(self, statement: str) -> Tuple[str, str]:
        action, effect = map(str.strip, statement.split("causes"))
        effect_formula = effect.split(" if ")[0].strip()
        precondition_formula = effect.split(" if ")[1] if " if " in effect else ""
        return action, effect_formula, precondition_formula

    def extract_fluents(self, statement: str) -> List[str]:
        _, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)

        effect_fluents = self.logical_formula_parser.extract_fluents(effect_formula)
        precondition_fluents = self.logical_formula_parser.extract_fluents(precondition_formula)
        
        return effect_fluents + precondition_fluents

    def parse(self, statement: str) -> None:
        action, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)
        all_states = self.transition_graph.generate_all_states()
        
        for from_state in all_states:
            if self.precondition_met(from_state, precondition_formula):
                for statement in self.logical_formula_parser.extract_logical_statements(effect_formula):
                    to_state = StateNode(fluents=from_state.fluents.copy())
                    for fluent, value in self.logical_formula_parser.extract_fluent_dict(statement).items():
                        to_state.fluents[fluent] = value
                    self.transition_graph.add_state(from_state)
                    self.transition_graph.add_state(to_state)
                    self.transition_graph.add_edge(from_state, action, to_state)


class ReleasesParser(CausesParser):

    def extract_fluents(self, statement: str) -> List[str]:
        statement = statement.replace("releases", "causes")
        return super().extract_fluents(statement)


    def parse(self, statement: str) -> None:
        statement = statement.replace("releases", "causes")
        action, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)
        effect_fluents = self.logical_formula_parser.extract_fluents(effect_formula)
        statement2 = f"{action} causes ~{effect_fluents[0]} if {precondition_formula}"
        
        super().parse(statement)
        super().parse(statement2)


class DurationParser(CustomParser):
    def extract_fluents(self, statement: str) -> List[str]:
        return []

    def parse(self, statement: str) -> None:
        action, duration = statement.split(" lasts ")
        for i, edge in enumerate(self.transition_graph.edges):
            if edge.action == action.strip() and edge.source != edge.target:
                edge.add_duration(int(duration))
                self.transition_graph.edges[i] = edge
