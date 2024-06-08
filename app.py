import streamlit as st
from source.graph.transition_graph import TransitionGraph
from source.parsers.query_parser import QueryParser
from source.parsers.statement_parser import StatementParser

def load_examples(file_path):
    examples = {}
    current_example = None
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#'):
                current_example = line[1:].strip()
                examples[current_example] = []
            elif current_example:
                examples[current_example].append(line)
    return examples

st.title("Action Domain Transition Graph")

if "statement_parser" not in st.session_state:
    st.session_state.statement_parser = StatementParser(TransitionGraph())

examples = load_examples('tests/examples.txt')
example_names = list(examples.keys())
selected_example = st.selectbox("Select an example:", example_names)

if selected_example:
    st.write(f"Selected Example: {selected_example}")
    example_statements = examples[selected_example]
    st.text_area("Example Statements:", value="\n".join(example_statements), height=200, disabled=True)

    if st.button("Parse Selected Example"):
        statements = [s.strip() for s in example_statements if s]
        st.session_state.statement_parser = StatementParser(TransitionGraph())
        st.session_state.statement_parser.parse(statements)
        fig = st.session_state.statement_parser.transition_graph.draw_graph()
        st.write("Fluents:", ", ".join(st.session_state.statement_parser.transition_graph.fluents))
        st.write("Actions:", ", ".join(st.session_state.statement_parser.transition_graph.actions))
        st.write("Graph:")
        st.pyplot(fig)


st.subheader("Manual Input")
new_statements = st.text_area("Enter statements (one per line):", height=200)
if st.button("Add Statements"):
    statements = new_statements.split("\n")
    statements = [s.strip() for s in statements if s]
    st.session_state.statement_parser = StatementParser(TransitionGraph())
    st.session_state.statement_parser.parse(statements)
    fig = st.session_state.statement_parser.transition_graph.draw_graph()
    st.write("Fluents:", ", ".join(st.session_state.statement_parser.transition_graph.fluents))
    st.write("Actions:", ", ".join(st.session_state.statement_parser.transition_graph.actions))
    st.write("Graph:")
    st.pyplot(fig)

query_parser = QueryParser(st.session_state.statement_parser.transition_graph)

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