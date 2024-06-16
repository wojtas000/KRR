import networkx as nx
import streamlit as st
class QueryParser:
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    @staticmethod
    def change_string(s, i, nowy_znak):
        if i < 0 or i >= len(s):
            raise IndexError("Index out of range")
        return s[:i] + nowy_znak + s[i+1:]

    def find_next_state(self, state, action):
        """Finds the next state after performing the given action from the given state."""
        for u, v, key, data in list(self.graph.edges(data=True, keys=True)):
            if 'action' in data:
                if u == state and data['action'] == action:
                    return v, data['weight']
        return None, 0

    def find_last_state(self, state, actions):
        """Finds the last state after performing the sequence of actions from the given state."""
        cost = 0
        for action in actions:
            state, subcost = self.find_next_state(state, action.replace(' ',''))
            if state is None:
                return None, 0
            else:
                cost += subcost
        return state, cost

    @staticmethod
    def state_satisfies(state, conditions):
        """Checks if a given state satisfies the given conditions."""
        for condition in conditions.split('&'):
            condition = condition.strip()
            if '~' in condition:
                fluent = condition.replace('~', '')
                if state.fluents[fluent] != False:
                    return False
            else:
                fluent = condition
                if state.fluents[fluent] != True:
                    return False
        return True

    def necessary_alpha_after(self, alpha, actions, pi):
        """Checks if α always holds after performing the sequence of actions from any state satisfying π."""
        for state in list(self.graph.nodes):
            if self.state_satisfies(state, pi):
                final_state, _ = self.find_last_state(state, actions)
                if final_state is None or not self.state_satisfies(final_state, alpha):
                    return False
        return True

    def possibly_alpha_after(self, alpha, actions, pi):
        """Checks if α sometimes holds after performing the sequence of actions from any state satisfying π."""
        for state in list(self.graph.nodes):
            if self.state_satisfies(state, pi):
                # st.write(state)
                # st.write(pi)
                final_state, _ = self.find_last_state(state, actions)
                # st.write(final_state)
                if final_state is not None and self.state_satisfies(final_state, alpha):
                    return True
        return False

    def necessary_executable(self, actions, pi):
        """Checks if the sequence of actions is always executable from any state satisfying π."""
        for state in list(self.graph.nodes):
            if self.state_satisfies(state, pi):
                final_state, _ = self.find_last_state(state, actions)
                if final_state is None:
                    return False
        return True

    def possibly_executable(self, actions, pi):
        """Checks if the sequence of actions is sometimes executable from any state satisfying π."""
        for state in list(self.graph.nodes):
            if self.state_satisfies(state, pi):
                final_state, _ = self.find_last_state(state, actions)
                if final_state is not None:
                    return True
        return False

    def necessary_executable_with_cost(self, actions, pi, max_cost):
        """Checks if the sequence of actions is always executable with a total cost ≤ max_cost from any state satisfying π."""
        for state in list(self.graph.nodes):
            if self.state_satisfies(state, pi):
                final_state, total_cost = self.find_last_state(state, actions)
                st.write('total_cost', total_cost)
                if final_state is None or total_cost > max_cost:
                    return False
        return True

    def possibly_executable_with_cost(self, actions, pi, max_cost):
        """Checks if the sequence of actions is sometimes executable with a total cost ≤ max_cost from any state satisfying π."""
        for state in list(self.graph.nodes):
            if self.state_satisfies(state, pi):
                final_state, total_cost = self.find_last_state(state, actions)
                st.write('total_cost', total_cost)
                if final_state is not None and total_cost <= max_cost:
                    return True
        return False