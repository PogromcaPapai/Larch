import typing as tp
import Output as utils

SOCKET = 'Output'
VERSION = '0.0.1'

def get_readable(sentence: utils.Sentence, lexem_parser: callable) -> str:
    """Returns a readable version of the sentence

    :param sentence: Transcribed sentence
    :type sentence: Sentence
    :param lexem_parser: Transforms tokens into lexems to use (get_lexem for example)
    :type lexem_parser: callable
    :return: Transcribed string
    :rtype: str
    """
    assert isinstance(sentence, list)
    readable = []
    for lexem in (lexem_parser(i) for i in sentence):
        if len(lexem) > 1:
            readable.append(f" {lexem} ")
        else:
            readable.append(lexem)
    return "".join(readable).replace("  ", " ")