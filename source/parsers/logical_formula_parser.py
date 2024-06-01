from pyeda.inter import expr
from typing import List


class LogicalFormulaParser:

    def normalize_to_dnf(self, formula: str) -> expr:

        replacements = {
            "and": "&",
            "or": "|",
            "not": "~",
            "implies": "=>",
            "iff": "<=>",
        }

        for word, symbol in replacements.items():
            formula_str = formula_str.replace(word, symbol)

        return expr(formula_str).to_dnf()


    def extract_and_statements(self, pyeda_formula) -> List[str]:
        and_statements = []
        for and_statement in normalized_formula.xs:
            s = ' and '.join(str(x) for x in and_statement.xs)
            s = s.replace('~', 'not ')
            and_statements.append(s)
        return and_statements


    def extract_logical_statements(self, formula: str) -> str:
        return extract_and_statements(normalize_to_dnf(formula_str))


    def extract_fluents(self, formula: str) -> List[str]:
        fluents = re.findall(r'~?\b\w+', statement)
        fluents = [fluent.strip().lstrip('~') for fluent in fluents if fluent.strip() not in ["and", "or", "implies", "iff", "(", ")"]]
        return fluents

    def extract_fluent_dict(self, formula: str) -> dict:
        fluents = map(str.strip, formula.split("and"))
        fluent_dict = {}
        for fluent in fluents:
            if "~" in fluent:
                fluent_dict[fluent.lstrip("~")] = False
            else:
                fluent_dict[fluent] = True
        return fluent_dict