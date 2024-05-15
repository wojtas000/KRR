import streamlit as st
from transition_graph import TransitionGraph
from query_parser import QueryParser

st.title("Action Domain Transition Graph")

if "graph" not in st.session_state:
    st.session_state.graph = TransitionGraph()

new_statements = st.text_area("Enter statements (one per line):", height=200)
if st.button("Add Statements"):
    statements = new_statements.split("\n")
    for statement in statements:
        if statement.strip():
            st.session_state.graph.parse_statement(statement.strip())
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