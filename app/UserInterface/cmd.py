import logging
import os
import sys
import typing as tp
from math import log10
from collections import OrderedDict
from xml.sax.saxutils import escape

import prompt_toolkit as ptk

import engine

SOCKET = 'UserInterface'
VERSION = '0.0.1'


# Logging config

logging.basicConfig(filename='log.log', level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logger = logging.getLogger('interface')


def UIlogged(func, *args, **kwargs):
    def new(*args, **kwargs):
        logger.debug(
            f"{func.__name__} with args={str(args)} and kwargs={str(kwargs)}")
        return func(*args, **kwargs)
    return new


# Command parsing execution

class ParsingError(Exception):
    pass


@UIlogged
def parser(statement: str, _dict: dict) -> list:  # Add ?/help handling
    comm = []
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
                    (f"Help for '{name}':", func['add_docs'], func['comm'].__doc__))
            else:
                doc = func['add_docs']
            comm.append({'func': func['comm'], 'docs': doc})
            continue

        # Argument conversion
        if func['args'] == 'multiple_strings':
            # mechanism for prove
            converted = command[len(name):].strip()
            if len(converted)==0:
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

        comm.append({'func': func['comm'], 'args': converted})
    return comm


@UIlogged
def performer(command: tp.Dict[str, tp.Any], session: engine.Session) -> str:
    if 'docs' in command.keys():
        return command['docs']
    else:
        if isinstance(command['args'], str):
            return command['func'](session, command['args'])
        else:
            return command['func'](session, *command['args'])


# Commands

def do_clear(session) -> str:
    """Clears the screen, useful when dealing with graphical bugs"""
    ptk.shortcuts.clear()
    return ""


def do_exit(session: engine.Session):
    """Exits the app"""
    logger.info("Exiting the app")
    sys.exit(0)


def do_plug_switch(session: engine.Session, socket_or_name: str, new: str) -> str:
    """Allows to plug in a script to a socket"""
    try:
        session.plug_switch(socket_or_name, new)
    except BaseException as e:  # TODO: Sprawdzić wyjątki i zrobić to ładniej
        logger.error(f"Exception caught: {e}")
        return f"błąd: {e}"
    else:
        return f"Plugin succesfully installed: {new}"


def do_plug_list(session: engine.Session, socket: str) -> str:
    """Lists all the plugins that can be connected to a socket"""
    plugins = "; ".join(session.plug_list(socket))
    return f"Plugins available locally for {socket}:\n{plugins}"


def do_plug_list_all(session: engine.Session) -> str:
    """Lists all the plugins that can be connected to a socket"""
    strings = []
    for i in session.get_socket_names():
        plugins = "; ".join(session.plug_list(i))
        strings.append(f"Plugins available locally for {i}:\n{plugins}")
    return "\n\n".join(strings)


def do_plug_gen(session: engine.Session, socket_or_name: str, name: str) -> str:
    try:
        session.plug_gen(socket_or_name, name)
    except BaseException as e:  # TODO: Sprawdzić wyjątki i zrobić to ładniej
        logger.error(f"Exception caught: {e}")
        return f"błąd: {e}"
    else:
        return f"Generated plugin {name} from template"


def do_prove(session: engine.Session, sentence: str) -> str:
    if session.proof:
        return "A proof would be deleted"
    try:
        session.new_proof(sentence)
    except ValueError:
        return "Wrong syntax"
    except engine.EngineError as e:
        return str(e)
    else:
        return session.proof.getroot()

def do_leave(session) -> str:
    session.proof = None
    session.branch = None
    return "Proof was deleted"


# command_dict powinien być posortowany od najdłuższej do najkrótszej komendy, jeśli jedna jest rozwinięciem drugiej
command_dict = OrderedDict({
    # Program interaction
    'plugin switch': {'comm': do_plug_switch, 'args': [str, str], 'add_docs': ''},
    'plugin list all': {'comm': do_plug_list_all, 'args': [], 'add_docs': ''},
    'plugin list': {'comm': do_plug_list, 'args': [str], 'add_docs': ''},
    'plugin gen': {'comm': do_plug_gen, 'args': [str, str], 'add_docs': ''},
    'clear': {'comm': do_clear, 'args': [], 'add_docs': ''},
    # Navigation
    'exit': {'comm': do_exit, 'args': [], 'add_docs': ''},
    'leave': {'comm': do_leave, 'args': [], 'add_docs': ''},  # Porzuca nieskończony dowód
    'prove': {'comm': do_prove, 'args': 'multiple_strings', 'add_docs': ''},
    'get always': {},
    'get branch': {},
    'get tree': {},
    'jump': {},
    'next': {},  # Nie wymaga argumentu, przenosi po prostu do kolejnej niezamkniętej gałęzi
    # Proof manipulation
    'save': {},  # Czy zrobić oddzielne save i write? save serializowałoby tylko do wczytania, a write drukowałoby input
    'auto always': {},
    'auto': {},
    'use': {},
})


def do_help(session) -> str:
    """Lists all possible commands"""
    return "\n".join(command_dict.keys())


command_dict['?'] = {'comm': do_help, 'args': [], 'add_docs': ''}


# Front-end setup

def get_rprompt(session):
    DEF_PROMPT = "Miejsce na twój dowód".split()

    # Proof retrieval
    if session.proof:
        prompt = session.getbranch()
    else:
        prompt = DEF_PROMPT

    # Formatting
    to_show = []
    max_len = max((len(i) for i in prompt))+1
    for i in range(len(prompt)):
        spaces = max_len-len(prompt[i])-int(log10(i+1))
        to_show.append("".join((str(i+1), ". ", prompt[i], " "*spaces)))
    new = " \n ".join(to_show)
    
    return ptk.HTML(f'\n<style fg="#000000" bg="#00ff00"> {escape(new)} </style>')


def get_toolbar():
    return ptk.HTML('This is a <b><style bg="ansired">Toolbar</style></b>!')


# run

def run() -> int:
    """
    Should be used similarly to `if __name__=="__main__"`. Function is ran by the program to generate a working UI.
    A `main.Session` object should be created for every user. To interact with the app engine use it's methods.

    Returns:
        int: Exit code; -1 will restart the app
    """
    session = engine.Session('config.json')
    ptk.print_formatted_text(ptk.HTML('<b>Logika -> Psychika</b>'))
    console = ptk.PromptSession(
        "~ ", rprompt=lambda: get_rprompt(session), bottom_toolbar=get_toolbar)
    while True:
        command = console.prompt()
        logger.info(f"Got a command: {command}")
        if command in (' '*n for n in range(100)):
            logger.debug("Command empty")
            continue
        try:
            to_perform = parser(command, command_dict)
        except ParsingError as e:  # TODO: dopisać sensowny handling
            ptk.print_formatted_text(f"błąd: {e}")
            logger.debug(f"Exception caught: {e}")
            continue
        except TypeError as e:
            ptk.print_formatted_text(f"błąd: złe argumenty")
            logger.debug(f"Exception caught: {e}")
            continue

        for procedure in to_perform:
            ptk.print_formatted_text(performer(procedure, session))
