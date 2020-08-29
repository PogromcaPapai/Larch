import pop_engine as pop
import os
import json
import sys

UI = pop.Socket('UserInterface', os.path.abspath('app/UserInterface'), '0.0.1', '__template__')

if __name__ == "__main__":
    exit_code = -1
    while exit_code==-1:
        UI.plug('__template__')
        exit_code = UI().run()
    sys.exit(exit_code)