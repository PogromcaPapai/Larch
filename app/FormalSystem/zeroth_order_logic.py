from collections import namedtuple
import typing as tp
import re
import __utils__ as utils

SOCKET = 'FormalSystem'
VERSION = '0.0.1'


# Rule definition


USED_TYPES = ('and', 'or', 'imp', 'not', 'sentvar')


RULES = { #TODO: Add implication rules
    'true and': Rule(
        symbolic="A and B / A; B",
        docs="",
        func=lambda x: strip_around(x, 'and', False),
        reusable = True
    ),
    'false and': Rule(
        symbolic="~(A and B) / ~A | ~B",
        docs="",
        func=lambda x: add_prefix(strip_around(
            reduce_prefix(x, 'not'), 'and', True), 'not', '~'),
        reusable = False
    ),
    'false or': Rule(
        symbolic="~(A or B) / ~A; ~B",
        docs="",
        func=lambda x: add_prefix(strip_around(
            reduce_prefix(x, 'not'), 'or', False), 'not', '~'),
        reusable = True
    ),
    'true or': Rule(
        symbolic="(A or B) / A | B",
        docs="",
        func=lambda x: strip_around(x, 'or', True),
        reusable = False
    ),
    'double not': Rule(
        symbolic="~~A / A",
        docs="",
        func=lambda x: tuple([reduce_prefix(reduce_prefix(x, 'not'), 'not')]),
        reusable = True
    )
}


# __template__


@utils.cleaned
def prepare_for_proving(statement: str) -> str:
    '''Cleaning the sentence'''
    return statement


def check_contradict(statement_1: str, statement_2: str) -> bool:
    if statement_1.startswith('<not') and not statement_2.startswith('<not'):
        negated, statement = statement_1, statement_2
    elif statement_2.startswith('<not') and not statement_1.startswith('<not'):
        negated, statement = statement_2, statement_1
    else:
        return False
    return reduce_brackets(">".join(negated.split(">")[1:])) == statement


def check_syntax(sentence: sentence) -> bool:
    """True if sentence's syntax is correct; Doesn't check brackets"""
    raise NotImplementedError()
    tested = "".join(tokenized_statement).replace("(", "").replace(")", "")
    pattern = re.compile(r'(<not_.{1,3}>)?(<sentvar_\w>)<.{2,3}_.{1,3}>(<not_.{1,3}>)?(<sentvar_\w>)')
    if pattern.match(tested):
        return None
    else:
        after = pattern.sub(tested, '<sentvar_X>')
        if after==tested:
            return "Wrong structure"
        else:
            tested=after[:]


def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    return RULES[rule_name].reusable


def get_rules() -> dict[str, str]:
    '''Returns the names and documentation of the rules'''
    rule_dict = dict()
    for name, rule in RULES.items():
        rule_dict[name] = "\n".join((rule.symbolic, rule.docs))
    return rule_dict


def get_used_types() -> tuple[str]:
    return USED_TYPES


def use_rule(name: str, tokenized_statement: str) -> tp.Union[str, None]:
    rule = RULES[name]
    return rule.func(tokenized_statement)
