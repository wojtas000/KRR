import re
from typing import Tuple, List
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from source.parsers.custom_parsers import (
    InitiallyParser, 
    CausesParser, 
    ReleasesParser, 
    LastsParser,
    AfterParser,
    AlwaysParser,
    ImpossibleParser,
    NoninertialParser
)


class StatementParser:

    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph
        self.statements = {
            "noninertial": [],
            "initially": [],
            "causes": [],
            "releases": [],
            "lasts": [],
            "after": [],
            "always": [],
            "impossible": []
        }
        self.parser_classes = {
            "initially": InitiallyParser,
            "causes": CausesParser,
            "releases": ReleasesParser,
            "lasts": LastsParser,
            "after": AfterParser,
            "always": AlwaysParser,
            "impossible": ImpossibleParser
        }

    def parse_statement(self, statement):
        keyword = next((k for k in self.parser_classes if k in statement), None)
        if keyword:
            parser = self.parser_classes[keyword](self.transition_graph)
            return parser.parse(statement)
        else:
            raise ValueError(f"Unsupported statement: {statement}")

    def add_statement(self, statement: str) -> None:
        keyword = next((k for k in self.statements if k in statement), None)
        if keyword:
            self.statements[keyword] = self.statements[keyword] + [statement]
        else:
            raise ValueError(f"Unsupported statement: {statement}") 

    def extract_all_actions(self) -> List[str]:
        actions = []
        for statement in self.prepare_statements():
            keyword = next((k for k in self.parser_classes if k in statement), None)
            if keyword:
                parser = self.parser_classes[keyword](self.transition_graph)
                actions += parser.extract_actions(statement)
            else:
                raise ValueError(f"Unsupported statement: {statement}")
        return actions  

    def extract_all_fluents(self) -> List[str]:
        fluents = []
        for statement in self.prepare_statements():
            keyword = next((k for k in self.parser_classes if k in statement), None)
            if keyword:
                parser = self.parser_classes[keyword](self.transition_graph)
                fluents += parser.extract_fluents(statement)
            else:
                raise ValueError(f"Unsupported statement: {statement}")
        return fluents

    def clear_transition_graph(self) -> None:
        self.transition_graph = TransitionGraph()

    def prepare_statements(self) -> List[str]:
        return  self.statements["always"] + self.statements["impossible"] + \
                self.statements["initially"] + self.statements["causes"] + self.statements["releases"] + \
                self.statements["after"] + self.statements["lasts"]

    def group_causes_statements_by_action(self, causes_statements) -> dict:
        causes_statements_by_action = {}
        for statement in causes_statements:
            action = CausesParser(self.transition_graph).extract_actions(statement)[0]
            if action in causes_statements_by_action:
                causes_statements_by_action[action] = causes_statements_by_action[action] + [statement]
            else:
                causes_statements_by_action[action] = [statement]
        return causes_statements_by_action

    def merge_initially_statements(self, statements: List[str]) -> str:
        base_statement = "initially" + f"({statements[0].split('initially')[1].strip()})"
        for statement in statements[1:]:
            base_statement += f" & ({statement.split('initially')[1].strip()})"
        return base_statement

    def parse(self, statements: str) -> None:
        
        # Prepare transition graph: clear graph, add all fluents and actions.

        for statement in statements:
            self.add_statement(statement)
        
        self.clear_transition_graph()
        self.transition_graph.add_fluents(self.extract_all_fluents())
        self.transition_graph.add_actions(self.extract_all_actions())

        # Parse always and impossible statements

        for statement in self.statements['always']:
            always_states = self.parse_statement(statement)
            self.transition_graph.always_states.extend(always_states)
        
        for statement in self.statements['impossible']:
            impossible_edges = self.parse_statement(statement)
            self.transition_graph.add_impossible_edges(impossible_edges)

        self.transition_graph.states = self.transition_graph.generate_possible_states()

        # Parse causes statements
        grouped_causes_statements = self.group_causes_statements_by_action(self.statements['causes'])
        for action, statements in grouped_causes_statements.items():
            edges = self.parser_classes['causes'](self.transition_graph).parse(statements)
            self.transition_graph.add_edges(edges)
        
        # Parse releases statements

        for statement in self.statements['releases']:
            edges = self.parse_statement(statement)
            self.transition_graph.add_edges(edges)

        # Parse initially statements
        if self.statements['initially']:
            initially_statement = self.merge_initially_statements(self.statements['initially'])
            self.transition_graph.add_possible_initial_states(self.parse_statement(initially_statement))

        # Parse after statements
        for statement in self.statements['after']:
            initial_states_for_removal, possible_ending_states = self.parse_statement(statement)
            self.transition_graph.remove_possible_initial_states(initial_states_for_removal)
            self.transition_graph.add_possible_ending_states(possible_ending_states)

        # Parse lasts statements
        for statement in self.statements['lasts']:
            durations = self.parse_statement(statement)
            self.transition_graph.add_durations(durations)

        # Parse noninertial statements
        for statement in self.statements['noninertial']:
            pass