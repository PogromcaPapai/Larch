import typing as tp
import FormalSystem as utils

SOCKET = 'FormalSystem'
VERSION = '0.0.1'


# Rule definition

USED_TYPES = ('and', 'or', 'imp', 'not', 'sentvar','sep','turnstile')
PRECEDENCE = {
    'and':4,
    'or':4,
    'imp':3,
    'sep':2,
    'turnstile':1
}


def rule_left_and(sentence, num):
    """ A,B,... => ...
        ______________
        A&B,... => ...
    """ 
    return utils.on_part(sentence, 'turnstile', 0, lambda x: utils.on_part(x, 'sep', num, lambda y: utils.merge_branch(utils.strip_around(y, 'and', True, PRECEDENCE), 'sep_;')))


def rule_right_and(sentence, num):
    """ ... => A,...  ... => B,...
        __________________________
        ... => A&B,...
    """
    return utils.on_part(sentence, 'turnstile', 1, lambda x: utils.on_part(x, 'sep', num, lambda y: utils.strip_around(y, 'and', True, PRECEDENCE)))


def rule_left_or(sentence, num):
    """ A,... => ...  B,... => ...
        __________________________
        AvB,... => ...
    """
    return utils.on_part(sentence, 'turnstile', 0, lambda x: utils.on_part(x, 'sep', num, lambda y: utils.strip_around(y, 'or', True, PRECEDENCE)))


def rule_right_or(sentence, num):
    """ ... => A,B,...
        ______________
        ... => AvB,...
    """ 
    return utils.on_part(sentence, 'turnstile', 1, lambda x: utils.on_part(x, 'sep', num, lambda y: utils.merge_branch(utils.strip_around(y, 'or', True, PRECEDENCE), 'sep_;')))


RULES = {
    'left and':utils.Rule(
        symbolic="",
        docs="",
        func=rule_left_and,
        reusable=False,
        context = [utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
            )]
    ),
    'left or':utils.Rule(
        symbolic="",
        docs="",
        func=rule_left_or,
        reusable=False,
        context = [utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
            )]
    ),
    'right and':utils.Rule(
        symbolic="",
        docs="",
        func=rule_right_and,
        reusable=False,
        context = [utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
            )]
    ),
    'right or':utils.Rule(
        symbolic="",
        docs="",
        func=rule_right_or,
        reusable=False,
        context = [utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
            )]
    )
}

# __template__

def prepare_for_proving(statement: utils.Sentence) -> utils.Sentence:
    return ['turnstile_=>']+statement


def check_contradict(s: utils.Sentence, t: utils.Sentence) -> bool:
    return False


def check_syntax(tokenized_statement: utils.Sentence) -> tp.Union[str, None]:
    """Should return string description of the problem in syntax"""
    return True


def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    return False


def get_rules() -> dict[str, str]:
    """Returns the names and documentation of the rules"""
    rule_dict = dict()
    for name, rule in RULES.items():
        rule_dict[name] = "\n".join((rule.symbolic, rule.docs))
    return rule_dict


def get_needed_context(rule_name: str) -> tuple[utils.ContextDef]:
    """Returns needed arguments for the given rule"""
    if (rule := RULES.get(rule_name, None)):
        return tuple(rule.context)
    else:
        return None


def get_used_types() -> tuple[str]:
    return USED_TYPES


def use_rule(name: str, branch: list[utils.Sentence], context: dict[str, tp.Any]) -> tuple[tp.Union[tuple[tuple[utils.Sentence]], None], int]:
    """Uses a rule of the given name on the provided branch.
        Context allows to give the FormalSystem additional arguments. 
        Use `self.access('FormalSystem').get_needed_context(rule)` to check for needed context

    :param name: Rule name
    :type name: str
    :param branch: List of sentences in a branch
    :type branch: list[utils.Sentence]
    :param context: Additional arguments
    :type context: dict[str,tp.Any]
    :return: Generated tuple structure with the sentences and sentence ID
    :rtype: tuple[tp.Union[tuple[tuple[utils.Sentence]], None], int]
    """
    rule = RULES[name]
    sent = branch[-1]

    # Rule usage
    fin = rule.func(sent, *context.values())
    if not fin is None:
        return fin, len(branch)-1
    else:
        return None, -1
