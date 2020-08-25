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

    def __init__(self, socket_name: str, directory: str,  functions: tp.Dict[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]], plugin: Module = None):
        self.name = socket_name
        self.functions = functions
        self.func_names = functions.keys()
        self.dir = directory
        self.plugin = None

    def plug(self, module_name: str) -> None:
        # TODO: napisać to xD
        pass

    def fits(self, plugin: Module) -> bool:
        set_names = set(self.func_names)
        set_plugin = set(dir(plugin))
        if set_names.issubset(set_plugin):
            raise LackOfFunctionsError(
                self, plugin.__name__, set_names-set_plugin)
        for i in inspect.getmembers(plugin):
            self._functionfit(i[1])
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
            raise FunctionInterfaceError(False, self, func, sig.return_annotation)
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
        info = f"{module_name} can't be connected to {socket.name}, because it lacks {len(functions)} function{'s'*len(functions)>1}"
        self.lacking = [
            f"{i}: {', '.join(socket.functions[i][0])} -> {socket.functions[i][1]}" for i in functions]
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
