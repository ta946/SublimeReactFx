import os

import sublime
import sublime_plugin

from .sublime_react_fx import (ReactCompontentPassProps,
                               ReactFindComponentImports,
                               ReactFunctionalComponentPropsUpdate)
from .utils import (REACT_FUNCTIONAL_COMPONENT_REGEXC, find_package_json,
                    js_command_is_visible)


class SublimeReactFxReactDrillPropsCommand(sublime_plugin.TextCommand):
    def is_visible(self, **kwargs):
        ret = js_command_is_visible(self.view)
        return ret

    @staticmethod
    def _do_nothing(args, **kwargs):
        pass

    @staticmethod
    def _error(err):
        sublime.error_message(f"SublimeReactFxReactDrillPropsCommand Error!\n{err}")

    def run(self, edit):
        self.view.window().show_input_panel('props', '', self._on_done, self._do_nothing, self._do_nothing)

    def _on_done(self, props):
        props = props.strip().strip('"').strip("'")
        if not props:
            return

        sel = self.view.sel()
        if len(sel) != 1:
            sublime.error_message("SublimeReactFxReactDrillPropsCommand Error!\nOnly 1 selection is allowed")
            return

        pos = sel[0].begin()
        path = self.view.file_name()
        self._drill_props(path, props, pos)

    @staticmethod
    def _find_react_func_comp(text, pos_curr):
        pos = None
        for m in REACT_FUNCTIONAL_COMPONENT_REGEXC.finditer(text):
            p = m.span(2)[0]
            if p > pos_curr:
                continue
            if pos is None or p > pos:
                pos = p
        return pos

    def _drill_props(self, path, props, pos, parents=""):
        with open(path, 'r') as f:
            text = f.read()

        err, props_update_output = ReactFunctionalComponentPropsUpdate().run(text, props, pos)
        if err:
            self._error(err)
            return

        rfc_name = props_update_output['name']
        props_to_add = props_update_output['props_to_add']

        folder = os.path.dirname(path)
        package_json_path = find_package_json(folder)
        if not package_json_path:
            self._error("No package.json found")
            return
        package_json_dir = os.path.dirname(package_json_path)

        if not parents:
            rel_path = os.path.relpath(path, package_json_dir)
            parents = rel_path

        new_text = props_update_output['text']
        with open(path, 'w') as f:
            f.write(new_text)

        imports = ReactFindComponentImports().run(package_json_dir, path, rfc_name)
        if not imports:
            self._error("No imports found")
            return

        for import_dict in imports:
            file = import_dict["file"]
            rel_path = os.path.relpath(file, package_json_dir)
            parents_chain = f"{parents}\n{rel_path}"
            ret = sublime.ok_cancel_dialog(f"Drill prop to\n{parents_chain}?")
            if not ret:
                continue
            matched_import_items = import_dict["import_items"]
            alias = None
            for import_item in matched_import_items:
                name = import_item.group(1)
                if name != rfc_name:
                    continue
                alias = import_item.group(2)
            with open(file, 'r') as f:
                text = f.read()
            err, new_text, span = ReactCompontentPassProps().run(text, props_to_add, rfc_name, alias)
            if err:
                self._error(err)
                return

            self.view.window().open_file(file)
            with open(file, 'w') as f:
                f.write(new_text)

            matched_import_items = import_dict["import_items"]
            pos = self._find_react_func_comp(new_text, span[0])
            if not pos:
                continue

            self._drill_props(file, props, pos, parents=parents_chain)
