import os
import re
from glob import glob

import sublime
import sublime_plugin

from .sublime_react_fx import ReactFileRename
from .utils import find_package_json, js_command_is_visible, text_replace_span

JS_GLOB = "**/*.js"
JSX_GLOB = "**/*.jsx"
# ESM_IMPORT_REGEX_TEMPLATE = r'import\s+([\w{},\s*]+)\s+from\s+[\'"](\.{1,2}\/(?:(?:\.{2}|\w+)\/)*(<FILENAME>)(\.\w*)?)[\'"]'
ESM_IMPORT_LOCAL_REGEX = r'import\s+([\w{},\s*]+)\s+from\s+[\'"](\.{1,2}\/(?:(?:\.{2}|\w+)\/)*(\w+)(\.\w*)?)[\'"]'
ESM_IMPORT_LOCAL_REGEXC = re.compile(ESM_IMPORT_LOCAL_REGEX)


class SublimeReactFxRenameFileCommand(sublime_plugin.WindowCommand):
    def is_visible(self, **kwargs):
        view = self.window.active_view()
        ret = js_command_is_visible(view)
        return ret

    def input(self, args=None):
        path = self.window.active_view().file_name()
        if not path:
            return
        self._path = os.path.realpath(path)
        file_name = os.path.basename(self._path)
        return FileNameInputHandler(file_name)

    def run(self, file_name=None):
        if not file_name:
            return

        folder = os.path.dirname(self._path)
        package_json_path = find_package_json(folder)
        if package_json_path is None:
            sublime.error_message(f"SublimeReactFxRenameFileCommand Error!\nNo package.json found")
            return
        package_json_dir = os.path.dirname(package_json_path)

        err, change_list = ReactFileRename().run(package_json_dir, self._path, file_name)
        if err:
            sublime.error_message(f"SublimeReactFxRenameFileCommand Error!\n{err}")

        changed = []
        for change_dict in change_list:
            file = change_dict["file"]
            new_text = change_dict["new_text"]
            with open(file, 'w') as f:
                f.write(new_text)
            changed.append(file)
        self.window.run_command("rename_file", args={"new_name": file_name})
        changed_text = "\n".join(changed)
        sublime.message_dialog(f'The following files have updated their imports:\n{changed_text}')


class FileNameInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, file_name):
        super().__init__()
        self._file_name = file_name

    def placeholder(self):
        return self._file_name

    def initial_text(self):
        return self._file_name

    def initial_selection(self):
        if '.' not in self._file_name:
            return
        idx = self._file_name.rindex('.')
        return [(0, idx)]
