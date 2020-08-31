import json
import logging as log
import os
import typing as tp

import pop_engine as pop
import logging

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


def logged(parameter_list):
    pass


class Session(object):
    ENGINE_VERSION = '0.0.1'

    def __init__(self, config_file: str):
        self.config_name = config_file
        self.read_config()
        self.iu_socket = self.config['chosen_plugins']['UserInterface']
        self.sockets = {

        }

    # Plugin manpiulation

    @EngineChangeLog
    def plug_switch(self, socket_or_old: str, new: str):
        if socket_or_old == 'UserInterface' or socket_or_old == config['chosen_plugins']['UserInterface']:
            socket_name = 'UserInterface'
        else:
            if socket_or_old in self.sockets.keys():
                pass
        self.config['chosen_plugins'][socket_name] = new
        self.write_config()

    # config reading and writing

    def read_config(self):
        logger.debug("Config loading")
        with open(self.config_name, 'r') as target:
            self.config = json.load(target)

    def write_config(self):
        logger.debug("Config writing")
        with open(self.config_name, 'w') as target:
            json.dump(self.config, target)
