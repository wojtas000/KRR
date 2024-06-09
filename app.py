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

st.title("Knowledge Representation and Reasoning: Actions with Duration")

if "statement_parser" not in st.session_state:
    st.session_state.statement_parser = StatementParser(TransitionGraph())

if "query_parser" not in st.session_state:
    st.session_state.query_parser = QueryParser(TransitionGraph())

if "transition_graph" not in st.session_state:
    st.session_state.transition_graph = TransitionGraph()

tab1, tab2, tab3 = st.tabs(["Examples", "Manual Input", "Queries"])

with tab1:
    st.subheader("Examples")
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
            st.session_state.transition_graph = st.session_state.statement_parser.transition_graph
            fig = st.session_state.statement_parser.transition_graph.draw_graph()
            st.write("Fluents:", ", ".join(st.session_state.statement_parser.transition_graph.fluents))
            st.write("Actions:", ", ".join(st.session_state.statement_parser.transition_graph.actions))
            st.write("Graph:")
            st.pyplot(fig)

with tab2:
    st.subheader("Manual Input")
    new_statements = st.text_area("Enter statements (one per line):", height=200)
    if st.button("Add Statements"):
        statements = new_statements.split("\n")
        statements = [s.strip() for s in statements if s]
        st.session_state.statement_parser = StatementParser(TransitionGraph())
        st.session_state.statement_parser.parse(statements)
        st.session_state.transition_graph = st.session_state.statement_parser.transition_graph
        fig = st.session_state.statement_parser.transition_graph.draw_graph()
        st.write("Fluents:", ", ".join(st.session_state.statement_parser.transition_graph.fluents))
        st.write("Actions:", ", ".join(st.session_state.statement_parser.transition_graph.actions))
        st.write("Graph:")
        st.pyplot(fig)


with tab3:
    st.session_state.query_parser = QueryParser(st.session_state.transition_graph.generate_graph())

    st.subheader("Queries")
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
        'necessary_alpha_after': [st.session_state.query_parser.necessary_alpha_after, (alpha, actions, pi)],
        'possibly_alpha_after': [st.session_state.query_parser.possibly_alpha_after, (alpha, actions, pi)],
        'necessary_executable': [st.session_state.query_parser.necessary_executable, (actions, pi)],
        'possibly_executable': [st.session_state.query_parser.possibly_executable, (actions, pi)],
        'necessary_executable_with_cost': [st.session_state.query_parser.necessary_executable_with_cost, (actions, pi, max_cost)],
        'possibly_executable_with_cost': [st.session_state.query_parser.possibly_executable_with_cost, (actions, pi, max_cost)]
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

    args_ = args2func[query][1]
    st.write('Arguments:', *argnames2func[query])
    all_filled = all([arg != '' and arg is not None for arg in args_])

    if all_filled:
        result = args2func[query][0](*args_)
        st.write('Result:', result)
    else:
        st.write('Fill all arguments to get result')