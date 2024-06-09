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

def display_aligned_text(text):
    st.markdown(
        f"<div style='padding-top: 35px; font-weight: bold; text-align: center;'>{text}</div>",
        unsafe_allow_html=True
    )


def display_statement(statement_type, statement):
    color_mapping = {
        "initially": "green",
        "causes": "blue",
        "releases": "red",
        "lasts": "orange",
        "after": "purple",
        "always": "brown",
        "impossible": "black"
    }

    color = color_mapping.get(statement_type, "black")  # Default to black if statement type not found

    st.markdown(f"<p style='color:{color}; font-size:18px; font-weight:bold;'>{statement}</p>", unsafe_allow_html=True)


st.title("Knowledge Representation and Reasoning: Actions with Duration")

if "statement_parser" not in st.session_state:
    st.session_state.statement_parser = StatementParser(TransitionGraph())

if "query_parser" not in st.session_state:
    st.session_state.query_parser = QueryParser(TransitionGraph())

if "transition_graph" not in st.session_state:
    st.session_state.transition_graph = TransitionGraph()

if "statements" not in st.session_state:
    st.session_state.statements = []

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
    
    statement_types = ["initially", "causes", "releases", "lasts", "after", "always", "impossible"]
    selected_statement = st.selectbox("Select statement type:", statement_types)
    
    statement = ""
    if selected_statement == "initially":
        col1, col2 = st.columns([1, 2])
        with col1:
            display_aligned_text("initially")
        with col2:
            initial_formula = st.text_input("Initial formula:")
        statement = f"initially {initial_formula}"
    
    elif selected_statement == "causes":
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 2])
        with col1:
            action = st.text_input("Action:")
        with col2:
            display_aligned_text("causes")
        with col3:
            effect = st.text_input("Effect formula:")
        with col4:
            display_aligned_text("if")
        with col5:
            precondition = st.text_input("Precondition formula:")
        statement = f"{action} causes {effect} if {precondition}"
    
    elif selected_statement == "releases":
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 2])
        with col1:
            action = st.text_input("Action:")
        with col2:
            display_aligned_text("releases")
        with col3:
            effect = st.text_input("Effect formula:")
        with col4:
            display_aligned_text("if")
        with col5:
            precondition = st.text_input("Precondition formula:")
        statement = f"{action} releases {effect} if {precondition}"
    
    elif selected_statement == "lasts":
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            action = st.text_input("Action:")
        with col2:
            display_aligned_text("lasts")
        with col3:
            time = st.text_input("Time:")
        statement = f"{action} lasts {time}"
    
    elif selected_statement == "after":
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            effect = st.text_input("Effect formula:")
        with col2:
            display_aligned_text("after")
        with col3:
            action = st.text_input("Action:")
        statement = f"{effect} after {action}"
    
    elif selected_statement == "always":
        col1, col2 = st.columns([1, 2])
        with col1:
            display_aligned_text("always")
        with col2:
            formula = st.text_input("Formula:")
        statement = f"always {formula}"
    
    elif selected_statement == "impossible":
        col1, col2 = st.columns([1, 2])
        with col1:
            display_aligned_text("impossible")
        with col2:
            formula = st.text_input("Formula:")
        statement = f"impossible {formula}"
    
    if st.button("Add Statement", key="add_statement"):
        st.session_state.statements.append((selected_statement, statement))
        st.write("Current Statements:")
        for stmt_type, stmt in st.session_state.statements:
            display_statement(stmt_type, stmt)

    if st.button("Parse Statements"):
        st.session_state.statement_parser = StatementParser(TransitionGraph())
        st.session_state.statement_parser.parse([stmt for _, stmt in st.session_state.statements])
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