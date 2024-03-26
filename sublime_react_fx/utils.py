import os
import re
from glob import glob

JS_GLOB = "**/*.js"
JSX_GLOB = "**/*.jsx"
ESM_IMPORT_LOCAL_REGEXC = re.compile(
    r'import\s+([\w{},\s*]+)\s+from\s+[\'"](\.{1,2}\/(?:(?:\.{2}|\w+)\/)*(\w+)(\.\w*)?)[\'"]')
IMPORT_ITEM_REGEXC = re.compile(r'(\w+)(?:\s*as\s*(\w+))?')
REACT_FUNCTIONAL_COMPONENT_REGEXC = re.compile(r'\b(export\s+(?:default\s+)?function\s+([A-Z]\w*)\(([\w\s,{}]*?)\)\s*{)')


def js_command_is_visible(view):
    syntax = view.syntax()
    if not syntax:
        return False
    if syntax.scope not in ("source.jsx", "source.js"):
        return False
    return True


def find_package_json(folder):
    folder_prev = None
    while True:
        path = os.path.join(folder, 'package.json')
        if os.path.exists(path):
            return path
        folder = os.path.dirname(folder)
        if folder == folder_prev:
            return
        folder_prev = folder


def find_js_files(folder):
    jsx_files = glob(os.path.join(folder, JSX_GLOB), recursive=True)
    js_files = glob(os.path.join(folder, JS_GLOB), recursive=True)
    files = jsx_files + js_files
    files = [file for file in files if "node_modules" not in file.split(os.sep)]
    return files


def parse_comma_separated(text):
    lst = []
    for s in text.split(','):
        txt = s.strip()
        if txt:
            lst.append(txt)
    return lst


def text_replace_span(text, span, new):
    new_text = f'{text[:span[0]]}{new}{text[span[1]:]}'
    return new_text
