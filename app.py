import streamlit as st
from transition_graph import TransitionGraph
from query_parser import QueryParser

st.title("Action Domain Transition Graph")

if "graph" not in st.session_state:
    st.session_state.graph = TransitionGraph()

# States and edges
new_statement = st.text_input("Enter a statement:")
if st.button("Add Statement"):
    st.session_state.graph.parse_statement(new_statement)

fig = st.session_state.graph.generate_graph()
st.pyplot(fig)

query_parser = QueryParser(st.session_state.graph)

# Queries
st.subheader("Queries")
query = st.text_input("Enter a query:")
if st.button("Execute Query"):
    try:
        result = query_parser.parse_query(query)
        st.write("Query:", query)
        st.write("Answer:", "Yes" if result else "No")
    except ValueError as e:
        st.write("Invalid query format.")