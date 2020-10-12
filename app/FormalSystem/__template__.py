import typing as tp

SOCKET = 'FormalSystem'
VERSION = '0.0.1'

def prepare_for_proving(statement: str) -> str:
    pass

def check_contradict(s: str, t:str) -> bool:
    pass

def check_syntax(tokenized_statement: str) -> tp.Union[str, None]:
    """Should return string description of the problem in syntax"""
    pass

def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    pass

def get_rules() -> tp.Dict[str, str]:
    """Returns the names and documentation of the rules"""
    pass

def get_used_types() -> tp.Tuple[str]:
    pass

def use_rule(name: str, tokenized_statement: str) -> tp.Union[str, None]:
    pass