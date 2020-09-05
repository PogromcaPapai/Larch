from __future__ import annotations
import json
import logging as log
import os
import typing as tp
from string import ascii_uppercase as alphabet

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
        if leaves_list:
            leaves_list[branch_name] = self
        self.leaves = leaves_list

    # Technical

    @EngineLog
    def _gen_name(self) -> tp.Tuple[str]:
        if self.parent:
            dist = 2*alphabet.index(self.name) - (alphabet.index(self.parent.children()[0].name) - alphabet.index(self.parent.children()[1].name))
            assert dist != 0
            new=abs(dist)//2
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

    def children(self):
        return self.left, self.right

    def getbranch(self):
        if self.parent:
            return self.parent.getbranch() + self.statements
        else:
            return self.statements

    def gettree(self):
        if self.left:  # Trees with only one child aren't supported
            return self.statements
        else:
            return (self.statements, self.left.get_tree(), self.right.get_tree())

    # Tree modification

    @EngineLog
    def add_statement(self, statement: str):
        self.statements.append(statement)

    @EngineLog
    def add_child(self, l_statement: str, r_statement: str):
        names=self._gen_name()
        self.left=Tree(l_statement, names[0], self, leaves_list=self.leaves)
        self.right=Tree(r_statement, names[1], self, leaves_list=self.leaves)

    def append(self, *statements):
        if len(statements) == 1:
            self.add_statement(*statements)
        elif len(statements) == 2:
            self.add_child(*statements)
        else:
            TreeError(
                f'Trying to append {len(statements)} statements to the tree')

# ENGINE

# Exceptions


class EngineError(Exception):
    def __init__(self, msg: str, *args, **kwargs):
        logger.error(msg)
        super().__init__(msg, *args, **kwargs)

# Session


class Session(object):
    ENGINE_VERSION='0.0.1'

    def __init__(self, config_file: str):
        self.config_name=config_file
        self.read_config()
        self.iu_socket=self.config['chosen_plugins']['UserInterface']
        self.sockets={
            'FormalSystem': pop.Socket('FormalSystem', os.path.abspath(
                'FormalSystem'), '0.0.1', '__template__.py'),

        }

    # Plugin manpiulation

    @EngineChangeLog
    def plug_switch(self, socket_or_old: str, new: str) -> None:
        if socket_or_old == 'UserInterface' or socket_or_old == self.config['chosen_plugins']['UserInterface']:
            socket_name='UserInterface'
        else:
            # Socket name searching
            socket=self.sockets.get(socket_or_old, None)
            if not socket:
                for i in self.config['chosen_plugins'].items():
                    if i[1] == socket_or_old:
                        socket_name=i[0]
                        socket=self.sockets[socket_name]
            if not socket:
                raise EngineError(f"Socket/plugin {socket_or_old} not found")

            # Plugging
            socket.plug(new)

        # Config editing
        self.config['chosen_plugins'][socket.name]=new
        self.write_config()

    def plug_list(self, socket: str) -> list:
        sock=self.sockets.get(socket, None)
        if sock is None:
            if socket == "UserInterface":
                return [file[:-3] for file in os.listdir("UserInterface") if (
                    file.endswith(".py") and not (file in {"__template__.py", "__init__.py"}))]
            raise EngineError(f"There is no socket named {socket}")
        else:
            return sock.find_plugins()

    def plug_gen(self, socket: str, name: str) -> None:
        sock=self.sockets.get(socket, None)
        if sock is None:
            if socket == "UserInterface":
                raise EngineError(
                    "UserInterface sockets need to be created manually")
            raise EngineError(f"There is no socket named {socket}")
        else:
            sock.generate_template(name)

    # config reading and writing

    def read_config(self):
        logger.debug("Config loading")
        with open(self.config_name, 'r') as target:
            self.config=json.load(target)

    def write_config(self):
        logger.debug("Config writing")
        with open(self.config_name, 'w') as target:
            json.dump(self.config, target)

    # Misc

    def get_socket_names(self):
        return {"UserInterface"} | self.sockets.keys()
