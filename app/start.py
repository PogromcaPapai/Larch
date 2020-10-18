import json
import os
import sys

import pop_engine as pop

#             Import schema
#
#   pop_engine (imported by everything)
#           /       |      \
#    start.py<-UI plugin<-engine.py
#                    \-----/
#                  not possible
#
# I don't think UI plugin can be connected to engine.py, hence this file.
# Due to the dependency graph (Import schema) engine.py can't import UI plugins.
# Maybe there will be a DummySocket, which allows other operations, but doesn't import the package.
# For now just do what you can to avoid this.

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Log clearing
    if os.path.exists('log.log'):
        os.remove('log.log')

    # UserInterface socket generation
    UI = pop.Socket('UserInterface', os.path.abspath(
        'UserInterface'), '0.0.1', '__template__')

    # return exit code -1 to initiate a restart (useful for UI plugin switching)
    exit_code = -1  # Not implemented in cmd plugin
    while exit_code == -1:

        # App run
        with open('config.json', 'r') as file:
            config = json.load(file)
        UI.plug(config['chosen_plugins']['UserInterface'])
        exit_code = UI().run()
    sys.exit(exit_code)
