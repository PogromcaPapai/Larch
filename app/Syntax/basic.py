import typing as tp
from collections import OrderedDict
from string import ascii_lowercase, ascii_uppercase
from functools import lru_cache
import re
from functools import reduce

SOCKET = 'Syntax'
VERSION = '0.0.1'


class CompilerError(Exception):
    pass


lexicon = OrderedDict(
    constants=sorted((
        # AND
        ('^', 'and'),
        ('and', 'and'),
        ('&', 'and'),
        # OR
        ('v', 'or'),
        ('or', 'or'),
        #('|', 'or'),
        # NEGATION
        ('~', 'not'),
        ('not', 'not'),
        # IMPLICATION
        ('->', 'imp'),
        ('then', 'imp'),
        # QUANTIFICATION
        ('A', 'forall'),
        ('/\\', 'forall'),
        ('forall', 'forall'),
        ('E', 'exists'),
        ('\\/', 'exists'),
        ('exists', 'exists'),
    ), key=lambda x: len(x[1]), reverse=True),
    semantic=(
        # =, <, > and other things that need to carry semantics
    ),
    variables=reduce(lambda x,y: x+y,
        (tuple([(i, 'indvar')
         for i in ascii_lowercase[20:]]),  # from u and onwards
        tuple([(i, 'constant') for i in ascii_lowercase]),  # from a and onwards
        tuple([(i, 'predicate')
         for i in ascii_uppercase[15:]]),  # from P and onwards
        tuple([(i, 'function')
         for i in ascii_uppercase[5:]]),  # from F and onwards

        # Zero order logic
        tuple([(i, 'sentence')
         for i in ascii_lowercase[15:]]),  # from p and onwards
    ), tuple()), #TODO: zoptymalizować to kiedyś
)

@lru_cache(2)
def simplify_lexicon(*used_tokens: tp.Iterable[str]):
    """Filters out patterns that aren't used"""
    new = OrderedDict()
    for i in lexicon.items():
        filtered = [(j[0], f" <{i[0][0]}_{j[1]}_{j[0]}> ")
                          for j in filter(lambda x: x[1] in used_tokens, i[1])]
        dict_filtered = dict(filtered)
        assert len(filtered) == len(dict_filtered), f"An entry in {i[0]} was overwritten"
        pattern = re.compile("|".join((re.escape(j[0]) for j in filtered)))
        new[i[0]] = (pattern, dict_filtered)
    return new

def tokenize(statement: str, used_tokens: tp.Iterable[str], defined: tp.Dict[str, str] = dict()) -> str:
    dictionary = simplify_lexicon(*used_tokens)
    s = statement
    subdict = dictionary['constants']
    if len(subdict[1])>0:
        func = lambda x: subdict[1][x.group()]
        s = subdict[0].sub(func, s)
    const_ready = s.split()
    subdict = dictionary['variables']
    for i in range(len(const_ready)):
        if len(subdict[1])>0 and not '<' in const_ready[i]:
            func = lambda x: subdict[1][x.group()]
            const_ready[i] = subdict[0].sub(func, const_ready[i])
    ready = "".join(const_ready)
    return ready

# Działa, ale warto by przeprowadzić refaktoryzację