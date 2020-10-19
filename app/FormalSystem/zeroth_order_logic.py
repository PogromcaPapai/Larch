import typing as tp
import FormalSystem as utils

SOCKET = 'FormalSystem'
VERSION = '0.0.1'


# Rule definition


USED_TYPES = ('and', 'or', 'imp', 'not', 'sentvar')


RULES = {  # TODO: Add implication rules
    'true and': utils.Rule(
        symbolic="A and B / A; B",
        docs="",
        func=lambda x: utils.strip_around(x, 'and', False),
        reusable=True
    ),
    'false and': utils.Rule(
        symbolic="~(A and B) / ~A | ~B",
        docs="",
        func=lambda x: utils.add_prefix(utils.strip_around(
            utils.reduce_prefix(x, 'not', ('not')), 'and', True), 'not', '~'),
        reusable=False
    ),
    'false or': utils.Rule(
        symbolic="~(A or B) / ~A; ~B",
        docs="",
        func=lambda x: utils.add_prefix(utils.strip_around(
            utils.reduce_prefix(x, 'not', ('not')), 'or', False), 'not', '~'),
        reusable=True
    ),
    'true or': utils.Rule(
        symbolic="(A or B) / A | B",
        docs="",
        func=lambda x: utils.strip_around(x, 'or', True),
        reusable=False
    ),
    'double not': utils.Rule(
        symbolic="~~A / A",
        docs="",
        func=lambda x: utils.reduce_prefix(
            utils.reduce_prefix(utils.empty_creator(x), 'not', ('not')), 'not', ('not')),
        reusable=True
    )
}


# __template__


@utils.cleaned
def prepare_for_proving(statement: utils.Sentence) -> str:
    """Cleaning the sentence"""
    return statement


def check_contradict(statement_1: utils.Sentence, statement_2: utils.Sentence) -> bool:
    """Checks whether statements collide with eachother"""
    if statement_1[0].startswith('not') and not statement_2[0].startswith('not'):
        negated, statement = statement_1, statement_2
    elif statement_2[0].startswith('not') and not statement_1[0].startswith('not'):
        negated, statement = statement_2, statement_1
    else:
        return False
    return utils.reduce_brackets(negated[1:]) == statement


def check_syntax(sentence: utils.Sentence) -> tp.Union[str, None]:
    """True if sentence's syntax is correct; Doesn't check brackets"""
    return None
    # TODO: napisać check oparty na redukcji ze sprawdzaniem nawiasów i sprawdzanie czy w każdym występuje "_"
    # tested = "".join(tokenized_statement).replace("(", "").replace(")", "")
    # pattern = re.compile(r'(<not_.{1,3}>)?(<sentvar_\w>)<.{2,3}_.{1,3}>(<not_.{1,3}>)?(<sentvar_\w>)')
    # if pattern.match(tested):
    #     return None
    # else:
    #     after = pattern.sub(tested, '<sentvar_X>')
    #     if after==tested:
    #         return "Wrong structure"
    #     else:
    #         tested=after[:]


def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    return RULES[rule_name].reusable


def get_rules() -> dict[str, str]:
    """Returns the names and documentation of the rules"""
    rule_dict = dict()
    for name, rule in RULES.items():
        rule_dict[name] = "\n".join((rule.symbolic, rule.docs))
    return rule_dict


def get_used_types() -> tuple[str]:
    return USED_TYPES


def use_rule(name: str, tokenized_statement: utils.Sentence) -> tp.Union[tuple[tuple[utils.Sentence]], None]:
    """Gets a rule from `RULES` and uses it on `tokenized_statement`. If the result is false it returns None.

    :param name: Name of the rule
    :type name: str
    :param tokenized_statement: Tokenized sentence
    :type tokenized_statement: Sentence
    :raises KeyError: Rule not found
    :return: The result of rule usage
    :rtype: tuple[tuple[utils.Sentence]] or None
    """
    rule = RULES[name]
    fin = rule.func(tokenized_statement)
    if fin:
        return fin
    else:
        return None
