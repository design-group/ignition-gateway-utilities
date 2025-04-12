#!/usr/bin/env python3
"""
This script manages parameters in view.json files for the frontend of Ignition Projects.

It supports dumping parameters to a file, loading them back, purging sensitive data,
formatting JSON files, setting private access modes, and cleaning up unused properties.

License: MIT (see LICENSE file in repository)
"""

import argparse
import json
import logging
import sys
import re
from collections import OrderedDict
from pathlib import Path

TARGET_FOLDER = Path("services/projects")
DEV_PARAMS_PATH = Path("services/env/dev-params.json")
UNICODE_REPLACEMENTS = {
	r"\\u003c": "UNICODE_LT",
	r"\\u003e": "UNICODE_GT",
	r"\\u0026": "UNICODE_AMP",
	r"\\u003d": "UNICODE_EQ",
	r"\\u0027": "UNICODE_APOS",
}
UNICODE_RESTORE = {v: k for k, v in UNICODE_REPLACEMENTS.items()}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)

HELP_TEXT = """
This script manages dump, load, and purge of parameters in Perspective Views of Ignition Projects.
Actions:
  --dump         Dump all parameters from view.json files into dev-params.json.
				 When the script runs, dev-params.json is loaded and new changes get appended to it.
				 dev-params.json should be updated before submitting a pull request.

  --load         Load all parameters from dev-params.json into all view.json files in frontend DanPT project.
				 This should be done before starting work on a new feature.

  --purge        Remove all parameters from all view.json files in frontend DanPT project.
				 --dump should be run before this action, so that dev-params.json is up-to-date with all parameters.
				 This action should be run before submitting a pull request.

  --format-files Format all JSON files in the target folder, preserving Unicode escapes.
				 This ensures consistent formatting across all JSON files.

Options:
  --set-private-access  Set access mode to "PRIVATE" for all custom properties in propConfig.
  --cleanup-props       Remove custom properties that only have access: PRIVATE configuration.

You can combine multiple actions and options in a single command, e.g.:
python3 view_param_editor.py --dump --purge --format-files
"""


def preserve_unicode_escapes(text):
	"""Preserve specific Unicode escapes in JSON content."""
	for escape, placeholder in UNICODE_REPLACEMENTS.items():
		text = re.sub(escape, placeholder, text)
	return text


def restore_unicode_escapes(text):
	"""Restore Unicode escapes from placeholders."""
	for placeholder, escape in UNICODE_RESTORE.items():
		# We need to use a raw string for the replacement to handle backslashes properly
		text = text.replace(placeholder, escape.replace('\\\\', '\\'))
	return text


def format_json(obj):
	"""Format JSON with 2-space indentation and no trailing whitespace.

	Args:
		obj: JSON-serializable object.

	Returns:
		str: Formatted JSON string.
	"""
	return json.dumps(obj, indent=2, ensure_ascii=False).rstrip()


def read_json_file(file_path):
	"""Read and parse a JSON file while preserving Unicode escapes.

	Args:
		file_path (Path): Path to the JSON file.

	Returns:
		OrderedDict: Parsed JSON data.

	Raises:
		SystemExit: If the file is not found or JSON is invalid.
	"""
	file_path = Path(file_path).resolve()
	try:
		with file_path.open("r", encoding="utf-8") as file:
			content = file.read()
			preserved_content = preserve_unicode_escapes(content)
			return json.loads(preserved_content, object_pairs_hook=OrderedDict)
	except FileNotFoundError:
		LOGGER.error(f"File not found: {file_path}")
		sys.exit(1)
	except json.JSONDecodeError as e:
		LOGGER.error(f"Invalid JSON in {file_path}: {e}")
		sys.exit(1)


def write_json_file(file_path, data):
	"""Write formatted JSON to a file, restoring Unicode escapes.

	Args:
		file_path (Path): Path to the JSON file.
		data: JSON-serializable object.

	Raises:
		SystemExit: If the file cannot be written.
	"""
	file_path = Path(file_path).resolve()
	try:
		# Ensure the parent directory exists
		file_path.parent.mkdir(parents=True, exist_ok=True)

		formatted_json = format_json(data)
		restored_content = restore_unicode_escapes(formatted_json)
		with file_path.open("w", encoding="utf-8", newline="\n") as file:
			file.write(restored_content)
	except (OSError, IOError) as e:
		LOGGER.error(f"Failed to write {file_path}: {e}")
		sys.exit(1)


def set_private_access(target_folder):
	"""Set access mode to PRIVATE for all custom properties in propConfig.

	Args:
		target_folder (Path): Directory containing view.json or props.json files.
	"""
	update_count = 0
	custom_prop_count = 0

	for file_path in target_folder.rglob("*.[view|props].json"):
		LOGGER.info(f"Processing {file_path}")
		view_data = read_json_file(file_path)

		if "propConfig" in view_data:
			modified = False
			for key, value in view_data["propConfig"].items():
				if key.startswith("custom") and isinstance(value, dict):
					if "access" not in value or value["access"] != "PRIVATE":
						new_value = OrderedDict([("access", "PRIVATE")])
						for k in sorted(value.keys()):
							new_value[k] = value[k]
						view_data["propConfig"][key] = new_value
						modified = True
						custom_prop_count += 1
						LOGGER.info(f"Set access=PRIVATE for: {key}")

			if modified:
				update_count += 1
				write_json_file(file_path, view_data)

	LOGGER.info(f"Updated {custom_prop_count} custom properties in {update_count} files in {target_folder}")


def params_dump(target_folder, output_file):
	"""Dump parameters from view.json files to the output file.

	Args:
		target_folder (Path): Directory containing view.json files.
		output_file (Path): Path to the output JSON file.
	"""
	# Initialize dump_data with existing data if file exists
	dump_data = {}
	if output_file.exists():
		try:
			dump_data = read_json_file(output_file)
		except (json.JSONDecodeError, OSError) as e:
			LOGGER.warning(f"Could not read existing {output_file}: {e}")
			LOGGER.info(f"Creating new {output_file}")

	files_dumped = 0

	for file_path in target_folder.rglob("view.json"):
		LOGGER.info(f"Processing {file_path}")
		view_data = read_json_file(file_path)
		if "params" in view_data:
			dump_data[str(file_path)] = dict(view_data["params"])
			files_dumped += 1
			LOGGER.info(f"Dumped {len(dump_data[str(file_path)])} params")

	LOGGER.info(f"Dumping {files_dumped} files to {output_file}")
	write_json_file(output_file, dump_data)
	LOGGER.info(f"Params dumped to {output_file}")


def params_load(input_file):
	"""Load parameters from the input file into view.json files.

	Args:
		input_file (Path): Path to the input JSON file.

	Raises:
		SystemExit: If the input file does not exist.
	"""
	input_file = Path(input_file).resolve()
	if not input_file.exists():
		LOGGER.error(f"Input file not found: {input_file}")
		sys.exit(1)

	dump_data = read_json_file(input_file)
	for file_path, params in dump_data.items():
		file_path = Path(file_path)
		if not file_path.exists():
			LOGGER.warning(f"Skipping {file_path}: file not found")
			continue
		view_data = read_json_file(file_path)
		view_data["params"] = params
		write_json_file(file_path, view_data)
		LOGGER.info(f"Loaded params into {file_path}")

	LOGGER.info(f"Params loaded from {input_file}")


def purge_value(value):
	"""Recursively purge sensitive data while preserving structure.

	Args:
		value: Data to purge.

	Returns:
		Purified data with sensitive values removed.
	"""
	if isinstance(value, dict):
		if value.get("$ts") is not None:
			return None
		return {k: purge_value(v) for k, v in value.items()}
	elif isinstance(value, list):
		return []
	elif isinstance(value, str):
		return ""
	elif isinstance(value, bool):
		return value
	return None


def params_purge(target_folder):
	"""Purge parameters from view.json files.

	Args:
		target_folder (Path): Directory containing view.json files.
	"""
	update_count = 0
	for file_path in target_folder.rglob("view.json"):
		LOGGER.info(f"Processing {file_path}")
		view_data = read_json_file(file_path)

		if "params" in view_data:
			params = view_data["params"]
			param_list = {k: v for k, v in params.items() if not k.startswith("_")}

			for key, value in param_list.items():
				params[key] = purge_value(value)
				LOGGER.info(f"Purged: {key} ({value})")

			if param_list:
				update_count += 1
				write_json_file(file_path, view_data)

	LOGGER.info(f"Params purged from {update_count} files in {target_folder}")


def format_json_files(target_folder):
	"""Format all JSON files in the target folder.

	Args:
		target_folder (Path): Directory containing JSON files.
	"""
	files_processed = 0
	formatted_count = 0
	for file_path in target_folder.rglob("*.json"):
		files_processed += 1
		LOGGER.info(f"Formatting {file_path}")
		try:
			data = read_json_file(file_path)
			write_json_file(file_path, data)
			formatted_count += 1
		except (json.JSONDecodeError, OSError, ValueError) as e:
			LOGGER.error(f"Failed to format {file_path}: {e}")

	LOGGER.info(f"Processed {files_processed} files")
	LOGGER.info(f"Formatted {formatted_count} JSON files in {target_folder}")


def cleanup_unused_props(target_folder):
	"""Remove custom properties with only PRIVATE access configuration.

	Args:
		target_folder (Path): Directory containing view.json files.
	"""
	files_processed = 0
	update_count = 0
	removed_props_count = 0

	for file_path in target_folder.rglob("view.json"):
		files_processed += 1
		LOGGER.info(f"Processing {file_path}")
		view_data = read_json_file(file_path)

		if "propConfig" in view_data:
			props_to_remove = []
			for key, value in view_data["propConfig"].items():
				if (
					key.startswith("custom.") and isinstance(value, dict) and len(value) == 1 and
					value.get("access") == "PRIVATE"
				):
					props_to_remove.append(key)

			if props_to_remove:
				for key in props_to_remove:
					del view_data["propConfig"][key]
					LOGGER.info(f"Removed unused prop: {key}")
					removed_props_count += 1
				update_count += 1
				write_json_file(file_path, view_data)
	LOGGER.info(f"Processed {files_processed} files")
	LOGGER.info(f"Removed {removed_props_count} unused custom properties from {update_count} files in {target_folder}")


def parse_args():
	"""Parse command-line arguments."""
	parser = argparse.ArgumentParser(description=HELP_TEXT, formatter_class=argparse.RawTextHelpFormatter)
	actions_group = parser.add_argument_group("Actions")
	options_group = parser.add_argument_group("Options")

	actions_group.add_argument(
		"--dump",
		action="store_true",
		help="Dump view parameters from view.json files to dev-params.json.",
	)
	actions_group.add_argument(
		"--load",
		action="store_true",
		help="Load view parameters from dev-params.json to view.json files.",
	)
	actions_group.add_argument(
		"--purge",
		action="store_true",
		help="Purge view parameters from view.json files.",
	)
	actions_group.add_argument(
		"--format-files",
		action="store_true",
		help="Format JSON files in the target folder.",
	)

	options_group.add_argument(
		"--set-private-access",
		action="store_true",
		help="Set access mode to PRIVATE for custom properties.",
	)
	options_group.add_argument(
		"--cleanup-props",
		action="store_true",
		help="Remove unused custom properties with only PRIVATE access.",
	)

	return parser


def main():
	"""Execute the script based on command-line arguments."""
	parser = parse_args()
	args = parser.parse_args()

	try:
		# Execute actions based on flags
		if args.dump:
			params_dump(TARGET_FOLDER, DEV_PARAMS_PATH)
		if args.load:
			params_load(DEV_PARAMS_PATH)
		if args.purge:
			params_purge(TARGET_FOLDER)
		if args.format_files:
			format_json_files(TARGET_FOLDER)
		if args.set_private_access:
			set_private_access(TARGET_FOLDER)
		if args.cleanup_props:
			cleanup_unused_props(TARGET_FOLDER)

	except KeyboardInterrupt:
		LOGGER.info("Operation cancelled by user.")
		sys.exit(1)
	except Exception as e:
		LOGGER.error(f"An error occurred: {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
