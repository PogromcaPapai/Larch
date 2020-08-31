SOCKET = 'UserInterface'
VERSION = '0.0.1'

import importlib
import os
import sys
import prompt_toolkit as ptk
import typing as tp
from math import log10

import engine

# Command parsing

# command_dict powinien być posortowany od najdłuższej do najkrótszej komendy
command_dict = {
    'clear' : {'comm':ptk.shortcuts.clear, 'args':[], 'add_docs':''}
}

class ParsingError(Exception):
    pass

def parser(statement: str, _dict: dict = command_dict) -> list: # Add ?/help handling
    comm = []
    for command in statement.split(';'):
        # Function parsing
        func = None
        for i in _dict.items():
            if command.startswith(i[0]):
                func = i[1]
                name = i[0]
                break
        if func==None:
            raise ParsingError("Command not found")
        args = command[len(name):].split()
        
        # Argument conversion
        if len(args)>len(func['args']):
            raise ParsingError("Too many arguments")
        elif len(args)<len(func['args']):
            raise ParsingError("More arguments needed")
        converted = []
        for form, val in zip(func['args'], args):
            try:
                new = form(val)
            except ValueError:
                raise TypeError("Wrong argument type")
            converted.append(new)
        
        # Documentation generating and yielding
        if func['comm'].__doc__:
            doc = "\n".join((func['add_docs'], func['comm'].__doc__))
        else:
            doc = func['add_docs']
        comm.append({'func':func['comm'],'args':converted,'docs':doc})
    return comm
    


# Front-end setup

def get_rprompt():
    prompt = 'tutaj\nbędzie\nwyświetlał\nsię dowód\narka\ngdynia\ndodana\nkolejna\nlinia\nmusi\nwyjść\nwięcej\nod\n10'.split('\n')*2
    
    
    max_len = max((len(i) for i in prompt))+1
    for i in range(len(prompt)):
        spaces = max_len-len(prompt[i])-int(log10(i+1))
        prompt[i] = "".join((str(i+1), ". ", prompt[i], " "*spaces))
    new = " \n ".join(prompt)
    return ptk.HTML(f'\n<style fg="#000000" bg="#00ff00"> {new} </style>')

def get_toolbar():
    return ptk.HTML('This is a <b><style bg="ansired">Toolbar</style></b>!')

def run() -> int:
    """
    Should be used similarly to `if __name__=="__main__"`. Function is ran by the program to generate a working UI.
    A `main.Session` object should be created for every user. To interact with the app engine use it's methods.

    Returns:
        int: Exit code; -1 will restart the app
    """
    session = engine.Session('config.json')
    ptk.print_formatted_text(ptk.HTML('<b>Logika -> Psychika</b>'))
    console = ptk.PromptSession("~ ", rprompt=get_rprompt, bottom_toolbar=get_toolbar)
    while True:
        command = console.prompt()
        if command in (' '*n for n in range(100)):
            continue
        try:
            to_perform = parser(command)
        except ParsingError as e: #TODO: dopisać sensowny handling
            ptk.print_formatted_text(f"błąd: {e}")
            continue
        except TypeError:
            ptk.print_formatted_text(f"błąd: złe argumenty")
            continue

        for procedure in to_perform:
            procedure['func'](*procedure['args'])