from .react_drill_props import SublimeReactFxReactDrillPropsCommand
from .rename_file import SublimeReactFxRenameFileCommand
from .run_package_json import SublimeReactFxRunPackageJsonCommand
from .settings import plugin_loaded

__all__ = [
    'SublimeReactFxReactDrillPropsCommand',
    'SublimeReactFxRenameFileCommand',
    'SublimeReactFxRunPackageJsonCommand',
    'plugin_loaded',
]

# import os
# import importlib
# __globals = globals()
# def _init():
#     global __globals
#     for file in os.listdir(os.path.dirname(__file__)):
#         mod_name, ext = os.path.splitext(file)   # strip .py at the end
#         if ext != '.py' or mod_name == '__init__':
#             continue
#         __globals[mod_name] = importlib.import_module('.' + mod_name, package=__name__)
#         module = __globals[mod_name]
#         importlib.reload(module)
#         for mod in dir(module):
#             if not (mod.upper().endswith('COMMAND') or mod.upper().endswith('EVENT')):
#                 continue
#             __globals[mod] = getattr(module, mod)
# _init()
