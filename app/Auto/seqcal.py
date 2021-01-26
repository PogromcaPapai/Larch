import typing as tp
import Auto as utils
from collections import namedtuple
from math import inf

SOCKET = 'Auto'
VERSION = '0.0.1'


RULES = ['left and', 'right imp', 'right and', 'left or', 'left imp', 'right or', " "]
RULES_types = {i.split()[1] for i in RULES[:-1]}

PRECEDENCE = {
    'and': 2,
    'or': 2,
    'imp': 1
}

def find_rule(sen: utils.Sentence) -> tp.Union[str, None]:
    side = 'left'
    top = ("", "")
    bracket_lvl = 0
    lowest_precedence = inf
    sep_count = 0
    for i in sen:
        if i.startswith('sep_'):
            highest_precedence = 0
            sep_count += 1
            assert bracket_lvl == 0, "Wrong brackets"
        elif i.startswith('turnstile_'):
            highest_precedence = 0
            side = 'right'
            assert bracket_lvl == 0, "Wrong brackets"
        elif i == '(':
            bracket_lvl += 1
        elif i == ')':
            bracket_lvl -= 1
        elif bracket_lvl == 0:
            for j in RULES_types:
                if i.startswith(j+"_") and PRECEDENCE[j]<=lowest_precedence:
                    if RULES.index(" ".join((top[0], top[1])))>RULES.index(" ".join((side, j))):
                        if side=='left':
                            top = (side, j, str(sep_count))
                        else:
                            top = (side, j)
    
    if top == ("", ""):
        return None
    else:
        return " ".join(top)



# __template__.py

def solve(delegate: callable, branch: list[utils.Sentence]) -> tp.Union[str, None]:
    test = find_rule(branch[-1])
    return test


def compatible() -> tuple[str]:
    return ('int_seqcal')