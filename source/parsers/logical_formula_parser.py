import re

from pyeda.inter import *
from pyeda.boolalg.expr import AndOp, Complement, OrOp, Variable
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
            formula = formula.replace(word, symbol)

        return expr(formula).to_dnf()


    def extract_and_statements(self, pyeda_formula) -> List[str]:
        def extract_and_statement(and_statement: expr) -> str:
            return ' and '.join(str(x) for x in and_statement.xs).replace('~', 'not ')
        
        and_statements = []

        if isinstance(pyeda_formula, AndOp):
            and_statements.append(extract_and_statement(pyeda_formula))
        elif isinstance(pyeda_formula, Variable) or isinstance(pyeda_formula, Complement):
            and_statements.append(str(pyeda_formula))
        elif pyeda_formula.__class__.__name__ == "_Zero":
            return None
        else:
            for and_statement in pyeda_formula.xs:
                print(type(and_statement))
                if isinstance(and_statement, AndOp):
                    and_statements.append(extract_and_statement(and_statement))
                elif isinstance(and_statement, Variable) or isinstance(and_statement, Complement):
                    and_statements.append(str(and_statement))
        return and_statements


    def extract_logical_statements(self, formula: str) -> str:
        return self.extract_and_statements(self.normalize_to_dnf(formula))


    def extract_fluents(self, formula: str) -> List[str]:
        fluents = re.findall(r'~?\b\w+', formula)
        fluents = [fluent.strip().lstrip('~') for fluent in fluents if fluent.strip() not in ["and", "or", "implies", "iff", "(", ")"]]
        return fluents

    def extract_fluent_dict(self, formula: str) -> dict:
        formula = formula.replace("not ", "~")
        fluents = map(str.strip, formula.split("and"))
        fluent_dict = {}
        for fluent in fluents:
            if "~" in fluent:
                fluent_dict[fluent.lstrip("~")] = False
            else:
                fluent_dict[fluent] = True
        return fluent_dict
