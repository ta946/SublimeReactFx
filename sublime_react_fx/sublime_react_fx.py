import os
import re

from .utils import (ESM_IMPORT_LOCAL_REGEXC, IMPORT_ITEM_REGEXC,
                    REACT_FUNCTIONAL_COMPONENT_REGEXC, find_js_files,
                    parse_comma_separated, text_replace_span)

REACT_COMPONENT_REGEX_TEMPLATE = r'<<COMPONENT>([\n> ])(\s*)'


class ReactFindComponentImports:
    def __init__(self):
        self._esm_import_local_regexc = ESM_IMPORT_LOCAL_REGEXC
        self._import_item_regexc = IMPORT_ITEM_REGEXC

    def _find_component_import(self, file, rfc_file, name=None):
        folder = os.path.dirname(file)
        rfc_file_name = os.path.basename(rfc_file)
        rfc_file_title = os.path.splitext(rfc_file_name)[0]

        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
        if rfc_file_title not in text:
            return None, None

        matched_import = None
        for m in self._esm_import_local_regexc.finditer(text):
            rel_path = m[2]
            abspath = os.path.realpath(os.path.normpath(os.path.join(folder, rel_path)))
            if os.path.splitext(abspath)[0] == os.path.splitext(rfc_file)[0]:
                matched_import = m
                break
        if not matched_import:
            return None, None

        imports = matched_import.group(1)
        matched_import_items = list(self._import_item_regexc.finditer(imports))
        if name is not None:
            name_found = False
            for m in matched_import_items:
                import_item = m.group(1)
                if import_item == name:
                    name_found = True
            if not name_found:
                return None, None
        return matched_import, matched_import_items

    def _find_files_with_component_import(self, files, rfc_file, name=None):
        imports = []
        rfc_file = os.path.realpath(os.path.normpath(rfc_file))
        for file in files:
            file_real_path = os.path.realpath(os.path.normpath(file))
            if file_real_path == rfc_file:
                continue
            matched_import, matched_import_items = self._find_component_import(file_real_path, rfc_file, name=name)
            if matched_import is None or matched_import_items is None:
                continue
            import_dict = {
                "file": file_real_path,
                "import": matched_import,
                "import_items": matched_import_items,
            }
            imports.append(import_dict)
        return imports

    def run(self, project_dir, rfc_file, name=None):
        files = find_js_files(project_dir)
        if not files:
            return
        imports = self._find_files_with_component_import(files, rfc_file, name=name)
        """
        imports = matched_import.group(1)
        rel_path = matched_import.group(2)
        import_from = matched_import.group(3)
        ext = matched_import.group(4)

        import_statement = m.group(0)
        import_item = m.group(1)
        import_alias = m.group(2)
        """
        return imports


class ReactFileRename:
    def _update_file_import(self, new_file_name, file, matched_import):
        new_text = None
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
        ext_group = matched_import.group(4)
        if not ext_group:
            new_import_text = new_file_name
        else:
            new_import_text = os.path.splitext(new_file_name)[0]
        import_from_span = matched_import.span(3)
        new_text = text_replace_span(text, import_from_span, new_import_text)
        return new_text

    def run(self, project_dir, path, new_file_name):
        imports = ReactFindComponentImports().run(project_dir, path)
        if not imports:
            return "No imports found", None

        change_list = []
        for import_dict in imports:
            file = import_dict['file']
            matched_import = import_dict['import']
            new_text = self._update_file_import(new_file_name, file, matched_import)
            if new_text:
                change_dict = {
                    "file": file,
                    "new_text": new_text,
                }
                change_list.append(change_dict)
        return None, change_list


class ReactFunctionalComponentPropsUpdate:
    def __init__(self):
        self._react_func_comp_regexc = REACT_FUNCTIONAL_COMPONENT_REGEXC

    @staticmethod
    def _validate(text, props, pos):
        if not text:
            return "text cannot be empty"
        if not props:
            return "props cannot be empty"
        if pos < 0 or pos >= len(text):
            return "pos must be inside text"

    def _find_react_func_comp_at_pos(self, text, pos):
        matched = None
        for m in self._react_func_comp_regexc.finditer(text):
            span = m.span()
            if span[0] <= pos <= span[1]:
                matched = m
                break
        return matched

    @staticmethod
    def _check_react_func_comp_props_non_deconstructed(rfc_props):
        ret = rfc_props and rfc_props[0] != "{" and rfc_props[-1] != "}"
        return ret

    @staticmethod
    def _get_props_to_add(props_list, rfc_props):
        if not rfc_props:
            props_list_curr = []
            props_list_to_add = props_list
        else:
            props_list_curr = parse_comma_separated(rfc_props[1:-1])
            props_list_to_add = [prop for prop in props_list if prop not in props_list_curr]
        return props_list_to_add, props_list_curr

    @staticmethod
    def _form_props_text(props_list):
        if len(props_list) == 1:
            new_props_text = "{ %s }" % props_list[0]
        else:
            new_props_text = "{\n  %s,\n}" % ',\n  '.join(props_list)
        return new_props_text

    def run(self, text, props, pos):
        err = self._validate(text, props, pos)
        if err:
            return err, None

        matched = self._find_react_func_comp_at_pos(text, pos)
        if not matched:
            return "No React functional component found at pos", None

        rfc_name = matched[2]
        rfc_props = matched[3]
        rfc_props_span = matched.span(3)

        ret = self._check_react_func_comp_props_non_deconstructed(rfc_props)
        if ret:
            return "React functional component contains non-deconstructed props", None

        props_list = parse_comma_separated(props)
        props_list_to_add, props_list_curr = self._get_props_to_add(props_list, rfc_props)
        if not props_list_to_add:
            return "Props already exist", None

        props_list_new = props_list_curr + props_list_to_add

        new_props_text = self._form_props_text(props_list_new)

        new_text = text_replace_span(text, rfc_props_span, new_props_text)
        output = {
            "text": new_text,
            "name": rfc_name,
            "props_to_add": props_list_to_add,
        }
        return None, output


class ReactCompontentPassProps:
    def __init__(self):
        self._react_component_regex_template = REACT_COMPONENT_REGEX_TEMPLATE

    @staticmethod
    def _validate(text, props, rfc_name):
        if not text:
            return "text cannot be empty"
        if not props:
            return "props cannot be empty"
        if not rfc_name:
            return "rfc_name cannot be empty"
        return

    def run(self, text, props, rfc_name, alias=None):
        err = self._validate(text, props, rfc_name)
        if err:
            return err, None
        new_text = text
        name = alias or rfc_name
        react_component_regex = self._react_component_regex_template.replace('<COMPONENT>', name)
        span = None
        for m in reversed(list(re.finditer(react_component_regex, new_text))):
            after_name = m.group(1)
            if after_name == '\n':
                newline_spaces = m.group(2)
                prefix = f'\n{newline_spaces}'
            else:
                prefix = " "
            props_text = ""
            for prop in props:
                prop_text = "%s%s={%s}" % (prefix, prop, prop)
                props_text = f'{props_text}{prop_text}'
            after_name_span = m.span(1)
            span = (after_name_span[0], after_name_span[0])
            new_text = text_replace_span(new_text, span, props_text)
        return None, new_text, span
