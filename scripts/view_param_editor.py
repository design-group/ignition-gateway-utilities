#!/usr/bin/env python3
#pylint: disable=invalid-name
"""
DESCRIPTION: This script is used to dump, load, purge, format parameters, or set private access modes for custom properties in view.json files.
Usage: python3 view-params-editor.py [dump] [load] [purge] [format] [--set-private-access-modes] [--help]
"""

import os
import json
import sys
import re
from collections import OrderedDict

# Specify the target folder path and output/input files
TARGET_FOLDER = 'services/projects'
DEV_PARAMS_PATH = 'services/env/dev-view-params.json'

HELP_TEXT = """
Parameter Scripts

Usage: python3 view_param_editor.py [dump] [load] [purge] [format] [--set-private-access-modes] [--help]

Actions:
  dump   - Dump all parameters from view.json files into dev-params.json
		   When the script runs, dev-params.json is loaded and new changes get appended to it
		   dev-params.json should be updated before submitting a pull request

  load   - Load all parameters from dev-params.json into all view.json files in frontend DanPT project
		   This should be done before starting work on a new feature

  purge  - Remove all parameters from all view.json files in frontend DanPT project
		   dump should be run before this action, so that dev-params.json is up-to-date with all the parameters
		   This action should be run before submitting a pull request

  format - Format all JSON files in the target folder, preserving Unicode escapes
		   This ensures consistent formatting across all JSON files

Options:
  --set-private-access-modes - Set access mode to "PRIVATE" for all custom properties in propConfig
  --cleanup-props            - Remove custom properties that only have access: PRIVATE configuration
  --help                     - Display this help message

You can combine multiple actions in a single command, e.g.:
python3 view_param_editor.py dump purge format
"""


def preserve_unicode_escapes(text):
    """Preserve specific Unicode escapes."""
    replacements = {
        r'\\u003c': 'UNICODE_LT',
        r'\\u003e': 'UNICODE_GT',
        r'\\u0026': 'UNICODE_AMP',
        r'\\u003d': 'UNICODE_EQ',
        r'\\u0027': 'UNICODE_APOS'
    }
    for escape, placeholder in replacements.items():
        text = re.sub(escape, placeholder, text)
    return text


def restore_unicode_escapes(text):
    """Restore specific Unicode escapes."""
    replacements = {
        'UNICODE_LT': r'\u003c',
        'UNICODE_GT': r'\u003e',
        'UNICODE_AMP': r'\u0026',
        'UNICODE_EQ': r'\u003d',
        'UNICODE_APOS': r'\u0027'
    }
    for placeholder, escape in replacements.items():
        text = text.replace(placeholder, escape)
    return text


def format_json(obj):
    """Format JSON with 2-space indentation and no trailing whitespace."""
    return json.dumps(obj, indent=2, ensure_ascii=False).rstrip()


def read_json_file(file_path):
    """Read and parse JSON file, preserving Unicode escapes."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        preserved_content = preserve_unicode_escapes(content)
        return json.loads(preserved_content, object_pairs_hook=OrderedDict)


def write_json_file(file_path, data):
    """Write formatted JSON to file, restoring Unicode escapes."""
    formatted_json = format_json(data)
    restored_content = restore_unicode_escapes(formatted_json)
    with open(file_path, 'w', encoding='utf-8', newline='\n') as file:
        file.write(restored_content)


def set_private_access_modes(target_folder):
    """Set access mode to PRIVATE for all custom properties in propConfig."""
    update_count = 0
    custom_prop_count = 0

    for root, _, files in os.walk(target_folder):
        for view in files:
            if view in ('view.json', 'props.json'):
                file_path = os.path.join(root, view)
                print('Processing %s' % file_path)
                view_data = read_json_file(file_path)

                if 'propConfig' in view_data:
                    modified = False
                    for key, value in view_data['propConfig'].items():
                        if key.startswith('custom'):
                            if isinstance(value, dict):
                                # Create new ordered dict with 'access' first
                                if 'access' not in value or value[
                                        'access'] != 'PRIVATE':
                                    new_value = OrderedDict()
                                    value['access'] = 'PRIVATE'

                                    # Add all other existing keys in alphabetical order
                                    for k in sorted(value.keys()):
                                        new_value[k] = value[k]

                                    view_data['propConfig'][key] = new_value
                                    modified = True
                                    custom_prop_count += 1
                                    print('--set access=PRIVATE for: %s' % key)

                    if modified:
                        update_count += 1
                        write_json_file(file_path, view_data)

    print("Updated %s custom properties in %s files in %s" %
          (custom_prop_count, update_count, target_folder))


def params_dump(target_folder, output_file):
    """Dump all parameters from view.json files in the target folder."""
    dump_data = {}
    files_dumped = 0

    for root, _, files in os.walk(target_folder):
        for view in files:
            if view == 'view.json':
                file_path = os.path.join(root, view)
                print('Processing %s' % file_path)
                view_data = read_json_file(file_path)
                if 'params' in view_data:
                    dump_data[file_path] = dict(view_data['params'])
                    files_dumped += 1
                    print('--dumped %d params' % len(dump_data[file_path]))

    print("Dumping %d files to %s" % (files_dumped, output_file))
    write_json_file(output_file, dump_data)
    print("Params dumped to %s" % output_file)


def params_load(input_file):
    """Load parameters from the specified file and inject them into Perspective views."""
    dump_data = read_json_file(input_file)

    for file_path, params in dump_data.items():
        view = read_json_file(file_path)
        view['params'] = params
        write_json_file(file_path, view)

    print("Params loaded from %s" % input_file)


def purge_value(value, depth=0):
    """Recursively purge values while maintaining structure."""
    if depth >= 4:
        return {} if isinstance(value, dict) else None

    if isinstance(value, dict):
        if value.get('$ts') is not None:  # Timestamp special case
            return None
        return {k: purge_value(v, depth + 1) for k, v in value.items()}
    elif isinstance(value, list):
        return [] if value else value
    elif isinstance(value, str):
        return ""
    elif isinstance(value, bool):
        return value
    return None


def params_purge(target_folder):
    """Purge all parameters from view.json files in the target folder."""
    update_count = 0
    for root, _, files in os.walk(target_folder):
        for view in files:
            if view == 'view.json':
                file_path = os.path.join(root, view)
                print('Processing %s' % file_path)
                view_data = read_json_file(file_path)

                if 'params' in view_data:
                    params = view_data['params']
                    param_list = {}

                    for key, value in list(params.items()):
                        if not key.startswith('_'):
                            param_list[key] = value
                            params[key] = purge_value(value)

                    for key, value in param_list.items():
                        print('--purged: %s (%s)' % (key, value))

                    if param_list:
                        update_count += 1
                        write_json_file(file_path, view_data)

    print("Params purged from %d files in %s" % (update_count, target_folder))


def format_json_files(target_folder):
    """Format all JSON files in the target folder, preserving Unicode escapes."""
    formatted_count = 0
    for root, _, files in os.walk(target_folder):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                print('Formatting %s' % file_path)
                try:
                    data = read_json_file(file_path)
                    write_json_file(file_path, data)
                    formatted_count += 1
                except json.JSONDecodeError:
                    print('Error: Unable to parse JSON in %s' % file_path)
                except (OSError, IOError) as e:
                    print('File error while formatting %s: %s', file_path,
                          str(e))
                except ValueError as e:
                    print('Value error in %s: %s', file_path, str(e))
    print("Formatted %d JSON files in %s" % (formatted_count, target_folder))


def cleanup_unused_props(target_folder):
    """Remove custom properties that only have access: PRIVATE configuration."""
    update_count = 0
    removed_props_count = 0

    for root, _, files in os.walk(target_folder):
        for view in files:
            if view == 'view.json':
                file_path = os.path.join(root, view)
                print('Processing %s' % file_path)
                view_data = read_json_file(file_path)

                if 'propConfig' in view_data:
                    modified = False
                    props_to_remove = []

                    for key, value in view_data['propConfig'].items():
                        if (key.startswith('custom.')
                                and isinstance(value, dict) and len(value) == 1
                                and 'access' in value
                                and value['access'] == 'PRIVATE'):
                            props_to_remove.append(key)

                    if props_to_remove:
                        for key in props_to_remove:
                            del view_data['propConfig'][key]
                            print('--removed unused prop: %s' % key)
                            removed_props_count += 1
                            modified = True

                    if modified:
                        update_count += 1
                        write_json_file(file_path, view_data)

    print("Removed %s unused custom properties from %s files in %s" %
          (removed_props_count, update_count, target_folder))


def main():
    if len(sys.argv) < 2 or '--help' in sys.argv:
        print(HELP_TEXT)
        sys.exit(0)

    actions = [action for action in sys.argv[1:] if action != '--help']

    for action in actions:
        if action == 'dump':
            params_dump(TARGET_FOLDER, DEV_PARAMS_PATH)
        elif action == 'load':
            params_load(DEV_PARAMS_PATH)
        elif action == 'purge':
            params_purge(TARGET_FOLDER)
        elif action == 'format':
            format_json_files(TARGET_FOLDER)
        elif action == '--set-private-access-modes':
            set_private_access_modes(TARGET_FOLDER)
        elif action == '--cleanup-props':
            cleanup_unused_props(TARGET_FOLDER)
        else:
            print("Unknown action: %s" % action)
            print("Use --help for usage information")


if __name__ == '__main__':
    main()
