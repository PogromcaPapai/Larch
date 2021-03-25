from __future__ import annotations
from app.tree_helpers import Close, History

import typing as tp
import json, random
from collections import namedtuple, OrderedDict
from math import inf as INFINITY
from anytree import NodeMixin
from tree_helpers import *

with open('colors.json') as f:
    colors = list(json.load(f).keys())

Sentence = tp.NewType("Sentence", list[str])
PrintedProofNode = namedtuple('PrintedProofNode', ('sentences', 'children', 'closer'))


class ProofNodeError(Exception):
    def __init__(self, msg: str, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ProofElement(object):
    namegen = random.Random()

    def __init__(self, sentence: Sentence, branch_name: str, layer: int = 0, history: History = None) -> None:
        super().__init__()
        self.sentence = sentence
        self.branch = branch_name
        self.closed = None
        if history is None:
            self.history = History()
        else:    
            self.history = history
        self.editable = True
        self.layer = layer

    def close(self, closer: Close):
        self.closed = Close
        self.editable = False



class ProofNode(ProofElement, NodeMixin):
    child_limit = 2

    # Class methods

    # gen_name should be changed before implementing the possibility of changing the child limit
    # @classmethod
    # def set_child_limit(cls, amount: int) -> None:
    #     """Sets the limit of children in the class to the given amount"""
    #     assert isinstance(amount, int)
    #     cls.child_limit = amount

    #Konstruktor od nowa
    def __init__(self, start_statement: Sentence, branch_name: str = 'A', parent: ProofNode = None, leaves_dict: dict[str, ProofNode] = None, closed: tp.Union[None, tuple[int]] = None, used: set[int] = None):
        self.name = ''

    # Technical

    def gen_name(self, am=2) -> tuple[str]:
        """Generates two possible names for the children of this node"""
        possible = [i for i in colors if not i in self.leaves.keys()]
        if len(possible)<am-1:
            if len(self.leaves) == 1000:
                raise ProofNodeError("No names exist")
            return self.name, *[str(self.namegen.randint(0, 1000)) for i in range(am-1)]
        return self.name, *random.choices(possible, k=am-1) 


    # ProofNode reading


    def getroot(self) -> ProofNode:
        return self.path[0]


    def getchildren(self, index=None) -> tuple[ProofNode]:
        if not index is None:
            return self.children[index]
        else:
            return tuple(self.children)


    def getbranch(self) -> tuple[str, bool]:
        """Returns all the sentences in this node's branch and information about branch's closure"""
        return self._getbranch(), self.closed


    def _getbranch(self):
        """Returns all the sentences in this node's branch; `getbranch` is recommended"""
        if self.parent:
            return self.parent._getbranch() + self.statements
        else:
            return self.statements


    def gettree(self):
        """Creates recursively a named tuple with the sentences"""
        if self.children:
            children = (i.gettree() for i in self.children)
            closer = ''
        else:
            children = None
            if self.closed:
                closer = self.closed[0]
            else:
                closer = ''
        return PrintedProofNode(sentences=self.statements, children=children, closer=closer)


    def findleaves(self, *names: tp.Iterable[str]) -> list[ProofNode]:
        """Returns all or chosen leaves (if names are provided as args)

        :return: List of the leaves
        :rtype: list[ProofNode]
        """
        return (i for i in self.leaves if i.)


    def getopen(self) -> tp.Iterator[ProofNode]:
        """Returns all or chosen open leaves (if names are provided as args)

        :return: Iterator of the leaves
        :rtype: tp.Iterator[ProofNode]
        """
        return (i for i in self.leaves if not i.closed)


    #NA PEWNO ZBĘDNE, JEST DO TEGO FUNKCJA
    def getbranch_neighbour(self, left_right: str):
        """Return left/right neighbour of the branch

        :param left_right: 'L/Left' or 'R/Right'
        :type left_right: str
        :raises ProofNodeError: left_right is not a valid direction
        :return: A leaf of the neighbour branch
        :rtype: ProofNode
        """
        min_dist = INFINITY
        obj_w_min = None
        if left_right.upper() in ('R', 'RIGHT'):
            for _, i in self.leaves.items():
                dist = self._dist(i, self)
                if dist > 0 and dist < min_dist:
                    min_dist = dist
                    obj_w_min = i
            return obj_w_min

        # Copy of the previous part, but with different distance computing
        elif left_right.upper() in ('L', 'LEFT'):
            for _, i in self.leaves.items():
                dist = self._dist(self, i)
                if dist > 0 and dist < min_dist:
                    min_dist = dist
                    obj_w_min = i
            return obj_w_min

        else:
            raise ProofNodeError(f"'{left_right}' is not a valid direction")
            return None


    #NA PEWNO ZBĘDNE, JEST DO TEGO FUNKCJA
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
            index += 1
        elif left_right.upper() in ('L', 'LEFT'):
            index -= 1
        else:
            raise ProofNodeError(f"'{left_right}' is not a valid direction")

        # Get neighbour
        if index >= len(self.parent.getchildren()) or index < 0:
            if (parent_neigh := self.parent.getnode_neighbour(left_right)):
                if parent_neigh.getchildren():
                    return parent_neigh.getchildren(-1*(index < 0))
                else:
                    return parent_neigh
            else:
                return None
        else:
            return self.parent.getchildren(index)


    def is_closed(self) -> bool:
        """Sprawdza, czy wszystkie gałęzie zamknięto"""
        return all((i.closed for i in self.leaves))

    def is_successful(self) -> bool:
        """Sprawdza, czy wszystkie liście zamknięto ze względu na sukces"""
        return all((i.closed is not None and i.closed.success == 1 for i in self.getroot().leaves))


    # ProofNode modification


    def _add_statements(self, statements: tuple[Sentence]) -> None:
        """Adds statement(s) to the node

        :param statements: statement(s)
        :type statements: Sentence
        """
        self.statements.extend(statements)


    def _add_children(self, *statements: tp.Iterable[tuple[Sentence]]):
        """Adds statements as children of the node"""
        names = self.gen_name()
        for i, sentence in enumerate(statements):
            self.children.append(ProofNode(
                sentence[0], names[i], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy()))
            if (to_add := sentence[1:]):
                self.children[-1].append((to_add,))


    def append(self, statements: tuple[tuple[Sentence]]):
        """Prefered way of adding new statements. Use a tuple with tuples filled with sentences.
        Every tuple of strings is interpreted as a new branch. If there is only one statement it will be added to the existing node. 

        :param statements: Statements grouped into branches
        :type statements: tuple[tuple[str]]
        :raises ProofNodeError: Too much branches to append
        """
        assert isinstance(statements, tuple)
        if len(statements) == 1:
            self._add_statements(*statements)
        elif len(statements) == self.child_limit:
            self._add_children(*statements)
        else:
            raise ProofNodeError(
                f'Trying to append {len(statements)} branches to the tree')


    def close(self, info: str, code: int = 1) -> None:
        """Closes the branch using the last

        Code list:
        0 - Empty (nothing more can be done)
        1 - Classic closure
        8 - Loop prevention (get it? the loop?)
        """
        assert isinstance(info, str) and isinstance(code, int)
        self.closed = (code, info)

    def get_used(self) -> set[Sentence]:
        """
        Adds the statement ID to the used statements set
        Should only be used after non-reusable rules
        """
        return self.used.copy()

    def add_used(self, used_l: tuple[tp.Union[int, tuple[str]]]) -> None:
        """
        Adds the statement ID to the used statements set
        Should only be used after non-reusable rules
        """
        for used in used_l:
            assert not isinstance(used, str)
            #               Code handling:
            if used == -1:  # Reset set
                self.used.clear()
            elif used == 0: # Pass
                return
            else:
                self.used.add(tuple(used))
