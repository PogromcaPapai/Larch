import typing as tp
from collections import namedtuple
from string import ascii_letters as alphabet
from functools import lru_cache
import re
from functools import reduce
import __utils__ as ut

SOCKET = 'Lexicon'
VERSION = '0.0.1'


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


def group_by_value(l: list[tuple[str, str]]) -> dict[str, list[str]]:
    """When given a list of (key, value) returns a dictionary, where keys are grouped by values"""
    allfound = dict()
    for i in l:
        if i[0] in allfound.keys():
            allfound[i[0]].append(i[1])
        else:
            allfound[i[0]] = [i[1]]
    return allfound


def letter_range(regex: str) -> tuple[int, int]:
    """For a regex given in lexicon.variables returns the indexes of first and last letter"""
    assert regex[1].islower() is regex[3].islower(), "One letter is higher case and one is lower case"
    return alphabet.index(regex[1]), alphabet.index(regex[3])


def check_range(letter: str, indexA: int, indexB: int) -> bool:
    """Checks if letter's index is in <indexA, indexB>"""
    assert len(letter) == 1
    return (alphabet.index(letter) := v) >= indexA and v <= indexB


Lexicon = namedtuple(
    'Lexicon', ['pattern', 'defined', 'keywords', 'variables'])

@lru_cache(3)
def simplify_lexicon(used_tokens: set[str], defined: set[tuple[str]]) -> Lexicon:
    """Filters out patterns that aren't used, creates a regex pattern at Lexicon.pattern, returns a lexicon object"""
    lack = used_tokens - full_lexicon['types']
    if lack:
        raise ut.CompilerError(
            f"Lexicon lacks following types: {', '.join(lack)}")

    # Filtering
    filtered_def = list(filter(lambda x: x[1] in used_tokens, defined))
    filtered_keywords = list(filter(lambda x: x[1] in used_tokens, full_lexicon['constants'])) + list(
        filter(lambda x: x[1] in used_tokens, full_lexicon['semantic']))
    filtered_var = list(filter(lambda x: x[1] in used_tokens, full_lexicon['variables']))

    # Check for lexicon fullness
    assert len(filtered_keywords) > 0, "No keywords"
    assert any(filtered_var), "No variables" # Turn off for testing

    # Check for duplicates
    dup_key = [i for i in group_by_value(filtered_keywords).items() if len(i[1]) > 1]
    if len(dup_key) > 0:
        raise ut.MultipleTypesError(dup_key)
    dup_var = [i for i in group_by_value(filtered_keywords).items() if len(i[1]) > 1]
    if len(dup_var) > 0:
        raise ut.MultipleTypesError(dup_var)

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
    :return: [type]_[string]
    :rtype: str
    """
    # Check if _ exists in string
    if '_' in string:
        raise ut.CompilerError(f'"{string}" contains "_", which is a reserved sign')

    # Check defined
    found = lex.defined.get(string, None)

    # Check keywords
    if not found:
        found = lex.keywords.get(string, None)
        
    # Check variables
    if not found:
        for i in lex.variables:
            if check_range(string, i[0][0], i[0][1]):
                found = i[1].replace('+', string)

    # Raise exception
    if not found:
        raise ut.CompilerError(f'Token not found for "{string}"')
    return found


def not_fully_tokenized(sent: ut.Sentence) -> bool:
    return all(("_" in i for i in sent))


def tokenize(statement: str, used_tokens: tp.Iterable[str], defined: dict[str, str] = dict()) -> ut.Sentence:
    dictionary = simplify_lexicon(
        frozenset(used_tokens), frozenset(defined.items()))
    s = statement[:]
    sentence = dictionary.pattern.split()
    sentence = [find_token(lexem, dictionary) for lexem in sentence]
    
    # Formating
    for i in sentence:
        i.replace(" ", "")
    
    # Additional check
    if not_fully_tokenized(s):
        raise ut.CompilerError("System didn't fully tokenize the sentence")
    return s

def get_lexem(token: str) -> str:
    """Returns the lexem which was used to find the token"""
    return token.split('_')[-1]

def get_type(token: str) -> str:
    """Returns the type of a token"""
    return token.split('_')[0]

def join_to_string(sentence: ut.Sentence) -> str:
    """Writes the sentence as a string, where tokens are written as `<[token type]_[lexem]>`"""
    new = []
    for token in sentence:
        if token in ('(', ')'):
            new.append(token)
        else:
            new.append(f"<{token}>")
    return "".join(new)
