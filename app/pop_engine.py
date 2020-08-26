import importlib, importlib.util
import inspect
import typing as tp
import os

Module = type(tp)


def gen_functionDS(func_name: str, returns: tp.Any, *args: tp.Any) -> tp.Tuple[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]]:
    return (func_name, (args, returns))

####
# Socket Interface
####


class Socket(object):

    # Magic

    def __init__(self, socket_name: str, abs_path: str, version: str, functions: tp.Dict[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]]):
        if abs_path != "<> test <>":
            assert os.path.isabs(abs_path), "Path not absolute"
            if not os.path.exists(abs_path):
                os.mkdir(abs_path)
        self.dir = abs_path
        self.name = socket_name
        self.functions = functions
        self.func_names = functions.keys()
        self.plugin = None
        self.version = version

    def __call__(self):
        if self.plug:
            return self.plugin
        else:
            raise PluginError("Nothing is plugged in")

    # Plugin manipulation

    def generate_template(self, plugin_name: str) -> None:
        pass

    def find_plugins(self) -> tp.List[str]:
        return [file[:-3] for file in os.listdir(self.dir) if (file.endswith(".py") and file != "__init__.py")]

    def unplug(self) -> None:
        self.plug = None

    def plug(self, plugin_name: str) -> None:
        assert self.dir!="<> test <>"
        if plugin_name.endswith(".py"):
            plugin_name = plugin_name[:-3]
        if not plugin_name in self.find_plugins():
            raise FileNotFoundError(f"{plugin_name} doesn't exist in {self.dir}")
        plug_obj = self._import(plugin_name)

        if plug_obj.SOCKET != self.name:
            raise PluginError(f"{plug_obj.__name__} is meant to be plugged into {plug_obj.SOCKET}, not {self.name}")
        self.fits(plug_obj)
        self.check_verion(plug_obj)
        
        self.plugin = plug_obj


    def _import(self, name: str) -> Module:
        spec = importlib.util.spec_from_file_location(name, f"{self.dir}/{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

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
