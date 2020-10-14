import typing as tp
from __utils__ import *

SOCKET = 'FormalSystem'
VERSION = '0.0.1'

def prepare_for_proving(statement: Sentence) -> str:
    pass

def check_contradict(s: Sentence, t:Sentence) -> bool:
    pass

def check_syntax(tokenized_statement: Sentence) -> tp.Union[str, None]:
    """Should return string description of the problem in syntax"""
    pass

def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    pass

def get_rules() -> dict[str, str]:
    """Returns the names and documentation of the rules"""
    pass

def get_used_types() -> tuple[str]:
    pass

def use_rule(name: str, tokenized_statement: Sentence) -> tp.Union[tuple[tuple[Sentence]], None]:
    pass