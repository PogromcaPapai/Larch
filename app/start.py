import os
import json
import sys

import pop_engine as pop

if __name__ == "__main__":
    UI = pop.Socket('UserInterface', os.path.abspath('UserInterface'), '0.0.1', '__template__')

    exit_code = -1
    while exit_code==-1:
        with open('config.json', 'r') as file:
            config = json.load(file)
        UI.plug(config['chosen_plugins']['UserInterface'])
        exit_code = UI().run()
        input()