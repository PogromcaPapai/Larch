from collections import namedtuple
import typing as tp

Sentence = tp.NewType("Sentence", list[str])

Rule = namedtuple('Rule', ('symbolic', 'docs', 'func', 'reusable'))

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
def strip_around(statement: Sentence, border_type: str, split: bool) -> Sentence:
    lvl = 0
    middle = None
    for i, s in enumerate(statement):
        if s == '(':
            lvl += 1
        elif s == ')':
            lvl -= 1
        elif lvl == 0 and s.startswith(border_type):
            middle = i
            break

    if middle is None:
        return ()
    elif split:
        return ((statement[:middle],), (statement[middle+1:],))
    else:
        return ((statement[:middle], statement[middle+1:]),)


@cleaned
@Modifier
def reduce_prefix(statement: Sentence, prefix_type: str, prefixes: tuple[str]) -> Sentence:
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
def add_prefix(statement: Sentence, prefix: str, symbol: str) -> Sentence:
    if len(statement) == 1:
        return [f"{prefix}_{symbol}", *statement]
    else:
        return [f"{prefix}_{symbol}", '(', *statement, ')']


def filter(tuple_structure: tuple[tuple[Sentence]], which: tuple[tuple[True]], func: callable) -> tuple[tuple[Sentence]]:

    # Tests
    if not tuple_structure:
        return ()
    assert len(tuple_structure)==len(which)
    assert all((len(tuple_structure[i])==len(which[i]) for i in range(len(which))))

    # Execution
    return _filter(tuple_structure, which, func)


def _filter(filtered, which, func: callable) -> tuple[tuple[Sentence]]:
    after = []

    for s, use in zip(to_split, which):
        if isinstance(use, bool):
            if use:
                after.append(func(s))
            else:
                after.append(s)
        else:
            after.append(_filter(s, use, func))
    return tuple(after)