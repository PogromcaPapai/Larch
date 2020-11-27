import typing as tp
import FormalSystem as ut

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
    return ut.merge_branch(ut.select(ut.strip_around(sentence, 'turnstile', True, PRECEDENCE), ((True,), (False,)), lambda x: ut.on_part(x, 'sep', num, lambda y: ut.merge_branch(ut.strip_around(y, 'and', True, PRECEDENCE), 'sep_;'))), 'turnstile_=>')

def rule_right_or(sentence, num):
    return ut.merge_branch(ut.select(ut.strip_around(sentence, 'turnstile', True, PRECEDENCE), ((False,), (True,)), lambda x: ut.on_part(x, 'sep', num, lambda y: ut.merge_branch(ut.strip_around(y, 'or', True, PRECEDENCE), 'sep_;'))), 'turnstile_=>')

RULES = {
    'Left and':ut.Rule(
        symbolic="",
        docs="",
        func=rule_left_and,
        context = [ut.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
            )]
    )
}

# __template__

def prepare_for_proving(statement: ut.Sentence) -> ut.Sentence:
    return ['turnstile_=>']+statement


def check_contradict(s: ut.Sentence, t: ut.Sentence) -> bool:
    return False


def check_syntax(tokenized_statement: ut.Sentence) -> tp.Union[str, None]:
    """Should return string description of the problem in syntax"""
    return True


def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    return True


def get_rules() -> dict[str, str]:
    """Returns the names and documentation of the rules"""
    pass


def get_needed_context(rule_name: str) -> tuple[ut.ContextDef]:
    """Returns needed arguments for the given rule"""
    pass


def get_used_types() -> tuple[str]:
    return USED_TYPES


def use_rule(name: str, branch: list[ut.Sentence], context: dict[str, tp.Any]) -> tuple[tp.Union[tuple[tuple[ut.Sentence]], None], int]:
    """Uses a rule of the given name on the provided branch.
        Context allows to give the FormalSystem additional arguments. 
        Use `self.access('FormalSystem').get_needed_context(rule)` to check for needed context

    :param name: Rule name
    :type name: str
    :param branch: List of sentences in a branch
    :type branch: list[ut.Sentence]
    :param context: Additional arguments
    :type context: dict[str,tp.Any]
    :return: Generated tuple structure with the sentences and sentence ID
    :rtype: tuple[tp.Union[tuple[tuple[ut.Sentence]], None], int]
    """
    rule = RULES[name]
    sent = branch[-1]

    # Rule usage
    fin = rule.func(sent, **context)
    if fin:
        return fin, statement_ID
    else:
        return None, -1
