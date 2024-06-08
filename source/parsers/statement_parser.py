import re
from typing import Tuple, List
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from source.parsers.custom_parsers import (
    InitiallyParser, 
    CausesParser, 
    ReleasesParser, 
    DurationParser,
    AfterParser,
    AlwaysParser,
    ImpossibleParser
)


class StatementParser:

    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph
        self.statements = {
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
            "lasts": DurationParser,
            "after": AfterParser,
            "always": AlwaysParser,
            "impossible": ImpossibleParser
        }

    def parse_statement(self, statement: str) -> None:
        keyword = next((k for k in self.parser_classes if k in statement), None)
        if keyword:
            parser = self.parser_classes[keyword](self.transition_graph)
            parser.parse(statement)
            self.transition_graph = parser.get_transition_graph()
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

    def parse(self, statements: str) -> None:
        for statement in statements:
            self.add_statement(statement)
        
        self.clear_transition_graph()
        self.transition_graph.add_fluents(self.extract_all_fluents())
        self.transition_graph.add_actions(self.extract_all_actions())

        for statement in self.prepare_statements():
            self.parse_statement(statement)
