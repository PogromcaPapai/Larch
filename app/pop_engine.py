import importlib
import inspect
import typing as tp

Module = type(tp)


def gen_functionDS(func_name: str, returns: tp.Any, *args: tp.Any) -> tp.Tuple[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]]:
    return (func_name, (args, returns))

####
# Socket Interface
####


class Socket(object):

    # Magic

    def __init__(self, socket_name: str, directory: str, version: str, functions: tp.Dict[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]]):
        self.name = socket_name
        self.functions = functions
        self.func_names = functions.keys()
        self.dir = directory
        self.plug = None
        self.version = version

    def __call__(self):
        if self.plug:
            return self.plugin
        else:
            raise PluginError("Nothing is plugged in")

    # Plugin manipulation

    def generate_template(self, plugin_name: str) -> None:
        pass

    def discover(self) -> tp.List[str]:
        pass

    def unplug(self) -> None:
        self.plug = None

    def plug(self, module_name: str) -> None:
        # TODO: napisać to xD
        self.discover()

    # Verification

    def check_verion(self, plugin: Module) -> bool:
        # TODO: Czy dodawać częściową kompatybilność?
        if self.version == plugin.VERSION:
            return True
        else:
            raise PluginError(
                f"Wrong version - Socket: {self.version}; Plugin: {plugin.VERSION}")

    def fits(self, plugin: Module) -> bool:
        set_names = set(self.func_names)
        set_plugin = set(dir(plugin))
        if not set_names.issubset(set_plugin):
            raise LackOfFunctionsError(
                self, plugin.__name__, set_names-set_plugin)
        members = dict(inspect.getmembers(plugin))
        for i in set_names:
            self._functionfit(members[i])
        return True

    def _functionfit(self, func: tp.Callable) -> bool:
        if self.functions.get(func.__name__, None) == None:
            return True
        sig = inspect.signature(func)
        args = tuple(
            [sig.parameters[j].annotation for j in sig.parameters.keys()])
        proper = self.functions[func.__name__]
        if args != proper[0]:
            raise FunctionInterfaceError(True, self, func, args)
        elif sig.return_annotation != proper[1]:
            raise FunctionInterfaceError(
                False, self, func, sig.return_annotation)
        else:
            return True

####
# Exceptions
####


class PluginError(Exception):
    """Mother of exceptions used to deal with plugin problems"""


class LackOfFunctionsError(PluginError):
    """Raised if module lacks important functions"""

    def __init__(self, socket: Socket, module_name: str, functions: tp.List[str]):
        info = f"{module_name} can't be connected to {socket.name}, because it lacks {len(functions)} function{'s'*(len(functions)>1)}"
        self.lacking = [
            f"{i}: {', '.join(str(socket.functions[i][0]))} -> {str(socket.functions[i][1])}" for i in functions]
        super().__init__(info)


class FunctionInterfaceError(PluginError):
    """Raised if function has a bad interface"""

    def __init__(self, argument_problem: bool, socket: Socket, func: tp.Callable, what_is: tp.Any):
        if argument_problem:
            info = f"{func.__name__} can't be connected to {socket.name}; " + \
                f"Arguments are: {str(what_is)}, should be: {str(socket.functions[func.__name__][0])}"
        else:
            info = f"{func.__name__} can't be connected to {socket.name}; " + \
                f"Return is: {str(what_is)}, should be: {str(socket.functions[func.__name__][1])}"
        super().__init__(info)
