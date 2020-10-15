import typing as tp
import Lexicon as utils

SOCKET = 'Lexicon'
VERSION = '0.0.1'

def tokenize(word: str, used_lexems: tp.Iterable[str], defined: dict[str, str] = dict()) -> utils.Sentence:
    pass

def get_lexem(token: str) -> str:
    """Returns the lexem which was used to find the token"""
    pass

def get_type(token: str) -> str:
    """Returns the type of a token"""
    pass

def join_to_string(s: utils.Sentence) -> str:
    """Writes the sentence as a string, where tokens are written as `<[token type]_[lexem]>`"""
    pass

def get_readable(sentence: utils.Sentence) -> str:
    """Returns the sentence in a readable form"""
    pass