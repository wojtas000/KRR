import networkx as nx
import matplotlib.pyplot as plt
from itertools import product
from typing import List, Dict, Union


class StateNode:
    def __init__(self, fluents: Dict[str, bool]):
        self.fluents = fluents
        self.label = "\n".join([f"{fluent}: {str(value).lower()}"
                                for fluent, value in fluents.items()])

    def __eq__(self, other: 'StateNode') -> bool:
        return self.fluents == other.fluents

    def __hash__(self) -> int:
        return hash(frozenset(self.fluents.items()))

    def __str__(self) -> str:
        return self.label


class Edge:
    def __init__(self, source: StateNode, action: str,
                 target: StateNode, duration: int):
        self.source = source
        self.action = action
        self.target = target
        self.duration = duration
        self.label = f"{action}\nDuration: {duration}"

    def __str__(self) -> str:
        return f"{self.source} --{self.action}--> {self.target} ({self.duration})"


class TransitionGraph:
    def __init__(self):
        self.states: List[StateNode] = []
        self.edges: List[Edge] = []
        self.initial_state: Union[StateNode, None] = None

    def add_state(self, state: StateNode) -> None:
        if state not in self.states:
            self.states.append(state)

    def set_initial_state(self, state: StateNode) -> None:
        self.initial_state = state

    def add_edge(self, source: StateNode, action: str,
                 target: StateNode, duration: int) -> None:
        self.edges.append(Edge(source, action, target, duration))

    def generate_graph(self) -> plt.Figure:
        G = nx.DiGraph()
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, label=edge.label)
        for state in self.states:
            G.add_node(state, label=state.label)
        pos = nx.spring_layout(G)
        fig, ax = plt.subplots(figsize=(8, 6))
        nx.draw_networkx_nodes(G, pos, node_size=500, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='black', arrows=True, ax=ax)
        nx.draw_networkx_labels(G, pos, labels={node: G.nodes[node]['label']
                                                for node in G.nodes()}, ax=ax)
        nx.draw_networkx_edge_labels(G, pos,
                                     edge_labels=nx.get_edge_attributes(G, 'label'),
                                     ax=ax)
        ax.axis('off')
        return fig

    def parse_initially(self, statement: str) -> None:
        fluents = statement.split("initially ")[1].split(" and ")
        fluent_dict = {}
        for fluent in fluents:
            if fluent.startswith("~"):
                fluent_dict[fluent[1:]] = False
            else:
                fluent_dict[fluent] = True
        self.add_state(StateNode(fluent_dict))
        self.set_initial_state(StateNode(fluent_dict))

    def parse_causes(self, statement: str) -> None:
        action, effect = statement.split(" causes ")
        effect_fluents = effect.split(" with time ")[0].split(" and ")
        duration = int(effect.split(" with time ")[1].strip().split(" ")[0])
        precondition = effect.split(" if ")[1] if " if " in effect else None
        effect_dict = {}
        for fluent in effect_fluents:
            if fluent.startswith("~"):
                effect_dict[fluent[1:]] = False
            else:
                effect_dict[fluent] = True
        for state in self.states:
            if precondition is None:
                new_fluents = state.fluents.copy()
                new_fluents.update(effect_dict)
                new_state = StateNode(new_fluents)
                self.add_state(new_state)
                self.add_edge(state, action, new_state, duration)

    def parse_statement(self, statement: str) -> 'TransitionGraph':
        if statement.startswith("initially"):
            self.parse_initially(statement)
        elif "causes" in statement:
            self.parse_causes(statement)
