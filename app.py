import streamlit as st
from transition_graph import TransitionGraph

st.title("Action Domain Transition Graph")

graph = TransitionGraph()

# Add states and edges

new_statement = st.text_input("Enter a statement:")
if st.button("Add Statement"):
    graph.parse_statement(new_statement)
    fig = graph.generate_graph()
    st.pyplot(fig)


# Execute queries

st.subheader("Queries")
query = st.text_input("Enter a query:")
if st.button("Execute Query"):
    # Implement query execution logic here
    # Display the query results
    st.write("Query:", query)
    st.write("Answer: (Not implemented yet)")