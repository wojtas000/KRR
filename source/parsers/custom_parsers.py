import re

from abc import ABC, abstractmethod
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from source.parsers.logical_formula_parser import LogicalFormulaParser
from typing import List, Dict, Tuple, Union


class CustomParser(ABC):
    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph
        self.logical_formula_parser = LogicalFormulaParser()
        self.name = self.__class__.__name__.split("Parser")[0].lower()
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
        logical_statements = self.logical_formula_parser.extract_logical_statements(formula)
        if logical_statements == None:
            raise ValueError(f"Contradictory statement for {self.name} statement. In formula: {formula}")
        for logical_statement in logical_statements:
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
    
    def parse(self, statement: str) -> List:
        initial_logic = statement.split("initially")[1].strip()
        return list(
            filter(lambda state: self.evaluate_formula(initial_logic, state), 
            self.transition_graph.generate_possible_states())
        )


class CausesParser(CustomParser):
    
    def get_action_effect_and_precondition(self, statement: str) -> Tuple[str, str]:
        action, effect = map(str.strip, statement.split("causes"))
        effect_formula = effect.split(" if ")[0].strip() if " if " in effect else effect.strip()
        precondition_formula = effect.split(" if ")[1] if " if " in effect else ""
        return action, effect_formula, precondition_formula

    def extract_actions(self, statement: str) -> str:
        all_actions = []
        for statement in statements:
            action, _, _ = self.get_action_effect_and_precondition(statement)
            all_actions.append(action)
        return all_actions

    def extract_fluents(self, statements: str) -> List[str]:
        all_fluents = []
        for statement in statements:
            _, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)

            effect_fluents = self.logical_formula_parser.extract_fluents(effect_formula)
            precondition_fluents = self.logical_formula_parser.extract_fluents(precondition_formula)
            all_fluents += effect_fluents + precondition_fluents
    
        return list(set(all_fluents))

    def parse(self, statements: List) -> List:

        edges = []

        action, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)
        for from_state in self.transition_graph.states:
            effect_formulas = []
            for statement in statements:
                action, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)
                if self.evaluate_formula(precondition_formula, from_state):
                    effect_formulas.append(effect_formula)
            for to_state in self.transition_graph.states:
                if all(self.evaluate_formula(effect_formula, to_state) for effect_formula in effect_formulas):
                    edges.append(Edge(from_state, action, to_state))
        return edges


class ReleasesParser(CausesParser):

    def extract_fluents(self, statement: str) -> List[str]:
        statement = statement.replace("releases", "causes")
        return super().extract_fluents(statement)

    def extract_actions(self, statement: str) -> str:
        statement = statement.replace("releases", "causes")
        return super().extract_actions(statements)

    def parse(self, statement: str) -> List:

        edges = []

        action, modified_fluent, precondition_formula = self.get_action_effect_and_precondition(statement.replace("releases", "causes"))
        for from_state in self.transition_graph.states:
            if self.precondition_met(from_state, precondition_formula):
                to_state = StateNode(fluents=from_state.fluents.copy())
                to_state.update({modified_fluent: not from_state.fluents[modified_fluent]})

                if to_state in self.transition_graph.states:
                    edges.append(Edge(from_state, action, to_state))
        
        return edges


class LastsParser(CustomParser):

    def extract_actions(self, statements: str) -> str:
        all_actions = []
        for statement in statements:
            all_actions.append(statement.split("lasts")[0].strip())
        return all_actions

    def extract_fluents(self, statements: str) -> List[str]:
        return []
    
    def parse(self, statements: str) -> None:
        durations = []
        for statement in statements:
            action, duration = map(str.strip, statement.split("lasts"))
            for i, edge in enumerate(self.transition_graph.edges):
                if edge.action == action and edge.source != edge.target:
                    durations.append((i, duration))
        return durations


class AfterParser(CustomParser):

    def extract_actions(self, statements: str) -> str:
        all_actions = []
        for statement in statements:
            all_actions += statement.split("after")[0].strip().split(",")
        return all_actions

    def extract_fluents(self, statements: str) -> List[str]:
        all_fluents = []
        for statement in statements:
            effect_formula, actions = statement.split("after")
            all_fluents += self.logical_formula_parser.extract_fluents(effect_formula)
        return all_fluents
    
    def parse(self, statements: str) -> None:
        possible_initial_states = self.transition_graph.possible_initial_states
        possible_ending_states = []
        for statement in statements:
            effect_formula, actions = map(str.strip, statement.split("after"))
            actions = actions.split(",")[::-1]

            # Find possible ending states
            for logical_statement in self.logical_formula_parser.extract_logical_statements(effect_formula):
                for edge in self.transition_graph.edges:
                    if edge.action == action[0]:
                        fluent_dict = self.logical_formula_parser.extract_fluent_dict(logical_statement)
                        if all(fluent in edge.target.fluents for fluent in fluent_dict):
                            possible_ending_states.append(edge.target)

            # Find possible initial states
            possible_states = possible_ending_states
            possible_states_prev = []
            for action in actions:
                for edge in self.transition_graph.edges:
                    if edge.action == action and edge.target in possible_states:
                        possible_states_prev.append(edge.source)
                if not possible_states_prev:
                    raise ValueError(f"Contradictory statement for after statement. In formula: {effect_formula}")
                possible_states = possible_states_prev
                possible_states_prev = []
            
            for state in set(possible_initial_states).intersection(possible_states):
                self.transition_graph.add_possible_initial_state(state)
            for state in possible_ending_states:
                self.transition_graph.add_possible_ending_state(state) 


class AlwaysParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return []

    def extract_fluents(self, statement: str) -> List[str]:
        always_logic = statement.split("always")[1].strip()
        return self.logical_formula_parser.extract_fluents(always_logic)

    def always(self, state: StateNode, always_statements: List = []) -> bool:
        if always_statements and all(not self.evaluate_formula(always_statement, state) for always_statement in always_statements):
            return False
        return True

    def parse(self, statement: str) -> None:
        always_logic = statement.split("always")[1].strip()
        always_statements = self.logical_formula_parser.extract_logical_statements(always_logic)
        self.transition_graph.always += always_statements
        return list(filter(lambda state: self.always(state, always_statements), self.transition_graph.generate_all_states()))


class ImpossibleParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return []

    def extract_fluents(self, statement: str) -> List[str]:
        impossible_logic = statement.split("impossible")[1].strip()
        return self.logical_formula_parser.extract_fluents(impossible_logic)

    def impossible(self, state: StateNode, impossible_statements: List = []) -> bool:
        if impossible_statements and any(self.evaluate_formula(impossible_statement, state) for impossible_statement in impossible_statements):
            return True
        return False

    def parse(self, statement: str) -> None:
        impossible_logic = statement.split("impossible")[1].strip()
        impossible_statements = self.logical_formula_parser.extract_logical_statements(impossible_logic)
        self.transition_graph.impossible += impossible_statements
        return list(filter(lambda state: self.impossible(state, impossible_statements), self.transition_graph.generate_all_states()))
