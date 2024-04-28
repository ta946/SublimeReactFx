import json
import os
import subprocess

import sublime
import sublime_plugin

from .utils import find_package_json


class SublimeReactFxRunPackageJsonCommand(sublime_plugin.WindowCommand):
    @staticmethod
    def _check_folder_is_ancestor(folder, path):
        try:
            ret = os.path.commonpath([folder, os.path.realpath(path)]) == os.path.normpath(folder)
        except ValueError:
            ret = False
        return ret

    @staticmethod
    def _get_package_json_scripts(path):
        with open(path, 'r') as f:
            package_json = json.load(f)
        scripts = package_json.get('scripts', {})
        return scripts

    @staticmethod
    def _run_script(cmd, directory=None):
        cmd = ["cmd", "/k"] + cmd
        print(' '.join(cmd))
        subprocess.Popen(cmd, shell=False, cwd=directory, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _get_and_run_package_json_script(self, path):
        if not os.path.exists(path):
            return
        scripts_dict = self._get_package_json_scripts(path)
        if not scripts_dict:
            return
        self._scripts_list = list(scripts_dict.items())
        self._directory = os.path.dirname(path)
        self.window.show_quick_panel(self._scripts_list, self._on_select)

    def _on_select(self, idx):
        if idx == -1:
            return
        alias, command = self._scripts_list[idx]
        cmd = ['npm', 'run', alias]
        self._run_script(cmd, directory=self._directory)

    def run(self):
        file_name = self.window.active_view().file_name()
        folders = self.window.folders()

        if file_name:
            folder = os.path.dirname(file_name)
            path = os.path.join(folder, 'package.json')
            if os.path.exists(path):
                self._get_and_run_package_json_script(path)
                return

            if folders:
                for folder in folders:
                    ret = self._check_folder_is_ancestor(folder, file_name)
                    if ret:
                        path = os.path.join(folder, 'package.json')
                        if os.path.exists(path):
                            self._get_and_run_package_json_script(path)
                            return
                        break

            folder = os.path.dirname(file_name)
            path = find_package_json(folder)
            if path is not None:
                self._get_and_run_package_json_script(path)
                return

        if folders:
            for folder in folders:
                path = os.path.join(folder, 'package.json')
                if os.path.exists(path):
                    self._get_and_run_package_json_script(path)
                    return
                break
