from collections import OrderedDict, namedtuple
import typing as tp
import regex

SOCKET = 'FormalSystem'
VERSION = '0.0.1'


Rule = OrderedDict('Rule', ('symbolic', 'docs', 'func'))

# sentence regex


def regular_sentence(name: str) -> str:
    return r"(?<__name__>((<not_[^>]{1,3}>)?(?:<sentvar_.>)|\(\g'__name__'\))(?:<[^>_]{1,3}_.{1,3}>((?:<not_[^>]{1,3}>)?(?:<sentvar_.>)|\((?0)\)))?)".replace("__name__", name)


# Useful functions for creating rules

def strip_around(statement: str, border_type: str, split: bool) -> tp.Tuple[tp.Tuple[str]]:
    match = regex.fullmatch("".join((regular_sentence(
        'left'), '<', border_type, '_.{1,3}>', regular_sentence('right'))), statement)
    if match:
        if split:
            return ((match.group('left')), (match.group('right')))
        else:
            return (match.group('left'), match.group('right'))
    else:
        return ()


def reduce_prefix(statement: str, prefix_type: str) -> str:
    match = regex.fullmatch(
        r'<__type___.{1,3}>\((.+)\)'.replace('__type__', prefix_type), statement)
    if match:
        return match.group(1)
    else:
        return ''


def add_prefix(statements: tp.Union[str, tp.Tuple[tp.Tuple[str]]], prefix: str, symbol: str) -> tp.Union[str, tp.Tuple[tp.Tuple[str]]]:
    if isinstance(statements, str):
        return f'<{prefix}_{symbol}>({statements})'
    else:
        return tuple([add_prefix(i, prefix, symbol) for i in statements])

# Transformation functions


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

def check_syntax(tokenized_statement: str) -> bool:
    # full match with:
    pass


def get_rules() -> tp.Dict[str, str]:
    '''Returns the names and documentation of the rules'''
    rule_dict = dict()
    for name, rule in RULES.items():
        rule_dict[name] = "\n".join((rule.symbolic, rule.docs))
    return rule_dict


def get_used_types() -> tp.Tuple[str]:
    pass


def use_rule(name: str, tokenized_statement: str) -> tp.Union[str, None]:
    pass
