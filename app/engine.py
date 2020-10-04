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

# DATA STRUCTURE


PrintedTree = namedtuple('PrintedTree', ('sentences', 'left', 'right'))


class TreeError(Exception):
    def __init__(self, msg: str, *args, **kwargs):
        logger.error(msg)
        super().__init__(msg, *args, **kwargs)


class Tree(object):

    def __init__(self, start_statement: str, branch_name: str = 'A', parent: Tree = None, children_l: Tree = None, children_r: Tree = None, leaves_list: tp.Dict[str, Tree] = None):
        self.name = branch_name
        self.statements = [start_statement]
        self.parent = parent
        assert (children_l and children_r) or (
            not children_l and not children_r), "One child"
        self.left = children_l
        self.right = children_r
        self.closed = False
        if leaves_list is None:
            leaves_list = dict()
        leaves_list[branch_name] = self
        self.leaves = leaves_list

    # Technical

    @staticmethod
    def _distalph(letter_a: str, letter_b: str) -> int:
        assert len(letter_a) == 1 and len(
            letter_b) == 1, "_distalph only checks chars"
        return alphabet.index(letter_a) - alphabet.index(letter_b)

    def _gen_name(self) -> tp.Tuple[str]:
        if self.parent:
            dist = self._distalph(self.name, self.parent.getchildren()[
                                  0].name) + self._distalph(self.name, self.parent.getchildren()[1].name)
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

    def getroot(self):
        if self.parent:
            return self.parent.getroot()
        else:
            return self.statements[0]

    def getchildren(self):
        if not self.left:  # Trees with only one child aren't supported
            return None
        else:
            return self.left, self.right

    def getbranch(self):
        if self.parent:
            return self.parent.getbranch() + self.statements
        else:
            return self.statements

    def gettree(self):
        if not self.left:  # Trees with only one child aren't supported
            return None
        else:
            return PrintedTree(sentences=self.statements, left=self.left.get_tree(), right=self.right.get_tree())

    def getleaves(self, *names: tp.Iterableo[str]) -> tp.List[Tree]:
        if name:
            return [self.leaves.get(i, None) for i in names]
        else:
            return list(self.leaves.values())

    def getneighbour(self, left_right: str) -> tp.Union[Tree, None]:
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
    def add_statement(self, statements: tp.Union[str, tp.List[str]]):
        if isinstance(statements, str):
            self.statements.append(statements)
        else:
            self.statements.extend(statements)

    @EngineLog
    def add_child(self, l_statements: tp.Union[str, tp.List[str]], r_statements: tp.Union[str, tp.List[str]]):
        names = self._gen_name()
        if isinstance(l_statements, str):
            self.left = Tree(
                l_statements, names[0], self, leaves_list=self.leaves)
        else:
            self.left = Tree(
                l_statements[0], names[0], self, leaves_list=self.leaves)
            self.left.add_statement(l_statements[1:])
        if isinstance(r_statements, str):
            self.right = Tree(
                r_statements, names[1], self, leaves_list=self.leaves)
        else:
            self.right = Tree(
                r_statements[0], names[1], self, leaves_list=self.leaves)
            self.right.add_statement(r_statements[1:])

    def append(self, statements):
        if len(statements) == 1:
            self.add_statement(*statements)
        elif len(statements) == 2:
            self.add_child(*statements)
        else:
            raise TreeError(
                f'Trying to append {len(statements)} branches to the tree')

# ENGINE

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
        self.sockets.update({"UserInterface": pop.DummySocket("UserInterface", os.path.abspath("UserInterface"), self.ENGINE_VERSION, '__template__.py')})
        
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
            self.proof = Tree(tokenized, branch_name='A')
            self.branch = 'A'

    @EngineLog
    def reset_proof(self) -> None:
        self.proof = None
        self.branch = ''

    @EngineLog
    def use_rule(self, rule: str, statement_number: int) -> None:
        if not self.sockets['FormalSystem'].isplugged():
            raise EngineError(
                "System lacks FormalSystem plugin")
        if not self.proof:
            raise EngineError(
                "There is no proof started")

        branch = self.proof.leaves[self.branch].getbranch()
        if statement_number <= 0 or statement_number > len(branch):
            raise EngineError("No such statement")
        try:
            out = self.sockets['FormalSystem']().use_rule(
                rule, branch[statement_number-1])
        except Exception as e:
            if str(e) == "No such rule":
                raise EngineError("No such rule")
            else:
                raise e
        if out:
            self.proof.leaves[self.branch].append(out)

    # Proof navigation

    def getbranch(self):
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
