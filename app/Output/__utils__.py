import typing as tp
from collections import namedtuple
import close

Sentence = tp.NewType("Sentence", list[str])
PrintedTree = namedtuple('PrintedTree', ('sentences', 'children', 'closer'))