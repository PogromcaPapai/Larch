from collections import OrderedDict, namedtuple
import typing as tp
import regex

SOCKET = 'FormalSystem'
VERSION = '0.0.1'


# Structures

Rule = namedtuple('Rule', ('symbolic', 'docs', 'func'))


def regular_sentence(name: str) -> str:
    '''Recursive definition of a sentence in Zeroth Order Logic'''
    return r"(?<__name__>((<not_[^>]{1,3}>)?(?:<sentvar_.>)|(?:\(\g'__name__'\)))(?:<[^>_]{1,3}_.{1,3}>((?:<not_[^>]{1,3}>)?(?:<sentvar_.>)|(?:\(\g'__name__'\))))?)".replace("__name__", name)


# Formating and cleaning

def reduce_brackets(statements: tp.Union[str, tp.Tuple[tp.Tuple[str]]]) -> tp.Union[str, tp.Tuple[tp.Tuple[str]]]:
    if isinstance(statements, str):
        s = statements.strip('()')

        # Check bracket
        opened_left = 0
        opened_right = 0
        min_left = 0
        min_right = 0
        for i in s:
            if i == '(':
                opened_left += 1
            elif i == ')':
                opened_right += 1
            else:
                continue
            delta_left = opened_left-opened_right
            delta_right = opened_right-opened_left+min_left
            if min_left > delta_left:
                min_left = delta_left
            elif min_right > delta_right:
                min_right = delta_right

        return "".join((-min_left*"(", s, -min_right*")"))
    else:
        return tuple([reduce_brackets(i) for i in statements])


def cleaned(func):
    def wrapped(*args, **kwargs):
        returned = func(*args, **kwargs)
        returned = reduce_brackets(returned)
        return returned
    return wrapped


# Useful functions for creating rules

@cleaned
def strip_around(statements: tp.Union[str, tp.Tuple[tp.Tuple[str]]], border_type: str, split: bool) -> tp.Tuple[tp.Tuple[str]]:
    if isinstance(statements, str):
        buffor = list()
        lvl = 0
        left_end = None
        right_start = None
        for i, s in enumerate(statements):
            if s == '(':
                lvl += 1
            elif s == ')':
                lvl -= 1
            elif lvl == 0:
                if s == '<':
                    buffor = list()
                    left_end = i
                elif s == '>':
                    if "".join(buffor).startswith(border_type+'_'):
                        right_start = i+1
                        break
                else:
                    buffor.append(s)

        if left_end is None or right_start is None:
            return ()
        if split:
            return ((statements[:left_end]), (statements[right_start:]))
        else:
            return (statements[:left_end], statements[right_start:])
    else:
        return tuple([strip_around(s, border_type, split) for s in statements])


@cleaned
def reduce_prefix(statements: tp.Union[str, tp.Tuple[tp.Tuple[str]]], prefix_type: str) -> str:
    if isinstance(statements, str):
        match = regex.fullmatch(
            r'<__type___.{1,3}>(.+)'.replace('__type__', prefix_type), statements)
        if match:
            return (match.group(1))
        else:
            return ()
    else:
        return tuple([reduce_prefix(s, prefix_type) for s in statements])


def add_prefix(statements: tp.Union[str, tp.Tuple[tp.Tuple[str]]], prefix: str, symbol: str, side: str = '') -> tp.Union[str, tp.Tuple[tp.Tuple[str]]]:
    if isinstance(statements, str):
        if len(statements)==11: # 11 is the length of '<sentvar_X>'
            return f'<{prefix}_{symbol}>{statements}'
        else:
            return f'<{prefix}_{symbol}>({statements})'
    else:
        if side == '':
            return tuple([add_prefix(i, prefix, symbol) for i in statements])
        elif side[0] in ('l', 'L'):
            return tuple(add_prefix(statements[0], prefix, symbol, side=side[1:]), (statements[1]))
        elif side[0] in ('r', 'R'):
            return tuple((statements[0]), add_prefix(statements[1], prefix, symbol, side=side[1:]))
        else:
            raise Exception("Wrong side symbol")


# Rule definition

USED_TYPES = ('and', 'or', 'imp', 'not', 'sentvar')

RULES = {
    'true and': Rule(
        symbolic="A and B / A; B",
        docs="",
        func=lambda x: strip_around(x, 'and', False)
    ),
    'false and': Rule(
        symbolic="~(A and B) / ~A | ~B",
        docs="",
        func=lambda x: add_prefix(strip_around(
            reduce_prefix(x, 'not'), 'and', True), 'not', '~')
    ),
    'false or': Rule(
        symbolic="~(A or B) / ~A; ~B",
        docs="",
        func=lambda x: add_prefix(strip_around(
            reduce_prefix(x, 'not'), 'or', False), 'not', '~')
    ),
    'true or': Rule(
        symbolic="(A or B) / A | B",
        docs="",
        func=lambda x: strip_around(x, 'or', True)
    ),
    'double not': Rule(
        symbolic="~~A / A",
        docs="",
        func=lambda x: reduce_prefix(reduce_prefix(x, 'not'), 'not')
    )
}

# The rest


@cleaned
def prepare_for_proving(statement: str) -> str:
    '''Cleaning the sentence'''
    pass


def check_syntax(tokenized_statement: str) -> bool:
    if regex.fullmatch(regular_sentence('a'), tokenized_statement):
        return True
    else:
        return False


def get_rules() -> tp.Dict[str, str]:
    '''Returns the names and documentation of the rules'''
    rule_dict = dict()
    for name, rule in RULES.items():
        rule_dict[name] = "\n".join((rule.symbolic, rule.docs))
    return rule_dict


def get_used_types() -> tp.Tuple[str]:
    return USED_TYPES


def use_rule(name: str, tokenized_statement: str) -> tp.Union[str, None]:
    rule = RULES.get(name, None)
    if rule:
        return rule.func(tokenized_statement)
    else:
        raise Exception("No such rule")
