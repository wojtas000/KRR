import re

from abc import ABC, abstractmethod
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from source.parsers.logical_formula_parser import LogicalFormulaParser
from typing import List, Dict, Tuple, Union


class CustomParser(ABC):
    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph
        self.logical_formula_parser = LogicalFormulaParser()
        self.statements = []

    @abstractmethod
    def extract_actions(self, statement: str) -> str:
        pass

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

    def precondition_met(self, state: StateNode, precondition: Union[str, bool]) -> bool:
        if len(precondition) == 0:
            return True
        return self.evaluate_formula(precondition, state)

    def possible(self, state: StateNode) -> bool:

        if self.transition_graph.always and all(not self.evaluate_formula(always_statement, state) for always_statement in self.transition_graph.always):
            return False
        if self.transition_graph.impossible and any(self.evaluate_formula(impossible_statement, state) for impossible_statement in self.transition_graph.impossible):
            return False
        return True


class InitiallyParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return []

    def extract_fluents(self, statement: str) -> List[str]:
        formula = statement.split("initially")[1].strip()
        return self.logical_formula_parser.extract_fluents(formula)
    
    def parse(self, statement: str) -> None:
        initial_logic = statement.split("initially")[1].strip()
        for state in self.transition_graph.generate_all_states():
            if self.evaluate_formula(initial_logic, state) and self.possible(state):
                self.transition_graph.add_possible_initial_state(state)


class CausesParser(CustomParser):
    
    def get_action_effect_and_precondition(self, statement: str) -> Tuple[str, str]:
        action, effect = map(str.strip, statement.split("causes"))
        effect_formula = effect.split(" if ")[0].strip() if " if " in effect else effect.strip()
        precondition_formula = effect.split(" if ")[1] if " if " in effect else ""
        return action, effect_formula, precondition_formula

    def extract_actions(self, statement: str) -> str:
        action, _, _ = self.get_action_effect_and_precondition(statement)
        return [action]

    def extract_fluents(self, statement: str) -> List[str]:
        _, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)

        effect_fluents = self.logical_formula_parser.extract_fluents(effect_formula)
        precondition_fluents = self.logical_formula_parser.extract_fluents(precondition_formula)
    
        return effect_fluents + precondition_fluents

    def parse(self, statement: str) -> None:
        action, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)
        all_states = self.transition_graph.generate_all_states()

        visited_states = self.update_existing_edges(action, effect_formula, precondition_formula, all_states)
        self.add_new_edges(action, effect_formula, precondition_formula, visited_states, all_states)

    def update_existing_edges(self, action, effect_formula, precondition_formula, all_states):
        visited_states = []
        edges_to_remove = []
        edges_to_add = []
        
        for edge in self.transition_graph.edges:
            if edge.action == action:
                from_state = edge.source
                if self.precondition_met(from_state, precondition_formula) and self.possible(from_state):
                    for statement in self.logical_formula_parser.extract_logical_statements(effect_formula):
                        to_state = StateNode(fluents=edge.target.fluents.copy())
                        to_state.update(self.logical_formula_parser.extract_fluent_dict(statement))
                        if self.possible(to_state):
                            new_edge = Edge(from_state, action, to_state, edge.duration)
                            edges_to_add.append(new_edge)
                            edges_to_remove.append(edge)
                            visited_states.append(to_state)

        for edge in edges_to_remove:
            self.transition_graph.remove_edge(edge.action, edge.source, edge.target)

        for edge in edges_to_add:
            self.transition_graph.add_edge(edge.source, edge.action, edge.target, edge.duration)

        return visited_states

    def add_new_edges(self, action, effect_formula, precondition_formula, visited_states, all_states):
        for from_state in all_states:
            if self.precondition_met(from_state, precondition_formula) and self.possible(from_state):
                    for statement in self.logical_formula_parser.extract_logical_statements(effect_formula):
                        to_state = StateNode(fluents=from_state.fluents.copy())
                        to_state.update(self.logical_formula_parser.extract_fluent_dict(statement))
                        if self.possible(to_state) and to_state not in visited_states:
                            self.transition_graph.add_edge(from_state, action, to_state)


class ReleasesParser(CausesParser):

    def extract_fluents(self, statement: str) -> List[str]:
        statement = statement.replace("releases", "causes")
        return super().extract_fluents(statement)

    def extract_actions(self, statement: str) -> str:
        statement = statement.replace("releases", "causes")
        return super().extract_actions(statement)

    def parse(self, statement: str):
        action, modified_fluent, precondition_formula = self.get_action_effect_and_precondition(statement.replace("releases", "causes"))
        all_states = self.transition_graph.generate_all_states()
        for from_state in all_states:
            if self.precondition_met(from_state, precondition_formula) and self.possible(from_state):
                to_state = StateNode(fluents=from_state.fluents.copy())
                to_state.update({modified_fluent: not from_state.fluents[modified_fluent]})

                if self.possible(to_state):
                    self.transition_graph.add_edge(from_state, action, to_state)


class DurationParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return [statement.split("lasts")[0].strip()]

    def extract_fluents(self, statement: str) -> List[str]:
        return []
    
    def parse(self, statement: str) -> None:
        action, duration = map(str.strip, statement.split("lasts"))
        for i, edge in enumerate(self.transition_graph.edges):
            if edge.action == action and edge.source != edge.target:
                edge.add_duration(int(duration))
                self.transition_graph.edges[i] = edge


class AfterParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return statement.split("after")[1].strip().split(",")

    def extract_fluents(self, statement: str) -> List[str]:
        effect_formula, actions = statement.split("after")
        return self.logical_formula_parser.extract_fluents(effect_formula)
    
    def parse(self, statement: str) -> None:
        effect_formula, action = map(str.strip, statement.split("after"))
        for statement in self.logical_formula_parser.extract_logical_statements(effect_formula):
            for edge in self.transition_graph.edges:
                if edge.action == action:
                    fluent_dict = self.logical_formula_parser.extract_fluent_dict(statement)
                    if all(fluent in edge.target.fluents for fluent in fluent_dict):
                        self.transition_graph.add_possible_ending_state(edge.target)



    def prepare_statement(self, statement:str) -> None:
        effect_formula, action = map(str.strip, statement.split("after"))
        effect_fluents = self.logical_formula_parser.extract_fluents(effect_formula)
        statement = f"{action} causes {effect_formula}"
        return statement


class AlwaysParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return []

    def extract_fluents(self, statement: str) -> List[str]:
        always_logic = statement.split("always")[1].strip()
        return self.logical_formula_parser.extract_fluents(always_logic)

    def parse(self, statement: str) -> None:
        always_logic = statement.split("always")[1].strip()
        self.transition_graph.always += self.logical_formula_parser.extract_logical_statements(always_logic)


class ImpossibleParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return []

    def extract_fluents(self, statement: str) -> List[str]:
        impossible_logic = statement.split("impossible")[1].strip()
        return self.logical_formula_parser.extract_fluents(impossible_logic)

    def parse(self, statement: str) -> None:
        impossible_logic = statement.split("impossible")[1].strip()
        self.transition_graph.impossible += self.logical_formula_parser.extract_logical_statements(impossible_logic)

