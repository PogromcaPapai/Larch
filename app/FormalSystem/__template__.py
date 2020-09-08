from collections import OrderedDict, namedtuple
import typing as tp

SOCKET = 'FormalSystem'
VERSION = '0.0.1'

Rule = namedtuple('Rule', 'docs', 'pattern_match', 'pattern_sub')

def check_syntax(tokenized_statement: str) -> bool:
    pass

def get_rules() -> tp.Dict[str, str]:
    '''Returns the names and documentation of the rules'''
    pass

def get_used_types() -> tp.Tuple[str]:
    pass

def use_rule(name: str, tokenized_statement: str) -> tp.Union[str, None]:
    pass