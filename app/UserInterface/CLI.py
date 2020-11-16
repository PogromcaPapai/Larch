import json
import logging
import os
import sys
import typing as tp
from collections import OrderedDict, namedtuple
from math import log10
from xml.sax.saxutils import escape

import engine
import prompt_toolkit as ptk

SOCKET = 'UserInterface'
VERSION = '0.0.1'

with open('colors.json') as f:
    colors = json.load(f)

# Logging config

logging.basicConfig(filename='log.log', level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logger = logging.getLogger('interface')


def UIlogged(func):
    def new(*args, **kwargs):
        logger.debug(
            f"{func.__name__} with args={str(args)} and kwargs={str(kwargs)}")
        return func(*args, **kwargs)
    return new


# Command parsing execution

class ParsingError(Exception):
    pass

Command = namedtuple('Command', ('func', 'args', 'docs'))

def parser(statement: str, _dict: dict) -> list[Command]:
    """Parses the statement into a list of commands to execute

    :param statement: parsed command
    :type statement: str
    :param _dict: Command dict
    :type _dict: dict
    :raises ParsingError: Wrong amount of arguments
    :raises ParsingError: Command not found in `_dict`
    :raises TypeError: Wrong argument type
    :return: List of commands to execute
    :rtype: list[Command]
    """
    comm = []
    if ';' in statement:
        raise ParsingError("Multiple commands not supported yet")
    for command_raw in statement.split(';'):
        # Function parsing
        command = command_raw.strip()
        func = None
        for i in _dict.items():
            if command.startswith(i[0]):
                func = i[1]
                name = i[0]
                break
        if not func:
            raise ParsingError("Command not found")
        args = command[len(name):].split()

        # Invoking the help command
        if '?' in args or '--help' in args or 'help' in args:
            if func['comm'].__doc__:
                doc = "\n".join(
                    (f"Help for '{name}':", func['summary'], func['comm'].__doc__))
            else:
                doc = func['summary']
            comm.append(Command(func['comm'], None, doc))
            continue

        # Argument conversion
        if func['args'] == 'multiple_strings':
            # mechanism for prove
            converted = command[len(name):].strip()
            if len(converted) == 0:
                raise ParsingError("More arguments needed")
        else:
            # mechanism for other types
            if len(args) > len(func['args']):
                raise ParsingError("Too many arguments")
            elif len(args) < len(func['args']):
                raise ParsingError("More arguments needed")
            converted = []
            for form, val in zip(func['args'], args):
                try:
                    new = form(val)
                except ValueError:
                    raise TypeError("Wrong argument type")
                converted.append(new)

        comm.append(Command(func['comm'], converted, None))
    return comm


@UIlogged
def performer(command: Command, session: engine.Session) -> str:
    """Performs the command on the session"""
    if command.docs:
        return command.docs
    else:
        if isinstance(command.args, str):
            return command.func(session, command.args)
        else:
            return command.func(session, *command.args)


# Commands

def do_clear(session) -> str:
    """Clears the screen, useful when dealing with graphical bugs"""
    ptk.shortcuts.clear()
    return ""


def do_exit(session: engine.Session):
    """Exits the app"""
    logger.info("Exiting the app")
    sys.exit(0)


# Plugin manipulation


def do_plug_switch(session: engine.Session, socket_or_name: str, new: str) -> str:
    """Allows to plug in a plugin to a socket
    
    Arguments:
        - Socket/Old plugin name [str]
        - New plugin's name [str]
    """
    try:
        session.plug_switch(socket_or_name, new)
    except BaseException as e: # Not sure if this should be rewritten
        logger.error(f"Exception caught: {e}")
        return str(e)
    else:
        return f"Plugin succesfully installed: {new}"


def do_plug_list(session: engine.Session, socket: str) -> str:
    """Lists all the plugins that can be connected to a socket
    
    Arguments:
        - Socket name [str]
    """
    plugins = "; ".join(session.plug_list(socket))
    return f"Plugins available locally for {socket}:\n{plugins}"


def do_plug_list_all(session: engine.Session) -> str:
    """Lists all the plugins that can be connected to all of the Sockets"""
    strings = []
    for i in session.get_socket_names():
        plugins = "; ".join(session.plug_list(i))
        strings.append(f"Plugins available locally for {i}:\n{plugins}")
    return "\n\n".join(strings)


def do_plug_gen(session: engine.Session, socket: str, name: str) -> str:
    """Generates an empty plugin

    Arguments:
        - Socket name [str]
        - Plugin name [str]
    """
    try:
        session.plug_gen(socket, name)
    except engine.EngineError as e:
        logger.error(e)
        return e
    else:
        return f"Generated plugin {name} from template"


def do_write(session: engine.Session, filename: str):
    """
    Writes a whole proof to a file with the provided name; if the file already exists program will append to it.

    Arguments:
        - filename [str]
    """
    proof = session.gettree()
    if os.path.exists(filename):
        with open(filename, 'ab') as f:
            f.write('\n---\n')
            f.writelines([(i+'\n').encode('utf-8') for i in proof])
        return f"Proof appended to {filename}"
    else:
        with open(filename, 'wb') as f:
            f.writelines([(i+'\n').encode('utf-8') for i in proof])
        return f"Proof saved as {filename}"


# Proof manipulation


def do_prove(session: engine.Session, sentence: str) -> str:
    """Initiates a new proof

    Arguments:
        - Sentence to prove [str]
    """
    if session.proof:
        return "A proof would be deleted"
    try:
        session.new_proof(sentence)
    except engine.EngineError as e:
        return str(e)
    else:
        return "Sentence tokenized successfully \nProof initialized"


def do_use(session, name1: str, name2: str, statement: int) -> str:
    """Uses a rule in the proof

    Arguments:
        - Rule name [str]
        - ID of the statement to use the rule on [int]
    """
    out = []

    # Rule usage
    name = " ".join((name1, name2))
    try:
        val = session.use_rule(name, statement)
    except engine.EngineError as e:
        return str(e)
    if val:
        out.append(f"Used '{name}' successfully")

        # Contradiction handling
        for i in val:
            out.append(do_contra(session, i))
        if session.proof_finished():
            out.append("Every branch is closed")

    else:
        out.append("Rule couldn't be used")

    return "\n".join(out)


def do_contra(session, branch: str):
    """Detects contradictions and handles them by closing their branches"""
    cont = session.deal_contradiction(branch, 2)
    if cont:
        return f"Sentences {cont[0]+1}. and {cont[1]+1}. contradict. Branch {branch} was closed."
    else:
        return f"No contradictions found on branch {branch}."


def do_leave(session) -> str:
    """Resets the proof"""
    session.reset_proof()
    return "Proof was deleted"


# Proof navigation


def do_jump(session: engine.Session, where: str) -> str:
    """Changes the branch, 
    
    Arguments:
        - Branch name [str/">"/"right"/"left"/"<"]
    """
    try:
        session.jump({'<': 'left', '>': 'right'}.get(where, where))
        name = {'<': 'the left neighbour',
                '>': 'the right neighbour'}.get(where, where)
        return f"Branch changed to {name}"
    except engine.EngineError as e:
        return str(e)

def do_next(session: engine.Session):
    """Finds an open branch and jumps to it"""
    try:
        session.next()
    except engine.EngineError as e:
        return str(e)

def do_get_rules(session):
    """Returns all of the rules that can be used in this proof system"""
    try:
        return "\n".join((" - ".join(i) for i in session.getrules().items()))
    except engine.EngineError as e:
        return str(e)

def do_get_tree(session: engine.Session) -> str:
    return "\n".join(session.gettree())

command_dict = OrderedDict({
    # Navigation
    'exit': {'comm': do_exit, 'args': [], 'summary': ''},
    'get rules': {'comm': do_get_rules, 'args': [], 'summary': ''},
    'get tree': {'comm': do_get_tree, 'args': [], 'summary': ''},
    'jump': {'comm': do_jump, 'args': [str], 'summary': ''},
    'next': {'comm': do_next, 'args': [], 'summary': ''},
    # Proof manipulation
    'write': {'comm': do_write, 'args': [str], 'summary': ''},  # Czy zrobić oddzielne save i write? save serializowałoby tylko do wczytania, a write drukowałoby input
    'use': {'comm': do_use, 'args': [str, str, int], 'summary': ''},
    'leave': {'comm': do_leave, 'args': [], 'summary': ''},
    'prove': {'comm': do_prove, 'args': 'multiple_strings', 'summary': ''},
    # Program interaction
    'plugin switch': {'comm': do_plug_switch, 'args': [str, str], 'summary': ''},
    'plugin list all': {'comm': do_plug_list_all, 'args': [], 'summary': ''},
    'plugin list': {'comm': do_plug_list, 'args': [str], 'summary': ''},
    'plugin gen': {'comm': do_plug_gen, 'args': [str, str], 'summary': ''},
    'clear': {'comm': do_clear, 'args': [], 'summary': ''},
    'kaja godek': {'comm': lambda x: "***** ***", 'args': [], 'summary': ''}
})


def do_help(session) -> str:
    """Lists all possible commands"""
    return "\n".join(command_dict.keys())


command_dict['?'] = {'comm': do_help, 'args': [], 'summary': ''}


# Front-end setup

def get_rprompt(session):
    """Generates the branch preview in the bottom right corner"""
    DEF_PROMPT = "Miejsce na twój dowód".split()
    THRESHOLD = 128

    # Proof retrieval
    if session.proof:
        prompt, closed = session.getbranch()
        background = colors[session.branch]
    else:
        prompt = DEF_PROMPT
        closed = None
        background = colors['Grey']

    # Formatting
    to_show = []
    max_len = max((len(i) for i in prompt))+1
    for i in range(len(prompt)):
        spaces = max_len-len(prompt[i])-int(log10(i+1))
        to_show.append("".join((str(i+1), ". ", prompt[i], " "*spaces)))

    # Adding branch closing symbol
    if closed:
        s = f"XXX ({closed[0]+1}, {closed[1]+1})"
        spaces = max_len-len(s)+int(log10(i+1))+3
        to_show.append(s+spaces*" ")

    # Foreground color calculating
    if max_color(background)>THRESHOLD:
        foreground = "#000000"
    else:
        foreground = "#FFFFFF"

    new = " \n ".join(to_show)
    return ptk.HTML(f'\n<style fg="{foreground}" bg="{background}"> {escape(new)} </style>')


def max_color(rgb_color: str) -> int:
    """
    Calculates highest value from the RGB format
    """
    assert len(rgb_color)==7
    red = int(rgb_color[1:3], 16)
    green = int(rgb_color[3:5], 16)
    blue = int(rgb_color[5:], 16)
    return max((red, green, blue))

def get_toolbar():
    return ptk.HTML('This is a <b><style bg="ansired">Toolbar</style></b>!')


class Autocomplete(ptk.completion.Completer):

    def __init__(self, session: engine.Session,*args, **kwargs):
        self.engine = session
        super().__init__(*args, **kwargs)

    def get_completions(self, document, complete_event):
        full = document.text
        last = document.get_word_before_cursor()
        if not any((full.startswith(com) for com in command_dict.keys())):
            for i in filter(lambda x: x.startswith(full), command_dict.keys()):
                yield ptk.completion.Completion(i, start_position=-len(full))
        elif full.startswith('jump '):
            try:
                for i in ['<','>']+self.engine.getbranches():
                    yield ptk.completion.Completion(i, start_position=-len(last))
            except engine.EngineError:
                return
        elif full.startswith('use '):
            if any((full.rstrip().endswith(rule) for rule in self.engine.getrules().keys())):
                yield ptk.completion.Completion(" ", display=ptk.HTML("<b>Sentence number</b>"))
            else:
                try:
                    for i in filter(lambda x: x.startswith(last), self.engine.getrules()):
                        yield ptk.completion.Completion(i, start_position=-len(last))
                except engine.EngineError:
                    return
        elif full.startswith('plugin switch '):
            trigger_socket_entered = False
            for socket in self.engine.get_socket_names():
                if full.rstrip().endswith(socket):
                    trigger_socket_entered = True
                    break
            if trigger_socket_entered:
                for i in filter(lambda x: x.startswith(last), self.engine.plug_list(socket)):
                    yield ptk.completion.Completion(i, start_position=-len(last))
            else:
                for i in filter(lambda x: x.startswith(last), self.engine.get_socket_names()):
                    yield ptk.completion.Completion(i, start_position=-len(last))
        elif full.startswith('prove '):
            pass

# run

def run() -> int:
    """
    Should be used similarly to `if __name__=="__main__"`. Function is ran by the program to generate a working UI.
    A `main.Session` object should be created for every user. To interact with the app engine use it's methods.

    Returns:
        int: Exit code; -1 will restart the app
    """
    session = engine.Session('main', 'config.json')
    ptk.print_formatted_text(ptk.HTML('<b>Logika -> Psychika</b>\nType ? to get command list; type [command]? to get help'))
    console = ptk.PromptSession(message=lambda: f"{session.branch+bool(session.branch)*' '}# ", rprompt=lambda: get_rprompt(
        session), complete_in_thread=True, complete_while_typing=True, completer=Autocomplete(session))
    while True:
        command = console.prompt()
        logger.info(f"Got a command: {command}")
        if command in (' '*n for n in range(100)):
            logger.debug("Command empty")
            continue
        try:
            to_perform = parser(command, command_dict)
        except ParsingError as e:
            ptk.print_formatted_text(e)
            logger.debug(f"ParingError: {e}")
            continue
        except TypeError as e:
            ptk.print_formatted_text(f"błąd: złe argumenty")
            logger.debug(f"Exception caught: {e}")
            continue

        for procedure in to_perform:
            ptk.print_formatted_text(performer(procedure, session))
