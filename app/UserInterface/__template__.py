SOCKET = 'UserInterface'
VERSION = '0.0.1'

import importlib
import os
import sys

# main.py import
# pls help im trapped in __import__'s documentation and i don't understand anything
spec = importlib.util.spec_from_file_location('engine', os.path.abspath('app/engine.py'))
engine = importlib.util.module_from_spec(spec)
sys.modules['engine'] = engine
spec.loader.exec_module(engine)
del spec

def run() -> int:
    """
    Should be used similarly to `if __name__=="__main__"`. Function is ran by the program to generate a working UI.
    A `main.Session` object should be created for every user. To interact with the app engine use it's methods.

    Returns:
        int: Exit code; -1 will restart the app
    """
    pass