# View Parameter Editor

A utility script for managing parameters in Ignition Perspective view.json files.

## Overview

This script helps manage the development workflow for Ignition Perspective views by providing tools to:

- Dump parameters from view.json files to a centralized file
- Load parameters from a centralized file back into view.json files
- Purge sensitive data from view.json files before committing
- Format JSON files consistently
- Set private access modes for custom properties
- Clean up unused properties

## Installation

No installation required. Simply download the script and run it using Python 3.

## Usage

```bash
python3 view_param_editor.py [options]
```

### Actions

The script supports the following actions:

- `--dump`: Dump all parameters from view.json files into dev-params.json
  - When the script runs, dev-params.json is loaded and new changes get appended to it
  - dev-params.json should be updated before submitting a pull request

- `--load`: Load all parameters from dev-params.json into all view.json files
  - This should be done before starting work on a new feature

- `--purge`: Remove all parameters from all view.json files
  - `--dump` should be run before this action, so that dev-params.json is up-to-date
  - This action should be run before submitting a pull request

- `--format-files`: Format all JSON files in the target folder, preserving Unicode escapes
  - This ensures consistent formatting across all JSON files

### Options

- `--set-private-access`: Set access mode to "PRIVATE" for all custom properties in propConfig
- `--cleanup-props`: Remove custom properties that only have access: PRIVATE configuration

### Examples

You can combine multiple actions and options in a single command:

```bash
python3 view_param_editor.py --dump --purge --format-files
```

## How It Works

### Parameter Management

The script manages parameters in view.json files, which are used by Ignition Perspective views. These parameters can contain sensitive information that shouldn't be committed to version control. The script provides a workflow to:

1. Dump parameters to a separate file for local development
2. Purge sensitive data before committing changes
3. Load parameters back when needed

### Unicode Handling

The script includes special handling for Unicode escape sequences commonly found in Ignition JSON files:
- Preserves specific Unicode escapes during processing
- Restores them when writing files back

### File Structure

The script expects the following file structure:
- Target folder: `services/projects`
- Development parameters file: `services/env/dev-params.json`

## Development Workflow

A typical development workflow using this script would be:

1. Before starting work: `python3 view_param_editor.py --load`
2. Make changes to your Perspective views in Ignition Designer
3. Before committing: `python3 view_param_editor.py --dump --purge`
4. Commit your changes (without sensitive parameter data)

## Requirements

- Python 3.x
- Ignition Perspective view.json files

## License

MIT (see LICENSE file in repository)