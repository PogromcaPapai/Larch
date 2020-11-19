from collections import namedtuple
import typing as tp

Sentence = tp.NewType("Sentence", list[str])

Rule = namedtuple('Rule', ('symbolic', 'docs', 'func', 'reusable'))

ContextDef = namedtuple('ContextDef', ('variable', 'official', 'docs', 'type_'))

class FormalSystemError(Exception):
    pass


# Rule decorators


def Creator(func):
    """Will allow the function to generate new tuple structures"""
    def wrapper(statement, *args, **kwargs):
        assert not isinstance(
            statement, tuple), "Tuple structure already exists"
        return func(statement, *args, **kwargs)
    return wrapper


def Modifier(func):
    """Will only iterate iterate through existing tuple structures"""
    def wrapper(statement, *args, **kwargs):
        if isinstance(statement, tuple):
            calculated = tuple([wrapper(i, *args, **kwargs)
                                for i in statement])
            if any((not i for i in calculated)):
                return ()
            else:
                return calculated
        else:
            return func(statement[:], *args, **kwargs)

    return wrapper


# Formating and cleaning


@Modifier
def reduce_brackets(statement: Sentence) -> Sentence:
    """Reduces the amount of brackets around a sentence"""
    assert isinstance(statement, list)

    if statement == []:
        return []

    reduced = statement[:]

    # Deleting brackets
    while reduced[0] == '(' and reduced[-1] == ')':
        reduced = reduced[1:-1]

    # Check bracket
    opened_left = 0
    opened_right = 0
    min_left = 0
    for i in reduced:
        if i == '(':
            opened_left += 1
        elif i == ')':
            opened_right += 1
        else:
            continue
        delta_left = opened_left-opened_right
        if min_left > delta_left:
            min_left = delta_left

    right = opened_left-opened_right-min_left
    return -min_left*["("] + reduced + right*[")"]


@Modifier
def quick_bracket_check(reduced: Sentence):
    return reduced.count('(') == reduced.count(')')


def cleaned(func):
    """Cleans the result of a function"""
    def wrapper(*args, **kwargs):
        returned = func(*args, **kwargs)
        returned = reduce_brackets(returned)
        if returned:
            assert quick_bracket_check(returned)
        return returned
    return wrapper

# Useful functions for creating rules


@Creator
def empty_creator(statement: Sentence):
    """Doesn't do nothing; Use when no Creator has been used to generate a tuple structure"""
    return ((statement,),)


@cleaned
@Creator
def strip_around(statement: Sentence, border_type: str, split: bool, precedence: dict[str, int]) -> tuple[tuple[Sentence]]:
    """Splits the sentence on the given string (only when all brackets yet are closed)

    :param statement: Sentence to split
    :type statement: Sentence
    :param border_type: type of the object around which the object should be split
    :type border_type: str
    :param split: True for creation of new branches
    :type split: bool
    :return: Tuple of generated branch additions
    :rtype: tuple[tuple[Sentence]]
    """
    lvl = 0
    middle = None
    precedence_keys = precedence.keys()
    border_precedence = precedence.get(border_type, 0)
    for i, s in enumerate(statement):
        if s == '(':
            lvl += 1
        elif s == ')':
            lvl -= 1
        elif lvl == 0 and (toktype := s.split('_')[0]) in precedence_keys:
            if border_precedence>precedence[toktype]:
                return ()
            elif toktype==border_type and middle is None:
                middle = i

    if middle is None:
        return ()
    elif split:
        return ((statement[:middle],), (statement[middle+1:],))
    else:
        return ((statement[:middle], statement[middle+1:]),)


@cleaned
@Modifier
def reduce_prefix(statement: Sentence, prefix_type: str, prefixes: tuple[str]) -> Sentence: #TODO: Needs optimalization
    """ Deletes a prefix if it closes the rest of the sentence

    :param statement: Modified sentence
    :type statement: Sentence
    :param prefix_type: Type of the prefix (`x` in `x_y`)
    :type prefix_type: str
    :param prefixes: Prefixes used in this Formal system
    :type prefixes: tuple[str]
    :raises Exception: After bracket reduction the statement_no_prefix gained a bracket
    :return: Modified sentence
    :rtype: Sentence
    """
    
    assert isinstance(statement, list)

    if statement[0].startswith(prefix_type):
        start = 1
        while any((statement[start].startswith(i) for i in prefixes)):
            start += 1
        statement_no_prefix = statement[start:]

        if len(statement_no_prefix) == 1:
            return reduce_brackets(statement[1:])
        else:
            reduction = reduce_brackets(statement_no_prefix)
            if reduction.count("(") == statement_no_prefix.count("("):
                return []
            elif reduction.count("(") < statement_no_prefix.count("("):
                return reduce_brackets(statement[1:])
            else:
                raise Exception(
                    "After bracket reduction the statement_no_prefix gained a bracket")
    else:
        return []


@Modifier
def add_prefix(statement: Sentence, prefix: str, lexem: str) -> Sentence:
    """Adds a prefix to the whole sentence

    :param statement: Sentence do modify
    :type statement: Sentence
    :param prefix: Prefix type to insert (`x` in `x_y`)
    :type prefix: str
    :param lexem: Prefix lexem to insert  (`y` in `x_y`)
    :type lexem: str
    :return: Modified sentence
    :rtype: Sentence
    """

    if len(statement) == 1:
        return [f"{prefix}_{lexem}", *statement]
    else:
        return [f"{prefix}_{lexem}", '(', *statement, ')']


def select(tuple_structure: tuple[tuple[Sentence]], selection: tuple[tuple[bool]], func: callable) -> tuple[tuple[Sentence]]:
    """Allows selective function application in the tuple structure

    Examples:


    tuple_structure :   ((A, B))
    selection       :   ((True, False))
    ___________________________________
    Result          :   ((func(A), B))


    tuple_structure :   ((A, B), (C, D))
    selection       :   ((False, False), (True, False))
    ___________________________________
    Result          :   ((A, B), (func(C), D))


    tuple_structure :   ((A, B), (C, D))
    selection       :   ((False, True), (False, True))
    ___________________________________
    Result          :   ((A, func(B)), (C, func(D)))


    :param tuple_structure: tuple of branch additions
    :type tuple_structure: tuple[tuple[Sentence]]
    :param selection: Selected sentences
    :type selection: tuple[tuple[bool]]
    :param func: Function to perform on the selected sentences
    :type func: callable
    :return: Modified tuple of branch additions
    :rtype: tuple[tuple[Sentence]]
    """

    # Tests
    if not tuple_structure:
        return ()
    assert len(tuple_structure)==len(selection)
    assert all((len(tuple_structure[i])==len(selection[i]) for i in range(len(selection))))

    # Execution
    return _select(tuple_structure, selection, func)


def _select(filtered, selection, func: callable) -> tuple[tuple[Sentence]]:
    """Recursion used in `select`; DO NOT USE"""
    after = []

    for s, use in zip(filtered, selection):
        if isinstance(use, bool):
            if use:
                after.append(func(s))
            else:
                after.append(s)
        else:
            after.append(_select(s, use, func))
    return tuple(after)