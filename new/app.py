import streamlit as st
import pandas as pd
import numpy as np
import pickle
import networkx as nx
import matplotlib.pyplot as plt
from query import *

st.write('Enter sentences and queries to check the model')
st.write('Possible syntax:')
st.write('initially <fluent>;')
st.write('<Action> causes <fluent>;')
st.write('<Action> causes <fluent> if <condition>;')

sentences_ = st.text_area('Enter sentences: ', '''initially ¬loaded;
initially alive;
Load causes loaded;
Shoot causes ¬loaded;
Shoot causes ¬alive if loaded;''')

# try:
sentences = sentences_.replace('¬','~').replace(' and ','&').split(';')[:-1]

tab1, tab2 = st.tabs(['Sentences', 'Queries'])

with tab1:
    st.write('Sentences:',sentences)

    # Przetwarzanie zdania początkowego
    initials = [sent for sent in sentences if 'initially' in sent]
    fluents = {}
    for sent in initials:
        sent = sent.replace('initially','')
        for sub_sent in sent.split('&'):
            sub_sent = sub_sent.strip()
            if sub_sent.replace('~','') in fluents:
                assert fluents[sub_sent.replace('~','')] == (True if '~' not in sub_sent else False), 'Initial values are conflicting for ' + '"' + sub_sent + '"'
            fluents[sub_sent.replace('~','')] = True if '~' not in sub_sent else False
    st.write('Fluents:', fluents)        

    # Mapowanie kolejności do fluentów
    order2fluents = {}
    for i, key in enumerate(fluents.keys()):
        order2fluents[i] = key
    fluents2order = {}
    for i, key in enumerate(fluents.keys()):
        fluents2order[key] = i
        
    # Tworzenie grafu z multi-edge directed
    G = nx.MultiDiGraph()
    for i in range(2**len(fluents)):
        G.add_node(np.binary_repr(i, width=len(fluents)))

    # Przetwarzanie akcji i przejść
    causes = [sent for sent in sentences if 'causes' in sent]
    actions = list(set([sent.split('causes')[0].strip() for sent in causes]))
    transitions = {}
    for action in actions:
        sents_with_action = [sent for sent in causes if action in sent]
        transitions[action] = []
        
        for sent in sents_with_action:
            what_causes = sent.split('causes')[1].split('if')[0].strip()
            if_what = sent.split('if')
            if len(if_what) > 1:
                if_what = if_what[1].strip()
            else:
                if_what = None
            transitions[action].append((what_causes, if_what))
        
        for node in G.nodes:
            next_node = node
            for trans in transitions[action]:
                if trans[1] is not None:   
                    if trans[1].replace('~','') not in fluents:
                        st.error('Fluent ' + '"' + trans[1].replace('~','') + '"' + ' not defined in initial state')
                    if int(node[fluents2order[trans[1].replace('~','')]]) != (1 if '~' not in trans[1] else 0):
                        continue
                value = 1 if '~' not in trans[0] else 0
                next_node = change_string(next_node, fluents2order[trans[0].replace('~','')], str(value))
            G.add_edge(node, next_node)
            G.edges[node, next_node, 0]['label'] = action
            G.edges[node, next_node, 0]['weight'] = 1
            G.edges[node, next_node, 0]['color'] = 'black'

    st.write('Actions:', actions)

    initial_node = ''
    for state in fluents.keys():
        initial_node += '1' if fluents[state] else '0'
        
    G.nodes[initial_node]['color'] = 'green'

    # Funkcja do rysowania grafu z etykietami na krawędziach
    def draw_graph(graph):
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(graph)  # Pozycjonowanie wierzchołków
        
        # Rysowanie wierzchołków, jesli ma kolor to z kolorem
        for node in graph.nodes():
            color = 'skyblue'
            if 'color' in graph.nodes[node]:
                color = graph.nodes[node]['color']
            nx.draw_networkx_nodes(graph, pos, nodelist=[node], node_color=color, node_size=700)
            
        # Rysowanie krawędzi
        edge_labels = {}
        for edge in graph.edges(data=True):
            edge_labels[(edge[0], edge[1])] = edge[2]['label']
            color = 'black'
            if 'color' in edge[2]:
                color = edge[2]['color']
            nx.draw_networkx_edges(graph, pos, edgelist=[(edge[0], edge[1])], edge_color=color, width=2)        
        # Rysowanie etykiet na krawędziach
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
        
        plt.axis('off')
        st.pyplot(plt)
        
    draw_graph(G)

with tab2:

    st.write('Enter query:')
    st.write('Alpha: desired state')
    alpha = st.text_input('Alpha:')
    st.write('Actions: list of actions to be performed')
    actions = st.text_input('Actions:').split(',')
    st.write('Pi: initial state')
    pi = st.text_input('Pi:')
    st.write('Max cost: maximum cost of actions')
    max_cost = st.text_input('Max cost:')
    max_cost = int(max_cost) if max_cost != '' else None

    args2func = {
        'necessary_alpha_after': [necessary_alpha_after, (G, alpha, actions, pi, fluents2order)],
        'possibly_alpha_after': [possibly_alpha_after, (G, alpha, actions, pi, fluents2order)],
        'necessary_executable': [necessary_executable, (G, actions, pi, fluents2order)],
        'possibly_executable': [possibly_executable, (G, actions, pi, fluents2order)],
        'necessary_executable_with_cost': [necessary_executable_with_cost, (G, actions, pi, max_cost, fluents2order)],
        'possibly_executable_with_cost': [possibly_executable_with_cost, (G, actions, pi, max_cost, fluents2order)]
    }

    argnames2func = {
        'necessary_alpha_after': ['alpha', 'actions', 'pi'],
        'possibly_alpha_after': ['alpha', 'actions', 'pi'],
        'necessary_executable': ['actions', 'pi'],
        'possibly_executable': ['actions', 'pi'],
        'necessary_executable_with_cost': ['actions', 'pi', 'max_cost'],
        'possibly_executable_with_cost': ['actions', 'pi', 'max_cost']
    }

    query = st.selectbox('Choose query:', list(args2func.keys()))

    # check if all arguments are filled
    args_ = args2func[query][1]
    st.write('Arguments:', *argnames2func[query])
    all_filled = all([True if arg != '' else False for arg in args_[1:]])
    if all_filled:
        result = args2func[query][0](*args_)
        st.write('Result:', result)
    else:
        st.write('Fill all arguments to get result')
# except:
#     st.write('Fill sentences to get started')