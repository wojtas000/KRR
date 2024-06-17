import re

from abc import ABC, abstractmethod
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from source.parsers.logical_formula_parser import LogicalFormulaParser
from typing import List, Dict, Tuple, Union, Any, Callable
from functools import wraps

def exception_handler_decorator(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return method(*args, **kwargs)
        except Exception as e:
            statement = kwargs.get('statement')
            error_message = f"An error occurred in {method.__name__} with statement '{statement}': {e}"
            raise RuntimeError(error_message) from e
    return wrapper

class CustomParser(ABC):
    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph
        self.logical_formula_parser = LogicalFormulaParser()
        self.name = self.__class__.__name__.split("Parser")[0].lower()
        self.statements = []

    @exception_handler_decorator 
    @abstractmethod
    def extract_actions(self, statement: str) -> str:
        pass

    @exception_handler_decorator
    @abstractmethod
    def extract_fluents(self, statement: str) -> List[str]:
        pass
    
    @exception_handler_decorator
    @abstractmethod
    def parse(self, statement: str, *args, **kwargs):
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
        if logical_statements is None:
            return None
        for logical_statement in logical_statements:
            formula = replace_fluents_with_values(logical_statement, state)
            if eval(formula):
                return True
        return False

    def precondition_met(self, precondition: Union[str, bool], state: StateNode,) -> bool:
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
        for state in self.transition_graph.generate_possible_states():
            assert self.evaluate_formula(initial_logic, state) is not None, f"Contradictory statement in formula: {statement}"

        return list(
            filter(lambda state: self.evaluate_formula(initial_logic, state), 
            self.transition_graph.generate_possible_states())
        )


class CausesParser(CustomParser):
    
    def get_action_effect_and_precondition(self, statement: str) -> Tuple[str, str, str]:
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

    def parse(self, statements: List) -> List:

        edges = []

        for from_state in self.transition_graph.states:
            effect_formulas = []
            updates = []
            
            for statement in statements:
                action, effect_formula, precondition_formula = self.get_action_effect_and_precondition(statement)
                
                if self.precondition_met(precondition_formula, from_state):
                    effect_formulas.append(effect_formula)
            
            for to_state in self.transition_graph.states:
                if effect_formulas:
                    formula = " & ".join(effect_formulas)
                    assert self.evaluate_formula(formula, to_state) is not None, f"Inconsistent domain in formula(s): {statements}"   

                if all(self.evaluate_formula(effect_formula, to_state) for effect_formula in effect_formulas) and \
                        Edge(from_state, action, to_state) not in self.transition_graph.impossible_edges:
                    difference = self.diff_between_states(from_state, to_state)
                    updates.append((to_state, difference, len(difference)))
            
            # get all states with least amount of changes and create edges
            if updates:
                min_changes = min([update[2] for update in updates])
                for update in updates:
                    if update[2] == min_changes:
                        to_state, difference, _ = update
                        edges.append(Edge(from_state, action, to_state))
        
        return edges


    def diff_between_states(self, from_node: StateNode, to_node: StateNode) -> Dict[str, bool]:
        diff = {}
        for fluent, value in to_node.fluents.items():
            if from_node.fluents[fluent] != value:
                diff[fluent] = value
        return diff

class ReleasesParser(CausesParser):

    def extract_fluents(self, statement: str) -> List[str]:
        statement = statement.replace("releases", "causes")
        return super().extract_fluents(statement)

    def extract_actions(self, statement: str) -> str:
        statement = statement.replace("releases", "causes")
        return super().extract_actions(statement)

    def parse(self, statement: str) -> List:

        edges = []

        action, modified_fluent, precondition_formula = self.get_action_effect_and_precondition(statement.replace("releases", "causes"))
        for from_state in self.transition_graph.states:
            if self.precondition_met(precondition_formula, from_state):
                to_state = StateNode(fluents=from_state.fluents.copy())
                to_state.update({modified_fluent: not from_state.fluents[modified_fluent]})

                if to_state in self.transition_graph.states and Edge(from_state, action, to_state) not in self.transition_graph.impossible_edges:
                    edges.append(Edge(from_state, action, to_state))
        
        return edges


class LastsParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        return [statement.split("lasts")[0].strip()]

    def extract_fluents(self, statement: str) -> List[str]:
        return []
    
    def parse(self, statement: str) -> None:
        durations = []
        action, duration = map(str.strip, statement.split("lasts"))
        for i, edge in enumerate(self.transition_graph.edges):
            if edge.action == action and edge.source != edge.target:
                durations.append((i, int(duration)))
        return durations


class AfterParser(CustomParser):

    def extract_actions(self, statement: str) -> str:
        action_chain = statement.split("after")[1].strip()
        if ',' in action_chain:
            return action_chain.split(",")
        return [action_chain]

    def extract_fluents(self, statement: str) -> List[str]:
        effect_formula, actions = statement.split("after")
        return self.logical_formula_parser.extract_fluents(effect_formula)
    
    def parse(self, statement: str) -> None:
        possible_initial_states = self.transition_graph.possible_initial_states
        possible_ending_states = []
        effect_formula, actions = map(str.strip, statement.split("after"))
        actions = actions.split(",")[::-1] if "," in actions else [actions]

        # Find possible ending states
        for logical_statement in self.logical_formula_parser.extract_logical_statements(effect_formula):
            for edge in self.transition_graph.edges:
                if edge.action == actions[0]:
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
        
        initial_states_for_removal = [state for state in possible_initial_states if state not in possible_states]
        return initial_states_for_removal, possible_ending_states


class AlwaysParser(CustomParser):

    def get_effect_and_precondition(self, statement):
        always_logic = statement.split("always")[1].strip()
        if 'if' in always_logic:
            effect_formula, precondition_formula = map(str.strip, always_logic.split("if"))
        else:
            effect_formula = always_logic
            precondition_formula = ""
        return effect_formula, precondition_formula

    def extract_actions(self, statement: str) -> str:
        return []

    def extract_fluents(self, statement: str) -> List[str]:
        effect_formula, precondition_formula = self.get_effect_and_precondition(statement)
        return self.logical_formula_parser.extract_fluents(effect_formula) + self.logical_formula_parser.extract_fluents(precondition_formula)

    def parse(self, statement: str) -> None:
        effect_formula, precondition_formula = self.get_effect_and_precondition(statement)
        if precondition_formula:
            formula = f"{precondition_formula} => {effect_formula}"
        else:
            formula = effect_formula
        return list(filter(lambda state: self.evaluate_formula(formula, state), self.transition_graph.generate_all_states()))


class ImpossibleParser(CustomParser):

    def get_action_and_precondition(self, statement):
        impossible_logic = statement.split("impossible")[1].strip()
        if 'if' in impossible_logic:
            action, precondition_formula = map(str.strip, impossible_logic.split("if"))
        else:
            action = impossible_logic
            precondition_formula = ""
        return action, precondition_formula

    def extract_actions(self, statement: str) -> str:
        action, _ = self.get_action_and_precondition(statement)
        return [action]

    def extract_fluents(self, statement: str) -> List[str]:
        _, precondition_formula = self.get_action_and_precondition(statement)
        return self.logical_formula_parser.extract_fluents(precondition_formula)

    def parse(self, statement: str) -> None:
        impossible_edges = []
        action, precondition_formula = self.get_action_and_precondition(statement)
        for from_state in self.transition_graph.generate_all_states():
            if self.evaluate_formula(precondition_formula, from_state):
                for to_state in self.transition_graph.generate_all_states():
                    impossible_edges.append(Edge(from_state, action, to_state))
        return impossible_edges


class NoninertialParser(CustomParser):
    
        def extract_actions(self, statement: str) -> str:
            return []
    
        def extract_fluents(self, statement: str) -> List[str]:
            noninertial_logic = statement.split("noninertial")[1].strip()
            return self.logical_formula_parser.extract_fluents(noninertial_logic)
    
        def parse(self, statement: str) -> None:
            pass