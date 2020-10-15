from collections import namedtuple
import typing as tp

Sentence = tp.NewType("Sentence", list[str])

Rule = namedtuple('Rule', ('symbolic', 'docs', 'func', 'reusable'))

# Rule decorators

def Creator(func):
    """Will allow the function to generate new tuple structures"""
    def wrapper(statement, *args, **kwargs):
        assert not isinstance(statement, tuple), "Tuple structure already exists"
        return func(statement, *args, **kwargs)
    return wrapper

def Modifier(func):
    """Will only iterate iterate through existing tuple structures"""
    def wrapper(statement, *args, **kwargs):
        if isinstance(statement, tuple):
            calculated = tuple([wrapper(i, *args, **kwargs) for i in statement])
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

    # Deleting brackets
    while statement[0]=='(' and statement[-1]==')': 
        statement = statement[1:-1]

    # Check bracket
    opened_left = 0
    opened_right = 0
    min_left = 0
    for i in statement:
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
    return -min_left*["("] + statement + right*[")"]

@Modifier
def quick_bracket_check(statement: Sentence):
    return statement.count('(')==statement.count(')')

def cleaned(func):
    def wrapper(*args, **kwargs):
        returned = func(*args, **kwargs)
        returned = reduce_brackets(returned)
        if returned:
            assert quick_bracket_check(returned)
        return returned
    return wrapper

# Useful functions for creating rules

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
def reduce_prefix(statement: Sentence, prefix_type: str) -> Sentence:
    if statement[0].startswith(prefix_type):
        if len(statement)<=2:
            return statement[1:]
        else:
            reduction = reduce_brackets(statement[1:])
            if reduction.count("(")==statement[1:].count("("):
                return []
            elif reduction.count("(")<statement[1:].count("("):
                return reduction
            else:
                raise Exception("After bracket reduction the statement gained a bracket")
    else:
        return []

@Modifier
def split_filter(statement: Sentence, splitter: int, func_left = lambda x: x, func_right = lambda x: x):
    return [func_left(i) for i in statement[:splitter]]+[func_right(i) for i in statement[splitter:]]

@Modifier
def add_prefix(statement: Sentence, prefix: str, symbol: str) -> Sentence:
    if len(statement)==1:
        return [f"{prefix}_{symbol}", *statement]
    else:
        return [f"{prefix}_{symbol}", '(', *statement, ')']