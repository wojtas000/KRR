import networkx as nx
import matplotlib.pyplot as plt
from itertools import product
from typing import List, Dict, Union


class StateNode:
    def __init__(self, fluents: Dict[str, bool]):
        self.fluents = fluents
        self.label = "\n".join([fluent if value else f"~{fluent}" for fluent, value in fluents.items()])

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
        self.all_states: List[StateNode] = []
        self.states: List[StateNode] = []
        self.edges: List[Edge] = []
        self.initial_state: Union[StateNode, None] = None

    def add_state(self, state: StateNode) -> None:
        if state not in self.states:
            self.states.append(state)

    def set_initial_state(self, state: StateNode) -> None:
        self.initial_state = state
        self.fluents = list(state.fluents.keys())
        self.all_states = [StateNode(dict(zip(self.fluents, values))) for values in product([True, False], repeat=len(self.fluents))]
        self.add_state(state)

    def add_edge(self, source: StateNode, action: str,
                 target: StateNode, duration: int) -> None:
        edge = Edge(source, action, target, duration)
        if edge not in self.edges:
            self.edges.append(edge)

    def generate_graph(self) -> plt.Figure:
        G = nx.DiGraph()
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, label=edge.label)
        for state in self.all_states:
            G.add_node(state, label=state.label)
        pos = nx.spring_layout(G)
        fig, ax = plt.subplots(figsize=(16, 16))
        nx.draw_networkx_nodes(G, pos, node_size=100, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='black', arrows=True, ax=ax)
        labels = {node: node.label for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=6)
        nx.draw_networkx_edge_labels(G, pos,
                                    edge_labels=nx.get_edge_attributes(G, 'label'),
                                    ax=ax, font_size=8)
        if self.initial_state in G.nodes():
            nx.draw_networkx_nodes(G, pos, nodelist=[self.initial_state], node_color='r', node_size=200, ax=ax)
        ax.axis('off')

        def on_zoom(event):
            ax.set_xlim(event.xdata - 0.5, event.xdata + 0.5)
            ax.set_ylim(event.ydata - 0.5, event.ydata + 0.5)
            fig.canvas.draw()

        fig.canvas.mpl_connect('scroll_event', on_zoom)

        return fig
