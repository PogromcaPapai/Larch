from __future__ import annotations
from tree_helpers import Close, History

import typing as tp
import json, random
from collections import namedtuple, OrderedDict
from math import inf as INFINITY
from anytree import NodeMixin, util, LevelOrderIter
from tree_helpers import *

with open('colors.json') as f:
    colors = list(json.load(f).keys())

Sentence = tp.NewType("Sentence", list[str])
PrintedProofNode = namedtuple('PrintedProofNode', ('sentences', 'children', 'closer'))


class ProofNodeError(Exception):
    def __init__(self, msg: str, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ProofElement(object):


    def __init__(self, sentence: Sentence, branch: str, layer: int = 0, history: History = None) -> None:
        super().__init__()
        self.sentence = sentence
        self.branch = branch
        self.closed = None
        if history is None:
            self.history = History()
        else:    
            self.history = history
        self.editable = True
        self.layer = layer


    def close(self, close: Close = None, text: str = None, success: bool = None) -> None:
        """Zamyka gałąź używając obiektu `Close`, lub tekstu do wyświetlania użytkownikowi oraz informacje, czy można uznać to zamknięcie za sukces (dla przykładu: sprzeczność w tabeli analitycznej jest sukcesem, próba zapobiegnięcia pętli już nie)"""
        assert self.is_leaf, "Można zamykać tylko liście"
        if close:
            self.closed = close
        else:
            assert isinstance(text, str) and isinstance(success, bool)
            self.closed = Close(success, text)
        self.editable = False


    def gethistory(self) -> History:
        """
        Zwraca hashowane wartości zdań znajdujących się w historii (w formie `History` - podklasy zbioru). Hashowaną wartość można uzyskać z `hash(Sentence)`.
        """
        return self.history.copy()


    def History(self, *commands: tuple[tp.Union[Sentence, int, callable]]) -> None:
        """ Używane do manipulacji historią

            Możliwe argumenty:
                - `Sentence`    - dodaje formułę do historii 
                - `callable`    - wykonuje operacje `callable(history)` na obiekcie historii, a wynik nadpisuje jako nową historię; traktuj ją jako `set`
                - `int`         - wykonuje jedną z predefiniowanych operacji:
                    - 0 - operacja pusta
                    - 1 - reset historii

            :raises TypeError: Typ nie jest obsługiwany 
        """
        self.history(commands)



class ProofNode(ProofElement, NodeMixin):
    namegen = random.Random()


    def __init__(self, sentence: Sentence, branch_name: str, layer: int = 0, history: History = None, parent: ProofNode = None, children: tp.Iterable[ProofNode] = []):
        """Reprezentacja pojedynczego zdania w drzewie

        :param sentence: Opisywane zdanie
        :type sentence: Sentence
        :param branch_name: Nazwa gałęzi
        :type branch_name: str
        :param layer: numer warstwy, można go utożsamiać z numerem ruchu w dowodzie, pozwala na wycofywanie ruchów w przyszłości
        :type layer: int, defaults to 0
        :param history: obiekt historii, przechowuje informacjęo użytych formułach, defaults to None
        :type history: History, optional
        :param parent: poprzednik węzłu w drzewie, defaults to None
        :type parent: ProofNode, optional
        :param children: następniki węzłu w drzewie, defaults to []
        :type children: tp.Iterable[ProofNode], optional
        """
        super().__init__(sentence=sentence, branch=branch_name, layer=layer, history=history)
        if parent:
            self.parent=parent
        else:
            self.parent=None
        self.children = children
    

    def gen_name(self, am=2) -> tuple[str]:
        """Generates two possible names for the children of this node"""
        branch_names = self.getbranchnames()
        possible = [i for i in colors if not i in branch_names]
        if len(possible)<am-1:
            if len(self.leaves) == 1000:
                raise ProofNodeError("No names exist")
            return self.branch, *[str(self.namegen.randint(0, 1000)) for i in range(am-1)]
        return self.branch, *random.choices(possible, k=am-1)
    

    # ProofNode reading


    def getbranchnames(self):
        return [i.branch for i in self.getleaves()]



    def getbranch(self) -> tuple[list[Sentence], Close]:
        """Zwraca gałąź dowodu z informacjami o jej zamknięciu"""
        assert self.is_leaf, "Gałąź nie jest kompletna, gdyż węzeł nie jest drzewem"
        return [i.sentence for i in self.path], self.closed


    def gettree(self) -> PrintedProofNode:
        """Rekurencyjnie opracowuje PrintedProofNode - jest to namedtuple wykorzystywana podczas printowania drzewa"""
        if not self.is_leaf:
            children = (i.gettree() for i in self.children)
            closer = ''
        else:
            children = None
            if self.closed:
                closer = self.closed[0]
            else:
                closer = None
        return PrintedProofNode(sentences=self.statements, children=children, closer=closer)


    def getleaves(self, *names: tp.Iterable[str]) -> list[ProofNode]:
        """Returns all or chosen leaves (if names are provided as args)

        :return: List of the leaves
        :rtype: list[ProofNode]
        """
        if names:
            return [i for i in self.root.leaves if i.branch in names]
        else:
            return self.root.leaves


    def getopen(self) -> tp.Iterator[ProofNode]:
        """Returns all or chosen open leaves (if names are provided as args)

        :return: Iterator of the leaves
        :rtype: tp.Iterator[ProofNode]
        """
        return (i for i in self.getleaves() if not i.closed)


    def getnode_neighbour(self, left_right: str) -> tp.Union[ProofNode]:
        """Return left/right neighbour of the node 

        :param left_right: 'L/Left' or 'R/Right'
        :type left_right: str
        :raises ProofNodeError: left_right is not a valid direction
        :return: The neighbour
        :rtype: ProofNode
        """
        if not self.parent:
            return None

        # Find neighbour's index
        index = self.parent.getchildren().index(self)
        if left_right.upper() in ('R', 'RIGHT'):
            util.rightsibling(self)
        elif left_right.upper() in ('L', 'LEFT'):
            util.leftsibling(self)
        else:
            raise ProofNodeError(f"'{left_right}' is not a valid direction")


    def is_closed(self) -> bool:
        """Sprawdza, czy wszystkie gałęzie zamknięto"""
        return all((i.closed for i in self.leaves))


    def is_successful(self) -> bool:
        """Sprawdza, czy wszystkie liście zamknięto ze względu na sukces"""
        return all((i.closed is not None and i.closed.success == 1 for i in self.getleaves()))


    # ProofNode modification

    def append(self, sentences: tp.Iterable[tuple[Sentence]]):
        """Dodaje zdania do drzewa"""
        names = self.gen_name(am=len(sentences))
        layer = max((i.layer for i in self.getleaves()))+1
        for i, branch in enumerate(sentences):
            par = self
            for sen in branch:
                par = ProofNode(sen, names[i], layer, self.history, parent=par)
