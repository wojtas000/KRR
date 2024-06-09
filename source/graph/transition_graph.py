from itertools import product
from math import sqrt
from typing import Dict, List, Union

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


class StateNode:
    def __init__(self, fluents: Dict[str, bool]):
        self.fluents = fluents
        self.label = "\n".join(
            [
                fluent if value else f"~{fluent}"
                for fluent, value in fluents.items()
            ]
        )

    def __eq__(self, other: "StateNode") -> bool:
        return self.fluents == other.fluents

    def __hash__(self) -> int:
        return hash(frozenset(self.fluents.items()))

    def __str__(self) -> str:
        return self.label

    def update(self, fluents: Dict[str, bool]) -> None:
        self.fluents.update(fluents)
        self.label = "\n".join(
            [
                fluent if value else f"~{fluent}"
                for fluent, value in self.fluents.items()
            ]
        )


class Edge:
    def __init__(
        self,
        source: StateNode,
        action: str,
        target: StateNode,
        duration: int = 0,
    ):
        self.source = source
        self.action = action
        self.target = target
        self.duration = duration
        self.label = f"{action}\nDuration: {duration}"

    def __str__(self) -> str:
        return (
            f"{self.source} --{self.action}--> {self.target} ({self.duration})"
        )

    def __eq__(self, other: "Edge") -> bool:
        return (
            self.source == other.source
            and self.action == other.action
            and self.target == other.target
        )

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
        self.possible_ending_states = []
        self.always = []
        self.impossible = []
        self.always_states = []
        self.impossible_states = []

    def add_fluents(self, fluents: str) -> None:
        for fluent in fluents:
            if fluent not in self.fluents:
                self.fluents.append(fluent)

    def add_possible_initial_state(self, state: StateNode) -> None:
        self.possible_initial_states.append(state)

    def add_possible_ending_state(self, state: StateNode) -> None:
        self.possible_ending_states.append(state)

    def add_state(self, state: StateNode) -> None:
        if state not in self.states:
            self.states.append(state)

    def add_actions(self, actions: str) -> None:
        for action in actions:
            if action not in self.actions:
                self.actions.append(action)

    def remove_edge(
        self, action: str, from_state: StateNode, to_state: StateNode
    ) -> None:
        edges_copy = []
        for i, edge in enumerate(self.edges):
            if (
                edge.action == action
                and edge.source == from_state
                and edge.target == to_state
            ):
                continue
            edges_copy.append(edge)
        self.edges = edges_copy

    def generate_all_states(self) -> None:
        return [
            StateNode(dict(zip(self.fluents, values)))
            for values in product([True, False], repeat=len(self.fluents))
        ]

    def generate_possible_states(self) -> None:
        always_impossible_intersection = set(self.always_states) & set(self.impossible_states)
        if always_impossible_intersection:
            raise ValueError(
                f"Contradiction: state {always_impossible_intersection} is both always and impossible."
            )
        if self.always_states:
            return self.always_states
        all_states = self.generate_all_states()
        if self.impossible_states:
            return list(set(all_states) - set(self.impossible_states))
        return all_states

    def add_edge(
        self,
        source: StateNode,
        action: str,
        target: StateNode,
        duration: int = 0,
    ) -> None:
        edge = Edge(source, action, target, duration)
        if edge not in self.edges:
            self.edges.append(edge)

    def update_states_with_new_fluents(self) -> None:
        new_edges = []
        for edge in self.edges:
            new_fluents_source = set(self.fluents) - set(edge.source.fluents)
            new_fluents_target = set(self.fluents) - set(edge.target.fluents)

            source_state_combinations = self.generate_state_combinations(
                edge.source, new_fluents_source
            )
            self.states.extend(source_state_combinations)

            target_state_combinations = self.generate_state_combinations(
                edge.target, new_fluents_target
            )
            self.states.extend(target_state_combinations)

            for new_source in source_state_combinations:
                for new_target in target_state_combinations:
                    new_edges.append(
                        Edge(
                            new_source, edge.action, new_target, edge.duration
                        )
                    )

        self.edges.extend(new_edges)

    def generate_state_combinations(
        self, state: StateNode, new_fluents: Union[set, List]
    ) -> List[StateNode]:
        combinations = []
        for values in product([True, False], repeat=len(new_fluents)):
            new_state_fluents = state.fluents.copy()
            new_state_fluents.update(dict(zip(new_fluents, values)))
            combinations.append(StateNode(new_state_fluents))
        return combinations

    def generate_graph(self) -> nx.MultiDiGraph:
        G = nx.MultiDiGraph()

        for edge in self.edges:
            G.add_edge(edge.source, edge.target, label=edge.label, weight=edge.duration)

        for state in self.generate_possible_states():
            G.add_node(state)

        return G

    def draw_graph(self) -> plt.Figure:
        G = self.generate_graph()

        pos = nx.spring_layout(G, k=10 / sqrt(G.order()))
        fig, ax = plt.subplots(figsize=(20, 20))

        node_colors = []
        for node in G.nodes:
            if node in self.possible_initial_states:
                node_colors.append("green")
            elif node in self.possible_ending_states:
                node_colors.append("red")
            else:
                node_colors.append("lightblue")

        node_sizes = [1000 + 500 * len(str(node)) for node in G.nodes]
        nx.draw_networkx_nodes(
            G,
            pos,
            node_shape="o",
            node_size=node_sizes,
            ax=ax,
            node_color=node_colors,
            linewidths=1,
            edgecolors="black",
            alpha=0.3,
        )
        center_x = sum(x for x, y in pos.values()) / len(pos)
        center_y = sum(y for x, y in pos.values()) / len(pos)

        labels = {node: node.label for node in G.nodes()}
        label_positions = {}
        for node, (x, y) in pos.items():
            dx = x - center_x
            dy = y - center_y
            angle = np.arctan2(dy, dx)
            offset = 0.1  # Adjust this value to set the distance of the labels from the nodes
            label_positions[node] = (
                x + offset * np.cos(angle),
                y + offset * np.sin(angle),
            )
        nx.draw_networkx_labels(
            G,
            label_positions,
            labels,
            ax=ax,
            font_size=13,
            font_weight="bold",
            font_color="black",
            bbox=dict(
                facecolor="white", edgecolor="black", boxstyle="round,pad=0.2"
            ),
            alpha=0.8,
        )

        # Generate a color map for the edge labels dynamically
        unique_labels = list(set(nx.get_edge_attributes(G, "label").values()))
        colors = list(
            mcolors.TABLEAU_COLORS.keys()
        )  # Use a predefined color palette
        color_map = {
            label: colors[i % len(colors)][4:]
            for i, label in enumerate(unique_labels)
        }

        for edge in G.edges(data=True):
            u, v, label = edge
            edge_color = color_map.get(
                label["label"], "black"
            )  # Default to black if label not found
            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=[(u, v)],
                ax=ax,
                arrowstyle="->",
                arrowsize=30,
                edge_color=edge_color,
                width=2,
                connectionstyle="arc3,rad=0.10",  # Adjust 'rad' for more curvature
            )
        ax.set_zorder(2)

        edge_labels = nx.get_edge_attributes(G, "label")

        nx.draw_networkx_edge_labels(
            G,
            pos,
            edge_labels=edge_labels,
            ax=ax,
            font_size=10,
            font_weight="bold",
            font_color="black",
            label_pos=0.3,
            rotate=True,
        )

        ax.set_axis_off()

        return fig
