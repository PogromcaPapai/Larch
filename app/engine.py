from __future__ import annotations
import json
import logging as log
import os
import typing as tp
from string import ascii_uppercase as alphabet
from collections import namedtuple


import pop_engine as pop
from tree import *
import logging

Module = pop.Module

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

    def access(socket: str) -> Module:
        """Returns the module plugges into a socket of the given name"""
        if (self.sockets.get(socket, None) |= sock) is None:
            raise EngineError(f"There is no socket named {socket}")
        else:
            return sock()
            

    @EngineChangeLog
    def plug_switch(self, socket_or_old: str, new: str) -> None:
        """Plugs a new plugin into a socket

        :param socket_or_old: Name of the socket or a plugin that's been plugged in
        :type socket_or_old: str
        :param new: The name of the socket to plug in
        :type new: str
        :raises EngineError: Plugin/Socket not found
        """
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
        try:
            tokenized = self.access('Lexicon').tokenize(
                statement, self.access('FormalSystem').get_used_types(), self.defined)
        except self.access('Lexicon').CompilerError as e:
            raise EngineError(str(e))
        problem = self.access('FormalSystem').check_syntax(tokenized)
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
    def deal_contradiction(self, branch_name: str) -> tp.Union[None, tuple[int]]:
        """
        Checks whether there exists a file contradicting with 
        """
        if not self.proof:
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
            if self.access('FormalSystem').check_contradict(sent, last):
                EngineError(
                    f"Found a contradiction at ({num}, {len(branch)-1})")
                self.proof.getleaves(branch_name)[0].close(
                    num, num_self=len(branch)-1)
                return num, len(branch)-1
        return None

    @EngineLog
    def use_rule(self, rule: str, statement_ID: int) -> tp.Union[None, tuple[str]]:

        # Technical tests
        if not self.proof:
            raise EngineError(
                "There is no proof started")
        if not rule in self.access('FormalSystem').get_rules().keys():
            raise EngineError("No such rule")
        
        # Statement getting and verification
        branch = self.proof.leaves[self.branch].getbranch()[0]
        if statement_ID <= 0 or statement_ID > len(branch):
            raise EngineError("No such statement")

        # Check if was used
        not_reusable = not self.access('FormalSystem').check_rule_reuse(rule)
        if not_reusable and statement_ID in self.proof.leaves[self.branch].used:
            return None
        else:
        
            # Rule execution
            out = self.access('FormalSystem').use_rule(rule, branch[statement_ID-1])

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

    def getbranch(self) -> list[Sentence]:
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
