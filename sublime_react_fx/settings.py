import os
import shutil

import sublime

PACKAGE_NAME = "SublimeReactFx"
SETTINGS_NAME = f"{PACKAGE_NAME}.sublime-settings"


def plugin_loaded():
    return
    user_settings_path = os.path.join(
        sublime.packages_path(),
        "User",
        SETTINGS_NAME)

    if not os.path.exists(user_settings_path):
        default_settings_path = os.path.join(
            sublime.packages_path(),
            PACKAGE_NAME,
            SETTINGS_NAME)

        shutil.copyfile(default_settings_path, user_settings_path)


def get_plugin_settings():
    plugin_settings = sublime.load_settings(SETTINGS_NAME)
    return plugin_settings
