from __future__ import annotations
import json
import logging as log
import os
import typing as tp
from string import ascii_uppercase as alphabet
from collections import namedtuple


import pop_engine as pop
import logging

# Logging config

logger = logging.getLogger('engine')


def EngineLog(func, *args, **kwargs):
    def new(*args, **kwargs):
        logger.debug(
            f"{func.__name__} with args={str(args)} and kwargs={str(kwargs)}")
        return func(*args, **kwargs)
    return new


def EngineChangeLog(func, *args, **kwargs):
    def new(*args, **kwargs):
        logger.info(
            f"{func.__name__} with args={str(args)} and kwargs={str(kwargs)}")
        return func(*args, **kwargs)
    return new

#################################### DATA STRUCTURE ####################################


PrintedTree = namedtuple('PrintedTree', ('sentences', 'left', 'right'))


class TreeError(Exception):
    def __init__(self, msg: str, *args, **kwargs):
        logger.error(msg)
        super().__init__(msg, *args, **kwargs)


class Tree(object):

    def __init__(self, start_statement: str, branch_name: str = 'A', parent: Tree = None, child_l: Tree = None,
                 child_r: Tree = None, leaves_dict: tp.Dict[str, Tree] = None, closed: tp.Union[None, tp.Tuple[int]] = None, used: tp.Set[int] = set()):
        """The representation of one node in a tree; non-diverging rules add to this one's statement list. It's accounted for in the interface

        :param start_statement: The first statement to insert into the node
        :type start_statement: str
        :param branch_name: Name of the branch; use `gen_name` on the parent to find the name, defaults to 'A'
        :type branch_name: str, optional
        :param parent: Parent node
        :type parent: Tree, optional
        :param child_l: Left child of the node
        :type child_l: Tree, optional
        :param child_r: Right child of the node
        :type child_r: Tree, optional
        :param leaves_dict: If the tree has a dict of leaves it can be stored here; when not provided system will create an empty dict
        :type leaves_dict: tp.Dict[str, Tree], optional
        :param closed: Stores information about the closing sentences of this leaf, defaults to None
        :type closed: tp.Tuple[int], optional
        :param used: A set for storing IDs of sentences which can't be used again in this branch, defaults to an empty set
        :type used: tp.Set[int], optional
        """
        self.name = branch_name
        self.statements = [start_statement]
        self.parent = parent
        assert (child_l and child_r) or (
            not child_l and not child_r), "One child"
        self.left = child_l     # TODO: zaimplementować to jako self.children, a nie left i right
        self.right = child_r
        self.closed = closed
        self.used = used
        if leaves_dict is None:
            leaves_dict = dict()
        leaves_dict[branch_name] = self
        self.leaves = leaves_dict

    # Technical

    @staticmethod
    def _distalph(letter_a: str, letter_b: str) -> int:
        """Calculates distance between two letters"""
        assert len(letter_a) == 1 and len(
            letter_b) == 1, "_distalph only checks chars"
        return alphabet.index(letter_a) - alphabet.index(letter_b)

    def gen_name(self) -> tp.Tuple[str]:
        """Generates two possible names for the children of this node"""
        if self.parent:
            dist = self._distalph(self.name, self.parent.getchildren()[
                                  0].name) + self._distalph(self.name, self.parent.getchildren()[-1].name)
            assert dist != 0
            new = abs(dist)//2
            if dist < 0:
                if self.leaves:
                    assert not alphabet[new] in self.leaves.keys()
                return self.name, alphabet[new]
            else:
                if self.leaves:
                    assert not alphabet[25-new] in self.leaves.keys()
                return alphabet[25-new], self.name
        else:
            return 'A', 'Z'

    # Tree reading

    def getroot(self) -> Tree:
        if self.parent:
            return self.parent.getroot()
        else:
            return self

    def getchildren(self) -> tp.Tuple[Tree, Tree]:
        if not self.left:  # Trees with only one child aren't supported
            return None
        else:
            return self.left, self.right

    def getbranch(self) -> tp.Tuple[str, bool]:
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
        if not self.left:  # Trees with only one child aren't supported
            return PrintedTree(sentences=self.statements, left=None, right=None)
        else:
            return PrintedTree(sentences=self.statements, left=self.left.get_tree(), right=self.right.get_tree())

    def getleaves(self, *names: tp.Iterable[str]) -> tp.List[Tree]:
        """Returns all or chosen leaves (if names are provided as args)

        :return: List of the leaves
        :rtype: tp.List[Tree]
        """
        if names:
            return [self.leaves.get(i, None) for i in names]
        else:
            return list(self.leaves.values())

    def getopen(self, *names: tp.Iterable[str]) -> tp.Iterator[Tree]:
        """Returns all or chosen open leaves (if names are provided as args)

        :return: Iterator of the leaves
        :rtype: tp.Iterator[Tree]
        """
        return (i for i in self.getleaves(*names) if not i.closed)

    def getneighbour(self, left_right: str) -> tp.Union[Tree, None]: 
        #TODO:  Verify whether it makes sense algorithmically
        #       Maybe separete a method for leaves and the rest of the tree 
        min_dist = 100
        obj_w_min = None
        if left_right.upper() in ('R', 'RIGHT'):
            for i in self.leaves.items():
                dist = self._distalph(i[0], self.name)
                if dist > 0 and dist < min_dist:
                    min_dist = dist
                    obj_w_min = i[1]
            return obj_w_min
        elif left_right.upper() in ('L', 'LEFT'):
            for i in self.leaves.items():
                dist = self._distalph(self.name, i[0])
                if dist > 0 and dist < min_dist:
                    min_dist = dist
                    obj_w_min = i[1]
            return obj_w_min
        else:
            raise EngineError(f"'{left_right}' is not a valid direction")
            return None

    # Tree modification

    @EngineLog
    def _add_statement(self, statements: tp.Union[str, tp.List[str]]) -> None:
        """Adds statement(s) to the node

        :param statements: statement(s)
        :type statements: str or tp.List[str]
        """
        if isinstance(statements, str):
            self.statements.append(statements)
        else:
            self.statements.extend(statements)

    @EngineLog
    def _add_child(self, l_statements: tp.Union[str, tp.List[str]], r_statements: tp.Union[str, tp.List[str]]):
        """Adds statements as children of the node

        :param l_statements: Statement(s) to be added to the left child
        :type l_statements: str, tp.List[str]
        :param r_statements: Statement(s) to be added to the right child
        :type r_statements: str, tp.List[str]
        """
        names = self.gen_name()
        if isinstance(l_statements, str):
            self.left = Tree(
                l_statements, names[0], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
        else:
            self.left = Tree(
                l_statements[0], names[0], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
            self.left.append((l_statements[1:],))
        if isinstance(r_statements, str):
            self.right = Tree(
                r_statements, names[1], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
        else:
            self.right = Tree(
                r_statements[0], names[1], self, leaves_dict=self.leaves, closed=self.closed, used=self.used.copy())
            self.right.append((r_statements[1:],))

    def append(self, statements: tuple):
        """Prefered way of adding new statements. Use a tuple with tuples filled with sentences.
        Every tuple of strings is interpreted as a new branch. If there is only one statement it will be added to the existing node. 

        :param statements: Statements grouped into branches
        :type statements: tuple[tuple[str]]
        :raises TreeError: Too much branches to append
        """
        assert isinstance(statements, tuple)
        if len(statements) == 1:
            self._add_statement(*statements)
        elif len(statements) == 2:
            self._add_child(*statements)
        else:
            raise TreeError(
                f'Trying to append {len(statements)} branches to the tree')

    def close(self, contradicting: int, num_self: int = None) -> None:
        """Close the 

        :param contradicting: ID of the colliding sentence
        :type contradicting: int
        :param num_self: Use if you already have ID of the colliding sentence
        :type num_self: int, optional
        """
        if num_self:
            self.closed = (num_self, contradicting)
        else:
            self.closed = (len(self.getbranch())-1, contradicting)

    def add_used(self, used: int) -> None:
        """
        Adds the statement ID to the used statements set
        Should only be used after non-reusable rules
        """
        assert used not in self.used
        self.used.add(used)

#################################### ENGINE ####################################

# Exceptions


class EngineError(Exception):
    def __init__(self, msg: str, *args, **kwargs):
        logger.error(msg)
        super().__init__(msg, *args, **kwargs)

# Session


class Session(object):
    ENGINE_VERSION = '0.0.1'
    SOCKETS = ('FormalSystem', 'Lexicon')

    def __init__(self, config_file: str):
        self.config_name = config_file
        self.read_config()
        self.sockets = {name: pop.Socket(name, os.path.abspath(name), self.ENGINE_VERSION, '__template__.py',
                                         self.config['chosen_plugins'].get(name, None)) for name in self.SOCKETS}
        self.sockets["UserInterface"] = pop.DummySocket("UserInterface", os.path.abspath(
            "UserInterface"), self.ENGINE_VERSION, '__template__.py')

        self.defined = {}
        self.proof = None
        self.branch = ""

    # Plugin manpiulation

    @EngineChangeLog
    def plug_switch(self, socket_or_old: str, new: str) -> None:
        if socket_or_old == 'UserInterface' or socket_or_old == self.config['chosen_plugins']['UserInterface']:
            socket_name = 'UserInterface'
        else:
            # Socket name searching
            socket = self.sockets.get(socket_or_old, None)
            if not socket:
                for i in self.config['chosen_plugins'].items():
                    if i[1] == socket_or_old:
                        socket_name = i[0]
                        socket = self.sockets[socket_name]
            if not socket:
                raise EngineError(f"Socket/plugin {socket_or_old} not found")

            # Plugging
            socket.plug(new)

        # Config editing
        self.config['chosen_plugins'][socket_name] = new
        self.write_config()

    def plug_list(self, socket: str) -> list:
        sock = self.sockets.get(socket, None)
        if sock is None:
            raise EngineError(f"There is no socket named {socket}")
        else:
            return sock.find_plugins()

    def plug_gen(self, socket: str, name: str) -> None:
        sock = self.sockets.get(socket, None)
        if sock is None:
            raise EngineError(f"There is no socket named {socket}")
        else:
            sock.generate_template(name)

    # config reading and writing

    def read_config(self):
        logger.debug("Config loading")
        with open(self.config_name, 'r') as target:
            self.config = json.load(target)

    def write_config(self):
        logger.debug("Config writing")
        with open(self.config_name, 'w') as target:
            json.dump(self.config, target)


    # Proof manipulation

    @EngineLog
    def new_proof(self, statement: str) -> None:
        """Initializes a tree for a new proof

        :param statement: Proved statement (will be tokenized)
        :type statement: str
        :raises EngineError: System lacks Lexicon plugin or FormalSystem plugin
        :raises ValueError: Wrong statement syntax
        """
        if not self.sockets['Lexicon'].isplugged() or not self.sockets['FormalSystem'].isplugged():
            raise EngineError(
                "System lacks Lexicon plugin or FormalSystem plugin")
        try:
            tokenized = self.sockets['Lexicon']().tokenize(
                statement, self.sockets['FormalSystem']().get_used_types(), self.defined)
        except self.sockets['Lexicon']().CompilerError as e:
            raise EngineError(str(e))
        problem = self.sockets['FormalSystem']().check_syntax(tokenized)
        if problem:
            logger.warning(f"{statement} is not a valid statement \n{problem}")
            raise ValueError(f"Syntax error: {problem}")
        else:
            tokenized = self.sockets['FormalSystem'](
            ).prepare_for_proving(tokenized)
            self.proof = Tree(tokenized, branch_name='A')
            self.branch = 'A'

    @EngineLog
    def reset_proof(self) -> None:
        self.proof = None
        self.branch = ''

    @EngineLog
    def deal_contradiction(self, branch_name: str) -> tp.Union[None, tp.Tuple[int]]:
        """
        Checks whether there exists a file contradicting with 
        """
        if not self.sockets['FormalSystem'].isplugged():
            raise EngineError(
                "System lacks FormalSystem plugin")
        elif not self.proof:
            raise EngineError(
                "There is no proof started")

        try:
            branch, closed = self.proof.getleaves(branch_name)[0].getbranch()
        except ValueError as e:
            if e.message == 'not enough values to unpack (expected 2, got 1)':
                raise EngineError(
                    "Proof too short to check for contradictions")
            else:
                raise e

        last = branch[-1]
        for num, sent in enumerate(branch[:-1]):
            if self.sockets['FormalSystem']().check_contradict(sent, last):
                EngineError(
                    f"Found a contradiction at ({num}, {len(branch)-1})")
                self.proof.getleaves(branch_name)[0].close(
                    num, num_self=len(branch)-1)
                return num, len(branch)-1
        return None

    @EngineLog
    def use_rule(self, rule: str, statement_ID: int) -> tp.Union[None, tp.Tuple[str]]:

        # Technical tests
        if not self.sockets['FormalSystem'].isplugged():
            raise EngineError(
                "System lacks FormalSystem plugin")
        if not self.proof:
            raise EngineError(
                "There is no proof started")
        if not rule in self.sockets['FormalSystem']().get_rules().keys():
            raise EngineError("No such rule")
        
        # Statement getting and verification
        branch = self.proof.leaves[self.branch].getbranch()[0]
        if statement_ID <= 0 or statement_ID > len(branch):
            raise EngineError("No such statement")

        # Check if was used
        not_reusable = not self.sockets['FormalSystem']().check_rule_reuse(rule)
        if not_reusable and statement_ID in self.proof.leaves[self.branch].used:
            return None
        else:
        
            # Rule execution
            out = self.sockets['FormalSystem']().use_rule(rule, branch[statement_ID-1])

            if out:
                old = self.proof.leaves[self.branch]
                self.proof.leaves[self.branch].append(out)
                children = old.getchildren()
                
                if children is None:
                    if not_reusable:
                        self.proof.leaves[self.branch].add_used(statement_ID)
                    return old.name
                else:
                    if not_reusable:    
                        for j in children:
                            j.add_used(statement_ID)
                    return tuple([i.name for i in children])
            else:
                return None

    # Proof navigation

    def getbranch(self) -> tp.List[str]:
        try:
            return self.proof.leaves[self.branch].getbranch()
        except KeyError:
            raise EngineError(
                f"Branch '{self.branch.name}' doesn't exist in this proof")
        except AttributeError:
            raise EngineError("There is no proof started")

    def jump(self, new: str):
        if not self.proof:
            raise EngineError("There is no proof started")
        new = new.upper()
        if new in ('LEFT', 'RIGHT'):
            changed = self.proof.leaves[self.branch].getneighbour(new)
            if changed is None:
                raise EngineError(f"There is no branch on the {new.lower()}")
            else:
                self.branch = changed.name
        else:
            changed = self.proof.leaves.get(new, None)
            if not changed:
                if len(new) > 1:
                    raise EngineError(f"Branch name too long")
                else:
                    raise EngineError(
                        f"Branch '{new}' doesn't exist in this proof")
            else:
                self.branch = changed.name

    # Misc

    def get_socket_names(self):
        return self.SOCKETS
