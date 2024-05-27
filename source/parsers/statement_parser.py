from source.graph.transition_graph import TransitionGraph


class StatementParser:
    def init(self, transition_graph: TransitionGraph):
        self.transition_graph = transition_graph

    def parse_initially(self, statement: str) -> None:
        fluents = statement.split("initially ")[1].split(" and ")
        fluent_dict = {}
        for fluent in fluents:
            if fluent.startswith("~"):
                fluent_dict[fluent[1:]] = False
            else:
                fluent_dict[fluent] = True
        self.transition_graph.add_state(StateNode(fluent_dict))
        self.transition_graph.set_initial_state(StateNode(fluent_dict))

    def parse_causes(self, statement: str) -> None:
        action, effect = statement.split(" causes ")
        effect_fluents = effect.split(" if ")[0].split(" and ")
        precondition = effect.split(" if ")[1] if " if " in effect else None
        effect_dict = {}
        for fluent in effect_fluents:
            if fluent.startswith("~"):
                effect_dict[fluent[1:]] = False
            else:
                effect_dict[fluent] = True
        for state in self.transition_graph.all_states:
            if precondition is None or all(
                state.fluents.get(fluent[1:], True) == (not fluent.startswith("~"))
                for fluent in precondition.split(" and ")
            ):
                new_fluents = state.fluents.copy()
                new_fluents.update(effect_dict)
                new_state = StateNode(new_fluents)
                self.transition_graph.add_state(new_state)
                duration = self.transition_graph.action_durations.get(action, 1)
                self.transition_graph.add_edge(state, action, new_state, duration)

    def parse_releases(self, statement: str) -> None:
        action, effect = statement.split(" releases ")
        effect_fluents = effect.split(" if ")[0].split(" and ")
        precondition = effect.split(" if ")[1] if " if " in effect else None
        effect_dict = {}
        for fluent in effect_fluents:
            effect_dict[fluent] = False
        for state in self.transition_graph.all_states:
            if precondition is None or all(
                state.fluents.get(fluent[1:], True) == (not fluent.startswith("~"))
                for fluent in precondition.split(" and ")
            ):
                new_fluents = state.fluents.copy()
                for fluent, value in effect_dict.items():
                    new_fluents[fluent] = not new_fluents[fluent]
                new_state = StateNode(new_fluents)
                self.transition_graph.add_state(new_state)
                duration = self.transition_graph.action_durations.get(action, 1)
                self.transition_graph.add_edge(state, action, new_state, duration)

    def parse_duration(self, statement: str) -> None:
        action, duration = statement.split(" lasts ")
        self.transition_graph.action_durations[action] = int(duration)

    def parse_statement(self, statement: str) -> None:
        if statement.startswith("initially"):
            self.parse_initially(statement)
        elif "causes" in statement:
            self.parse_causes(statement)
        elif "releases" in statement:
            self.parse_releases(statement)
        elif "lasts" in statement:
            self.parse_duration(statement)