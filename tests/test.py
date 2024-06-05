from source.parsers.statement_parser import StatementParser
from source.graph.transition_graph import TransitionGraph


if __name__ == "__main__":
    statement_parser = StatementParser(transition_graph=TransitionGraph())
    statements= [
        'initially alive',
        'LOAD causes loaded',
        'SHOOT causes ~loaded',
        'SHOOT causes ~alive if loaded',
        '~alive after SHOOT',
        'LOAD lasts 1',
        'SHOOT lasts 2'
    ]

    for statement in statements:
        statement_parser.parse(statement)
    statement_parser.transition_graph.generate_graph()