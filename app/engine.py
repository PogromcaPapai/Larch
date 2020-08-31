import json
import logging as log
import os
import typing as tp

import pop_engine as pop


class Session(object):
    ENGINE_VERSION = '0.0.1'

    def __init__(self, config_file: str):
        self.config_name = config_file
        self.read_config()
        self.iu_socket = self.config['chosen_plugins']['UserInterface']
        self.sockets = {
            
        }

    # Plugin manpiulation

    def plug_switch(self, socket_or_old: str, new: str):
        if socket_or_old=='UserInterface' or socket_or_old==config['chosen_plugins']['UserInterface']:
            socket_name = 'UserInterface'
        else:
            if socket_or_old in self.sockets.keys():
                pass
        self.config['chosen_plugins'][socket_name] = new
        self.write_config()

    

    # config reading and writing

    def read_config(self):
        with open(self.config_name, 'r') as target:
            self.config = json.load(target)

    def write_config(self):
        with open(self.config_name, 'w') as target:
            json.dump(self.config, target)
