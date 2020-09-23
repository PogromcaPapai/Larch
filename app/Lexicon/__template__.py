import typing as tp

SOCKET = 'Lexicon'
VERSION = '0.0.1'

lexicon = None

class CompilerError(Exception):
    pass

def tokenize(word: str, used_lexems: tp.Iterable[str], defined: tp.Dict[str, str] = dict()) -> str:
    pass
