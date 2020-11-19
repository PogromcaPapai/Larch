import typing as tp
import FormalSystem as utils

SOCKET = 'FormalSystem'
VERSION = '0.0.1'


def prepare_for_proving(statement: utils.Sentence) -> str:
    pass


def check_contradict(s: utils.Sentence, t: utils.Sentence) -> bool:
    pass


def check_syntax(tokenized_statement: utils.Sentence) -> tp.Union[str, None]:
    """Should return string description of the problem in syntax"""
    pass


def check_rule_reuse(rule_name: str) -> bool:
    """Checks whether the rule can be reused on one statement in one branch"""
    pass


def get_rules() -> dict[str, str]:
    """Returns the names and documentation of the rules"""
    pass

def get_needed_context(rule_name: str) -> tuple[utils.ContextDef]:
    """Returns needed arguments for the given rule"""
    pass

def get_used_types() -> tuple[str]:
    pass


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
    pass
