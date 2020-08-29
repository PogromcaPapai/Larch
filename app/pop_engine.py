import importlib
import importlib.util
import inspect
import shutil
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

    def __init__(self, socket_name: str, abs_path: str, version: str, template: tp.Union[str, tp.Dict[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]]], plugged: str = ""):
        """Allows the user to smoothly interchange plugins by providing the interface call functions

        Args:
            socket_name (str): Name given to the socket, will be used to identify plugins
            abs_path (str): Absolute path to the directory with plugins; use `<> test <>` for testing
            version (str): Version of the socket, will be checked with sockets. Supported format: "x.x.z", changes on "z level" will be omitted in version checking
            template (str OR tp.Dict[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]]): Used as a reference in interface verification. When supplied with file name system 
                                                                                will use it to generate templates. `gen_functionDS` generates the primitive version.
            plugged (str, optional): Name of a plugin which will be connected. Defaults to "".
        """
        # Plugin's directory
        if abs_path != "<> test <>":
            assert os.path.isabs(abs_path), "Path not absolute"
            if not os.path.exists(abs_path):
                os.mkdir(abs_path)
        self.dir = abs_path

        # Version checking
        self.version = [int(i) for i in version.split('.')]
        assert len(self.version) == 3, "Wrong version format"

        # Misc
        self.name = socket_name
        if isinstance(template, str):
            if template.endswith(".py"):
                template = template[:-3]
            if not os.path.isfile(f"{abs_path}\\{template}.py"):
                raise FileNotFoundError(
                    f"{template}.py doesn't exist in {abs_path}")
            else:
                self.template = template
                self.functions = self._get_functions_from_template(template)
        else:
            self.template = None
            self.functions = template
        self.func_names = self.functions.keys()
        if plugged == "":
            self.plugin = None
        else:
            self.plug(plugged)

    def __call__(self) -> Module:
        """Use this to get access to the plugin

        Raises:
            PluginError: Raised if nothing is plugged in

        Returns:
            Module: Plugged module
        """
        if self.plug:
            return self.plugin
        else:
            raise PluginError("Nothing is plugged in")

    # Plugin manipulation

    def generate_template(self, plugin_name: str) -> None:
        if plugin_name.endswith(".py"):
            plugin_name = plugin_name[:-3]
        if plugin_name in self.find_plugins():
            raise FileExistsError(
                f"{plugin_name} already exists in {self.name}'s directory")
        if self.template:
            shutil.copyfile(f"{self.dir}/{self.template}.py",
                            f"{self.dir}/{plugin_name}.py")
        else:
            raise FileNotFoundError(
                f"There is no template available for {self.name}'s plugins")

    def find_plugins(self) -> tp.List[str]:
        """
        Returns:
            tp.List[str]: List of all plugins in the socket's directory
        """
        return [file[:-3] for file in os.listdir(self.dir) if (file.endswith(".py") and not (file in {self.template, "__init__.py"}))]

    def unplug(self) -> None:
        """Unplugs the current plugin, not recommended"""
        self.plug = None

    def plug(self, plugin_name: str) -> None:
        """Connects the plugin to the socket

        Args:
            plugin_name (str): Name of the plugin

        Raises:
            FileNotFoundError: Raised if module with this name does not exist
            PluginError: Wrong socket
            VersionError: Wrong plugin version
            FunctionInterfaceError: Socket doesn't allow this function interface
            LackOfFunctionsError: Module lacks a function needed to connect to the socket
        """
        # Retrieval
        assert self.dir != "<> test <>"
        if plugin_name.endswith(".py"):
            plugin_name = plugin_name[:-3]
        if not plugin_name in self.find_plugins():
            raise FileNotFoundError(
                f"{plugin_name} doesn't exist in {self.dir}")
        plug_obj = self._import(plugin_name)

        # Verification
        self.check_name(
            plug_obj, f"{plug_obj.__name__} is meant to be plugged into {plug_obj.SOCKET}, not {self.name}")
        self.check_version(
            plug_obj, f'Wrong version - Socket: {".".join((str(i) for i in self.version))}; Plugin: {plug_obj.VERSION}')
        self.fits(plug_obj)

        # Connecting to the system
        self.plugin = plug_obj

    def _import(self, name: str) -> Module:
        """Imports a module of the given name and returns it; USE PLUG INSTEAD"""
        spec = importlib.util.spec_from_file_location(
            name, f"{self.dir}/{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # Verification

    def check_name(self, plugin: Module, message: str) -> bool:
        assert 'SOCKET' in dir(plugin), "No socket name in the plugin"
        if plugin.SOCKET != self.name:
            raise PluginError(message)
        else:
            return True

    def check_version(self, plugin: Module, message: str) -> bool:
        """Checks plugin versions. Supported format: "x.x.z", changes on "z level" will be omitted in version checking

        Raises:
            VersionError: Wrong plugin version
            SyntaxError: Wrong version formatting in the plugin
        """
        assert 'VERSION' in dir(plugin), "No plugin version in the plugin"
        plugin_ver = [int(i) for i in plugin.VERSION.split(".")]
        if len(plugin_ver) != 3:
            raise SyntaxError("Wrong version format used in the plugin")
        if plugin_ver[:-1] == self.version[:-1]:
            return True
        else:
            raise VersionError(message)

    def fits(self, plugin: Module) -> bool:
        """Function checks if module is connectable to the socket

        Args:
            plugin (Module)

        Raises:
            FunctionInterfaceError: Socket doesn't allow this function interface
            LackOfFunctionsError: Module lacks a function needed to connect to the socket
        """
        set_names = set(self.func_names)
        set_plugin = set(dir(plugin))
        if not set_names.issubset(set_plugin):
            raise LackOfFunctionsError(
                self, plugin.__name__, set_names-set_plugin)
        members = dict(inspect.getmembers(plugin, callable))
        for i in set_names:
            self._functionfit(members[i])
        return True

    def _functionfit(self, func: tp.Callable) -> bool:
        """Checks compatibility of the function's interface

        Raises:
            FunctionInterfaceError: Socket doesn't allow this function interface - wrong type of arguments/returned value.
        """
        if self.functions.get(func.__name__, None) == None:
            return True
        sig = inspect.signature(func)
        args = tuple(
            [sig.parameters[j].annotation for j in sig.parameters.keys()])
        proper = self.functions[func.__name__]

        # Argument checking
        if args != proper[0]:
            raise FunctionInterfaceError(True, self, func, args)

        # Return checking
        elif sig.return_annotation != proper[1]:
            raise FunctionInterfaceError(
                False, self, func, sig.return_annotation)
        else:
            return True

    def _get_functions_from_template(self, template_file_name: str) -> tp.Dict[str, tp.Tuple[tp.Tuple[tp.Any], tp.Any]]:
        # Verification
        template = self._import(template_file_name)
        self.check_version(
            template, f"Version of {template.__name__} not compatible with {self.name}")
        self.check_name(
            template, f"{template.__name__} can be a socket of {template.SOCKET}, not {self.name}")

        # Template reading
        funcs = dict()
        for i in inspect.getmembers(template, callable):
            sig = inspect.signature(i[1])
            args = tuple(
                [sig.parameters[j].annotation for j in sig.parameters.keys()])
            funcs[i[0]] = (args, inspect.signature(i[1]).return_annotation)
        return funcs

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


class VersionError(PluginError):
    """Raised if plugin has an incompatible version"""
    pass
