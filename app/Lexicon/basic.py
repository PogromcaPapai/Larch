import typing as tp
from collections import namedtuple
from string import ascii_letters
from functools import lru_cache
import re
from functools import reduce

SOCKET = 'Lexicon'
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
        ('imp', 'imp'),
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
def simplify_lexicon(used_tokens: tp.FrozenSet[str], defined: tp.FrozenSet[tp.Tuple[str]]) -> Lexicon:
    """Filters out patterns that aren't used, creates a regex pattern, returns a lexicon object"""
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
    assert any(filtered_var), "No variables" # Turn off for testing

    # Check for duplicates
    dup_key = [i for i in group_by_key(filtered_keywords).items() if len(i[1]) > 1]
    if len(dup_key) > 0:
        raise MultipleTypesError(dup_key)
    dup_var = [i for i in group_by_key(filtered_keywords).items() if len(i[1]) > 1]
    if len(dup_var) > 0:
        raise MultipleTypesError(dup_var)

    # Prepare data
    dict_keys = {i[0]: f"<{i[1]}_{i[0]}>" for i in filtered_keywords}
    dict_def = {i[0]: f"<{i[1]}_{i[0]}>" for i in filtered_def}
    tup_variables = [(letter_range(i[0]), f"<{i[1]}_+>") for i in filtered_var]

    # Generate pattern
    in_pattern = [re.escape(i[0]) for i in filtered_def]+sorted([re.escape(i[0]) for i in filtered_keywords], key=len, reverse=True) + [i[0] for i in filtered_var]
    pattern = re.compile("|".join(in_pattern))

    return Lexicon(pattern=pattern, defined=dict_def, keywords=dict_keys, variables=tup_variables)


def find_token(string: str, lex: Lexicon) -> str:
    """Finds the string in the lexicon and returns it

    :param string: Searched string
    :type string: str
    :param lex: Used lexicon object (generate with simplify_lexicon)
    :type lex: Lexicon
    :raises CompilerError: Raised if the string can't be properly tokenized
    :return: <[type]_[string]>
    :rtype: str
    """
    # Check defined
    found = lex.defined.get(string, None)
    # Check keywords
    if not found:
        found = lex.keywords.get(string, None)
    # Check variables
    if not found:
        for i in lex.variables:
            if check_range(string, i[0]):
                found = i[1].replace('+', string)
    # Raise exception
    if not found:
        raise CompilerError(f'Couldn\'t be tokenized: "{string}"')
    return found

def is_fully_tokenized(string: str) -> bool:
    flag = False
    for num, i in enumerate(string):
        if flag:
            if i=='>' and (string[num-5:num+1]!='imp_->'):
                flag = False
            else:
                continue
        elif i=='<':
            flag = True
        elif i in ('(', ')', ','):
            continue
        else:
            return False
    return True

def tokenize(statement: str, used_tokens: tp.Iterable[str], defined: tp.Dict[str, str] = dict()) -> str:
    dictionary = simplify_lexicon(
        frozenset(used_tokens), frozenset(defined.items()))
    s = statement[:]
    s = dictionary.pattern.sub(lambda x: find_token(x.group(), dictionary), s)
    
    # Formating
    s = s.replace(" ", "")
    
    # Additional check
    if not is_fully_tokenized(s):
        raise CompilerError("System didn't fully tokenize the sentence")
    return s
