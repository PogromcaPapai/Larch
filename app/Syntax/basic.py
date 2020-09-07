import typing as tp
from collections import namedtuple
from string import ascii_letters
from functools import lru_cache
import re
from functools import reduce

SOCKET = 'Syntax'
VERSION = '0.0.1'


class CompilerError(Exception):
    pass


class MultipleTypesError(CompilerError):

    def __init__(self, multiple, *args, **kwargs):
        lists = [" - ".join((i[0], ", ".join(i[1]))) for i in multiple.items()]
        msg = "\n".join(("Multiple types found for:", *lists))
        super().__init__(msg, *args, **kwargs)


full_lexicon = dict(
    constants=(
        # AND
        ('^', 'and'),
        ('and', 'and'),
        ('&', 'and'),
        # OR
        ('v', 'or'),
        ('or', 'or'),
        ('|', 'or'),
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
    ),
    semantic=(
        # =, <, > and other things that need to carry semantics in proofs
    ),
    variables=(
        (r'[u-z]', 'indvar'),
        (r'[a-t]', 'constant'),
        (r'[P-Z]', 'predicate'),
        (r'[F-O]', 'function'),
        # Zero order logic
        (r'[p-z]', 'sentvar'),
    ),
)
full_lexicon['types'] = reduce(lambda x, y: x | y, ((
    {i[1] for i in value} for value in full_lexicon.values())), set())


def group_by_key(l) -> tp.Dict[str, tp.List[str]]:
    allfound = dict()
    for i in l:
        if i in allfound.keys():
            allfound[i[0]].append(i[1])
        else:
            allfound[i[0]] = [i[1]]
    return allfound


def letter_range(regex: str) -> tp.Tuple[int]:
    return (ascii_letters.index(regex[1]), ascii_letters.index(regex[3]))


def check_range(letter: str, indexes: tp.Tuple[int]) -> bool:
    assert len(letter) == 1
    v = ascii_letters.index(letter)
    return v >= indexes[0] and v <= indexes[1]


Lexicon = namedtuple(
    'Lexicon', ['pattern', 'defined', 'keywords', 'variables'])


@lru_cache(3)
def simplify_lexicon(used_tokens: tp.FrozenSet[str], defined: tp.FrozenSet[tp.Tuple[str]]):
    """Filters out patterns that aren't used"""
    lack = used_tokens - full_lexicon['types']
    if lack:
        raise CompilerError(
            "Lexicon lacks following types: {}".format(", ".join(lack)))

    # Filtering
    filtered_def = list(filter(lambda x: x[1] in used_tokens, defined))
    filtered_keywords = list(filter(lambda x: x[1] in used_tokens, full_lexicon['constants'])) + list(
        filter(lambda x: x[1] in used_tokens, full_lexicon['semantic']))
    filtered_var = list(filter(lambda x: x[1] in used_tokens, full_lexicon['variables']))

    # Check for lexicon fullness
    assert len(filtered_keywords) > 0, "No keywords"
    #assert any(filtered_var), "No variables"

    # Check for duplicates
    dup = [i for i in group_by_key(filtered_keywords).items() if len(i[1]) > 1]
    if len(dup) > 0:
        raise MultipleTypesError(dup)
    # TODO: Add a check for variables?

    # Prepare data
    dict_keys = {i[0]: f"<{i[1]}_{i[0]}>" for i in filtered_keywords}
    dict_def = {i[0]: f"<{i[1]}_{i[0]}>" for i in filtered_def}
    tup_variables = [(letter_range(i[0]), f"<{i[1]}_+>") for i in filtered_var]

    # Generate pattern
    in_pattern = [re.escape(i[0]) for i in filtered_def]+[re.escape(i[0]) for i in filtered_keywords] + [i[0] for i in filtered_var]
    pattern = re.compile("|".join(in_pattern))

    return Lexicon(pattern=pattern, defined=dict_def, keywords=dict_keys, variables=tup_variables)


def find_token(string: str, lex: Lexicon) -> str:
    found = lex.defined.get(string, None)
    if not found:
        found = lex.keywords.get(string, None)
    if not found:
        for i in lex.variables:
            if check_range(string, i[0]):
                found = i[1].replace('+', string)
    if not found:
        raise CompilerError(f'Couldn\'t be tokenized: "{string}"')
    return found


def tokenize(statement: str, used_tokens: tp.Iterable[str], defined: tp.Dict[str, str] = dict()) -> str:
    dictionary = simplify_lexicon(
        frozenset(used_tokens), frozenset(defined.items()))
    s = statement[:]

    def func(x):
        return find_token(x.group(), dictionary)
    s = dictionary.pattern.sub(func, s)
    # dodać test dla sprawdzania czy istnieje jakieś nieprzekonwertowane gówno
    return s
