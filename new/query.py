import networkx as nx
import streamlit as st

def change_string(s, i, nowy_znak):
    if i < 0 or i >= len(s):
        raise IndexError("Indeks poza zakresem")
    nowy_string = s[:i] + nowy_znak + s[i+1:]
    return nowy_string

def find_next_state(graph, state, action):
    """Finds the next state after performing the given action from the given state."""
    for u, v, key, data in graph.edges(data=True, keys=True):
        if u == state and data['label'] == action:
            return v, data['weight']
    return None, 0

def find_last_state(graph, state, actions):
    """Finds the last state after performing the sequence of actions from the given state."""
    subcost = 0
    for action in actions:
        state, subcost = find_next_state(graph, state, action.replace(' ',''))
        if state is None:
            return None
        else:
            subcost += subcost
    return state, subcost

def state_satisfies(state, conditions, fluents2order):
    """Checks if a given state satisfies the given conditions."""
    for condition in conditions.split('&'):
        condition = condition.strip()
        if '~' in condition:
            fluent = condition.replace('~', '')
            if state[fluents2order[fluent]] != '0':
                return False
        else:
            fluent = condition
            if state[fluents2order[fluent]] != '1':
                return False
    return True


def necessary_alpha_after(graph, alpha, actions, pi, fluents2order):
    """Checks if α always holds after performing the sequence of actions from any state satisfying π."""
    for state in graph.nodes:
        if state_satisfies(state, pi, fluents2order):
            # st.write(state)
            # st.write(actions)
            final_state, _ = find_last_state(graph, state, actions)
            if final_state is None or not state_satisfies(final_state, alpha, fluents2order):
                st.write('α always holds after performing the sequence of actions from any state satisfying π?')
                return False
    st.write('α always holds after performing the sequence of actions from any state satisfying π?')
    return True

def possibly_alpha_after(graph, alpha, actions, pi, fluents2order):
    """Checks if α sometimes holds after performing the sequence of actions from any state satisfying π."""
    for state in graph.nodes:
        if state_satisfies(state, pi, fluents2order):
            final_state, _ = find_last_state(graph, state, actions)
            if final_state is not None and state_satisfies(final_state, alpha, fluents2order):
                st.write('α sometimes holds after performing the sequence of actions from any state satisfying π?')
                return True
    st.write('α sometimes holds after performing the sequence of actions from any state satisfying π?')
    return False


def necessary_executable(graph, actions, pi, fluents2order):
    """Checks if the sequence of actions is always executable from any state satisfying π."""
    for state in graph.nodes:
        if state_satisfies(state, pi, fluents2order):
            final_state, _ = find_last_state(graph, state, actions)
            if final_state is None:
                st.write('The sequence of actions is always executable from any state satisfying π?')
                return False
    st.write('The sequence of actions is always executable from any state satisfying π?')
    return True

def possibly_executable(graph, actions, pi, fluents2order):
    """Checks if the sequence of actions is sometimes executable from any state satisfying π."""
    for state in graph.nodes:
        if state_satisfies(state, pi, fluents2order):
            final_state, _ = find_last_state(graph, state, actions)
            if final_state is not None:
                st.write('The sequence of actions is sometimes executable from any state satisfying π?')
                return True
    st.write('The sequence of actions is sometimes executable from any state satisfying π?')
    return False


def necessary_executable_with_cost(graph, actions, pi, max_cost, fluents2order):
    """Checks if the sequence of actions is always executable with a total cost ≤ max_cost from any state satisfying π."""
    for state in graph.nodes:
        if state_satisfies(state, pi, fluents2order):
            final_state, total_cost = find_last_state(graph, state, actions)
            if final_state is None or total_cost > max_cost:
                st.write('The sequence of actions is always executable with a total cost ≤ max_cost from any state satisfying π?')
                st.write('Minimum cost:', total_cost)
                return False
    st.write('The sequence of actions is always executable with a total cost ≤ max_cost from any state satisfying π?')
    st.write('Minimum cost:', total_cost)
    return True

def possibly_executable_with_cost(graph, actions, pi, max_cost, fluents2order):
    """Checks if the sequence of actions is sometimes executable with a total cost ≤ max_cost from any state satisfying π."""
    for state in graph.nodes:
        if state_satisfies(state, pi, fluents2order):
            final_state, total_cost = find_last_state(graph, state, actions)
            if final_state is not None and total_cost <= max_cost:
                st.write('The sequence of actions is sometimes executable with a total cost ≤ max_cost from any state satisfying π?')
                st.write('Minimum cost:', total_cost)
                return True
    st.write('The sequence of actions is sometimes executable with a total cost ≤ max_cost from any state satisfying π?')
    st.write('Minimum cost:', total_cost)
    return False
