import re
from typing import Tuple, List
from source.graph.transition_graph import TransitionGraph, StateNode, Edge
from source.parsers.custom_parser import InitiallyParser, CausesParser, ReleasesParser, DurationParser

class StatementParser:

    def __init__(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph
        self.statements = []
        self.parser_classes = {
            "initially": InitiallyParser,
            "causes": CausesParser,
            "releases": ReleasesParser,
            "lasts": DurationParser
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
        if "initially" in statement:
            self.statements.insert(0, statement)
        elif "causes" in statement or "releases" in statement:
            insert_index = next((i for i, s in enumerate(self.statements) if s.startswith("lasts")), len(self.statements))
            self.statements.insert(insert_index, statement)
        elif "lasts" in statement:
            self.statements.append(statement)

    def extract_all_fluents(self) -> List[str]:
        for statement in self.statements:
            keyword = next((k for k in self.parser_classes if k in statement), None)
            if keyword:
                parser = self.parser_classes[keyword](self.transition_graph)
                fluents = parser.extract_fluents(statement)
                for fluent in fluents:
                    self.transition_graph.add_fluent(fluent)
            else:
                raise ValueError(f"Unsupported statement: {statement}")

    def parse(self, statement: str) -> None:
        self.add_statement(statement)
        self.extract_all_fluents()
        for statement in self.statements:
            self.parse_statement(statement)
