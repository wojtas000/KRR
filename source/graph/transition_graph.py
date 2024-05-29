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

    def update(self, fluents: Dict[str, bool]) -> None:
        self.fluents.update(fluents)
        self.label = "\n".join([fluent if value else f"~{fluent}" for fluent, value in self.fluents.items()])


class Edge:
    def __init__(self, source: StateNode, action: str,
                 target: StateNode, duration: int = 0):
        self.source = source
        self.action = action
        self.target = target
        self.duration = duration
        self.label = f"{action}\nDuration: {duration}"

    def __str__(self) -> str:
        return f"{self.source} --{self.action}--> {self.target} ({self.duration})"

    def add_duration(self, duration: int) -> None:
        self.duration = duration
        self.label = f"{self.action}\nDuration: {duration}"


class TransitionGraph:
    def __init__(self):
        self.fluents: List[str] = []
        self.actions: List[str] = []
        self.states: List[StateNode] = []
        self.edges: List[Edge] = []
        self.possible_initial_states = []

    def add_fluent(self, fluent: str) -> None:
        if fluent not in self.fluents:
            self.fluents.append(fluent)

    def add_possible_initial_state(self, state: StateNode) -> None:
        self.possible_initial_states.append(state)

    def add_state(self, state: StateNode) -> None:
        if state not in self.states:
            self.states.append(state)

    def add_action(self, action: str) -> None:
        if action not in self.actions:
            self.actions.append(action)

    def generate_all_states(self) -> None:
        return [StateNode(dict(zip(self.fluents, values))) for values in product([True, False], repeat=len(self.fluents))]

    def add_edge(self, source: StateNode, action: str,
                 target: StateNode, duration: int = 0) -> None:
        edge = Edge(source, action, target, duration)
        if edge not in self.edges:
            self.edges.append(edge)

    def update_states_with_new_fluents(self) -> None:
        new_edges = []
        for edge in self.edges:
            new_fluents_source = set(self.fluents) - set(edge.source.fluents)
            new_fluents_target = set(self.fluents) - set(edge.target.fluents)

            source_state_combinations = self.generate_state_combinations(edge.source, new_fluents_source)
            self.states.extend(source_state_combinations)

            target_state_combinations = self.generate_state_combinations(edge.target, new_fluents_target)
            self.states.extend(target_state_combinations)

            for new_source in source_state_combinations:
                for new_target in target_state_combinations:
                    new_edges.append(Edge(new_source, edge.action, new_target, edge.duration))

        self.edges.extend(new_edges)

    def generate_state_combinations(self, state: StateNode, new_fluents: Union[set, List]) -> List[StateNode]:
        combinations = []
        for values in product([True, False], repeat=len(new_fluents)):
            new_state_fluents = state.fluents.copy()
            new_state_fluents.update(dict(zip(new_fluents, values)))
            combinations.append(StateNode(new_state_fluents))
        return combinations
           
                    

    def generate_graph(self, layout_func=nx.kamada_kawai_layout) -> plt.Figure:
        G = nx.DiGraph()
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, label=edge.label)
        
        for state in self.generate_all_states():
            G.add_node(state, label=state.label)
        pos = nx.spring_layout(G, k=1.5, iterations=50)

        fig, ax = plt.subplots(figsize=(12, 12)) 

        node_sizes = [1000 + 200 * len(str(node)) for node in G.nodes]  
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, ax=ax, node_color='lightblue', linewidths=1, edgecolors='black', alpha=0.8)

        labels = {node: node.label for node in G.nodes()}
        nx.draw_networkx_labels(
            G, 
            pos, 
            labels, 
            ax=ax, 
            font_size=10, 
            font_weight='bold', 
            font_color='black', 
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2'),
            alpha=0.8
        )


        for edge in G.edges():
            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=[edge],
                ax=ax,
                arrowstyle='-|>',
                arrowsize=20,
                edge_color='black',
                connectionstyle='arc3,rad=0.2',
                width=2,
            )
        ax.set_zorder(2)
        
        nx.draw_networkx_edge_labels(
            G, 
            pos, 
            edge_labels=nx.get_edge_attributes(G, 'label'), 
            ax=ax, 
            font_size=10, 
            font_weight='bold', 
            font_color='black', 
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2'),
            alpha=0.8
        )


        ax.set_axis_off()

        return fig
