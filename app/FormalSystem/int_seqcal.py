import typing as tp
import FormalSystem as utils

SOCKET = 'FormalSystem'
VERSION = '0.0.1'


USED_TYPES = ('and', 'or', 'imp', 'sentvar', 'sep', 'turnstile','falsum')
PRECEDENCE = {
    'and': 4,
    'or': 4,
    'imp': 3,
    'sep': 2,
    'turnstile': 1
}

def get_part(sentence: utils.Sentence, split_type: str, sent_num: int):
    """
    Returns n-th part of the sentence (split_types is the type of separator)
    """
    split_count = 0
    for start_split, s in enumerate(sentence):
        if s.startswith(f"{split_type}_"):
            split_count += 1
        if split_count == sent_num:
            break

    if len(sentence) <= start_split or split_count<sent_num:
        raise IndexError("sent_num is too big")

    part = []
    if split_count>0:
        sentence.pop(start_split)
    while start_split<len(sentence) and not sentence[start_split].startswith(f"{split_type}_"):
        part.append(sentence.pop(start_split))
    return part


def merge_tupstruct(left: tuple[tuple[str]], right: tuple[tuple[str]], glue: str):
    """
    Merges two tuple structures into one
    """
    if isinstance(left, tuple) and isinstance(left, tuple):
        assert len(left) == len(right), "Tuples not of equal length"
        end = []
        for l, r in zip(left, right):
            end.append(merge_tupstruct(l, r, glue))
        return tuple(end)
    elif isinstance(left, list) and isinstance(left, list):
        return left + [glue] + right
    else:
        # Bug reporting
        l_correct = (isinstance(left, list) or isinstance(left, tuple))
        r_correct = (isinstance(right, list) or isinstance(right, tuple))
        if l_correct and r_correct:
            raise AssertionError("Tuples not of equal depth")
        else:
            raise AssertionError((l_correct*"left")+(l_correct*r_correct *' and ')+(r_correct*"right") + "tuple is messed up")


def sep(part: utils.Sentence = None) -> list[str]:
    if part is None or len(part)>0:
        return ['sep_;']
    else:
        return []


# Rule definition

"""TODO:

MOŻNA USUNĄĆ Z RIGHT ARGUMENT, BO TYLKO JEDEN ELEMENT JEST
jakiś błąd jest i czasem się duplikują ";"

"""

def rule_left_and(left: utils.Sentence, right: utils.Sentence, num):
    """ A,B,... => ...
        ______________
        A&B,... => ...
    """
    try:
        conj = get_part(left, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    split = utils.strip_around(conj, 'and', False, PRECEDENCE)
    if split is None or split[0] is None:
        return (None, None)
    split = split[0]
    return ((split[0]+sep()+split[1]+sep(left)+left,),), ((right,),)


def rule_right_and(left: utils.Sentence, right: utils.Sentence, num):
    """ ... => A      ... => B
        __________________________
        ... => A&B
    """
    conj = get_part(right, 'sep', num-1)
    if conj is None:
        return (None, None)

    split = utils.strip_around(conj, 'and', False, PRECEDENCE)
    if split is None or split[0] is None:
        return (None, None)
    split = split[0]
    return ((left,),(left,),), ((split[0],),(split[1],),)

def rule_left_or(left: utils.Sentence, right: utils.Sentence, num):
    """ A,... => ...  B,... => ...
        __________________________
        AvB,... => ...
    """
    try:
        conj = get_part(left, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    split = utils.strip_around(conj, 'or', False, PRECEDENCE)
    if split is None or split[0] is None:
        return (None, None)
    split = split[0]
    return ((split[0]+sep(left)+left,),(split[1]+sep(left)+left,),), ((right,),(right,),)


def rule_right_or(left: utils.Sentence, right: utils.Sentence, side: str, num: int):
    """ ... => (A,B)[side]
        ______________
        ... => AvB
    """
    if (side := {'l':0,'r':1}.get(side, None)) is None:
        return (None, None)

    try:
        conj = get_part(right, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    split = utils.strip_around(conj, 'or', False, PRECEDENCE)
    if split is None or split[0] is None:
        return (None, None)
    split = split[0]
    return ((left,),), ((split[side],),)


def rule_left_imp(left: utils.Sentence, right: utils.Sentence, num):
    """ A -> B, ... => A    B,... => ...
        ________________________________
        A -> B,... => ...
    """
    try:
        conj = get_part(left, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    split = utils.strip_around(conj, 'imp', False, PRECEDENCE)
    if split is None or split[0] is None:
        return (None, None)
    split = split[0]
    return ((conj+sep(left)+left,),(split[1]+sep(left)+left,),), ((split[0],),(right,),)


def rule_right_imp(left: utils.Sentence, right: utils.Sentence, num):
    """ ..., A => B
        ______________
        ... => A -> B
    """
    try:
        conj = get_part(right, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    split = utils.strip_around(conj, 'imp', False, PRECEDENCE)
    if split is None or split[0] is None:
        return (None, None)
    split = split[0]
    return ((split[0]+sep(left)+left,),), ((split[1],),)

def rule_left_strong(left: utils.Sentence, right: utils.Sentence, num):
    """ ..., A, A => ...
        ________________
        ..., A => ...
    """
    try:
        conj = get_part(right, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    try:
        conj = get_part(right, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    return ((conj+sep()+conj+sep(left)+left,),), ((right,),)

def rule_left_weak(left: utils.Sentence, right: utils.Sentence, num):
    """ ... => ...
        ______________
        ..., A => ...
    """
    try:
        conj = get_part(right, 'sep', num-1)
    except IndexError:
        return (None, None)
    
    return ((left,),), ((right,),)

RULES = {
    'left and': utils.Rule(
        symbolic="",
        docs="",
        func=rule_left_and,
        reusable=False,
        context=[utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
        )]
    ),
    'left or': utils.Rule(
        symbolic="",
        docs="",
        func=rule_left_or,
        reusable=False,
        context=[utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
        )]
    ),
    'right and': utils.Rule(
        symbolic="",
        docs="",
        func=rule_right_and,
        reusable=False,
        context=[utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
        )]
    ),
    'right or': utils.Rule(
        symbolic="",
        docs="",
        func=rule_right_or,
        reusable=False,
        context=[
        utils.ContextDef(
            variable='conn_side',
            official='Side of the or operation',
            docs='l/r',
            type_=str
        ),
        utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int,
        )]
    ),
    'left imp': utils.Rule(
        symbolic="",
        docs="",
        func=rule_left_imp,
        reusable=True,
        context=[utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
        )]
    ),
    'right imp': utils.Rule(
        symbolic="",
        docs="",
        func=rule_right_imp,
        reusable=False,
        context=[utils.ContextDef(
            variable='partID',
            official='Subsentence number',
            docs='',
            type_=int
        )]
    )
}

# __template__


def prepare_for_proving(statement: utils.Sentence) -> utils.Sentence:
    if not 'turnstile_=>' in statement:
        return ['turnstile_=>']+statement
    else:
        return statement


def check_contradict(s: utils.Sentence, t: utils.Sentence) -> bool:
    return False


def check_syntax(tokenized_statement: utils.Sentence) -> tp.Union[str, None]:
    """Should return string description of the problem in syntax"""
    return True


def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    if (r := RULES.get(rule_name, None)):
        return r.reusable


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

    if branch[-1] is None:
        raise utils.FormalSystemError("This sentence was already used in a non-reusable rule")

    start = utils.strip_around(branch[-1], "turnstile", False, PRECEDENCE)
    start_left, start_right = start[0]

    # Rule usage
    left, right = rule.func(start_left, start_right, *context.values())
    if not (left is None or right is None):
        return merge_tupstruct(left, right, "turnstile_=>"), len(branch)-1
    else:
        return None, -1
